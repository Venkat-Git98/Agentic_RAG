import os
import asyncio
import cohere
import logging
from typing import List, Dict, Any

class Reranker:
    """A wrapper for the Cohere Rerank API."""

    def __init__(self, api_key: str = None):
        """
        Initializes the Cohere async client.
        """
        api_key = api_key or os.getenv("COHERE_API_KEY") or os.getenv("COHERE_API")
        if not api_key:
            raise ValueError("Cohere API key not found. Please set COHERE_API_KEY or COHERE_API in your .env file.")
        
        # Note: The user mentioned COHERE_API, so we check for both.
        # The V2 client is now the standard async client.
        self.client = cohere.AsyncClient(api_key)
        logging.info("Cohere Reranker client initialized.")

    async def rerank(self, query: str, documents: List[Dict[str, Any]], top_n: int = 3) -> List[Dict[str, Any]]:
        """
        Reranks a list of documents against a query.

        Args:
            query: The search query.
            documents: A list of document dictionaries. Each dict must have a 'text' key.
            top_n: The number of top documents to return.

        Returns:
            A sorted list of the top N documents.
        """
        if not documents:
            return []
        
        logging.info(f"Reranking {len(documents)} documents for query: '{query[:50]}...'")
        
        try:
            # Perform the reranking.
            api_response = await self.client.rerank(
                model="rerank-english-v3.0",
                query=query,
                documents=documents, # Pass the list of dicts
                top_n=top_n,
                return_documents=True
            )

            # The API response contains the documents in the new sorted order.
            # Let's be defensive and explicitly convert to a list of dicts.
            sorted_docs = []
            for r in api_response.results:
                # r.document is the original dictionary we passed in.
                sorted_docs.append(dict(r.document))
            
            logging.info(f"Reranking complete. Returned {len(sorted_docs)} documents.")
            return sorted_docs

        except Exception as e:
            logging.error(f"Cohere rerank call failed: {e}")
            # Fallback: if reranking fails, return the original top_n documents to avoid crashing the flow.
            return documents[:top_n]

async def _rerank_batch(reranker: Reranker, query: str, documents: List[Dict[str, Any]], top_n: int) -> List[Dict[str, Any]]:
    """Helper for running a single rerank task."""
    return await reranker.rerank(query=query, documents=documents, top_n=top_n)

def run_parallel_rerank(query_doc_map: Dict[str, List[Dict[str, Any]]], top_n: int = 3) -> Dict[str, List[Dict[str, Any]]]:
    """
    Reruns multiple sets of documents for multiple queries in parallel.
    
    Args:
        query_doc_map: A dictionary where keys are queries and values are lists of documents.
        top_n: The number of top documents to return for each query.

    Returns:
        A dictionary with the same keys but with reranked document lists as values.
    """
    reranker = Reranker()

    async def main():
        tasks = []
        for query, docs in query_doc_map.items():
            tasks.append(_rerank_batch(reranker, query, docs, top_n))
        
        results = await asyncio.gather(*tasks)
        
        reranked_map = {}
        for query, reranked_docs in zip(query_doc_map.keys(), results):
            reranked_map[query] = reranked_docs
        
        return reranked_map

    # This is the standard way to run an async main function from a sync context.
    return asyncio.run(main()) 