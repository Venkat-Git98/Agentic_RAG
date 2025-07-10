from react_agent.base_tool import BaseTool
from tools.neo4j_connector import Neo4jConnector
import logging
import re
from typing import List

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

    def _extract_key_terms_from_query(self, query: str) -> List[str]:
        """
        Extract key searchable terms from complex queries.
        This helps convert question-style queries into specific terms that might appear in the database.
        """
        import re
        
        key_terms = []
        
        # Extract equation references (e.g., "Equation 16-7" -> "16-7")
        equation_matches = re.findall(r'equation\s+(\d+[-\.]\d+)', query, re.IGNORECASE)
        for eq in equation_matches:
            key_terms.extend([eq, eq.replace('-', '.'), f"Equation {eq}"])
        
        # Extract section references (e.g., "Section 1607.12.1" -> "1607.12.1")
        section_matches = re.findall(r'section\s+(\d+\.[\d\.]+)', query, re.IGNORECASE)
        key_terms.extend(section_matches)
        
        # Extract table references (e.g., "Table 1607.12.1" -> "1607.12.1")
        table_matches = re.findall(r'table\s+(\d+\.[\d\.]*)', query, re.IGNORECASE)
        key_terms.extend(table_matches)
        
        # Extract specific technical terms commonly found in building codes
        technical_terms = [
            'live load', 'reduced live load', 'design live load', 'tributary area',
            'unreduced live load', 'live load reduction', 'interior beams',
            'KLL', 'factor', 'office building', 'psf', 'square feet'
        ]
        
        for term in technical_terms:
            if term.lower() in query.lower():
                key_terms.append(term)
        
        # Extract numbers with units that might be relevant
        number_unit_matches = re.findall(r'(\d+(?:\.\d+)?\s*(?:psf|sq\s*ft|square\s*feet))', query, re.IGNORECASE)
        key_terms.extend(number_unit_matches)
        
        return list(set(key_terms))  # Remove duplicates

    def _try_multiple_keyword_searches(self, key_terms: List[str]) -> str:
        """
        Try multiple keyword searches with different terms and combine results.
        """
        all_results = []
        found_any_results = False
        
        for term in key_terms:
            if not term or len(term.strip()) < 2:
                continue
                
            query = """
            MATCH (n)
            WHERE (n:Passage OR n:Table OR n:Section OR n:Subsection OR n:Math)
            AND (n.text CONTAINS $keyword OR n.latex CONTAINS $keyword OR n.title CONTAINS $keyword)
            RETURN 
                n.uid AS uid, 
                labels(n)[0] AS type,
                n.number AS number,
                n.title AS title,
                n.text AS text,
                n.latex AS latex
            LIMIT 5
            """
            
            try:
                logging.info(f"Trying keyword search for term: '{term}'")
                results = Neo4jConnector.execute_query(query, {"keyword": term})
                
                if results:
                    found_any_results = True
                    all_results.append(f"\n=== Results for '{term}' ===")
                    for record in results:
                        data = record.data()
                        all_results.append(f"- Type: {data.get('type')}, UID: {data.get('uid')}")
                        if data.get('number'):
                            all_results.append(f"  Number: {data.get('number')}")
                        if data.get('title'):
                            all_results.append(f"  Title: {data.get('title')}")
                        if data.get('latex'):
                            all_results.append(f"  Formula: {data.get('latex')}")
                        if data.get('text'):
                            text_preview = (data['text'][:200] + '...') if len(data['text']) > 200 else data['text']
                            all_results.append(f"  Text: {text_preview}")
                        all_results.append("---")
                        
            except Exception as e:
                logging.warning(f"Keyword search failed for term '{term}': {e}")
                continue
        
        if found_any_results:
            return "\n".join(all_results)
        else:
            return f"No results found for any of the extracted terms: {', '.join(key_terms)}"

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
        Enhanced to handle complex queries by extracting key terms.

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

        # For complex queries, extract key terms and try multiple searches
        if len(keyword.split()) > 3:  # Complex query with multiple words
            logging.info(f"Complex query detected: '{keyword}'. Extracting key terms.")
            key_terms = self._extract_key_terms_from_query(keyword)
            
            if key_terms:
                logging.info(f"Extracted key terms: {key_terms}")
                return self._try_multiple_keyword_searches(key_terms)
            else:
                logging.info("No key terms extracted. Falling back to standard search.")

        # Standard keyword search for simple queries
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
            logging.info(f"Executing standard keyword search in Neo4j for: '{keyword}'")
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