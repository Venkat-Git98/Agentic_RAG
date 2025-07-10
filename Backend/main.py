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
from typing import Optional, Dict

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MainApp")
USER_THREAD_ID = "_personal_portfolio_session_uuid_01"

# --- Imports ---
from conversation_manager import ConversationManager
from thinking_workflow import ThinkingAgenticWorkflow, create_thinking_agentic_workflow
from thinking_logger import ThinkingMode
from config import redis_client

class LangGraphAgenticAI:
    """
    Main application class for the LangGraph Agentic AI system.
    """
    def __init__(self, debug: bool = False, detailed_thinking: bool = False):
        self.debug = debug
        self.thinking_mode = ThinkingMode.DETAILED if detailed_thinking else ThinkingMode.SIMPLE
        mode_desc = "detailed" if detailed_thinking else "simple"
        logger.info(f"🧠 LangGraph Agentic AI initialized (debug={debug}, mode={mode_desc})")
    
    async def query(self, user_query: str, thread_id: str, initial_state: Optional[Dict] = None) -> str:
        """
        Processes a single query through the agentic workflow.
        """
        logger.info(f"🧠 Processing query for thread '{thread_id}': {user_query[:100]}...")
        
        conversation_manager = ConversationManager(thread_id, redis_client, initial_state=initial_state)
        context_payload = conversation_manager.get_contextual_payload()
        
        workflow_instance = create_thinking_agentic_workflow(
            debug=self.debug,
            thinking_mode=True,
            thinking_detail_mode=self.thinking_mode
        )
        
        final_state = await workflow_instance.run(
            user_query=user_query,
            context_payload=context_payload,
            conversation_manager=conversation_manager,
            thread_id=thread_id
        )
        
        response = final_state.get("response", "No response generated.")
        
        conversation_manager.add_user_message(user_query)
        conversation_manager.add_assistant_message(response)
        
        return response
    
    async def interactive_mode(self):
        """
        Runs the system in an interactive command-line mode.
        """
        print("\n" + "="*60)
        print("🧠 LangGraph Agentic AI - Interactive Mode")
        print("="*60)
        print("Type 'quit' or 'exit' to end the conversation.")
        
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ['quit', 'exit']:
                print("👋 Goodbye!")
                break
            if not user_input:
                continue
                
            print("🤔 Processing...", end="", flush=True)
            response = await self.query(user_input, USER_THREAD_ID)
            print("\r" + " "*15 + "\r", end="")
            print(f"AI: {response}\n")
                
def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Run the LangGraph Agentic AI.")
    parser.add_argument('--query', type=str, help='A single user query to process.')
    parser.add_argument('--thread_id', type=str, help='The conversation thread ID.')
    parser.add_argument('--initial_state', type=str, help='A JSON string for the initial state.')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode.')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging.')
    parser.add_argument('--detailed', action='store_true', help='Enable detailed thinking mode.')
    
    args = parser.parse_args()
    
    ai_system = LangGraphAgenticAI(debug=args.debug, detailed_thinking=args.detailed)
    
    if args.interactive:
        asyncio.run(ai_system.interactive_mode())
    elif args.query:
        thread_id = args.thread_id or f"test_session_{uuid4()}"
        initial_state = {}
        if args.initial_state:
            try:
                initial_state = json.loads(args.initial_state)
            except json.JSONDecodeError:
                logger.warning("Could not parse --initial_state JSON. Starting fresh.")

        response = asyncio.run(ai_system.query(
            user_query=args.query, 
            thread_id=thread_id, 
            initial_state=initial_state
        ))
        print(response)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 