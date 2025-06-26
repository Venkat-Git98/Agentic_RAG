from react_agent.base_tool import BaseTool
from tools.neo4j_connector import Neo4jConnector
import logging
import re

class KeywordRetrievalTool(BaseTool):
    """
    A tool to perform a direct keyword search against the Neo4j database.
    This is useful for finding nodes with exact text matches, bypassing semantic search.
    Enhanced to handle table references by fetching complete subsections.
    """
    name = "keyword_search"
    description = (
        "Performs a direct keyword search for a specific term within the text content of the knowledge base. "
        "This is useful when you need to find exact phrases or terms mentioned in the code text. "
        "Input should be a single, specific keyword or a short, exact phrase."
    )

    def _extract_subsection_from_table_reference(self, keyword: str) -> str:
        """
        Extracts subsection number from table references like 'Table 1607.12.1' or 'table 1607.12.1'.
        Returns the subsection number if found, otherwise returns None.
        """
        # Pattern to match table references like "Table 1607.12.1" or "table 1607.12.1"
        table_pattern = r'table\s+(\d+\.\d+(?:\.\d+)?)'
        match = re.search(table_pattern, keyword.lower())
        if match:
            return match.group(1)
        return None

    def _fetch_complete_subsection(self, subsection_number: str) -> str:
        """
        Fetches a complete subsection with all its connected nodes (tables, math, diagrams, etc.).
        This ensures we get inline tables and all related content.
        """
        query = """
        // Find the subsection by its number
        MATCH (subsection:Subsection {number: $subsection_number})
        
        // Get all nodes connected to this subsection (children and referenced nodes)
        OPTIONAL MATCH (subsection)-[:HAS_CHUNK|CONTAINS*0..]->(child)
        
        // Also get any nodes that this subsection or its children reference
        WITH subsection, COLLECT(DISTINCT child) AS children
        UNWIND children AS c
        OPTIONAL MATCH (c)-[:REFERENCES]->(referenced)
        WHERE referenced:Table OR referenced:Math OR referenced:Diagram
        
        // Combine all nodes
        WITH subsection, children, COLLECT(DISTINCT referenced) AS referenced_nodes
        WITH subsection, children + referenced_nodes AS all_related_nodes
        
        RETURN 
            subsection.uid AS subsection_uid,
            subsection.number AS subsection_number, 
            subsection.title AS subsection_title,
            subsection.content AS subsection_content,
            [node IN all_related_nodes | {
                uid: node.uid,
                type: labels(node)[0],
                title: node.title,
                content: node.content,
                text: node.text,
                data: node.data,
                latex: node.latex
            }] AS related_nodes
        """
        
        try:
            logging.info(f"Fetching complete subsection: {subsection_number}")
            results = Neo4jConnector.execute_query(query, {"subsection_number": subsection_number})
            
            if not results:
                return f"No subsection found with number: {subsection_number}"
            
            record = results[0].data()
            formatted_result = f"Complete Subsection {record['subsection_number']}:\n\n"
            
            # Add subsection title and content
            if record.get('subsection_title'):
                formatted_result += f"Title: {record['subsection_title']}\n"
            if record.get('subsection_content'):
                formatted_result += f"Content: {' '.join(record['subsection_content'])}\n\n"
            
            # Add all related nodes (tables, math, etc.)
            if record.get('related_nodes'):
                formatted_result += "Related Content:\n"
                for node in record['related_nodes']:
                    if not node:  # Skip None values
                        continue
                    
                    node_type = node.get('type', 'Unknown')
                    formatted_result += f"\n- {node_type}"
                    if node.get('title'):
                        formatted_result += f" - {node['title']}"
                    formatted_result += ":\n"
                    
                    # Handle different node types
                    if node_type == 'Table' and node.get('data'):
                        # Format table data
                        table_data = node['data']
                        if isinstance(table_data, dict) and 'headers' in table_data:
                            formatted_result += f"  Headers: {', '.join(table_data['headers'])}\n"
                            if 'rows' in table_data:
                                for i, row in enumerate(table_data['rows'][:3]):  # Show first 3 rows
                                    formatted_result += f"  Row {i+1}: {row}\n"
                        else:
                            formatted_result += f"  Table Data: {str(table_data)[:200]}...\n"
                    
                    elif node_type == 'Math' and node.get('latex'):
                        formatted_result += f"  Formula: {node['latex']}\n"
                    
                    elif node.get('content'):
                        content = ' '.join(node['content']) if isinstance(node['content'], list) else str(node['content'])
                        formatted_result += f"  Content: {content[:200]}...\n"
                    
                    elif node.get('text'):
                        formatted_result += f"  Text: {node['text'][:200]}...\n"
            
            return formatted_result
            
        except Exception as e:
            logging.error(f"Error fetching complete subsection {subsection_number}: {e}")
            return f"Error: Failed to fetch subsection {subsection_number}: {e}"

    def __call__(self, keyword: str) -> str:
        """
        Executes a keyword search. If the keyword references a table, it fetches the complete
        subsection containing that table. Otherwise, performs a standard keyword search.

        Args:
            keyword: The keyword or phrase to search for.

        Returns:
            A formatted string of search results, or a message if no results are found.
        """
        if not keyword:
            return "Error: The keyword cannot be empty."

        # Check if this is a table reference
        subsection_number = self._extract_subsection_from_table_reference(keyword)
        if subsection_number:
            logging.info(f"Detected table reference. Fetching complete subsection: {subsection_number}")
            return self._fetch_complete_subsection(subsection_number)

        # Standard keyword search for non-table queries
        query = """
        MATCH (n)
        WHERE (n:Passage OR n:Table OR n:Section OR n:Subsection)
        AND n.text CONTAINS $keyword
        RETURN 
            n.uid AS uid, 
            labels(n)[0] AS type,
            n.number AS number,
            n.title AS title,
            n.text AS text
        LIMIT 10
        """
        
        try:
            logging.info(f"Executing keyword search in Neo4j for: '{keyword}'")
            results = Neo4jConnector.execute_query(query, {"keyword": keyword})

            if not results:
                return f"No results found for the keyword: '{keyword}'."

            formatted_results = f"Keyword search results for '{keyword}':\n\n"
            for record in results:
                data = record.data() 
                formatted_results += f"- Type: {data.get('type')}, UID: {data.get('uid')}\n"
                if data.get('number'):
                    formatted_results += f"  Number: {data.get('number')}\n"
                if data.get('title'):
                    formatted_results += f"  Title: {data.get('title')}\n"
                if data.get('text'):
                    text_preview = (data['text'][:200] + '...') if len(data['text']) > 200 else data['text']
                    formatted_results += f"  Text: {text_preview}\n"
                formatted_results += "---\n"
            
            return formatted_results

        except Exception as e:
            logging.error(f"An error occurred during keyword search: {e}")
            return f"Error: Failed to execute keyword search due to: {e}" 