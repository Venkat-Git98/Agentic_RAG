import logging
import re
from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field

from tools.neo4j_connector import Neo4jConnector
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from config import TIER_2_MODEL_NAME

# --- Pydantic Models for Structured LLM Output ---

class LuceneQuery(BaseModel):
    """Pydantic model for the structured Lucene query."""
    reasoning: str = Field(description="Brief reasoning for the chosen keywords and structure.")
    query: str = Field(description="The structured Lucene query string. Use + for mandatory terms.")

# --- Prompts ---

LUCENE_PROMPT = """
You are an expert in search query optimization. Your task is to convert a user's natural language question
into a structured Lucene query for a full-text search index.

The index contains documents about the Virginia Building Code. Focus on extracting the most
critical and specific technical terms.

RULES:
1.  Identify the core, non-negotiable keywords.
2.  Prefix mandatory keywords with a `+` sign.
3.  Combine terms with `AND` or `OR` where appropriate, though using `+` for each key term is often sufficient.
4.  Keep the query concise and focused. Do not include conversational filler.
5.  If the query contains a specific section number (e.g., '1607.12.1'), include it as a mandatory term.
6.  You MUST format your response as a JSON object with "reasoning" and "query" keys.

EXAMPLE:
User Question: What are the live load requirements for office building floors?
{{
  "reasoning": "The user is asking for specific requirements for 'live load' on 'office building' floors. These are the critical terms.",
  "query": "+live +load +office +building +floors"
}}

User Question:
{user_query}
"""

class KeywordRetrievalTool(BaseTool):
    """
    A tool to perform an optimized, relevance-scored keyword search against the 
    Neo4j database using its native full-text search capabilities.
    """
    name: str = "keyword_search"
    description: str = (
        "Performs a relevance-scored keyword search for a query within the knowledge base. "
        "Useful for finding specific terms or concepts when semantic search is too broad. "
        "Input should be a natural language query."
    )
    
    # Declare class fields for Pydantic
    llm: Optional[ChatGoogleGenerativeAI] = Field(default=None, exclude=True)
    parser: Optional[JsonOutputParser] = Field(default=None, exclude=True)
    prompt: Optional[ChatPromptTemplate] = Field(default=None, exclude=True)
    chain: Optional[Any] = Field(default=None, exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, llm_model_name: str = TIER_2_MODEL_NAME, **kwargs):
        super().__init__(**kwargs)
        self.llm = ChatGoogleGenerativeAI(model=llm_model_name, temperature=0.0)
        self.parser = JsonOutputParser(pydantic_object=LuceneQuery)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", LUCENE_PROMPT),
            ("user", "{user_query}")
        ])
        self.chain = self.prompt | self.llm | self.parser

    async def _generate_lucene_query_from_llm(self, query: str) -> str:
        """
        Uses an LLM to convert a natural language query into a structured Lucene query.
        """
        logging.info(f"Generating Lucene query for: '{query}'")
        try:
            result = await self.chain.ainvoke({"user_query": query})
            logging.info(f"LLM generated Lucene query: {result['query']} (Reasoning: {result['reasoning']})")
            return result['query']
        except Exception as e:
            logging.error(f"Failed to generate Lucene query from LLM: {e}")
            # Fallback to a simple keyword extraction if the LLM fails
            return " ".join(re.findall(r'\b\w+\b', query.lower()))

    def _execute_fulltext_search(self, lucene_query: str) -> List[Dict[str, Any]]:
        """
        Executes a full-text search against the pre-defined Neo4j indexes.
        """
        if not lucene_query or lucene_query.strip().upper() == "N/A":
            logging.warning(f"Skipping full-text search for invalid query: '{lucene_query}'")
            return []
            
        # Query both indexes and combine results, prioritizing the more specific passage index
        cypher_query = """
        CALL db.index.fulltext.queryNodes('passage_content_idx', $query) YIELD node, score
        RETURN node.content AS text, score
        UNION ALL
        CALL db.index.fulltext.queryNodes('knowledge_base_text_idx', $query) YIELD node, score
        RETURN node.text AS text, score
        ORDER BY score DESC
        LIMIT 10
        """
        
        try:
            logging.info(f"Executing full-text search with query: '{lucene_query}'")
            results = Neo4jConnector.execute_query(cypher_query, {"query": lucene_query})
            
            # The result from the driver is a list of Record objects
            # We need to convert them to a list of dictionaries
            return [record.data() for record in results] if results else []
        except Exception as e:
            logging.error(f"Full-text search failed: {e}")
            return []

    def _run(self, query: str, run_manager: CallbackManagerForToolRun = None) -> str:
        """
        Use the tool. This is the abstract method required by BaseTool.
        """
        # Since _run is expected to be sync by BaseTool, we need to run the async method
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.__call__(query))
        except RuntimeError:
            # If no event loop is running, create a new one
            return asyncio.run(self.__call__(query))

    async def __call__(self, query: str) -> str:
        """
        The main entry point for the tool (now async).
        """
        # Step 1: Generate a structured Lucene query from the natural language input
        lucene_query = await self._generate_lucene_query_from_llm(query)
        if not lucene_query or lucene_query.strip().upper() == 'N/A':
            logging.warning(f"Invalid Lucene query generated for '{query}'. Aborting keyword search.")
            return "Could not generate a valid search query."

        # Step 2: Execute the full-text search
        search_results = self._execute_fulltext_search(lucene_query)

        if not search_results:
            return f"No results found for query: '{query}' (Lucene: '{lucene_query}')."

        # Step 3: Format and return the results
        formatted_results = [
            f"Result (Score: {result['score']:.2f}):\n{result['text']}"
            for result in search_results
            if result.get('text')
        ]
        
        final_context = "\n\n---\n\n".join(formatted_results)
        logging.info(f"Keyword search completed. Returning {len(final_context)} characters of context.")
        
        return final_context 