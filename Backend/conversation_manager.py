"""
Implements the advanced ConversationManager for the agentic system.

This module is responsible for intelligent, long-term conversation history
management. It uses a hybrid "Structured + Narrative" approach to balance
perfect memory recall with the finite context windows of LLMs.
"""

import logging
import json
import os
from typing import List, Dict, Any, Literal
import google.generativeai as genai
from pydantic import BaseModel, Field

# Imports are now relative to the project root
from config import MEMORY_ANALYSIS_MODEL, GOOGLE_API_KEY, CONVERSATION_STATE_FILE
from prompts import UPDATE_STRUCTURED_MEMORY_PROMPT, GENERATE_NARRATIVE_SUMMARY_PROMPT

# Configure the Gemini client
# This should only be done once in the application's lifecycle.
# A good place is here, as this manager is a core service.
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# --- Pydantic Models for Structured Memory ---

class StructuredMemory(BaseModel):
    """
    Defines the structured, database-like memory of the conversation.
    This object is updated by an LLM and provides a precise, machine-readable
    record of the interaction.
    """
    user_profile: Dict[str, str] = Field(default_factory=dict, description="Inferred details about the user, like their role or goals.")
    topics_discussed: List[str] = Field(default_factory=list, description="A list of major topics covered in the conversation.")
    key_facts_established: Dict[str, Any] = Field(default_factory=dict, description="A dictionary of specific, critical facts, figures, and identifiers.")
    unresolved_questions: List[str] = Field(default_factory=list, description="Questions the user has asked that are not yet fully answered.")
    session_summary: str = Field(default="", description="A brief, high-level summary of the entire session's purpose.")

# --- The Conversation Manager ---

class ConversationManager:
    """
    Manages the state of a conversation with a user, providing context for the agents.
    """
    def __init__(self, conversation_id: str, history_prune_threshold: int = 10, window_size: int = 4):
        """
        Initializes the ConversationManager, loading state from disk if available.
        
        Args:
            conversation_id: A unique identifier for the conversation. This is used
                             to create a unique filename for storing the state.
            history_prune_threshold: The number of messages after which to trigger
                                     a memory consolidation.
            window_size: The number of recent user/assistant turns to keep in the
                         immediate context window.
        """
        self.conversation_id = conversation_id
        # Construct a unique file path for this conversation's state
        self.state_file_path = os.path.join(os.path.dirname(CONVERSATION_STATE_FILE), f"{self.conversation_id}.json")
        self.history_prune_threshold = history_prune_threshold
        self.window_size = window_size

        # Default state attributes
        self.full_history: List[Dict[str, str]] = []
        self.structured_memory = StructuredMemory()
        self.running_summary = "No summary has been generated yet."
        
        # Load state from disk if it exists
        self._load_state_from_disk()
        
        # Initialize the generative model for memory analysis
        try:
            self.memory_model = genai.GenerativeModel(MEMORY_ANALYSIS_MODEL)
            logging.info(f"Memory analysis model '{MEMORY_ANALYSIS_MODEL}' initialized.")
        except Exception as e:
            logging.error(f"Failed to initialize memory analysis model: {e}")
            self.memory_model = None

    def add_user_message(self, content: str):
        """Adds a new user message to the conversation history."""
        self.add_message(role="user", content=content)

    def add_assistant_message(self, content: str):
        """Adds a new assistant message to the conversation history."""
        self.add_message(role="assistant", content=content)

    def add_message(self, role: Literal["user", "assistant"], content: str):
        """
        Adds a new message to the conversation history and triggers memory updates if needed.
        """
        self.full_history.append({"role": role, "content": content})
        
        if len(self.full_history) > self.history_prune_threshold:
            logging.info("History prune threshold reached. Updating memory...")
            self._update_memory()
        
        # Persist the latest state to disk after every message
        self._save_state_to_disk()

    def get_formatted_history(self) -> str:
        """
        Returns the full conversation history as a single formatted string.
        """
        return "\n".join(
            f"{msg['role'].capitalize()}: {msg['content']}" for msg in self.full_history
        )

    def get_contextual_payload(self) -> str:
        """
        Constructs the final context payload to be sent to the main agentic workflow.

        This payload combines structured memory, a narrative summary, and the
        most recent messages into a single, comprehensive context block.
        """
        recent_history = self.full_history[-self.window_size*2:] # *2 for user/assistant turns

        # Format the recent history for display
        formatted_recent_history = "\n".join(
            f"{msg['role'].capitalize()}: {msg['content']}" for msg in recent_history
        )

        payload = f"""
Here is the context for the current query:

**[Structured Memory]**
{self.structured_memory.model_dump_json(indent=2)}

**[Conversation Summary]**
{self.running_summary}

**[Recent Messages]**
{formatted_recent_history}
"""
        return payload

    def _save_state_to_disk(self):
        """Saves the current conversation state to a JSON file."""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.state_file_path), exist_ok=True)
            
            state_to_save = {
                "conversation_id": self.conversation_id,
                "full_history": self.full_history,
                "structured_memory": self.structured_memory.model_dump(),
                "running_summary": self.running_summary
            }
            with open(self.state_file_path, 'w', encoding='utf-8') as f:
                json.dump(state_to_save, f, indent=2, ensure_ascii=False)
            logging.info(f"Conversation state successfully saved to {self.state_file_path}")
        except Exception as e:
            logging.error(f"Failed to save conversation state: {e}")

    def _load_state_from_disk(self):
        """Loads conversation state from a JSON file if it exists."""
        if not os.path.exists(self.state_file_path):
            logging.info("No saved state file found. Starting a new conversation.")
            return
        
        try:
            with open(self.state_file_path, 'r', encoding='utf-8') as f:
                loaded_state = json.load(f)
            
            self.full_history = loaded_state.get("full_history", [])
            # Load structured memory safely using Pydantic's model_validate
            self.structured_memory = StructuredMemory.model_validate(loaded_state.get("structured_memory", {}))
            self.running_summary = loaded_state.get("running_summary", "No summary found.")
            
            logging.info(f"Conversation state successfully loaded from {self.state_file_path}")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logging.error(f"Failed to load conversation state: {e}. Starting fresh.")
            # Reset to default state in case of corruption
            self.full_history = []
            self.structured_memory = StructuredMemory()
            self.running_summary = "No summary has been generated yet."

    def _update_memory(self):
        """
        The core logic for updating the agent's long-term memory.
        This function is private and should not be called directly.
        """
        if not self.memory_model:
            logging.error("Cannot update memory; memory analysis model not available.")
            return

        # --- Step 1: Update the Structured Memory JSON ---
        # We take the messages that need to be processed (those not in the recent window)
        messages_to_process = self.full_history[: -self.window_size*2]
        if not messages_to_process:
            logging.warning("Memory update triggered, but no messages to process.")
            return
            
        history_text = "\n".join(f"{msg['role'].capitalize()}: {msg['content']}" for msg in messages_to_process)

        prompt_for_json = UPDATE_STRUCTURED_MEMORY_PROMPT.format(
            structured_memory_json=self.structured_memory.model_dump_json(indent=2),
            history_text=history_text
        )

        try:
            logging.info("Updating structured memory...")
            response = self.memory_model.generate_content(prompt_for_json)
            # Clean up the response to ensure it's valid JSON
            cleaned_response = response.text.strip().lstrip("```json").rstrip("```").strip()
            self.structured_memory = StructuredMemory.model_validate_json(cleaned_response)
            logging.info("Structured memory updated successfully.")
        except Exception as e:
            logging.error(f"Failed to update structured memory. Error: {e}")
            # If this fails, we don't proceed to summary generation
            return

        # --- Step 2: Regenerate the Narrative Summary from the new JSON ---
        prompt_for_summary = GENERATE_NARRATIVE_SUMMARY_PROMPT.format(
            structured_memory_json=self.structured_memory.model_dump_json(indent=2)
        )
        try:
            logging.info("Regenerating narrative summary...")
            response = self.memory_model.generate_content(prompt_for_summary)
            self.running_summary = response.text.strip()
            logging.info("Narrative summary regenerated successfully.")
        except Exception as e:
            logging.error(f"Failed to regenerate narrative summary. Error: {e}")

        # --- Step 3: Prune the full history log ---
        # We've processed the old messages, so we can now discard them from the main log,
        # keeping only the recent window.
        self.full_history = self.full_history[-self.window_size*2:]
        logging.info(f"History pruned. New length: {len(self.full_history)}") 