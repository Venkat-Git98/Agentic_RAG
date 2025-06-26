"""
Implements the core ReAct dispatcher loop for the agent.
"""
import logging
import json
import re
from typing import Dict, Any, List
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from config import TIER_1_MODEL_NAME
from react_agent.master_agent_prompt import get_master_prompt
from react_agent.tools_registry import TOOL_REGISTRY, TOOLS_DESCRIPTION

def _sanitize_for_logging(data: Any, max_len: int = 150) -> Any:
    """Recursively sanitizes data for logging, truncating long strings and summarizing lists."""
    if isinstance(data, dict):
        return {k: _sanitize_for_logging(v, max_len) for k, v in data.items()}
    elif isinstance(data, list):
        if len(data) > 3:
            return f"[List with {len(data)} items]"
        return [_sanitize_for_logging(item, max_len) for item in data]
    elif isinstance(data, str) and len(data) > max_len:
        return data[:max_len] + "..."
    return data

class ReActDispatcher:
    """
    Orchestrates the ReAct "thought-action-observation" loop.
    """
    def __init__(self, conversation_manager, max_loops=15):
        self.conversation_manager = conversation_manager
        self.max_loops = max_loops
        self.model = genai.GenerativeModel(TIER_1_MODEL_NAME) # Use top-tier model for reasoning
        self.history: List[Dict[str, Any]] = []
        self.last_observation: Dict[str, Any] = {} # Holds the full data from the last observation

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parses the <thought> and <action> blocks from the LLM's raw response.
        """
        thought_match = re.search(r"<thought>(.*?)</thought>", response_text, re.DOTALL)
        action_match = re.search(r"<action>(.*?)</action>", response_text, re.DOTALL)

        if not thought_match:
            raise ValueError("Invalid response: Missing <thought> block.")
        if not action_match:
            raise ValueError("Invalid response: Missing <action> block.")

        thought = thought_match.group(1).strip()
        action_str = action_match.group(1).strip()

        try:
            action = json.loads(action_str)
            if "tool" not in action or "args" not in action:
                raise ValueError("Invalid action JSON: Must have 'tool' and 'args' keys.")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid action: Not a valid JSON object. Got: {action_str}")

        return {"thought": thought, "action": action}

    def run(self, initial_query: str):
        """
        Executes the main ReAct loop.
        """
        logging.info("--- Starting New ReAct Execution Loop ---")
        
        # Initial prompt setup
        prompt = get_master_prompt(TOOLS_DESCRIPTION)
        self.history.append({"role": "user", "parts": [{"text": prompt}]})
        
        # Inject the initial query and context
        context_payload = self.conversation_manager.get_contextual_payload()
        user_turn = f"""
        **Initial Query:**
        {initial_query}

        **Conversation Context:**
        {context_payload}
        
        Now, begin the thought-action process.
        """
        self.history.append({"role": "user", "parts": [{"text": user_turn}]})
        
        for i in range(self.max_loops):
            logging.info(f"--- Loop {i+1}/{self.max_loops} ---")
            
            # 1. THINK & ACT
            llm_response = self.model.generate_content(self.history)
            self.history.append(llm_response.candidates[0].content)
            
            try:
                parsed = self._parse_llm_response(llm_response.text)
                thought, action = parsed["thought"], parsed["action"]
                logging.info(f"Thought: {thought}")
            except ValueError as e:
                logging.error(f"Error parsing LLM response: {e}")
                observation = {"error": f"Invalid response format: {e}"}
            else:
                # 2. EXECUTE TOOL
                tool_name = action.get("tool")
                tool_args = action.get("args", {})

                # --- INTELLIGENT ARGUMENT INJECTION ---
                # This is a critical step to ensure data integrity between agent loops.
                # The LLM can sometimes fail to pass large JSON objects or forget context.
                # We override its arguments with the full data from the previous step.
                if self.last_observation:
                    # Inject the research plan AND original query into the parallel research tool
                    if tool_name == "execute_parallel_research":
                        if "plan" in self.last_observation:
                            logging.info("Injecting full research plan into parallel research tool.")
                            tool_args["plan"] = self.last_observation["plan"]
                        # The tool also needs the original query for context
                        tool_args["original_query"] = initial_query
                        logging.info("Injecting original query into parallel research tool.")

                    # Inject the generated sub-answers into the synthesis tool
                    if tool_name == "synthesize_final_answer" and "sub_answers" in self.last_observation:
                        logging.info("Injecting full sub-answers into synthesis tool.")
                        tool_args["sub_answers"] = self.last_observation["sub_answers"]
                    
                    # Inject the final answer into the finish tool
                    if tool_name == "finish" and "final_answer" in self.last_observation:
                        logging.info("Injecting full final answer into finish tool.")
                        tool_args["answer"] = self.last_observation["final_answer"]
                
                # Log the action *after* argument injection to get the full, rich data.
                logging.info(f"Action: {json.dumps({'tool': tool_name, 'args': tool_args}, default=str)}")
                
                if tool_name == "finish":
                    final_answer = tool_args.get("answer", "No answer provided.")
                    logging.info(f"Finish tool called. Final Answer: {final_answer}")
                    return final_answer
                
                if tool_name in TOOL_REGISTRY:
                    tool = TOOL_REGISTRY[tool_name]
                    # Pass context payload to the planning tool
                    if tool_name == "create_research_plan":
                         tool_args["context_payload"] = context_payload
                    try:
                        observation = tool(**tool_args)
                        self.last_observation = observation # Store the full observation
                        
                        # Handle all outcomes from the planning tool
                        if tool_name == "create_research_plan":
                            classification = observation.get("classification")
                            if classification == "simple_answer":
                                logging.info("Planning tool provided a simple answer. Finishing execution.")
                                return observation.get("direct_answer", "The query was answered directly.")
                            elif classification == "reject":
                                logging.info("Planning tool rejected the query. Finishing execution.")
                                return observation.get("direct_answer", "The query was determined to be not relevant.")
                            # If 'engage', the loop continues with the plan stored in the observation.

                    except Exception as e:
                        logging.error(f"Error executing tool '{tool_name}': {e}")
                        observation = {"error": f"Tool execution failed: {str(e)}"}
                else:
                    observation = {"error": f"Tool '{tool_name}' not found."}
            
            # 3. OBSERVE
            # Log the full, unsanitized observation to the file
            logging.info(f"Observation: {observation}")
            # Sanitize the observation ONLY for the LLM's history
            sanitized_observation = _sanitize_for_logging(observation)
            observation_turn = f"<observation>\n{json.dumps(sanitized_observation)}\n</observation>"
            self.history.append({"role": "user", "parts": [{"text": observation_turn}]})

        logging.warning("Max loops reached. Ending execution.")
        return "The agent could not reach a conclusion within the allowed number of steps." 