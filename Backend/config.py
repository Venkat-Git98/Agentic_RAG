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
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(project_root, '.env')
was_loaded = load_dotenv(dotenv_path=dotenv_path)

if was_loaded:
    logging.info(f"Loaded environment variables from: {dotenv_path}")
else:
    logging.warning(f".env file not found at {dotenv_path}. Please create one with the required variables.")

# --- Google Gemini API Configuration ---
# Your API key for accessing Google's generative models.
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("FATAL: GOOGLE_API_KEY not found in environment variables.")

# --- Cohere API Key ---
COHERE_API_KEY = os.environ.get("COHERE_API_KEY") or os.environ.get("COHERE_API")
if not COHERE_API_KEY:
    raise ValueError("FATAL: COHERE_API_KEY or COHERE_API not found in environment variables.")

# --- Tavily API Key ---
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY") or os.environ.get("TAVILY_API")
if not TAVILY_API_KEY:
    raise ValueError("FATAL: TAVILY_API_KEY or TAVILY_API not found in environment variables.")

# --- Neo4j Database Configuration ---
# Connection details for your Neo4j graph database.
NEO4J_URI = os.environ.get("NEO4J_URI")
NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")

if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
    raise ValueError("FATAL: Neo4j credentials (NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD) not fully set in environment variables.")

# --- Model Tiering Configuration ---
# Define which models to use for different tasks to balance cost and performance.
# This makes it easy to upgrade or change a model in one place.
TIER_1_MODEL_NAME = "gemini-1.5-pro-latest"#"gemini-2.5-pro"  # For final synthesis and critical validation
TIER_2_MODEL_NAME = "gemini-1.5-flash-latest" # For decomposition, HyDE, and initial validation
TIER_3_MODEL_NAME = "gemini-1.5-flash-latest" # For triage and simple lookups (can be same as Tier 2)
MEMORY_ANALYSIS_MODEL = "gemini-1.5-flash-latest" # For the cost-effective memory management tasks

# --- Embedding Model Configuration ---
EMBEDDING_MODEL = "models/embedding-001"

# --- Research Configuration ---
# Controls whether to use the reranker for result optimization
# Set to False if reranker is not performing well for building code documents
USE_RERANKER = os.environ.get("USE_RERANKER", "False").lower() == "true"

# Controls whether to use parallel execution for sub-queries in ResearchOrchestrator
# If True: Sub-queries are processed concurrently for faster execution (default)
# If False: Sub-queries are processed sequentially (for debugging/troubleshooting)
USE_PARALLEL_EXECUTION = os.environ.get("USE_PARALLEL_EXECUTION", "True").lower() == "true"

# --- Calculation Configuration ---
# Controls whether to use Docker for calculations
# If True: All calculations run in secure Docker containers (recommended for production)
# If False: Calculations run via LLM (faster startup, no Docker dependency)
USE_DOCKER = os.environ.get("USE_DOCKER", "False").lower() == "true"

# --- File Paths ---
# Defines the location for saving the persistent conversation state.
CONVERSATION_STATE_FILE = "data/conversation_state.json"

# --- Redis Configuration (Temporarily Disabled for Testing) ---
REDIS_URL = os.environ.get("REDIS_URL")
if not REDIS_URL:
    logging.warning("REDIS_URL not set. Redis functionality will be disabled.")
    redis_client = None # Set to None if Redis is not configured
else:
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        logging.info("Successfully connected to Redis.")
    except redis.exceptions.ConnectionError as e:
        logging.error(f"FATAL: Could not connect to Redis: {e}. Redis functionality will be disabled.")
        redis_client = None

# --- Tool Configuration ---
# Set to True to use the parallel research tool for sub-queries
USE_PARALLEL_RESEARCH = os.getenv("USE_PARALLEL_RESEARCH", "true").lower() == "true"

# --- LangSmith Tracing and Monitoring ---
# Set to "true" to enable LangSmith tracing for deep agent observability
# This is the master switch for all LangSmith functionality.
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"

# The API endpoint for LangSmith. This should not be changed.
LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

# Your personal LangSmith API key. Get this from the LangSmith settings page.
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")

# The name of the project in LangSmith where traces will be sent.
# This helps organize runs, e.g., "Agentic-AI-Prod" vs. "Agentic-AI-Dev".
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")


# --- Knowledge Graph Configuration ---
# ... existing code ...

logging.info(f"Model configuration: T1='{TIER_1_MODEL_NAME}', T2='{TIER_2_MODEL_NAME}', Memory='{MEMORY_ANALYSIS_MODEL}'")
logging.info(f"Research configuration: USE_RERANKER={USE_RERANKER}, USE_PARALLEL_EXECUTION={USE_PARALLEL_EXECUTION}")
logging.info(f"Calculation configuration: USE_DOCKER={USE_DOCKER}") 