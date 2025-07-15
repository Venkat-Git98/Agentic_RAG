"""
Thinking-Style Logger for AI Agents

This module provides a human-readable logging system that shows the AI agent's
reasoning process in a stream-of-consciousness format, similar to modern
thinking models like o1 or deep research models.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from contextlib import contextmanager
import json
from enum import Enum
import re

class ThinkingMode(Enum):
    """Thinking display modes"""
    SIMPLE = 1      # User-facing, clean and impressive
    DETAILED = 2    # Full understanding with more context

class ThinkingLogger:
    """
    Human-readable thinking process logger that shows AI reasoning flow.
    """
    
    # Clean thinking style prefixes (no emojis)
    ANALYZING = ""
    DECIDING = "" 
    CONSIDERING = ""
    DISCOVERING = ""
    VALIDATING = ""
    QUESTIONING = ""
    ADAPTING = ""
    CONCLUDING = ""
    PROBLEM = ""
    SUCCESS = ""
    WARNING = ""
    ATTEMPT = ""
    REVIEW = ""
    CRAFTING = ""
    REASONING = ""
    WEIGHING = ""
    NOTING = ""
    CONNECTING = ""
    WONDERING = ""
    REALIZING = ""
    STEPPING_BACK = ""
    DRILLING_DOWN = ""
    
    def __init__(self, agent_name: str, console_output: bool = True, detailed_logging: bool = True, thinking_mode: ThinkingMode = ThinkingMode.SIMPLE):
        """
        Initialize thinking logger for an agent.
        
        Args:
            agent_name: Name of the agent (e.g., "ValidationAgent")
            console_output: Whether to print thinking to console
            detailed_logging: Whether to include detailed step analysis
            thinking_mode: Simple or detailed thinking display mode
        """
        self.agent_name = agent_name
        self.console_output = console_output
        self.detailed_logging = detailed_logging
        self.thinking_mode = thinking_mode
        
        # Problem context (optional, for enhanced thinking)
        self.problem_context = None
        
        # Thinking session tracking
        self.session_start = None
        self.thinking_steps = []
        self.current_depth = 0
        self.step_counter = 0
        
        # Human-like thinking patterns
        self.user_query_analysis = None
        self.thinking_momentum = []  # Track thinking flow
        
        # Setup logging
        self.logger = logging.getLogger(f"Thinking.{agent_name}")
        self.logger.setLevel(logging.INFO)
        
        # Create thinking session
        self._start_thinking_session()
    
    def _start_thinking_session(self):
        """Start a new thinking session."""
        self.session_start = datetime.now()
        self.thinking_steps = []
        self.step_counter = 0
        
        if self.console_output:
            if self.thinking_mode == ThinkingMode.SIMPLE:
                print(f"\n{self.agent_name.upper()}")
            else:
                print(f"\n{'='*60}")
                print(f"{self.agent_name.upper()} THINKING SESSION")
                print(f"{'='*60}")
    
    def _log_step(self, emoji: str, action: str, content: str, depth: int = None, visibility_mode: ThinkingMode = ThinkingMode.DETAILED):
        """Log a thinking step with proper formatting."""
        if depth is None:
            depth = self.current_depth
        
        self.step_counter += 1
        
        # Create step record
        step = {
            "step": self.step_counter,
            "timestamp": datetime.now().isoformat(),
            "depth": depth,
            "action": action,
            "content": content,
            "emoji": emoji,
            "visibility": visibility_mode
        }
        self.thinking_steps.append(step)
        
        # Check if this step should be shown in current mode
        if visibility_mode.value > self.thinking_mode.value:
            return  # Skip if step requires higher detail level
        
        # Console output
        if self.console_output:
            if self.thinking_mode == ThinkingMode.SIMPLE:
                # Clean format without emojis
                prefix = "├─ " if action != "Result" else "└─ "
                print(f"{prefix}{action}: {content}")
            else:
                # Original detailed format without emojis
                indent = "│   " * depth
                if depth > 0:
                    prefix = "├─ " if depth == 1 else "└─ "
                else:
                    prefix = ""
                
                print(f"{indent}{prefix}{action}: {content}")
        
        # Detailed logging
        if self.detailed_logging:
            self.logger.info(f"[{action}] {content}")
    
    # Core thinking methods
    def think(self, content: str):
        """Agent is thinking/processing."""
        self._log_step(self.ANALYZING, "Thinking", content)
    
    def analyze(self, content: str):
        """Agent is analyzing information."""
        self._log_step(self.ANALYZING, "Analyzing", content)
    
    def consider(self, content: str):
        """Agent is considering options."""
        self._log_step(self.CONSIDERING, "Considering", content)
    
    def discover(self, content: str):
        """Agent discovered something important."""
        self._log_step(self.DISCOVERING, "Discovering", content)
    
    def decide(self, content: str):
        """Agent made a decision."""
        self._log_step(self.DECIDING, "Deciding", content)
    
    def conclude(self, content: str):
        """Agent reached a conclusion."""
        self._log_step(self.CONCLUDING, "Concluding", content)
    
    def reason(self, content: str):
        """Agent is reasoning through logic."""
        self._log_step(self.REASONING, "Reasoning", content)
    
    def weigh(self, content: str):
        """Agent is weighing options."""
        self._log_step(self.WEIGHING, "Weighing", content)
    
    def question(self, content: str):
        """Agent is questioning something."""
        self._log_step(self.QUESTIONING, "Questioning", content)
    
    def wondering(self, content: str):
        """Agent is wondering about something."""
        self._log_step(self.WONDERING, "Wondering", content)
    
    def adapt(self, content: str):
        """Agent is adapting approach."""
        self._log_step(self.ADAPTING, "Adapting", content)
    
    def validate(self, content: str):
        """Agent is validating something."""
        self._log_step(self.VALIDATING, "Validating", content)
    
    def note(self, content: str):
        """Agent is noting something important."""
        self._log_step(self.NOTING, "Noting", content)
    
    def review(self, content: str):
        """Agent is reviewing something."""
        self._log_step(self.REVIEW, "Reviewing", content)
    
    def craft(self, content: str):
        """Agent is crafting/creating something."""
        self._log_step(self.CRAFTING, "Crafting", content)
    
    # Status methods
    def success(self, content: str):
        """Something succeeded."""
        self._log_step(self.SUCCESS, "Success", content)
    
    def problem(self, content: str):
        """Agent encountered a problem."""
        self._log_step(self.PROBLEM, "Problem", content)
    
    def warning(self, content: str):
        """Agent has a warning."""
        self._log_step(self.WARNING, "Warning", content)
    
    def attempt(self, content: str):
        """Agent is attempting something."""
        self._log_step(self.ATTEMPT, "Attempting", content)
    
    # New clean thinking methods for structured output
    def goal(self, content: str, mode: ThinkingMode = ThinkingMode.SIMPLE):
        """Agent's goal or objective."""
        self._log_step("", "Goal", content, visibility_mode=mode)
    
    def key_facts(self, content: str, mode: ThinkingMode = ThinkingMode.DETAILED):
        """Key facts agent is working with."""
        self._log_step("", "Key Facts", content, visibility_mode=mode)
    
    def reasoning_step(self, content: str, mode: ThinkingMode = ThinkingMode.SIMPLE):
        """Agent's reasoning process."""
        self._log_step("", "Reasoning", content, visibility_mode=mode)
    
    def decision_made(self, content: str, mode: ThinkingMode = ThinkingMode.SIMPLE):
        """Final decision made by agent."""
        self._log_step("", "Decision", content, visibility_mode=mode)
    
    def result_achieved(self, content: str, mode: ThinkingMode = ThinkingMode.SIMPLE):
        """Result or outcome achieved."""
        self._log_step("", "Result", content, visibility_mode=mode)
    
    # Enhanced problem-aware thinking methods (universal for all query types)
    def understanding_problem(self, content: str, mode: ThinkingMode = ThinkingMode.SIMPLE):
        """Show understanding of the specific problem being asked."""
        self._log_step("", "Understanding", content, visibility_mode=mode)
    
    def breaking_down(self, content: str, mode: ThinkingMode = ThinkingMode.SIMPLE):
        """Show breaking down the problem into manageable parts."""
        self._log_step("", "Breaking down", content, visibility_mode=mode)
    
    def checking_requirements(self, content: str, mode: ThinkingMode = ThinkingMode.SIMPLE):
        """Show checking code requirements, constraints, or conditions."""
        self._log_step("", "Checking", content, visibility_mode=mode)
    
    def calculating_step(self, content: str, mode: ThinkingMode = ThinkingMode.SIMPLE):
        """Show specific calculation or mathematical step being performed."""
        self._log_step("", "Calculating", content, visibility_mode=mode)
    
    def discovering(self, content: str, mode: ThinkingMode = ThinkingMode.SIMPLE):
        """Show discovering or finding important information."""
        self._log_step("", "Found", content, visibility_mode=mode)
    
    def concluding_answer(self, content: str, mode: ThinkingMode = ThinkingMode.SIMPLE):
        """Show final conclusion or answer being reached."""
        self._log_step("", "Conclusion", content, visibility_mode=mode)
    
    # Universal problem analysis methods (work with any query type)
    def analyze_query_intent(self, user_query: str) -> str:
        """Analyze what the user is asking for (universal)."""
        query_lower = user_query.lower()
        
        # Extract key question words
        if any(word in query_lower for word in ["calculate", "compute", "determine"]):
            return "calculation"
        elif any(word in query_lower for word in ["what", "requirements", "rules"]):
            return "information_lookup"
        elif any(word in query_lower for word in ["how", "procedure", "steps"]):
            return "process_explanation"
        elif any(word in query_lower for word in ["can i", "permitted", "allowed"]):
            return "compliance_check"
        else:
            return "general_inquiry"
    
    def extract_key_details(self, user_query: str) -> List[str]:
        """Extract key details from any query (universal)."""
        details = []
        
        # Extract numbers with units (works for any engineering query)
        number_patterns = [
            r'(\d+(?:\.\d+)?)\s*(psf|psi|mph|ft|in|sq\s*ft|square\s*feet?)',
            r'(\d+(?:\.\d+)?)\s*(story|stories|floor|floors)',
            r'(\d+(?:\.\d+)?)\s*(inch|inches|foot|feet)',
        ]
        
        for pattern in number_patterns:
            matches = re.findall(pattern, user_query, re.IGNORECASE)
            for match in matches:
                details.append(f"{match[0]} {match[1]}")
        
        # Extract building types
        building_types = ["office", "residential", "commercial", "industrial"]
        for building_type in building_types:
            if building_type in user_query.lower():
                details.append(f"{building_type} building")
        
        # Extract code sections
        section_matches = re.findall(r'section\s+(\d+(?:\.\d+)*)', user_query, re.IGNORECASE)
        for section in section_matches:
            details.append(f"Section {section}")
        
        return details
    
    def show_problem_understanding(self, user_query: str):
        """Show understanding of the problem (works with any query)."""
        intent = self.analyze_query_intent(user_query)
        details = self.extract_key_details(user_query)
        
        # Create natural understanding based on intent
        if intent == "calculation":
            if details:
                self.understanding_problem(f"Need to calculate something with: {', '.join(details)}")
            else:
                self.understanding_problem("Mathematical calculation or engineering computation needed")
        
        elif intent == "information_lookup":
            if details:
                self.understanding_problem(f"Looking up requirements/rules for: {', '.join(details)}")
            else:
                self.understanding_problem("Need to find specific code requirements or information")
        
        elif intent == "compliance_check":
            if details:
                self.understanding_problem(f"Checking if something is permitted with: {', '.join(details)}")
            else:
                self.understanding_problem("Need to verify code compliance or permissions")
        
        elif intent == "process_explanation":
            self.understanding_problem("Need step-by-step process or procedure explanation")
        
        else:
            # Fallback for any query type
            if details:
                self.understanding_problem(f"Analyzing building code question involving: {', '.join(details)}")
            else:
                self.understanding_problem("Building code inquiry requiring research and analysis")
    
    # Context managers for structured thinking
    @contextmanager
    def thinking_block(self, title: str):
        """Context manager for a block of thinking."""
        if self.console_output:
            print(f"\n{title.upper()}")
        
        self.current_depth += 1
        try:
            yield self
        finally:
            self.current_depth -= 1
    
    @contextmanager
    def decision_point(self, question: str):
        """Context manager for decision-making process."""
        self._log_step(self.QUESTIONING, "Decision Point", question)
        self.current_depth += 1
        try:
            yield self
        finally:
            self.current_depth -= 1
    
    @contextmanager
    def analysis_block(self, analysis_type: str):
        """Context manager for detailed analysis."""
        self._log_step(self.ANALYZING, "Starting Analysis", analysis_type)
        self.current_depth += 1
        try:
            yield self
        finally:
            self.current_depth -= 1
    
    @contextmanager
    def execution_block(self, execution_type: str):
        """Context manager for execution process."""
        self._log_step(self.ATTEMPT, "Starting Execution", execution_type)
        self.current_depth += 1
        try:
            yield self
        finally:
            self.current_depth -= 1
    
    @contextmanager
    def creative_process(self, creation_type: str):
        """Context manager for creative/generation process."""
        self._log_step(self.CRAFTING, "Creative Process", creation_type)
        self.current_depth += 1
        try:
            yield self
        finally:
            self.current_depth -= 1
    
    @contextmanager
    def decision_tree(self, root_question: str):
        """Context manager for decision tree analysis."""
        self._log_step(self.DECIDING, "Decision Tree", root_question)
        self.current_depth += 1
        try:
            yield self
        finally:
            self.current_depth -= 1
    
    def start_section(self, section_name: str):
        """Start a major thinking section."""
        if self.console_output:
            print(f"\n{section_name}")
            print("─" * len(section_name))
    
    def end_session(self) -> Dict[str, Any]:
        """End thinking session and return summary."""
        if self.console_output:
            duration = (datetime.now() - self.session_start).total_seconds()
            print(f"\n{'─' * 60}")
            print(f"SESSION COMPLETE ({duration:.2f}s, {len(self.thinking_steps)} steps)")
            print(f"{'=' * 60}")
        
        return {
            "agent_name": self.agent_name,
            "session_duration": (datetime.now() - self.session_start).total_seconds(),
            "total_steps": len(self.thinking_steps),
            "thinking_steps": self.thinking_steps,
            "session_start": self.session_start.isoformat(),
            "session_end": datetime.now().isoformat()
        }
    
    def get_thinking_summary(self) -> str:
        """Get a summary of the thinking process."""
        if not self.thinking_steps:
            return "No thinking steps recorded."
        
        summary_parts = []
        summary_parts.append(f"Agent: {self.agent_name}")
        summary_parts.append(f"Steps: {len(self.thinking_steps)}")
        
        # Group by action types
        action_counts = {}
        for step in self.thinking_steps:
            action = step["action"]
            action_counts[action] = action_counts.get(action, 0) + 1
        
        summary_parts.append("Actions: " + ", ".join([f"{action}({count})" for action, count in action_counts.items()]))
        
        return " | ".join(summary_parts)

    # === HUMAN-LIKE THINKING METHODS ===
    
    def initial_impression(self, content: str):
        """First reaction to the query - like human first impression."""
        self._log_step(self.WONDERING, "Initial Impression", content)
    
    def deeper_look(self, content: str):
        """Taking a deeper look at something - natural follow-up."""
        self._log_step(self.DRILLING_DOWN, "Looking Deeper", content)
    
    def connecting_dots(self, content: str):
        """Making connections between pieces of information."""
        self._log_step(self.CONNECTING, "Connecting", content)
    
    def stepping_back(self, content: str):
        """Taking a step back to see the bigger picture."""
        self._log_step(self.STEPPING_BACK, "Step Back", content)
    
    def sudden_realization(self, content: str):
        """Moment of insight or sudden understanding."""
        self._log_step(self.REALIZING, "Realization", content)
    
    def building_on_thought(self, content: str):
        """Building on a previous thought - natural progression."""
        self._log_step(self.REASONING, "Building On", content)
    
    def checking_intuition(self, content: str):
        """Checking if initial intuition was right."""
        self._log_step(self.VALIDATING, "Checking", content)
    
    def reconsidering(self, content: str):
        """Second-guessing or reconsidering approach."""
        self._log_step(self.ADAPTING, "Reconsidering", content)
    
    # === ENHANCED QUERY ANALYSIS ===
    
    def analyze_query_deeply(self, user_query: str):
        """Perform deep, human-like analysis of the user's query."""
        
        with self.thinking_block("Understanding What You're Really Asking"):
            # Initial impression
            self.initial_impression(f"You're asking: '{user_query}'")
            
            # Break down the query naturally
            self.deeper_look("Let me break this down...")
            
            # Analyze complexity
            word_count = len(user_query.split())
            if word_count <= 5:
                self.note("This is a concise question - likely looking for specific information")
            elif word_count <= 15:
                self.note("Moderate complexity - probably needs some research and explanation")
            else:
                self.note("Complex, detailed question - will need comprehensive analysis")
            
            # Extract intent with human reasoning
            intent = self.analyze_query_intent(user_query)
            self.connecting_dots(f"This looks like a '{intent}' type question")
            
            # Look for key technical details
            details = self.extract_key_details(user_query)
            if details:
                self.discovering(f"Key technical details I noticed: {', '.join(details)}")
                self.building_on_thought("These details will help me provide a precise answer")
            else:
                self.question("No specific technical details mentioned - might need to ask clarifying questions")
            
            # Consider what makes this challenging
            self._analyze_query_complexity(user_query)
            
            # Set expectations
            self._set_thinking_approach(user_query, intent, details)
    
    def _analyze_query_complexity(self, user_query: str):
        """Analyze what makes this query complex or simple."""
        complexity_indicators = []
        
        # Check for multiple concepts
        building_terms = ["foundation", "structure", "fire", "electrical", "plumbing", "accessibility"]
        mentioned_terms = [term for term in building_terms if term.lower() in user_query.lower()]
        
        if len(mentioned_terms) > 2:
            complexity_indicators.append("multiple building systems involved")
        
        # Check for calculations
        if any(word in user_query.lower() for word in ["calculate", "determine", "size", "load"]):
            complexity_indicators.append("mathematical calculations required")
        
        # Check for comparisons
        if any(word in user_query.lower() for word in ["vs", "versus", "compare", "difference"]):
            complexity_indicators.append("comparison analysis needed")
        
        # Check for code sections
        if re.search(r'section\s+\d', user_query, re.IGNORECASE):
            complexity_indicators.append("specific code section lookup")
        
        if complexity_indicators:
            self.reasoning_step(f"This is complex because: {', '.join(complexity_indicators)}")
        else:
            self.note("Straightforward question - should be able to answer directly")
    
    def _set_thinking_approach(self, user_query: str, intent: str, details: List[str]):
        """Set the approach for thinking through this problem."""
        
        if intent == "calculation":
            self.decide("I'll need to find the right formulas and walk through the math step by step")
        elif intent == "information_lookup":
            self.decide("I'll search for the specific code requirements and explain them clearly")
        elif intent == "compliance_check":
            self.decide("I'll need to check multiple requirements and see if they're met")
        elif intent == "process_explanation":
            self.decide("I'll break this down into clear, sequential steps")
        else:
            self.decide("I'll research thoroughly and provide a comprehensive explanation")
        
        # Show thinking about approach
        if details:
            self.building_on_thought(f"I'll pay special attention to: {', '.join(details)}")
    
    # === NATURAL PROBLEM SOLVING FLOW ===
    
    def working_through_problem(self, step_description: str):
        """Show natural problem-solving progression."""
        self._log_step(self.REASONING, "Working Through", step_description)
    
    def having_second_thoughts(self, content: str):
        """Natural second-guessing of approach."""
        self._log_step(self.QUESTIONING, "Second Thoughts", content)
    
    def getting_clearer_picture(self, content: str):
        """Understanding is becoming clearer."""
        self._log_step(self.DISCOVERING, "Getting Clearer", content)
    
    def piecing_together(self, content: str):
        """Putting pieces of information together."""
        self._log_step(self.CONNECTING, "Piecing Together", content)
    
    def thinking_out_loud(self, content: str):
        """Stream of consciousness thinking."""
        self._log_step(self.WONDERING, "Thinking", content)
    
    def making_progress(self, content: str):
        """Showing progress in understanding."""
        self._log_step(self.SUCCESS, "Progress", content)
    
    # === ENHANCED DISPLAY METHODS ===
    
    def show_comprehensive_understanding(self, user_query: str):
        """Show comprehensive, human-like understanding of the problem."""
        
        # Start with query analysis
        self.analyze_query_deeply(user_query)
        
        # Show what comes next
        with self.thinking_block("Planning My Approach"):
            self.working_through_problem("Now I need to gather the right information to answer this properly")
            
            # Show anticipation of challenges
            if "calculate" in user_query.lower():
                self.thinking_out_loud("I'll need to be careful with the math - building codes have specific formulas")
            elif any(word in user_query.lower() for word in ["requirements", "rules", "must"]):
                self.thinking_out_loud("Need to make sure I get all the requirements - missing one could be problematic")
            elif "compare" in user_query.lower():
                self.thinking_out_loud("Comparisons can be tricky - need to be fair and comprehensive")
            
            self.decide("Let me start researching this systematically")

class ThinkingMixin:
    """
    Mixin class to add thinking capabilities to existing agents.
    """
    
    def _init_thinking(self, agent_name: str = None, thinking_mode: ThinkingMode = ThinkingMode.SIMPLE):
        """Initialize thinking logger for the agent."""
        if agent_name is None:
            agent_name = self.__class__.__name__
        
        self.thinking_logger = ThinkingLogger(
            agent_name=agent_name,
            console_output=getattr(self, 'debug_mode', True),
            detailed_logging=True,
            thinking_mode=thinking_mode
        )
    
    def _end_thinking_session(self) -> Dict[str, Any]:
        """End thinking session and return summary."""
        if hasattr(self, 'thinking_logger'):
            return self.thinking_logger.end_session()
        return {} 