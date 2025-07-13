import redis
import os
from dotenv import load_dotenv

def clear_query_cache():
    """Connects to Redis and clears the query cache."""
    load_dotenv()
    try:
        # Connect to Redis
        redis_client = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)
        redis_client.ping() 
        print("Successfully connected to Redis.")

        # Find all keys matching the query cache pattern
        cache_keys = redis_client.keys("query_cache:*")

        if not cache_keys:
            print("No query cache keys found to delete.")
            return

        # Delete the keys
        print(f"Found {len(cache_keys)} query cache keys to delete.")
        redis_client.delete(*cache_keys)
        print("✅ Successfully cleared the query cache.")

    except redis.exceptions.ConnectionError as e:
        print(f"Error connecting to Redis: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    clear_query_cache() 