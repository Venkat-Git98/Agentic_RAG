"""
Thinking-Enhanced Calculation Executor

This agent performs mathematical calculations with Docker execution
while providing detailed reasoning about the code generation and execution process.
"""

import sys
import os
import json
import time
from typing import Dict, Any, List, Optional
import docker
import logging
from datetime import datetime

from agents.base_agent import BaseLangGraphAgent
from state import AgentState
from thinking_logger import ThinkingLogger, ThinkingMixin, ThinkingMode
from config import USE_DOCKER

class ThinkingCalculationExecutor(BaseLangGraphAgent, ThinkingMixin):
    """
    Executes mathematical calculations based on research results.
    This agent can use either a secure Docker environment or LLM reasoning
    based on the `USE_DOCKER` configuration.
    """
    
    def __init__(self, thinking_mode: ThinkingMode = ThinkingMode.SIMPLE):
        """
        Initialize the Thinking Calculation Executor.
        
        Args:
            thinking_mode: The mode of thinking to use (simple or detailed)
        """
        super().__init__(model_tier="tier_1", agent_name="ThinkingCalculationExecutor")
        ThinkingMixin.__init__(self, agent_name="ThinkingCalculationExecutor", thinking_mode=thinking_mode)
        
        # Defer Docker availability check to when it's actually needed
        self.docker_available = False
        
        self.logger.info("Thinking-enhanced Calculation Executor initialized")

    def _check_docker_availability(self) -> bool:
        """Check if Docker is available and working - STRICT requirement."""
        try:
            client = docker.from_env()
            client.ping()
            self.logger.info("🐳 Docker is available and responding.")
            self.thinking_logger.recap("Docker check complete")
            return True
        except Exception as e:
            self.logger.warning(f"Could not connect to Docker: {e}")
            self.thinking_logger.recap("Docker check complete")
            return False
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute the calculation logic based on configuration.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with calculation results
        """
        user_query = state.get("user_query", "")
        calc_types = state.get("research_validation_results", {}).get("calculation_types", [])
        
        if USE_DOCKER:
            return await self._execute_docker_flow(state, user_query, calc_types)
        else:
            return await self._execute_llm_flow(state, user_query, calc_types)
    
    async def _execute_docker_flow(self, state: AgentState, user_query: str, calc_types: List[str]) -> Dict[str, Any]:
        """Execute calculations using Docker."""
        
        # Check for Docker availability only when this flow is triggered
        self.docker_available = self._check_docker_availability()
        
        if not self.docker_available:
            self.thinking_logger.problem("Docker is enabled but not available. Cannot execute calculations.")
            return self._create_docker_required_error_with_thinking()
            
        with self.thinking_logger.creative_process("Docker-Based Code Execution"):
            if not self._validate_prerequisites_with_thinking(state):
                return self._create_error_state_with_thinking("Missing prerequisites for calculation")
            
            # Extract calculation specs
            specs = self._extract_calculation_specs_with_thinking(state)
            
            # Generate Python code for calculation
            code = await self._generate_calculation_code_with_thinking(specs, state)
            
            # Execute code in Docker container
            docker_results = await self._execute_with_docker_only(code, specs)
            
            # Prepare state updates
            return self._prepare_calculation_state_updates_with_thinking(specs, docker_results, state)

    async def _execute_llm_flow(self, state: AgentState, user_query: str, calc_types: List[str]) -> Dict[str, Any]:
        """Execute calculations using LLM reasoning."""
        
        with self.thinking_logger.creative_process("LLM-Based Mathematical Reasoning"):
            if not self._validate_prerequisites_with_thinking(state):
                return self._create_error_state_with_thinking("Missing prerequisites for LLM calculation")
            
            # Extract calculation specs
            specs = self._extract_calculation_specs_with_thinking(state)
            
            # Execute LLM-based reasoning
            llm_results = await self._execute_with_llm_reasoning(specs, state)
            
            # Prepare state updates
            return self._prepare_calculation_state_updates_with_thinking(specs, llm_results, state)
            
    def _validate_prerequisites_with_thinking(self, state: AgentState) -> bool:
        """Validate prerequisites with thinking process."""
        
        self.thinking_logger.think("Checking prerequisites for calculation...")
        
        # Check for required validation results
        validation_results = state.get("research_validation_results")
        if not validation_results:
            self.thinking_logger.problem("🚫 Research validation results are missing")
            return False
            
        # Check for research context
        research_context = state.get("sub_query_answers")
        if not research_context:
            self.thinking_logger.problem("🚫 Research context (sub-query answers) is missing")
            return False
        
        # Check for calculation types
        calc_types = validation_results.get("calculation_types")
        if not calc_types:
            self.thinking_logger.problem("🚫 No calculation types identified in validation results")
            return False
        
        self.thinking_logger.success("✅ All prerequisites met")
        return True

    def _extract_calculation_specs_with_thinking(self, state: AgentState) -> Dict[str, Any]:
        """Extract calculation specs with thinking."""
        
        self.thinking_logger.craft("Extracting calculation specifications from state...")
        
        validation_results = state.get("research_validation_results", {})
        
        specs = {
            "user_query": state.get("user_query", ""),
            "research_context": state.get("sub_query_answers", []),
            "calculation_types": validation_results.get("calculation_types", []),
            "complexity": validation_results.get("complexity", "moderate")
        }
        
        self.thinking_logger.note(f"Extracted specs for {len(specs['calculation_types'])} calculation types")
        return specs
        
    async def _execute_with_docker_only(self, code: str, specs: Dict[str, Any]) -> Dict[str, Any]:
        """Executes Python code in a secure Docker container."""
        
        with self.thinking_logger.creative_process("Docker Code Execution"):
            start_time = time.time()
            total_attempts = 3
            
            for attempt in range(1, total_attempts + 1):
                self.thinking_logger.attempt(f"Executing code in Docker (Attempt {attempt}/{total_attempts})...")
                
                # Prepare Docker environment
                try:
                    client = docker.from_env()
                    
                    # Run in Docker container
                    container_start_time = time.time()
                    
                    self.thinking_logger.calculating_step("🐳 Launching Docker container with Python 3.11...")
                    
                    container = client.containers.run(
                        "python:3.11-slim",
                        command=["python", "-c", code],
                        detach=True,
                        mem_limit="256m",
                        cpu_shares=512,
                        network_disabled=True
                    )
                    
                    # Wait for container to finish
                    result = container.wait(timeout=30)
                    
                    # Get logs
                    output = container.logs(stdout=True, stderr=False).decode("utf-8").strip()
                    error = container.logs(stdout=False, stderr=True).decode("utf-8").strip()
                    
                    execution_time = time.time() - container_start_time
                    
                    # Clean up
                    container.remove(force=True)
                    
                    if result["StatusCode"] == 0 and not error:
                        self.thinking_logger.success(f"✅ Docker execution successful in {execution_time:.2f}s")
                        
                        return {
                            "success": True,
                            "output": output,
                            "error": "",
                            "execution_time": execution_time,
                            "attempts": attempt
                        }
                    else:
                        self.thinking_logger.problem(f"🚫 Docker execution failed on attempt {attempt}: {error or 'Unknown error'}")
                        if "MemoryError" in (error or ""):
                            self.thinking_logger.adapt("MemoryError detected, not retrying")
                            break
                        
                except docker.errors.ContainerError as e:
                    self.thinking_logger.problem(f"🚫 Docker container error on attempt {attempt}: {e}")
                    error = str(e)
                except docker.errors.ImageNotFound:
                    self.thinking_logger.problem("🚫 python:3.11-slim image not found. Please pull it.")
                    error = "Docker image not found"
                    break
                except Exception as e:
                    self.thinking_logger.problem(f"🚫 Unexpected error on attempt {attempt}: {e}")
                    error = str(e)
                    break
            
            total_execution_time = time.time() - start_time
            
            self.thinking_logger.problem("🚫 All Docker execution attempts failed.")
            
            return {
                "success": False,
                "output": "",
                "error": error or "All Docker attempts failed",
                "execution_time": total_execution_time,
                "attempts": total_attempts,
                "final_attempt": attempt
            }

    def _prepare_calculation_state_updates_with_thinking(self, specs: Dict[str, Any], results: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Prepare state updates with thinking."""
        
        with self.thinking_logger.creative_process("Preparing State Updates"):
            self.thinking_logger.craft("Processing calculation results and preparing state for synthesis...")
            
            if results["success"]:
                self.thinking_logger.success("✅ Calculation successful")
                
                # Combine original context with calculation results
                combined_context = state.get("sub_query_answers", []) + [{
                    "sub_query": "Calculation Results",
                    "answer": results["output"]
                }]
                
                return {
                    "sub_query_answers": combined_context,
                    "calculation_results": results,
                    "calculation_execution_success": True,
                    "error_state": None
                }
            else:
                self.thinking_logger.problem("Calculation failed, preserving original research context.")
                # On failure, we don't want to modify the sub_query_answers
                return {
                    "calculation_results": results,
                    "calculation_execution_success": False,
                    "error_state": {
                        "agent": "ThinkingCalculationExecutor",
                        "message": results.get("error", "Unknown calculation error")
                    }
                }

    def _format_research_for_code_generation(self, research_results: List[Dict]) -> str:
        """Format research for code generation."""
        
        self.thinking_logger.think("Formatting research context for code generation...")
        
        formatted_text = ""
        for item in research_results:
            formatted_text += f"- **Sub-query:** {item.get('sub_query', 'N/A')}\n"
            formatted_text += f"  - **Answer:** {item.get('answer', 'N/A')}\n\n"
        
        self.thinking_logger.note("Research context formatted successfully")
        return formatted_text

    def _extract_python_code_with_thinking(self, response: str) -> str:
        """Extract Python code with thinking."""
        
        self.thinking_logger.think("Extracting Python code from LLM response...")
        
        # Check for code blocks
        if "```python" in response:
            start = response.find("```python") + len("```python")
            end = response.find("```", start)
            if end != -1:
                code = response[start:end].strip()
                self.thinking_logger.success(f"✅ Extracted code block ({len(code)} characters)")
                return code
        
        # Try to find any code-like content
        lines = response.split('\\n')
        code_lines = []
        for line in lines:
            if (line.strip().startswith(('import ', 'def ', 'if ', 'for ', 'while ', 'print(', '#')) 
                or '=' in line or any(op in line for op in ['+', '-', '*', '/'])):
                code_lines.append(line)
        
        if code_lines:
            code = '\\n'.join(code_lines)
            self.thinking_logger.success(f"✅ Extracted code from mixed content ({len(code)} characters)")
            return code
        
        self.thinking_logger.warning("⚠️ No clear Python code found - returning response as-is")
        return response.strip()
    
    def _create_fallback_code_with_thinking(self, specs: Dict[str, Any]) -> str:
        """Create fallback code with thinking."""
        
        self.thinking_logger.craft("Creating fallback calculation code...")
        
        code = '''import math

# Fallback calculation for building code query
print("Performing fallback calculation...")

# Simple wind pressure calculation (common building code formula)
wind_speed = 85  # mph (from user query if available)
pressure = 0.00256 * (wind_speed ** 2)

print(f"Wind speed: {wind_speed} mph")
print(f"Calculated wind pressure: {pressure:.2f} psf")
print("Note: This is a simplified calculation. Consult building code for complete requirements.")
'''
        
        self.thinking_logger.note("Created simple wind pressure fallback calculation")
        return code
    
    def _create_error_state_with_thinking(self, error_message: str) -> Dict[str, Any]:
        """Create error state with thinking."""
        
        self.thinking_logger.problem(f"Creating error state: {error_message}")
        
        return {
            "calculation_execution_success": False,
            "calculation_errors": [error_message],
            "current_step": "synthesis",
            "workflow_status": "running",
            "context_enhanced_with_math": False,
            "synthesis_context_ready": True,
            "calculation_thinking_summary": self.thinking_logger.get_thinking_summary()
        }

    def _create_docker_required_error_with_thinking(self) -> Dict[str, Any]:
        """Create Docker required error state with thinking."""
        
        self.thinking_logger.problem("Docker setup required error")
        
        return {
            "calculation_execution_success": False,
            "calculation_errors": ["Docker setup required"],
            "current_step": "synthesis",
            "workflow_status": "running",
            "context_enhanced_with_math": False,
            "synthesis_context_ready": True,
            "calculation_thinking_summary": self.thinking_logger.get_thinking_summary()
        }

    async def _execute_with_llm_reasoning(self, specs: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Execute calculations via LLM reasoning (when USE_DOCKER=False)."""
        
        with self.thinking_logger.creative_process("LLM-Based Mathematical Reasoning"):
            start_time = time.time()
            
            self.thinking_logger.consider("Performing mathematical calculations via advanced language model reasoning")
            self.thinking_logger.consider(f"Calculation types: {', '.join(specs['calculation_types'])}")
            
            # Create calculation prompt
            calculation_prompt = f"""
            Perform precise mathematical calculations for this building code query.
            
            USER QUERY: {specs['user_query']}
            
            CALCULATION TYPES: {specs['calculation_types']}
            COMPLEXITY: {specs['complexity']}
            
            RESEARCH CONTEXT: {self._format_research_for_code_generation(specs['research_context'])}
            
            REQUIREMENTS:
            1. Show detailed step-by-step calculations
            2. Use precise formulas and building code standards
            3. Include all intermediate steps
            4. Provide final numerical results with proper units
            5. Explain the reasoning behind each calculation step
            
            Format your response as a complete mathematical solution.
            """
            
            try:
                self.thinking_logger.attempt("Generating LLM-based calculation solution...")
                
                # Use Tier 1 model for precise calculations
                response = await self.model.generate_content_async(calculation_prompt)
                calculation_result = response.text.strip()
                
                execution_time = time.time() - start_time
                
                if calculation_result and len(calculation_result) > 50:
                    self.thinking_logger.sudden_realization(f"🎉 LLM calculation successful! Generated in {execution_time:.3f}s")
                    self.thinking_logger.getting_clearer_picture(f"LLM reasoning: {calculation_result[:200]}{'...' if len(calculation_result) > 200 else ''}")
                    
                    return {
                        "success": True,
                        "output": calculation_result,
                        "error": "",
                        "execution_time": execution_time,
                        "attempts": 1,
                        "method": "LLM_reasoning",
                        "total_execution_time": execution_time,
                        "final_attempt": 1,
                        "code": f"# LLM Reasoning for: {specs['user_query'][:100]}..."
                    }
                else:
                    self.thinking_logger.having_second_thoughts("LLM calculation produced insufficient output")
                    return {
                        "success": False,
                        "output": "",
                        "error": "LLM calculation produced insufficient output",
                        "execution_time": execution_time,
                        "attempts": 1,
                        "method": "LLM_reasoning"
                    }
                    
            except Exception as e:
                execution_time = time.time() - start_time
                error_msg = str(e)
                self.thinking_logger.problem(f"🚫 LLM calculation failed: {error_msg}")
                
                return {
                    "success": False,
                    "output": "",
                    "error": f"LLM calculation error: {error_msg}",
                    "execution_time": execution_time,
                    "attempts": 1,
                    "method": "LLM_reasoning"
                }

    async def _generate_calculation_code_with_thinking(self, specs: Dict[str, Any], state: AgentState) -> str:
        """Generate Python code with detailed thinking."""
        
        with self.thinking_logger.creative_process("Python Code Generation"):
            self.thinking_logger.think("Analyzing calculation requirements and crafting appropriate Python code...")
            
            self.thinking_logger.consider(f"Need to handle: {', '.join(specs['calculation_types'])}")
            self.thinking_logger.consider(f"Complexity level: {specs['complexity']}")
            
            code_prompt = f"""
            Generate Python code for building code calculations using ONLY the math library.

            USER QUERY: {specs['user_query']}
            
            CALCULATION TYPES: {specs['calculation_types']}
            
            RESEARCH CONTEXT:
            {self._format_research_for_code_generation(specs['research_context'])}

            REQUIREMENTS:
            1. Use ONLY Python's built-in math library (import math)
            2. Include clear variable definitions with comments
            3. Show step-by-step calculations with intermediate results
            4. Print all results with descriptive labels
            5. Handle potential errors gracefully
            6. Use building code standard units (psf, psi, ft, etc.)

            Generate complete, executable Python code with print statements:
            """
            
            self.thinking_logger.reason("Sending code generation request to LLM...")
            
            try:
                response = await self.generate_content_async(code_prompt)
                code = self._extract_python_code_with_thinking(response)
                
                # Ensure math import is included
                if "import math" not in code:
                    self.thinking_logger.adapt("Adding missing math import to generated code")
                    code = "import math\n\n" + code
                
                code_lines = len(code.split('\n'))
                self.thinking_logger.success(f"✅ Generated {code_lines} lines of Python code")
                return code
                
            except Exception as e:
                self.thinking_logger.problem(f"LLM code generation failed: {str(e)}")
                self.thinking_logger.adapt("Falling back to template-based code generation")
                return self._create_fallback_code_with_thinking(specs)

    def _validate_agent_specific_state(self, state: AgentState) -> None:
        """Validate agent specific state."""
        pass
        
    def _apply_agent_specific_updates(self, state: AgentState, output_data: Dict[str, Any]) -> AgentState:
        """Apply agent specific updates."""
        return super()._apply_agent_specific_updates(state, output_data)
        
    def _handle_error(self, state: AgentState, error: Exception) -> AgentState:
        """Handle agent specific errors."""
        return super()._handle_error(state, error)
        
    def _extract_input_summary(self, state: AgentState) -> Dict[str, Any]:
        """Extract input summary."""
        return super()._extract_input_summary(state)
        
    def sanitize_for_logging(self, data: Any, max_length: int = 150) -> str:
        """Sanitize data for logging."""
        return super().sanitize_for_logging(data, max_length)
        
    async def generate_content_async(self, prompt: str, **kwargs) -> str:
        """Generate content asynchronously."""
        return await super().generate_content_async(prompt, **kwargs)
        
class ThinkingMixin:
    def __init__(self, agent_name: str, thinking_mode: ThinkingMode = ThinkingMode.SIMPLE):
        self.thinking_logger = ThinkingLogger(
            agent_name=agent_name,
            console_output=True,
            detailed_logging=True,
            thinking_mode=thinking_mode
        ) 