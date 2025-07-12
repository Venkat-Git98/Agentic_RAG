import redis
import os
from dotenv import load_dotenv

def clear_remote_redis_cache():
    """
    Connects to a remote Redis instance using environment variables
    and clears the entire database.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Get Redis connection details from environment variables
    redis_url = os.getenv("REDIS_URL")

    if not redis_url:
        print("🔴 REDIS_URL environment variable not found.")
        print("Please ensure your .env file is configured correctly.")
        return

    print(f"Connecting to Redis instance at: {redis_url}")

    try:
        # Connect to the Redis instance
        # The from_url method handles parsing the connection string.
        client = redis.from_url(redis_url)

        # Check the connection
        client.ping()
        print("✅ Successfully connected to Redis.")

        # Clear the database
        print("⚡ Clearing all keys from the Redis database...")
        client.flushdb()
        print("✅ Redis cache cleared successfully.")

    except redis.exceptions.ConnectionError as e:
        print(f"🔴 Failed to connect to Redis: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    clear_remote_redis_cache()
