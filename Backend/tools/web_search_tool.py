import os
import requests
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
    API_URL = "https://api.tavily.com/search"

    def __init__(self):
        """
        Initializes the Tavily client, retrieving the API key from environment variables.
        """
        super().__init__()
        self.api_key = os.getenv("TAVILY_API_KEY") or os.getenv("TAVILY_API")
        if not self.api_key:
            logging.error("TAVILY_API_KEY or TAVILY_API environment variable not found.")
            raise ValueError("TAVILY_API_KEY or TAVILY_API is not set in the environment.")

    def __call__(self, query: str) -> Dict[str, str]:
        """
        Executes the advanced search and formats the results.
        """
        if not query:
            return {"answer": "Error: The search query cannot be empty.", "retrieval_method": "web_search_error"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "search_depth": "advanced",
            "include_answer": True,
            "max_results": 5,
        }

        try:
            logging.info(f"Executing direct Tavily API call for query: '{query}'")
            response = requests.post(self.API_URL, headers=headers, json=payload)
            response.raise_for_status()  # Will raise an HTTPError for bad responses (4xx or 5xx)
            
            data = response.json()
            answer = data.get("answer", "No answer provided.")
            results = data.get("results", [])
            
            formatted_results = f"Search Answer: {answer}\\n\\n"
            formatted_results += "Search Results:\\n"
            if not results:
                formatted_results += "No search results found."
            
            for result in results:
                formatted_results += f"- Title: {result.get('title', 'N/A')}\\n"
                formatted_results += f"  URL: {result.get('url', 'N/A')}\\n"
                formatted_results += f"  Content: {result.get('content', 'N/A')}\\n\\n"

            return {"answer": formatted_results, "retrieval_method": "web_search"}

        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP error occurred during Tavily search: {e.response.text}")
            return {"answer": f"Error: Failed to execute search due to: {e.response.text}", "retrieval_method": "web_search_error"}
        except Exception as e:
            logging.error(f"An error occurred during Tavily search: {e}")
            return {"answer": f"Error: Failed to execute search due to: {e}", "retrieval_method": "web_search_error"}