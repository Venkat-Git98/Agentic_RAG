import logging
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables from .env file
load_dotenv()

# Get Neo4j credentials from environment
NEO4J_URI = os.environ.get("NEO4J_URI")
NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")



class Neo4jIndexManager:
    def __init__(self, uri, user, password):
        self._uri = uri
        self._user = user
        self._password = password
        self._driver = None

    def _ensure_connection(self):
        if self._driver is None:
            try:
                self._driver = GraphDatabase.driver(self._uri, auth=(self._user, self._password))
                logging.info("Successfully connected to Neo4j.")
            except Exception as e:
                logging.error(f"Failed to connect to Neo4j: {e}")
                raise

    def close(self):
        if self._driver is not None:
            self._driver.close()
            logging.info("Neo4j connection closed.")

    def _index_exists(self, session, index_name):
        """Check if a full-text index exists."""
        try:
            result = session.run("SHOW INDEXES YIELD name WHERE name = $index_name", index_name=index_name)
            return result.single() is not None
        except Exception as e:
            logging.error(f"Error checking for index {index_name}: {e}")
            return False

    def create_fulltext_index(self, index_name, node_labels, node_properties):
        """
        Creates a full-text index if it doesn't already exist.
        """
        self._ensure_connection()
        with self._driver.session() as session:
            if self._index_exists(session, index_name):
                logging.info(f"Index '{index_name}' already exists. No action taken.")
                return

            labels_str = "|".join(node_labels)
            properties_str = ", ".join([f"n.{prop}" for prop in node_properties])
            
            query = f"CREATE FULLTEXT INDEX {index_name} FOR (n:{labels_str}) ON EACH [{properties_str}]"
            
            try:
                logging.info(f"Attempting to create index '{index_name}'...")
                session.run(query)
                logging.info(f"Successfully created index '{index_name}'.")
            except Exception as e:
                logging.error(f"Failed to create index '{index_name}': {e}")

def main():
    """
    Main function to create all necessary indexes for the application.
    """
    try:
        manager = Neo4jIndexManager(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)

        # Index for Passage content
        manager.create_fulltext_index(
            "passage_content_idx",
            ["Passage"],
            ["content"]
        )

        # Broader index for hierarchical nodes
        manager.create_fulltext_index(
            "knowledge_base_text_idx",
            ["Chapter", "Section", "Subsection"],
            ["title", "text"]
        )

    except Exception as e:
        logging.error(f"An error occurred during index management: {e}")
    finally:
        if 'manager' in locals() and manager:
            manager.close()

if __name__ == "__main__":
    main() 