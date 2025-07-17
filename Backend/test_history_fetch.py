import os
import redis
import json
from dotenv import load_dotenv
import sys

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
        print("🔴 ERROR: REDIS_URL environment variable not found.")
        print("Please ensure your .env file is present in the 'Backend' directory and configured correctly.")
        return

    print(f"Connecting to Redis service...")

    try:
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        print("✅ Successfully connected to Redis.")

    except redis.exceptions.RedisError as e:
        print(f"🔴 FAILED: Could not connect to Redis: {e}")
        return

    try:
        history_key = user_id
        # LRANGE with 0 and -1 fetches all elements from the list
        history_json_list = client.lrange(history_key, 0, -1)

        if not history_json_list:
            print(f"🟡 WARNING: No history found in Redis for user_id '{user_id}'.")
            return

        print(f"✅ SUCCESS: Found {len(history_json_list)} messages in Redis history for user '{user_id}'.")
        print("--- Full Conversation History ---")

        for i, item_json in enumerate(history_json_list):
            try:
                item = json.loads(item_json)
                role = item.get('role', 'unknown').capitalize()
                content = item.get('content', 'No content').replace('\n', '\n' + ' ' * 11)
                print(f"  {i+1:02d}. Role: {role}")
                print(f"       Content: {content}")
                print("-" * 30)
            except json.JSONDecodeError:
                print(f"  - Could not decode message from Redis: {item_json}")

    except redis.exceptions.RedisError as e:
        print(f"🔴 FAILED: An error occurred while fetching history from Redis: {e}")
    except Exception as e:
        print(f"🔴 FAILED: An unexpected error occurred: {e}")


if __name__ == "__main__":
    # You can run this script with a user ID as a command-line argument:
    # python Backend/test_history_fetch.py your-user-id-here
    # If no argument is provided, it will use the default ID from your request.
    if len(sys.argv) > 1:
        user_id_to_fetch = sys.argv[1]
    else:
        user_id_to_fetch = "802da658-3c90-4b00-a02c-ba8114c18484"
    
    if not user_id_to_fetch:
        print("Please provide a user_id.")
    else:
        fetch_user_history(user_id_to_fetch)