"""
HyDE (Hypothetical Document Embedding) Generation Agent.

This agent takes a research plan (a list of sub-queries) and uses the
specialized HydeTool to generate a hypothetical document for each one.
Enhanced with mathematical content detection and contextual generation.
"""

from typing import Dict, Any, List
import asyncio

from .base_agent import BaseLangGraphAgent
from state import AgentState
from state_keys import RESEARCH_PLAN, CURRENT_STEP, INTERMEDIATE_OUTPUTS
from tools.hyde_tool import HydeTool
from tools.equation_detector import EquationDetector

class HydeAgent(BaseLangGraphAgent):
    """
    An agent dedicated to generating HyDE documents for a list of sub-queries.
    Enhanced with mathematical content detection and context awareness.
    """

    def __init__(self):
        """Initializes the HydeAgent with mathematical enhancement capabilities."""
        super().__init__(model_tier="tier_1", agent_name="HydeAgent")
        self.hyde_tool = HydeTool()
        self.equation_detector = EquationDetector()

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Executes the enhanced HyDE generation process in parallel for all sub-queries.
        Now includes mathematical content detection and context enhancement.
        
        Args:
            state: The current workflow state, containing the research plan.
            
        Returns:
            A dictionary containing the updated research plan with enhanced HyDE documents.
        """
        research_plan = state.get(RESEARCH_PLAN, [])
        if not research_plan:
            self.logger.warning("HydeAgent called without a research plan. Nothing to do.")
            return {RESEARCH_PLAN: []}

        self.logger.info(f"Generating enhanced HyDE documents for {len(research_plan)} sub-queries...")

        # Analyze all sub-queries for mathematical content first
        mathematical_analysis = await self._analyze_mathematical_content(research_plan)
        
        # Create a list of tasks to run concurrently with mathematical context
        tasks = [
            self._generate_enhanced_hyde_for_subquery(sq, mathematical_analysis) 
            for sq in research_plan
        ]
        
        # Run tasks and gather results
        updated_plan_steps = await asyncio.gather(*tasks)

        # Track mathematical enhancement statistics
        math_enhanced_count = sum(1 for step in updated_plan_steps if step.get("has_mathematical_context", False))
        
        self.logger.info(f"All HyDE documents generated successfully. "
                        f"{math_enhanced_count}/{len(updated_plan_steps)} enhanced with mathematical context.")
        
        return {
            RESEARCH_PLAN: updated_plan_steps,
            "hyde_mathematical_enhancement_stats": {
                "total_queries": len(updated_plan_steps),
                "math_enhanced_count": math_enhanced_count,
                "mathematical_analysis": mathematical_analysis
            }
        }

    async def _analyze_mathematical_content(self, research_plan: List[str]) -> Dict[str, Any]:
        """
        Analyze the entire research plan for mathematical content patterns.
        
        Args:
            research_plan: List of sub-query strings or dictionaries
            
        Returns:
            Dictionary containing mathematical content analysis
        """
        all_queries_text = ""
        query_analysis = {}
        
        for i, query_item in enumerate(research_plan):
            # Handle both string queries and dictionary format from planning
            if isinstance(query_item, dict):
                query_text = query_item.get("sub_query", str(query_item))
            else:
                query_text = str(query_item)
            
            all_queries_text += f" {query_text}"
            
            # Analyze each query individually
            query_math_analysis = self.equation_detector.resolve_equation_references(query_text)
            if (query_math_analysis["equation_references"] or 
                query_math_analysis["table_references"] or 
                query_math_analysis["context_sections"]):
                query_analysis[i] = query_math_analysis
        
        # Analyze overall mathematical content
        overall_analysis = self.equation_detector.resolve_equation_references(all_queries_text)
        
        self.logger.info(f"Mathematical content analysis: {len(overall_analysis['equation_references'])} equation refs, "
                        f"{len(overall_analysis['table_references'])} table refs, "
                        f"{len(overall_analysis['context_sections'])} sections detected")
        
        return {
            "overall_analysis": overall_analysis,
            "individual_query_analysis": query_analysis,
            "has_mathematical_content": bool(
                overall_analysis["equation_references"] or 
                overall_analysis["table_references"] or 
                overall_analysis["context_sections"]
            )
        }

    async def _generate_enhanced_hyde_for_subquery(
        self, 
        sub_query_item: Any, 
        mathematical_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhanced helper coroutine to generate HyDE documents with mathematical context awareness.
        
        Args:
            sub_query_item: A sub-query string or dictionary from the research plan
            mathematical_analysis: Results from mathematical content analysis
            
        Returns:
            Enhanced dictionary containing the original sub-query, hyde_document, and mathematical metadata
        """
        # Handle both string queries and dictionary format
        if isinstance(sub_query_item, dict):
            sub_query = sub_query_item.get("sub_query", str(sub_query_item))
            original_hyde = sub_query_item.get("hyde_document", "")
        else:
            sub_query = str(sub_query_item)
            original_hyde = ""
        
        # Detect mathematical content in this specific sub-query
        query_math_analysis = self.equation_detector.resolve_equation_references(sub_query)
        has_math_content = bool(
            query_math_analysis["equation_references"] or 
            query_math_analysis["table_references"] or 
            query_math_analysis["context_sections"]
        )
        
        # Generate enhanced HyDE document
        loop = asyncio.get_running_loop()
        if has_math_content:
            hyde_document = await loop.run_in_executor(
                None, self._generate_mathematical_hyde, sub_query, query_math_analysis
            )
        else:
            # Use standard HyDE generation for non-mathematical queries
            hyde_document = await loop.run_in_executor(
                None, self.hyde_tool, sub_query
            )
        
        return {
            "sub_query": sub_query,
            "hyde_document": hyde_document,
            "has_mathematical_context": has_math_content,
            "mathematical_references": {
                "equation_refs": len(query_math_analysis["equation_references"]),
                "table_refs": len(query_math_analysis["table_references"]),
                "section_refs": len(query_math_analysis["context_sections"])
            },
            "mathematical_analysis": query_math_analysis if has_math_content else None
        }

    def _generate_mathematical_hyde(self, sub_query: str, math_analysis: Dict[str, Any]) -> str:
        """
        Generate a HyDE document specifically enhanced for mathematical content.
        Uses a specialized prompt that includes mathematical context without generating LaTeX.
        
        Args:
            sub_query: The sub-query string
            math_analysis: Mathematical content analysis results
            
        Returns:
            Generated HyDE document with mathematical context
        """
        try:
            # Extract mathematical context information
            equation_refs = [ref["reference"] for ref in math_analysis["equation_references"]]
            table_refs = [ref["reference"] for ref in math_analysis["table_references"]]
            section_refs = math_analysis["context_sections"]
            
            # Build context information for the prompt
            math_context_info = []
            if equation_refs:
                math_context_info.append(f"References equations: {', '.join(equation_refs)}")
            if table_refs:
                math_context_info.append(f"References tables: {', '.join(table_refs)}")
            if section_refs:
                math_context_info.append(f"Relates to sections: {', '.join(section_refs)}")
            
            math_context_text = "; ".join(math_context_info) if math_context_info else "Contains mathematical content"
            
            # Enhanced HyDE prompt for mathematical content
            MATHEMATICAL_HYDE_PROMPT = f"""
You are a seasoned building code expert and technical writer for the state of Virginia.
Your task is to generate a hypothetical document that looks and reads *exactly* like an excerpt from the official Virginia Building Code, with special attention to mathematical and technical content.

**Mathematical Context Detected:**
{math_context_text}

**Your Persona & Style:**
- **Formal and Regulatory:** Use precise, formal, and unambiguous language.
- **Authoritative Tone:** Employ terms like "shall," "is permitted," "is required," and "in accordance with Section X.X."
- **Structure:** Mimic the hierarchical structure of code documents (e.g., "Section 1604.3.1 stipulates...").
- **Mathematical Awareness:** When mathematical content is involved, reference formulas, calculations, variables, and numerical requirements naturally.
- **Technical Detail:** Be specific about technical terms, standards, conditions, and mathematical relationships.

**Special Instructions for Mathematical Content:**
- Reference mathematical formulas by their designation (e.g., "Equation 16-7", "Formula in Section 1607.12")
- Mention variables, parameters, and calculation procedures when relevant
- Include references to tables that contain numerical values or coefficients
- Describe mathematical relationships conceptually without generating specific LaTeX expressions
- Reference calculation procedures and methodologies described in the code

**The User's Sub-Query:**
"{sub_query}"

**Your Task:**
Based on the sub-query and the detected mathematical context, write a concise, single-paragraph hypothetical document. This document should represent the *ideal* passage from the building code that would perfectly answer the sub-query, with proper attention to any mathematical, formula, or calculation aspects.

**Example for Mathematical Content:**
- **Sub-Query:** "What is the formula for calculating reduced live loads in Section 1607.12?"
- **Your Document:** "Section 1607.12 of the Virginia Building Code provides the methodology for live load reduction in structural design. The reduction formula specified in Equation 16-7 shall be used to calculate the reduced live load based on the tributary area and the number of floors contributing to the member. The variables in this equation include the tributary area, influence area, and appropriate reduction factors as defined in the code. This calculation procedure applies to structural members supporting multiple floors and shall not exceed the maximum reduction percentages specified in the accompanying tables."

**Your Hypothetical Document (single paragraph, text only):**
"""
            
            # Generate the enhanced HyDE document
            response = self.model.invoke(MATHEMATICAL_HYDE_PROMPT)
            hyde_document = response.content.strip()
            
            # Basic cleanup
            if hyde_document.startswith('"') and hyde_document.endswith('"'):
                hyde_document = hyde_document[1:-1]
                
            self.logger.info(f"Successfully generated mathematical HyDE document for query with {len(equation_refs)} equation refs")
            return hyde_document
            
        except Exception as e:
            self.logger.error(f"Error during mathematical HyDE document generation: {e}", exc_info=True)
            # Fallback to standard HyDE generation
            return self.hyde_tool(sub_query)

    def _validate_agent_specific_state(self, state: AgentState) -> None:
        """Validate that the research_plan is present in the state."""
        if RESEARCH_PLAN not in state or not state[RESEARCH_PLAN]:
            raise ValueError("research_plan is required for HydeAgent")

    def _apply_agent_specific_updates(self, state: AgentState, output_data: Dict[str, Any]) -> AgentState:
        """Update the state with the HyDE results and mathematical metadata."""
        state[RESEARCH_PLAN] = output_data[RESEARCH_PLAN]
        
        # Initialize mathematical_metadata if it doesn't exist
        if "mathematical_metadata" not in state or state["mathematical_metadata"] is None:
            state["mathematical_metadata"] = {}
            
        state["mathematical_metadata"]["hyde_enhancement"] = output_data["hyde_mathematical_enhancement_stats"]
        
        # Add a log entry to intermediate_outputs
        intermediate_log = state.get("intermediate_outputs", [])
        if not isinstance(intermediate_log, list):
            intermediate_log = []
        
        intermediate_log.append({
            "step": "hyde_generation",
            "agent": self.agent_name,
            "log": "Generated hypothetical documents for all sub-queries."
        })
        state["intermediate_outputs"] = intermediate_log
        
        return state 