import asyncio
import json
import argparse
import logging
from tools.neo4j_connector import Neo4jConnector

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_entity_retrieval(entity_type: str, entity_id: str):
    """
    Connects to Neo4j and attempts to retrieve a specific entity.
    """
    console = logging.getLogger()
    console.info(f"--- Starting test for {entity_type} with ID: {entity_id} ---")
    
    try:
        # We need an instance to call the async methods
        connector_instance = Neo4jConnector()
        content = None
        
        if entity_type == "section":
            console.info(f"Calling get_section_with_content for '{entity_id}'...")
            content = await connector_instance.get_section_with_content(entity_id)
        elif entity_type == "chapter":
            console.info(f"Calling get_chapter_with_content for '{entity_id}'...")
            content = await connector_instance.get_chapter_with_content(entity_id)
        else:
            console.error(f"Unknown entity type: {entity_type}. Please use 'section' or 'chapter'.")
            return

        if content:
            console.info(f"[SUCCESS] Found content for {entity_type} '{entity_id}':")
            # Pretty print the JSON string
            try:
                parsed_json = json.loads(content)
                print(json.dumps(parsed_json, indent=2))
            except json.JSONDecodeError:
                print(content)
        else:
            console.warning(f"[FAILURE] No content found for {entity_type} '{entity_id}'.")
            
    except Exception as e:
        console.error(f"An error occurred during the test: {e}", exc_info=True)
    finally:
        # Ensure the driver is closed
        Neo4jConnector.close_driver()
        console.info("--- Test finished ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test script for direct Neo4j retrieval.")
    parser.add_argument("entity_type", type=str, choices=['section', 'chapter'], help="The type of entity to query for.")
    parser.add_argument("entity_id", type=str, help="The ID of the section or chapter (e.g., '101' or '1').")
    
    args = parser.parse_args()
    
    asyncio.run(test_entity_retrieval(args.entity_type, args.entity_id)) 