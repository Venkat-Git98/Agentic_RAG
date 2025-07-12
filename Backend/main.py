"""
Main entry point for the LangGraph Agentic AI System.
"""

import sys
import os
import asyncio
import argparse
import json
from uuid import uuid4
import logging
from typing import Optional, Dict, AsyncGenerator, Any
from datetime import datetime

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MainApp")

# --- Imports ---
from conversation_manager import ConversationManager
from thinking_workflow import ThinkingAgenticWorkflow, create_thinking_agentic_workflow
from thinking_logger import ThinkingMode
from config import redis_client
from state import create_initial_state

class LangGraphAgenticAI:
    """Main class for the LangGraph Agentic AI system."""

    def __init__(self, debug: bool = False):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"🧠 LangGraph Agentic AI instance created (debug={debug}).")
        self.debug = debug
        self.workflow = create_thinking_agentic_workflow(
            debug=self.debug,
            thinking_mode=True,
            thinking_detail_mode=ThinkingMode.SIMPLE
        )
        self.app = self.workflow.app

    async def get_response_stream(self, user_query: str, thread_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Get a streaming response from the agentic AI.
        Args:
            user_query: The user's query.
            thread_id: The unique identifier for the conversation thread.
        Yields:
            A stream of dictionaries representing parts of the response.
        """
        initial_state = create_initial_state(user_query, "", None, thread_id)

        config = {
            "configurable": {
                "thread_id": thread_id,
                "metadata": {
                    "user_id": thread_id,
                    "trace_source": "production_api",
                    "timestamp_utc": datetime.utcnow().isoformat()
                }
            }
        }

        async for chunk in self.app.astream(initial_state, config=config):
            if "final_answer" in chunk:
                yield {"final_answer": chunk["final_answer"]}
            elif "response" in chunk:
                yield {"response": chunk["response"]}

async def interactive_main():
    """Async main execution function for interactive mode."""
    print("🤖 LangGraph Agentic AI - Interactive Mode")
    ai = LangGraphAgenticAI()
    
    while True:
        try:
            user_query = input("You: ")
            if user_query.lower() in ["exit", "quit"]:
                break
            
            thread_id = f"interactive_session_{uuid4().hex}"
            response = ""
            print("AI: ", end="", flush=True)

            async for chunk in ai.get_response_stream(user_query, thread_id):
                if chunk.get("final_answer"):
                    response = chunk.get("final_answer")

            print(f"\r{response}\n")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            logger.error("Error in interactive loop", exc_info=True)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Run the LangGraph Agentic AI.")
    parser.add_argument('--query', type=str, help='A single user query to process.')
    parser.add_argument('--thread_id', type=str, help='The conversation thread ID.')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode.')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging.')
    
    args = parser.parse_args()
    
    if args.interactive:
        asyncio.run(interactive_main())
    elif args.query:
        ai_system = LangGraphAgenticAI(debug=args.debug)
        thread_id = args.thread_id or f"test_session_{uuid4()}"
        
        async def run_query():
            response = ""
            async for chunk in ai_system.get_response_stream(args.query, thread_id):
                 if chunk.get("final_answer"):
                    response = chunk.get("final_answer")
            print(response)

        asyncio.run(run_query())
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 