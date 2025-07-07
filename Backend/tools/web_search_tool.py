import os
from tavily import TavilyClient
from react_agent.base_tool import BaseTool
import logging
from typing import Dict

class TavilySearchTool(BaseTool):
    """
    A tool to perform advanced web searches using the Tavily API.
    """
    name = "tavily_web_search"
    description = (
        "Performs an advanced web search using the Tavily API to find up-to-date information or "
        "to find information not available in the internal knowledge base. "
        "Input should be a concise, targeted search query."
    )

    def __init__(self):
        """
        Initializes the Tavily client, retrieving the API key from environment variables.
        """
        super().__init__()
        # The user has specified the API key is in the .env file under TAVILY_API
        # TavilyClient automatically reads this from the environment if not passed directly.
        tavily_api_key = os.getenv("TAVILY_API")
        if not tavily_api_key:
            logging.error("TAVILY_API environment variable not found.")
            raise ValueError("TAVILY_API is not set in the environment.")
        self.client = TavilyClient(api_key=tavily_api_key)

    def __call__(self, query: str) -> Dict[str, str]:
        """
        Executes the advanced search and formats the results.

        Args:
            query: The search query to execute.

        Returns:
            A dictionary containing the search answer and the retrieval method.
        """
        if not query:
            return {
                "answer": "Error: The search query cannot be empty.",
                "retrieval_method": "web_search_error"
            }

        try:
            logging.info(f"Executing Tavily search for query: '{query}'")
            # Using the advanced search parameters as requested.
            response = self.client.search(
                query=query,
                search_depth="advanced",
                include_answer=True,  # include_answer gives the AI-generated answer
                max_results=5
            )

            # Format the response for the agent
            answer = response.get("answer", "No answer provided.")
            results = response.get("results", [])
            
            formatted_results = f"Search Answer: {answer}\n\n"
            formatted_results += "Search Results:\n"
            if not results:
                formatted_results += "No search results found."
            
            for result in results:
                formatted_results += f"- Title: {result.get('title', 'N/A')}\\n"
                formatted_results += f"  URL: {result.get('url', 'N/A')}\\n"
                formatted_results += f"  Content: {result.get('content', 'N/A')}\\n\\n"

            return {
                "answer": formatted_results,
                "retrieval_method": "web_search"
            }

        except Exception as e:
            logging.error(f"An error occurred during Tavily search: {e}")
            return {
                "answer": f"Error: Failed to execute search due to: {e}",
                "retrieval_method": "web_search_error"
            }