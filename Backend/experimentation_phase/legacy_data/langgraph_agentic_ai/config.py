"""
Centralized configuration management.

This module loads environment variables from a .env file and makes them
available as Python constants. This approach keeps sensitive data like API keys
out of the source code.
"""

import os
from dotenv import load_dotenv
import logging
import redis

def setup_logging():
    """Configures logging to print to console and save to a file."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, "agent_run.log")

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove any existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Create and add handlers
    file_handler = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
    console_handler = logging.StreamHandler()

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

# --- Load Environment Variables ---
# Searches for a .env file in the current directory or parent directories.
# This makes it flexible for running scripts from different locations.
dotenv_path = load_dotenv()

if dotenv_path:
    logging.info(f"Loaded environment variables from: {dotenv_path}")
else:
    logging.warning("No .env file found. Please create one with the required variables.")

# --- Google Gemini API Configuration ---
# Your API key for accessing Google's generative models.
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    logging.error("FATAL: GOOGLE_API_KEY not found in environment variables.")
else:
    logging.info("GOOGLE_API_KEY loaded successfully.")

# --- Neo4j Database Configuration ---
# Connection details for your Neo4j graph database.
NEO4J_URI = os.environ.get("NEO4J_URI")
NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")

if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
    logging.error("FATAL: Neo4j credentials (URI, USERNAME, PASSWORD) not fully found in environment variables.")
else:
    logging.info("Neo4j credentials loaded successfully.")

# --- Model Tiering Configuration ---
# Define which models to use for different tasks to balance cost and performance.
# This makes it easy to upgrade or change a model in one place.
TIER_1_MODEL_NAME = "gemini-1.5-pro-latest"  # For final synthesis and critical validation
TIER_2_MODEL_NAME = "gemini-1.5-flash-latest" # For decomposition, HyDE, and initial validation
TIER_3_MODEL_NAME = "gemini-1.5-flash-latest" # For triage and simple lookups (can be same as Tier 2)
MEMORY_ANALYSIS_MODEL = "gemini-1.5-flash-latest" # For the cost-effective memory management tasks

# --- Embedding Model Configuration ---
EMBEDDING_MODEL = "models/embedding-001"

# --- Research Configuration ---
# Controls whether to use the reranker for result optimization
# Set to False if reranker is not performing well for building code documents
USE_RERANKER = os.environ.get("USE_RERANKER", "False").lower() == "true"

# --- Calculation Configuration ---
# Controls whether to use Docker for calculations
# If True: All calculations run in secure Docker containers (recommended for production)
# If False: Calculations run via LLM (faster startup, no Docker dependency)
USE_DOCKER = os.environ.get("USE_DOCKER", "False").lower() == "true"

# --- File Paths ---
# Defines the location for saving the persistent conversation state.
CONVERSATION_STATE_FILE = "data/conversation_state.json"

# --- Redis Configuration ---
# Your connection URL for the Redis instance on Railway.
REDIS_URL = os.environ.get("REDIS_URL")
redis_client = None
if REDIS_URL:
    try:
        # Use decode_responses=True to get strings back from Redis
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        # Check if the connection is alive
        redis_client.ping()
        logging.info("Redis connection successful.")
    except redis.exceptions.ConnectionError as e:
        logging.error(f"FATAL: Could not connect to Redis at {REDIS_URL}. Error: {e}")
        redis_client = None
else:
    logging.warning("REDIS_URL not found in environment variables. State management will not be persistent.")

logging.info(f"Model configuration: T1='{TIER_1_MODEL_NAME}', T2='{TIER_2_MODEL_NAME}', Memory='{MEMORY_ANALYSIS_MODEL}'")
logging.info(f"Research configuration: USE_RERANKER={USE_RERANKER}")
logging.info(f"Calculation configuration: USE_DOCKER={USE_DOCKER}") 