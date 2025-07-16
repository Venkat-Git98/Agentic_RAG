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

# --- Early Configuration Loading ---
# This is critical to ensure all environment variables are loaded from the .env
# file before any other module tries to access them.
from config import redis_client
# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MainApp")

# --- Imports ---
from core.conversation_manager import ConversationManager
from core.thinking_workflow import ThinkingAgenticWorkflow, create_thinking_agentic_workflow
from core.thinking_logger import ThinkingMode
from core.cognitive_flow import CognitiveFlowLogger
from core.state import create_initial_state

class LangGraphAgenticAI:
    """Main class for the LangGraph Agentic AI system."""

    def __init__(self, debug: bool = False, thinking_detail_mode: ThinkingMode = ThinkingMode.SIMPLE):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"🧠 LangGraph Agentic AI instance created (debug={debug}).")
        self.debug = debug
        
        self.cognitive_flow_queue = asyncio.Queue()
        cognitive_flow_logger = CognitiveFlowLogger(self.cognitive_flow_queue)
        
        self.workflow = create_thinking_agentic_workflow(
            debug=self.debug,
            thinking_mode=True,
            thinking_detail_mode=thinking_detail_mode,
            cognitive_flow_logger=cognitive_flow_logger
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
        # Create ConversationManager for this thread, passing the actual redis_client
        conversation_manager = ConversationManager(thread_id, redis_client=redis_client)
        
        # Add the user message to conversation history
        conversation_manager.add_user_message(user_query)
        
        # Get context payload from conversation manager
        context_payload = conversation_manager.get_contextual_payload()
        
        initial_state = create_initial_state(user_query, context_payload, conversation_manager, debug_mode=self.debug)

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

        async def _run_workflow():
            """Task to run the agent workflow and push results to the queue."""
            # Inject conversation manager into agents that need it
            self._inject_conversation_manager(conversation_manager)
            
            # The CognitiveFlowAgentWrapper is now responsible for putting all
            # cognitive messages (thinking and reasoning) on the queue. This
            # loop simply needs to watch for the final answer to know when to stop.
            async for chunk in self.app.astream(initial_state, config=config):
                for agent_name, agent_state in chunk.items():
                    if agent_state and (final_answer := agent_state.get("final_answer")):
                        await self.cognitive_flow_queue.put({"final_answer": final_answer})
                        return
                        
            # Signal the end of the stream
            await self.cognitive_flow_queue.put(None)

        # Start the workflow in a background task
        workflow_task = asyncio.create_task(_run_workflow())

        # Yield messages from the queue as they arrive
        while True:
            message = await self.cognitive_flow_queue.get()
            if message is None:
                break
            yield message
            if "final_answer" in message:
                # Save the final answer to the conversation history
                conversation_manager.add_assistant_message(message["final_answer"])
                break
        
        # Ensure the workflow task is complete
        await workflow_task

    async def invoke_for_test_async(self, user_query: str, thread_id: str) -> Dict[str, Any]:
        """
        Invoke the agent for testing purposes, returning the final state.
        This is a non-streaming, async version for test suites.
        """
        # Create ConversationManager for this thread, passing the actual redis_client
        conversation_manager = ConversationManager(thread_id, redis_client=redis_client)
        
        # Add the user message to conversation history
        conversation_manager.add_user_message(user_query)
        
        # Get context payload from conversation manager
        context_payload = conversation_manager.get_contextual_payload()
        
        initial_state = create_initial_state(user_query, context_payload, conversation_manager, debug_mode=self.debug)

        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }
        
        # Inject conversation manager
        self._inject_conversation_manager(conversation_manager)

        # Run the workflow asynchronously for testing
        final_state = await self.app.ainvoke(initial_state, config=config)
        
        # Save the final answer to history
        if final_answer := final_state.get("final_answer"):
            conversation_manager.add_assistant_message(final_answer)
            
        return final_state

    def _inject_conversation_manager(self, conversation_manager):
        """Inject conversation manager into agents that need it."""
        # Get the workflow from the thinking workflow
        workflow = self.workflow.workflow
        
        # Inject into memory agent
        if hasattr(workflow, 'nodes') and 'memory_update' in workflow.nodes:
            memory_node = workflow.nodes['memory_update']
            # The node is wrapped in CognitiveFlowAgentWrapper, so we need to access the inner agent
            if hasattr(memory_node, 'agent'):
                # Check if it's wrapped in CognitiveFlowAgentWrapper
                if hasattr(memory_node.agent, 'agent'):
                    # It's wrapped, access the inner agent
                    memory_node.agent.agent._workflow_conversation_manager = conversation_manager
                else:
                    # It's not wrapped, access directly
                    memory_node.agent._workflow_conversation_manager = conversation_manager


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
                if final_answer := chunk.get("final_answer"):
                    response = final_answer
                elif cognitive_message := chunk.get("cognitive_message"):
                    print(f"\r  🤔 {cognitive_message}...", end="", flush=True)

            print(f"\r{response}     \n")

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
    parser.add_argument('--file', type=str, help='Path to a file containing the user query.')
    parser.add_argument('--thread_id', type=str, help='The conversation thread ID.')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode.')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging.')
    
    args = parser.parse_args()

    query = args.query
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                query = f.read()
        except FileNotFoundError:
            print(f"Error: File not found at {args.file}")
            return
    
    if args.interactive:
        asyncio.run(interactive_main())
    elif query:
        ai_system = LangGraphAgenticAI(debug=args.debug)
        thread_id = args.thread_id or f"test_session_{uuid4()}"
        
        async def run_query():
            response = ""
            async for chunk in ai_system.get_response_stream(query, thread_id):
                if final_answer := chunk.get("final_answer"):
                    response = final_answer
                elif cognitive_message := chunk.get("cognitive_message"):
                    print(f"  🤔 {cognitive_message}...")
            print(f"\n{response}")

        asyncio.run(run_query())
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 