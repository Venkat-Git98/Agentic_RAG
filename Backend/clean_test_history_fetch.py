

import os
import redis
import json
from dotenv import load_dotenv
import sys
import re
from uuid import uuid4

def fetch_user_history(user_id: str):
    """
    Connects to Redis and fetches the full conversation history for a given user ID.
    """
    print(f"--- Attempting to fetch history for user_id: {user_id} ---")
    
    # Load .env file from the Backend directory
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path=dotenv_path)

    redis_url = os.getenv("REDIS_URL")

    if not redis_url:
        print("ERROR: REDIS_URL environment variable not found.")
        print("Please ensure your .env file is present in the 'Backend' directory and configured correctly.")
        return

    print(f"Connecting to Redis service...")

    try:
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        print("Successfully connected to Redis.")

    except redis.exceptions.RedisError as e:
        print(f"FAILED: Could not connect to Redis: {e}")
        return

    try:
        history_key = user_id
        # LRANGE with 0 and -1 fetches all elements from the list
        history_json_list = client.lrange(history_key, 0, -1)

        if not history_json_list:
            print(f"WARNING: No history found in Redis for user_id '{user_id}'.")
            return

        print(f"SUCCESS: Found {len(history_json_list)} messages in Redis history for user '{user_id}'.")
        print("--- Full Conversation History ---")

        for i, item_json in enumerate(history_json_list):
            print(f"DEBUG: Raw JSON from Redis for message {i+1}: {item_json}")
            try:
                item = json.loads(item_json)
                role = item.get('role', 'unknown').capitalize()
                content = item.get('content', 'No content').replace('\n', '\n' + ' ' * 11)
                print(f"DEBUG: Parsed content for message {i+1}: Role={role}, Content={content[:100]}...") # Truncate for brevity
                print(f"  {i+1:02d}. Role: {role}")
                print(f"       Content: {content}")
                print("-" * 30)
            except json.JSONDecodeError as e:
                print(f"ERROR: Could not decode message from Redis: {item_json}. Error: {e}")
            except Exception as e:
                print(f"ERROR: An unexpected error occurred while processing message: {item_json}. Error: {e}")

    except redis.exceptions.RedisError as e:
        print(f"FAILED: An error occurred while fetching history from Redis: {e}")
    except Exception as e:
        print(f"FAILED: An unexpected error occurred: {e}")


if __name__ == "__main__":
    # For testing, we'll use a fixed user ID and manually add a message to Redis
    user_id_to_fetch = "test_conversation_123"
    
    # Load .env file from the Backend directory
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path=dotenv_path)

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        print("ERROR: REDIS_URL environment variable not found.")
        print("Please ensure your .env file is present in the 'Backend' directory and configured correctly.")
        sys.exit(1)

    try:
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        print("Successfully connected to Redis for setup.")
    except redis.exceptions.RedisError as e:
        print(f"FAILED: Could not connect to Redis for setup: {e}")
        sys.exit(1)

    # Clear any existing history for this test user ID
    client.delete(user_id_to_fetch)
    print(f"Cleared existing history for user_id: {user_id_to_fetch}")

    # Add a sample user message
    sample_user_message = {
        "id": str(uuid4()),
        "role": "user",
        "content": "Show me Section 101.1 of the Virginia Building Code."
    }
    client.rpush(user_id_to_fetch, json.dumps(sample_user_message))
    print(f"Added sample user message to Redis.")

    # Add a sample assistant message with a section reference
    sample_assistant_message = {
        "id": str(uuid4()),
        "role": "assistant",
        "content": "Section 101.1 of the Virginia Building Code states that the provisions of this code shall apply to the construction, alteration, relocation, enlargement, replacement, repair, equipment, use and occupancy, location, maintenance, removal and demolition of every building or structure or any appurtenances connected or attached to such buildings or structures."
    }
    client.rpush(user_id_to_fetch, json.dumps(sample_assistant_message))
    print(f"Added sample assistant message to Redis.")

    fetch_user_history(user_id_to_fetch)

