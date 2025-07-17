import os
import json
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import re

# Configure logging


# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
EVALUATION_LOG_FILE = 'test_results.json'
TEST_SUITE_FILE = 'testing_suite.json'
RESULTS_CSV_FILE = 'evaluation_results.csv'
GEMINI_MODEL = 'gemini-2.5-pro' # Or your preferred Gemini model

# --- Gemini API Configuration ---
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")
    genai.configure(api_key=api_key)
    logging.info("Google Generative AI configured successfully.")
except Exception as e:
    logging.error(f"Failed to configure Google Generative AI: {e}")
    # Exit or handle gracefully if the API key is essential
    exit()


# --- Evaluation Prompt Template ---
EVALUATION_PROMPT = """
As an expert AI system evaluator, your task is to analyze the performance of an agentic AI based on its response to a user query.
You will be provided with the original query, the expected outcome, the agent's final answer, and a summary of its execution trace.

Please perform a comprehensive analysis and provide your evaluation in a structured JSON format.

**Evaluation Criteria:**

1.  **Accuracy (1-5):** How factually correct is the answer?
    - 1: Completely inaccurate.
    - 3: Partially correct but with significant errors.
    - 5: Completely accurate and factually sound.

2.  **Completeness (1-5):** Does the answer fully address all parts of the user's query?
    - 1: Completely misses the core question.
    - 3: Addresses some parts of the query but misses others.
    - 5: Thoroughly addresses all explicit and implicit parts of the query.

3.  **Relevance (1-5):** Is the answer directly relevant to the query without unnecessary information?
    - 1: Mostly irrelevant or contains significant off-topic information.
    - 3: Generally relevant but includes some unnecessary details.
    - 5: Highly relevant and concise.

4.  **Efficiency (1-5):** Did the agent take a logical and efficient path to the answer?
    - 1: Highly inefficient path with many unnecessary steps or tool calls.
    - 3: The path was somewhat logical but could have been more direct.
    - 5: The agent used the optimal path and tools to answer the query.

**Input Data:**

*   **User Query:** {query}
*   **Expected Outcome:** {expected_outcome}
*   **Agent's Final Answer:** {final_answer}
*   **Execution Summary:** {trace_summary}

**Your Task:**

Based on the provided data, return a single JSON object with the following keys. Do NOT include any explanatory text outside the JSON object.

-   `accuracy_score` (integer): Your score for Accuracy.
-   `accuracy_rationale` (string): Your detailed justification for the accuracy score.
-   `completeness_score` (integer): Your score for Completeness.
-   `completeness_rationale` (string): Your detailed justification for the completeness score.
-   `relevance_score` (integer): Your score for Relevance.
-   `relevance_rationale` (string): Your detailed justification for the relevance score.
-   `efficiency_score` (integer): Your score for Efficiency.
-   `efficiency_rationale` (string): Your justification, paying close attention to the agent's tool usage (e.g., was web search necessary? Were internal tools used correctly?).
-   `final_verdict` (string): A summary of your overall assessment. State whether the agent "PASSED" or "FAILED" based on a holistic view of its performance for this specific query.

**Example JSON Output:**
```json
{{
  "accuracy_score": 5,
  "accuracy_rationale": "The answer correctly identifies the live load requirements based on the ASCE 7-16 standard mentioned in the knowledge base.",
  "completeness_score": 4,
  "completeness_rationale": "The answer provides the correct live loads but does not explain the context of where in the standard this is found, which would have been helpful.",
  "relevance_score": 5,
  "relevance_rationale": "The response is highly relevant and focuses entirely on the user's question about roof design live loads.",
  "efficiency_score": 3,
  "efficiency_rationale": "The agent used a web search even though the information was available in its internal knowledge graph. This was an unnecessary step.",
  "final_verdict": "PASSED"
}}
```
"""

def get_gemini_evaluation(query, expected_outcome, final_answer, trace_summary):
    """
    Calls the Gemini API to get an evaluation of the agent's performance.

    Args:
        query (str): The original user query.
        expected_outcome (str): The expected outcome from the test suite.
        final_answer (str): The agent's final generated answer.
        trace_summary (dict): A summary of the execution trace from stderr.

    Returns:
        dict: A dictionary containing the parsed JSON evaluation from Gemini.
              Returns a failure dictionary if the API call fails or the response is invalid.
    """
    if not final_answer or final_answer == "N/A":
        return {
            "accuracy_score": 1, "accuracy_rationale": "No final answer was produced.",
            "completeness_score": 1, "completeness_rationale": "No final answer was produced.",
            "relevance_score": 1, "relevance_rationale": "No final answer was produced.",
            "efficiency_score": 1, "efficiency_rationale": "Agent failed to produce an answer.",
            "final_verdict": "FAILED",
        }
        
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        prompt = EVALUATION_PROMPT.format(
            query=query,
            expected_outcome=json.dumps(expected_outcome, indent=2),
            final_answer=final_answer,
            trace_summary=json.dumps(trace_summary, indent=2) # Pass the summary
        )
        response = model.generate_content(prompt)

        # Clean the response and extract the JSON object
        cleaned_response = response.text.strip()
        json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        else:
            logging.error(f"Could not find a valid JSON object in Gemini's response. Raw response: {cleaned_response}")
            return None

    except Exception as e:
        logging.error(f"Error during Gemini API call or parsing: {e}")
        return None

def analyze_trace(stderr_log: str) -> dict:
    """
    Performs deterministic analysis on the execution trace from stderr.

    Args:
        stderr_log (str): The raw stderr string from the test execution.

    Returns:
        dict: A dictionary with analysis results (e.g., tool usage).
    """
    tool_calls = {}
    web_searches = []
    
    # Regex to find agent/tool executions
    # Example log: 2025-07-05 20:25:19,659 - PlanningAgent - INFO - Starting execution of EnhancedPlanningAgent
    # Example log: 2025-07-05 20:26:17,547 - root - WARNING - Keyword context insufficient. Triggering Fallback 2: Web Search with Query Optimization.
    
    agent_pattern = re.compile(r"INFO - Starting execution of ([\w\d]+)")
    tool_pattern = re.compile(r"INFO - Executing ([\w\d\s]+) Tool")
    web_search_pattern = re.compile(r"INFO - Executing Tavily search for query: '(.*)'")
    fallback_pattern = re.compile(r"WARNING - .* Triggering Fallback \d+: (.*)\.")

    for line in stderr_log.split('\\n'): # Split by escaped newline
        agent_match = agent_pattern.search(line)
        if agent_match:
            agent_name = agent_match.group(1)
            tool_calls[agent_name] = tool_calls.get(agent_name, 0) + 1
            
        tool_match = tool_pattern.search(line)
        if tool_match:
            tool_name = tool_match.group(1).strip()
            tool_calls[tool_name] = tool_calls.get(tool_name, 0) + 1
            
        web_match = web_search_pattern.search(line)
        if web_match:
            query = web_match.group(1)
            web_searches.append(query)
        
        fallback_match = fallback_pattern.search(line)
        if fallback_match:
            fallback_name = fallback_match.group(1).strip()
            tool_calls[fallback_name] = tool_calls.get(fallback_name, 0) + 1


    return {
        "tool_calls": tool_calls,
        "web_search_queries": web_searches,
        "web_search_count": len(web_searches)
    }

def main():
    """
    Main function to run the evaluation analysis.
    """
    logging.info("Starting evaluation analysis...")

    # Load test suite
    try:
        with open(TEST_SUITE_FILE, 'r') as f:
            test_suite = json.load(f)
        test_cases = {case['test_id']: case for case in test_suite}
        logging.info(f"Loaded {len(test_cases)} test cases from {TEST_SUITE_FILE}")
    except FileNotFoundError:
        logging.error(f"Test suite file not found: {TEST_SUITE_FILE}")
        return
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {TEST_SUITE_FILE}")
        return


    # Load evaluation logs
    try:
        with open(EVALUATION_LOG_FILE, 'r') as f:
            eval_logs = json.load(f)
        logging.info(f"Loaded {len(eval_logs)} logs from {EVALUATION_LOG_FILE}")
    except FileNotFoundError:
        logging.error(f"Evaluation log file not found: {EVALUATION_LOG_FILE}")
        return
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {EVALUATION_LOG_FILE}")
        return

    results = []
    for log_entry in eval_logs:
        test_case = log_entry.get("test_case", {})
        test_id = test_case.get("test_id")

        if not test_id or test_id not in test_cases:
            logging.warning(f"Skipping log with missing or invalid test_id in test_case: {test_id}")
            continue

        query = test_case.get('query', 'N/A')
        expected_outcome = test_case.get('expected_outcome', {})
        status = log_entry.get('status', 'unknown')
        stdout_str = log_entry.get('stdout', '')
        stderr_str = log_entry.get('stderr', '')
        
        logging.info(f"--- Analyzing Test Case ID: {test_id} (Status: {status}) ---")
        logging.info(f"Query: {query}")
        
        # Handle timeout cases first
        if status == 'timeout':
            results.append({
                'test_id': test_id,
                'persona': test_case.get('persona', 'N/A'),
                'difficulty': test_case.get('difficulty', 'N/A'),
                'query': query,
                'expected_outcome': json.dumps(expected_outcome),
                'final_answer': "Test execution timed out.",
                'tool_calls': {},
                'web_search_queries': [],
                'web_search_count': 0,
                'accuracy_score': 1, 'accuracy_rationale': 'Timeout',
                'completeness_score': 1, 'completeness_rationale': 'Timeout',
                'relevance_score': 1, 'relevance_rationale': 'Timeout',
                'efficiency_score': 1, 'efficiency_rationale': 'Timeout',
                'final_verdict': 'FAILED'
            })
            continue

        # Extract final answer from stdout
        final_answer = "N/A"
        answer_marker = "Response:"
        if answer_marker in stdout_str:
            # Find the last occurrence of the marker and get everything after it
            parts = stdout_str.split(answer_marker)
            final_answer_raw = parts[-1]
            
            # Clean up the answer by removing the session complete marker and extra whitespace
            session_complete_marker = "============================================================"
            if session_complete_marker in final_answer_raw:
                final_answer = final_answer_raw.split(session_complete_marker)[0].strip()
            else:
                final_answer = final_answer_raw.strip()
        elif "I need more information" in stdout_str:
             final_answer = "Agent requested clarification."
        else:
            final_answer = "No final answer produced in stdout."


        # 1. Deterministic Analysis from stderr
        trace_analysis = analyze_trace(stderr_str)
        logging.info(f"Tool usage: {trace_analysis['tool_calls']}")
        if trace_analysis['web_search_count'] > 0:
            logging.info(f"Web searches performed: {trace_analysis['web_search_queries']}")

        # 2. LLM-as-a-Judge Evaluation
        logging.info("Getting evaluation from Gemini...")
        llm_eval = get_gemini_evaluation(query, expected_outcome, final_answer, trace_analysis)

        if not llm_eval:
            logging.error(f"Failed to get LLM evaluation for test case {test_id}. Marking as FAILED.")
            llm_eval = {
                'accuracy_score': 1, 'accuracy_rationale': 'LLM evaluation failed.',
                'completeness_score': 1, 'completeness_rationale': 'LLM evaluation failed.',
                'relevance_score': 1, 'relevance_rationale': 'LLM evaluation failed.',
                'efficiency_score': 1, 'efficiency_rationale': 'LLM evaluation failed.',
                'final_verdict': 'FAILED'
            }
        
        logging.info(f"Gemini evaluation received: {llm_eval.get('final_verdict', 'N/A')}")

        # 3. Combine results
        combined_result = {
            'test_id': test_id,
            'persona': test_case.get('persona', 'N/A'),
            'difficulty': test_case.get('difficulty', 'N/A'),
            'query': query,
            'expected_outcome': json.dumps(expected_outcome, indent=2),
            'final_answer': final_answer,
            **trace_analysis,
            **llm_eval
        }
        results.append(combined_result)

    if not results:
        logging.warning("No results were processed. Exiting.")
        return
        
    # 4. Save results to CSV
    try:
        df = pd.DataFrame(results)
        df.to_csv(RESULTS_CSV_FILE, index=False)
        logging.info(f"Full evaluation results saved to {RESULTS_CSV_FILE}")
    except Exception as e:
        logging.error(f"Failed to save results to CSV: {e}")


    # 5. Print summary
    logging.info("\n--- Evaluation Summary ---")
    summary_df = df[[
        'test_id', 'difficulty', 'final_verdict', 'accuracy_score', 
        'completeness_score', 'relevance_score', 'efficiency_score', 'web_search_count'
    ]]
    print(summary_df.to_string())

    # Aggregate stats
    avg_scores = df[['accuracy_score', 'completeness_score', 'relevance_score', 'efficiency_score']].mean()
    pass_rate = (df['final_verdict'] == 'PASSED').mean() * 100
    total_web_searches = df['web_search_count'].sum()

    print("\n--- Aggregate Statistics ---")
    print(f"Overall Pass Rate: {pass_rate:.2f}%")
    print(f"Total Web Searches Performed: {total_web_searches}")
    print("Average Scores (out of 5):")
    print(avg_scores.to_string())


if __name__ == "__main__":
    main() 