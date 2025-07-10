"""
Implements the focused HyDE (Hypothetical Document Embedding) Tool.
"""
import logging
import json
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from react_agent.base_tool import BaseTool
from config import TIER_1_MODEL_NAME
import re

# Configure logging
logging.basicConfig(level=logging.INFO)

class HydeTool(BaseTool):
    """
    A tool that generates a hypothetical document for a given sub-query.
    This tool is triggered by the HydeAgent for each step in the research plan.
    """

    @property
    def name(self) -> str:
        return "generate_hypothetical_document"

    @property
    def description(self) -> str:
        return (
            "For a given sub-query, generates a hypothetical document that reads as if "
            "it were an excerpt from the Virginia Building Code. This document is used "
            "to improve the accuracy of semantic search."
        )

    def __init__(self):
        """Initializes the HydeTool."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def __call__(self, sub_query: str) -> str:
        """
        Executes the HyDE generation logic.
        """
        logging.info(f"Generating HyDE document for sub-query: '{sub_query[:100]}...'")

        # This prompt is highly specialized for generating code-like documents.
        HYDE_PROMPT = """
You are a seasoned building code expert and technical writer for the state of Virginia.
Your sole task is to generate a hypothetical document that looks and reads *exactly* like an excerpt from the official Virginia Building Code.

**Your Persona & Style:**
- **Formal and Regulatory:** Use precise, formal, and unambiguous language.
- **Authoritative Tone:** Employ terms like "shall," "is permitted," "is required," and "in accordance with Section X.X."
- **Structure:** Mimic the hierarchical structure of code documents (e.g., "Section 1604.3.1 stipulates...").
- **Technical Detail:** Be specific. Mention technical terms, standards, and conditions relevant to the query.

**The User's Sub-Query:**
"{sub_query}"

**Your Task:**
Based on the sub-query, write a concise, single-paragraph hypothetical document. This document should represent the *ideal* passage from the building code that would perfectly answer the sub-query.

**Example:**
- **Sub-Query:** "What are the minimum width and height requirements for an exit door in a commercial building?"
- **Your Document:** "Section 1005.1 of the Virginia Building Code specifies the dimensional requirements for means of egress. All exit doors in commercial occupancies shall have a minimum clear width of 32 inches and a minimum height of 80 inches. The clear width shall be measured from the face of the door to the stop, with the door open 90 degrees. These requirements are intended to ensure unobstructed passage during an emergency evacuation."

**Your Hypothetical Document (single paragraph, text only):**
"""
        try:
            model = genai.GenerativeModel(TIER_1_MODEL_NAME)
            prompt = HYDE_PROMPT.format(sub_query=sub_query)
            
            response = model.generate_content(prompt)
            hyde_document = response.text.strip()
            
            # Basic cleanup
            if hyde_document.startswith('"') and hyde_document.endswith('"'):
                hyde_document = hyde_document[1:-1]

            self.logger.info(f"Successfully generated HyDE document.")
            return hyde_document

        except Exception as e:
            self.logger.error(f"Error during HyDE document generation: {e}", exc_info=True)
            # Fallback to a simple statement if generation fails.
            return f"A section of the Virginia Building Code that discusses the requirements related to: {sub_query}" 