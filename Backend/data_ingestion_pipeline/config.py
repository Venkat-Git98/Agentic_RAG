# config.py
import os
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', '')
# Leave unset to use the server's default database (newer Aura instances name it
# after the instance id rather than "neo4j").
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE') or None
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'graph-rag-builingcode-41c88f940fd5.json')

# Must match the backend's config.py EMBEDDING_MODEL / EMBEDDING_DIMENSIONS, since
# the backend embeds queries with the same model to search these vectors.
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'models/gemini-embedding-001')
EMBEDDING_DIMENSIONS = int(os.getenv('EMBEDDING_DIMENSIONS', '768'))
