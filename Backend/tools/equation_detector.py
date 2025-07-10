"""
Equation Detection and Mathematical Content Retrieval

This module provides utilities for detecting equation references in text
and retrieving mathematical content from the knowledge graph based on
the actual database structure discovered.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from tools.neo4j_connector import Neo4jConnector

logger = logging.getLogger(__name__)

class EquationDetector:
    """Detects and resolves equation references in text content."""
    
    def __init__(self):
        """Initialize the equation detector."""
        self.connector = Neo4jConnector()
        self.logger = logger  # Add reference to module logger
        
        # Equation reference patterns based on common building code formats
        self.equation_patterns = [
            r'Equation\s+(\d+[-\.]?\d*)',           # "Equation 16-7", "Equation 16.7"
            r'Eq\.?\s+(\d+[-\.]?\d*)',              # "Eq. 16-7", "Eq 16.7"
            r'Formula\s+(\d+[-\.]?\d*)',            # "Formula 16-7"
            r'equation\s+\((\d+[-\.]?\d*)\)',       # "equation (16-7)"
            r'Equation\s+\((\d+[-\.]?\d*)\)',       # "Equation (16-7)"
        ]
        
        # Table reference patterns
        self.table_patterns = [
            r'Table\s+(\d+\.[\d\.]*)',              # "Table 1607.1"
            r'table\s+(\d+\.[\d\.]*)',              # "table 1607.1"
        ]
        
        # Section reference patterns for context
        self.section_patterns = [
            r'Section\s+(\d+\.[\d\.]*)',            # "Section 1607.12.1"
            r'section\s+(\d+\.[\d\.]*)',            # "section 1607.12.1"
            r'\b(\d{4}\.\d+(?:\.\d+)*)\b',         # "1607.12.1" standalone
        ]
    
    def detect_equation_references(self, text: str) -> List[Dict[str, str]]:
        """
        Detect equation references in text.
        
        Args:
            text: Text content to search for equation references
            
        Returns:
            List of dictionaries with detected equation references
        """
        equation_refs = []
        
        for pattern in self.equation_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                equation_refs.append({
                    "type": "equation",
                    "reference": match.group(0),
                    "number": match.group(1),
                    "position": match.span()
                })
        
        return equation_refs
    
    def detect_table_references(self, text: str) -> List[Dict[str, str]]:
        """
        Detect table references in text.
        
        Args:
            text: Text content to search for table references
            
        Returns:
            List of dictionaries with detected table references
        """
        table_refs = []
        
        for pattern in self.table_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                table_refs.append({
                    "type": "table", 
                    "reference": match.group(0),
                    "number": match.group(1),
                    "position": match.span()
                })
        
        return table_refs
    
    def extract_section_context(self, text: str) -> List[str]:
        """
        Extract section numbers from text for context.
        Enhanced to infer sections from equation references.
        
        Args:
            text: Text content to search for section references
            
        Returns:
            List of section numbers found
        """
        sections = []
        
        # First, find explicit section references
        for pattern in self.section_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                section_num = match.group(1)
                if section_num not in sections:
                    sections.append(section_num)
        
        # ENHANCEMENT: Infer sections from equation references
        # E.g., "Equation 16-7" should search in Chapter 16 sections
        equation_refs = self.detect_equation_references(text)
        for eq_ref in equation_refs:
            eq_number = eq_ref['number']
            
            # Extract chapter number from equation (e.g., "16-7" -> "16")
            chapter_match = re.match(r'(\d+)[-\.]', eq_number)
            if chapter_match:
                chapter_num = chapter_match.group(1)
                
                # Add likely sections for this chapter
                potential_sections = [
                    f"{chapter_num}07",      # e.g., "1607" for Equation 16-7
                    f"{chapter_num}07.1",    # e.g., "1607.1"
                    f"{chapter_num}07.12",   # e.g., "1607.12" 
                    f"{chapter_num}07.12.1", # e.g., "1607.12.1"
                ]
                
                for section in potential_sections:
                    if section not in sections:
                        sections.append(section)
                        
                self.logger.info(f"Inferred sections {potential_sections} from equation {eq_number}")
        
        # ENHANCEMENT: Infer sections from table references  
        # E.g., "Table 1607.1" should search in Section 1607.1
        table_refs = self.detect_table_references(text)
        for table_ref in table_refs:
            table_number = table_ref['number']
            
            # Extract section from table number (e.g., "1607.1" -> "1607.1")
            if table_number not in sections:
                sections.append(table_number)
                self.logger.info(f"Inferred section {table_number} from table reference")
        
        return sections
    
    def get_equations_by_chapter(self, chapter_number: str) -> List[Dict[str, Any]]:
        """
        Retrieve all math nodes from a specific chapter.
        
        Args:
            chapter_number: Chapter number (e.g., "16")
            
        Returns:
            List of math node dictionaries
        """
        query = """
        MATCH (c:Chapter {number: $chapter_number})
        MATCH (c)-[:CONTAINS*1..]->(math:Math)
        RETURN 
            math.uid AS uid,
            math.latex AS latex,
            math.uid AS equation_id
        ORDER BY math.uid
        """
        
        try:
            records = self.connector.execute_query(query, {"chapter_number": chapter_number})
            return [dict(record) for record in records]
        except Exception as e:
            logger.error(f"Error retrieving equations for chapter {chapter_number}: {e}")
            return []
    
    def get_equations_by_subsection(self, subsection_number: str) -> List[Dict[str, Any]]:
        """
        Retrieve all math nodes from a specific subsection.
        
        Args:
            subsection_number: Subsection number (e.g., "1607.12.1")
            
        Returns:
            List of math node dictionaries
        """
        query = """
        MATCH (s:Subsection {number: $subsection_number})
        MATCH (s)-[:CONTAINS*0..]->(math:Math)
        RETURN 
            math.uid AS uid,
            math.latex AS latex,
            math.uid AS equation_id
        ORDER BY math.uid
        """
        
        try:
            records = self.connector.execute_query(query, {"subsection_number": subsection_number})
            return [dict(record) for record in records]
        except Exception as e:
            logger.error(f"Error retrieving equations for subsection {subsection_number}: {e}")
            return []
    
    def find_math_by_pattern(self, pattern: str, context_sections: List[str] = None) -> List[Dict[str, Any]]:
        """
        Find math nodes that might match an equation reference.
        
        Since math nodes don't have equation_number fields, we use UID patterns
        and context to find relevant equations.
        
        Args:
            pattern: Equation number pattern (e.g., "16-7", "16.7")
            context_sections: List of section numbers for context
            
        Returns:
            List of potential matching math nodes
        """
        # Convert pattern variations (16-7 -> 16.7, etc.)
        normalized_patterns = [
            pattern,
            pattern.replace('-', '.'),
            pattern.replace('.', '-')
        ]
        
        results = []
        
        # Search by UID patterns first
        for norm_pattern in normalized_patterns:
            query = """
            MATCH (math:Math)
            WHERE math.uid CONTAINS $pattern
            RETURN 
                math.uid AS uid,
                math.latex AS latex,
                math.uid AS equation_id
            ORDER BY math.uid
            LIMIT 10
            """
            
            try:
                records = self.connector.execute_query(query, {"pattern": norm_pattern})
                results.extend([dict(record) for record in records])
            except Exception as e:
                logger.warning(f"Error searching for pattern {norm_pattern}: {e}")
        
        # If we have context sections, search within those subsections
        if context_sections and not results:
            for section in context_sections:
                equations = self.get_equations_by_subsection(section)
                results.extend(equations)
        
        # Remove duplicates based on uid
        unique_results = []
        seen_uids = set()
        for result in results:
            if result['uid'] not in seen_uids:
                unique_results.append(result)
                seen_uids.add(result['uid'])
        
        return unique_results
    
    def resolve_equation_references(self, text: str) -> Dict[str, Any]:
        """
        Comprehensive equation reference resolution.
        
        Args:
            text: Text containing potential equation references
            
        Returns:
            Dictionary containing detected references and resolved equations
        """
        # Detect all references
        equation_refs = self.detect_equation_references(text)
        table_refs = self.detect_table_references(text)
        context_sections = self.extract_section_context(text)
        
        # Resolve equation references
        resolved_equations = []
        for eq_ref in equation_refs:
            equations = self.find_math_by_pattern(eq_ref['number'], context_sections)
            if equations:
                resolved_equations.extend(equations)
        
        # Get contextual equations from mentioned sections
        contextual_equations = []
        for section in context_sections:
            equations = self.get_equations_by_subsection(section)
            contextual_equations.extend(equations)
        
        return {
            "equation_references": equation_refs,
            "table_references": table_refs,
            "context_sections": context_sections,
            "resolved_equations": resolved_equations,
            "contextual_equations": contextual_equations[:10],  # Limit to avoid overflow
            "total_equations_found": len(resolved_equations) + len(contextual_equations)
        }
    
    def format_equations_for_context(self, equations: List[Dict[str, Any]]) -> str:
        """
        Format equations for inclusion in research context.
        
        Args:
            equations: List of equation dictionaries
            
        Returns:
            Formatted string containing equations
        """
        if not equations:
            return ""
        
        formatted = "=== MATHEMATICAL EQUATIONS ===\n\n"
        
        for i, eq in enumerate(equations, 1):
            formatted += f"Equation {i} (ID: {eq['uid']}):\n"
            formatted += f"LaTeX: {eq['latex']}\n\n"
        
        return formatted 