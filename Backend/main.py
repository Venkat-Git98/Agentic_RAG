"""
Main entry point for the LangGraph Agentic AI System with Thinking Capabilities.

This is your ONE app that does everything:
- Interactive mode with thinking-style reasoning display
- Single queries with full AI reasoning shown
- Virginia Building Code expert with mathematical calculations
"""

import sys
import os
import asyncio
import argparse
import logging
from typing import Optional

# --- Configure Logging First ---
# This must happen before any other local modules are imported to ensure
# the configuration is applied correctly.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add parent directories to path for imports
# Import original conversation manager
from conversation_manager import ConversationManager
from thinking_workflow import create_thinking_agentic_workflow, run_thinking_agentic_query
from thinking_logger import ThinkingMode

# --- Static User Identity ---
# This static ID ensures that the same conversation history is used across sessions.
USER_THREAD_ID = "_personal_portfolio_session_uuid_01"

# Configure logging
logger = logging.getLogger("LangGraphMain")

class LangGraphAgenticAI:
    """
    The ONE LangGraph Agentic AI System with Built-in Thinking.
    
    This is your complete Virginia Building Code expert system that shows
    its reasoning process while working through problems.
    """
    
    def __init__(self, debug: bool = False, detailed_thinking: bool = False):
        """
        Initialize the LangGraph Agentic AI system with thinking capabilities.
        
        Args:
            debug: Whether to enable debug mode
            detailed_thinking: Whether to use detailed thinking mode
        """
        self.debug = debug
        self.thinking_mode = ThinkingMode.DETAILED if detailed_thinking else ThinkingMode.SIMPLE
        
        # Initialize the thinking workflow (this is the default now)
        # The workflow itself is stateless and can be reused.
        self.workflow = create_thinking_agentic_workflow(debug=debug, thinking_mode=True, thinking_detail_mode=self.thinking_mode)
        
        mode_desc = "detailed" if detailed_thinking else "simple"
        logger.info(f"🧠 LangGraph Agentic AI with Thinking initialized (debug={debug}, mode={mode_desc})")
    
    async def query(self, user_query: str, thread_id: str) -> str:
        """
        Process a single query through the agentic workflow.
        
        This method is now stateless and uses the provided thread_id to manage
        the conversation context for each request.
        
        Args:
            user_query: The user's question
            thread_id: The unique thread ID for conversation continuity
            
        Returns:
            The AI's response
        """
        logger.info(f"🧠 Processing query for thread '{thread_id}': {user_query[:100]}...")
        
        # Create a ConversationManager for this specific thread
        conversation_manager = ConversationManager(thread_id)
        context_payload = conversation_manager.get_contextual_payload()
        
        # Run through the workflow
        result = await self.workflow.run(
            user_query=user_query,
            context_payload=context_payload,
            conversation_manager=conversation_manager,
            thread_id=thread_id
        )
        
        response = result["response"]
        
        # Log execution summary if in debug mode
        if self.debug:
            summary = result.get("execution_summary", {})
            logger.info(f"Execution summary for thread '{thread_id}': {summary}")
        
        return response
    
    async def interactive_mode(self):
        """
        Run the system in interactive mode for conversation.
        This mode preserves the original single-user session behavior.
        """
        print("\n" + "="*60)
        print("🧠 LangGraph Agentic AI with Thinking")
        print("🏗️  Virginia Building Code Expert System")
        print("="*60)
        print("🤔 You'll see my reasoning process as I work!")
        print("Type 'quit', 'exit', or 'bye' to end the conversation.")
        print("Type 'help' for more commands.\n")
        
        # For interactive CLI mode, we use the static user ID to maintain a single conversation.
        interactive_thread_id = USER_THREAD_ID
        conversation_manager = ConversationManager(interactive_thread_id)
        
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\n👋 Thank you for using LangGraph Agentic AI!")
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                elif user_input.lower() == 'stats':
                    self._show_stats(conversation_manager)
                    continue
                elif user_input.lower() == 'clear':
                    conversation_manager.clear_conversation()
                    print("🧹 Conversation history cleared.")
                    continue
                
                # Process the query using the interactive session's thread ID
                print("\n🤔 Processing...", end="", flush=True)
                response = await self.query(user_input, interactive_thread_id)
                print("\r" + " "*15 + "\r", end="")  # Clear processing message
                
                # Display response
                print(f"AI: {response}\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
                logger.error(f"Error in interactive mode: {e}")
    
    def _show_help(self):
        """Show help information."""
        print("""
📖 Available Commands:
- help: Show this help message
- stats: Show conversation statistics
- clear: Clear conversation history
- quit/exit/bye: End the conversation

💡 Tips:
- Ask questions about the Virginia Building Code
- I can help with calculations, comparisons, and requirements
- Be specific for better results

🔍 Example questions:
- "What are the requirements for residential stairs?"
- "How do I calculate wind load for a 3-story building?"
- "Calculate wind pressure for 85 mph wind speed"
- "Show me Section 1605.3.1"

🧠 Thinking Features:
- See my reasoning process in real-time
- Watch how I plan calculations
- Understand my decision-making logic
""")
    
    def _show_stats(self, conversation_manager: ConversationManager):
        """Show conversation statistics."""
        stats = {
            "message_count": len(conversation_manager.messages),
            "workflow_type": "🧠 Enhanced with Thinking",
            "debug_mode": self.debug
        }
        
        print(f"""
📊 Conversation Statistics:
- Messages exchanged: {stats['message_count']}
- Workflow type: {stats['workflow_type']}
- Debug mode: {'Enabled' if stats['debug_mode'] else 'Disabled'}
""")

async def main():
    """Main entry point for the ONE unified application."""
    parser = argparse.ArgumentParser(
        description="🧠 LangGraph Agentic AI with Thinking - Virginia Building Code Expert",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --interactive                                    # Interactive mode with thinking
  python main.py --query "Calculate wind pressure for 85 mph"    # Single query with reasoning
  python main.py --query "Requirements for stairs" --debug       # Debug mode with thinking
        """
    )
    
    parser.add_argument(
        "--query", 
        type=str, 
        help="Single query to process"
    )
    parser.add_argument(
        "--interactive", 
        action="store_true", 
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode"
    )
    parser.add_argument(
        "--detailed", 
        action="store_true", 
        help="Enable detailed thinking mode (default is simple)"
    )
    
    args = parser.parse_args()
    
    # Initialize the system
    ai_system = LangGraphAgenticAI(debug=args.debug, detailed_thinking=args.detailed)
    
    try:
        if args.interactive:
            # Run in interactive mode with thinking
            await ai_system.interactive_mode()
        elif args.query:
            # Process single query with thinking
            print(f"\n🧠 Processing query with thinking: {args.query}")
            print("=" * 60)
            
            # Use the static user ID for single-query CLI mode to maintain compatibility
            response = await ai_system.query(args.query, USER_THREAD_ID)
            
            print(f"\n📝 Response:\n{response}")
            print("\n" + "=" * 60)
        else:
            # No specific mode, show help
            parser.print_help()
            print("\n💡 Quick Start:")
            print("  🧠 Interactive: python main.py --interactive")
            print("  🧮 Test query:  python main.py --query 'Calculate wind pressure for 85 mph'")
            print("  🏗️ Ask anything about Virginia Building Code!")
            
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user.")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

# Simple function for direct integration with thinking
async def ask_langgraph_ai(question: str, debug: bool = False) -> str:
    """
    Simple function for asking a question to the LangGraph AI system with thinking.
    
    Args:
        question: The question to ask
        debug: Whether to enable debug mode
        
    Returns:
        The AI's response
    """
    return await run_thinking_agentic_query(
        user_query=question,
        debug=debug,
        thinking_mode=True
    )

# Compatibility function with thinking capabilities
async def langgraph_compatibility_wrapper(user_query: str, context_payload: str = "") -> str:
    """
    Compatibility wrapper with thinking capabilities.
    
    Args:
        user_query: The user's question
        context_payload: Context from conversation manager
        
    Returns:
        The AI's response
    """
    return await run_thinking_agentic_query(
        user_query=user_query,
        context_payload=context_payload,
        debug=False,
        thinking_mode=True
    )

if __name__ == "__main__":
    asyncio.run(main()) 