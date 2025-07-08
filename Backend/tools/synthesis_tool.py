"""
Implements the Synthesis Tool for the ReAct Agent.
"""
import logging
import google.generativeai as genai
from typing import List, Dict, Any
from react_agent.base_tool import BaseTool
from config import TIER_1_MODEL_NAME
from prompts import SYNTHESIS_PROMPT

class SynthesisTool(BaseTool):
    """
    A tool to synthesize a final answer from a collection of pre-answered sub-queries.
    """

    @property
    def name(self) -> str:
        return "synthesize_final_answer"

    @property
    def description(self) -> str:
        return (
            "Takes the original user query and a list of sub-query answers to generate a "
            "comprehensive, well-structured, and cited final answer. Use this as the "
            "last step before calling the 'finish' tool. "
            "Input: {'original_query': 'The query that started the research.', 'current_query': 'The user's most recent follow-up question.', 'sub_answers': [ ... ]}"
        )

    def _format_sub_answers_for_prompt(self, sub_answers: List[Dict[str, Any]]) -> str:
        """
        Formats the list of sub-answers into a readable string for the LLM prompt.
        """
        formatted_string = ""
        for i, sub_answer in enumerate(sub_answers):
            query = sub_answer.get('sub_query', 'N/A')
            answer = sub_answer.get('answer', 'N/A')
            
            formatted_string += f"--- Sub-Answer for Query: {query} ---\n"
            formatted_string += f"{answer}\n\n"
        return formatted_string

    def __call__(self, original_query: str, current_query: str, sub_answers: List[Dict[str, Any]]) -> dict:
        """
        Executes the synthesis logic.
        """
        logging.info(f"Executing Synthesis Tool. Processing {len(sub_answers)} sub-answers for query: '{original_query}'")
        try:
            model = genai.GenerativeModel(TIER_1_MODEL_NAME)
            
            # Use a helper to format the sub-answers to be more readable for the LLM
            sub_answers_str = self._format_sub_answers_for_prompt(sub_answers)

            prompt = SYNTHESIS_PROMPT.format(
                original_user_query=original_query,
                current_user_query=current_query,
                sub_answers_text=sub_answers_str
            )
            
            response = model.generate_content(prompt)
            final_answer = response.text.strip()
            
            logging.info("Synthesis complete.")
            return {"final_answer": final_answer}
        except Exception as e:
            logging.error(f"Error in SynthesisTool: {e}", exc_info=True)
            return {"final_answer": f"An error occurred during synthesis: {str(e)}"} 