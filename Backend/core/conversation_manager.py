"""
Implements the advanced ConversationManager for the agentic system.

This module is responsible for intelligent, long-term conversation history
management. It uses a hybrid "Structured + Narrative" approach to balance
perfect memory recall with the finite context windows of LLMs.
"""

import logging
import json
import os
from typing import List, Dict, Any, Literal, Optional
import google.generativeai as genai
from pydantic import BaseModel, Field
import redis
from uuid import uuid4

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
    def __init__(self, conversation_id: str, redis_client: redis.Redis, history_prune_threshold: int = 10, window_size: int = 4, initial_state: Optional[Dict] = None):
        """
        Initializes the ConversationManager, loading state from Redis as the primary source of truth.
        
        Args:
            conversation_id: A unique identifier for the conversation.
            redis_client: An active client for connecting to Redis.
            history_prune_threshold: The number of messages after which to trigger
                                     a memory consolidation.
            window_size: The number of recent user/assistant turns to keep in the
                         immediate context window.
            initial_state: An optional dictionary to initialize the state, bypassing Redis load.
        """
        self.conversation_id = conversation_id
        self.redis_client = redis_client
        # Construct a unique file path for this conversation's state (used for backup)
        self.state_file_path = os.path.join(os.path.dirname(CONVERSATION_STATE_FILE), f"{self.conversation_id}.json")
        self.history_prune_threshold = history_prune_threshold
        self.window_size = window_size

        # Default state attributes
        self.full_history: List[Dict[str, str]] = []
        self.structured_memory = StructuredMemory()
        self.running_summary = "No summary has been generated yet."
        
        # Determine if this is a new or existing conversation by checking Redis
        self.is_new_conversation = True
        if initial_state:
            logging.info(f"Initializing ConversationManager for '{self.conversation_id}' with provided initial state.")
            self._load_state_from_dict(initial_state)
            self.is_new_conversation = not self.full_history
        elif self.redis_client and self.redis_client.exists(self.conversation_id):
            logging.info(f"Conversation '{self.conversation_id}' exists in Redis. Loading state.")
            self._load_state_from_redis()
            self.is_new_conversation = False
        else:
            logging.info(f"Starting new conversation: '{self.conversation_id}'.")
        
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
        message = {
            "id": str(uuid4()),
            "role": role, 
            "content": content
        }
        self.full_history.append(message)
        
        # If the history grows too long, trigger the full memory update and state sync
        if len(self.full_history) > self.history_prune_threshold:
            logging.info("History prune threshold reached. Updating memory and performing full state sync.")
            self._update_memory()
            self._save_state() # Performs a full delete-and-rewrite sync
        else:
            # For normal messages, just append to Redis and save a backup to disk
            self._append_message_to_redis(message)
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

    def _append_message_to_redis(self, message: Dict[str, Any]):
        """Saves only the most recent message to the history list in Redis efficiently."""
        if self.redis_client:
            try:
                history_key = self.conversation_id
                self.redis_client.rpush(history_key, json.dumps(message))
                logging.info(f"Appended new message to Redis history for '{self.conversation_id}'.")
            except redis.exceptions.RedisError as e:
                logging.error(f"Failed to append message to Redis for '{self.conversation_id}': {e}")

    def _save_state(self):
        """
        Saves the current full conversation state to Redis and a backup JSON file.
        This method performs a full overwrite and is best used for synchronization
        after major events like memory pruning, not for every message.
        """
        # --- Save to Redis ---
        if self.redis_client:
            try:
                # Use a pipeline for transactional integrity
                pipe = self.redis_client.pipeline()

                # 1. Save dialogue history (overwrite the whole list for consistency)
                history_key = self.conversation_id
                pipe.delete(history_key)
                if self.full_history:
                    pipe.rpush(history_key, *[json.dumps(msg) for msg in self.full_history])

                # 2. Save memory and summary state in a separate hash
                state_key = f"{self.conversation_id}:state"
                state_to_save = {
                    "structured_memory": self.structured_memory.model_dump_json(),
                    "running_summary": self.running_summary
                }
                pipe.hset(state_key, mapping=state_to_save)
                
                # Execute the transaction
                pipe.execute()
                logging.info(f"Full conversation state for '{self.conversation_id}' successfully saved to Redis.")

            except redis.exceptions.RedisError as e:
                logging.error(f"Failed to save full state to Redis for conversation '{self.conversation_id}': {e}")
        
        # --- Save to disk as a backup ---
        self._save_state_to_disk()

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

    def _load_state_from_dict(self, state: Dict[str, Any]):
        """Loads the conversation state from a dictionary (for testing)."""
        self.full_history = state.get("full_history", [])
        
        # Handle structured memory, which might be a dict or a JSON string
        structured_memory_data = state.get("structured_memory", {})
        if isinstance(structured_memory_data, str):
            self.structured_memory = StructuredMemory.model_validate_json(structured_memory_data)
        elif isinstance(structured_memory_data, dict):
            self.structured_memory = StructuredMemory.model_validate(structured_memory_data)
        
        self.running_summary = state.get("running_summary", "No summary provided in initial state.")
        logging.info("Successfully loaded state from initial_state dictionary.")

    def _load_state_from_redis(self):
        """
        Loads the complete conversation state (history, memory, summary) from Redis.
        """
        if not self.redis_client:
            logging.warning("Redis client not available. Cannot load state.")
            return

        try:
            # Load the dialogue history from a Redis List
            history_key = self.conversation_id
            history_json = self.redis_client.lrange(history_key, 0, -1)
            
            loaded_messages = []
            if history_json:
                for item in history_json:
                    try:
                        loaded_messages.append(json.loads(item))
                    except json.JSONDecodeError:
                        logging.error(f"Failed to decode message from Redis for '{history_key}': {item}")
                self.full_history = loaded_messages
                logging.info(f"Successfully loaded {len(self.full_history)} messages from Redis for '{self.conversation_id}'.")

            # Load the structured memory and summary from a Redis Hash
            state_key = f"{self.conversation_id}:state"
            state_data = self.redis_client.hgetall(state_key)

            if state_data:
                if 'structured_memory' in state_data:
                    self.structured_memory = StructuredMemory.model_validate_json(state_data['structured_memory'])
                if 'running_summary' in state_data:
                    self.running_summary = state_data['running_summary']
                logging.info(f"Successfully loaded memory and summary from Redis for '{self.conversation_id}'.")

        except redis.exceptions.RedisError as e:
            logging.error(f"Failed to load full state from Redis for '{self.conversation_id}': {e}")
            # Reset to default state in case of Redis failure
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
        # Process only the last user query and assistant response for efficiency.
        if len(self.full_history) < 2:
            logging.warning("Not enough history to perform an incremental memory update.")
            return

        last_exchange = self.full_history[-2:]
        history_text = "\n".join(f"{msg['role'].capitalize()}: {msg['content']}" for msg in last_exchange)

        prompt_for_json = UPDATE_STRUCTURED_MEMORY_PROMPT.format(
            structured_memory_json=self.structured_memory.model_dump_json(indent=2),
            latest_exchange=history_text # Use the new prompt variable
        )

        try:
            logging.info("Updating structured memory based on the latest exchange...")
            response = self.memory_model.generate_content(prompt_for_json)
            # Clean up the response to ensure it's valid JSON
            cleaned_response = response.text.strip().lstrip("```json").rstrip("```").strip()
            
            # Harden the JSON parsing to prevent crashes
            for attempt in range(3):
                try:
                    self.structured_memory = StructuredMemory.model_validate_json(cleaned_response)
                    logging.info("Structured memory updated successfully.")
                    break  # Exit the loop if parsing is successful
                except Exception as json_error:
                    logging.warning(f"Attempt {attempt + 1}: Failed to parse structured memory JSON. Error: {json_error}")
                    # Attempt to fix the JSON by finding the start and end of the JSON object
                    start_index = cleaned_response.find('{')
                    end_index = cleaned_response.rfind('}')
                    if start_index != -1 and end_index != -1:
                        cleaned_response = cleaned_response[start_index:end_index+1]
                    if attempt == 2:
                        logging.error("Failed to parse structured memory JSON after 3 attempts.")
                        logging.debug(f"Malformed JSON received for memory update:\n{cleaned_response}")
                        # Do not proceed with the rest of the memory update if parsing fails
                        return

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

        # The state will be saved by the calling method (add_message) after this completes.
        # No need for an explicit save call here.

        # --- Step 3: Prune the full history log ---
        # We've processed the old messages, so we can now discard them from the main log,
        # keeping only the recent window.
        # This pruning logic is now handled differently, as we only process the last exchange.
        # The full history is preserved until the next explicit pruning cycle.
        # logging.info(f"History pruned. New length: {len(self.full_history)}")
        pass 