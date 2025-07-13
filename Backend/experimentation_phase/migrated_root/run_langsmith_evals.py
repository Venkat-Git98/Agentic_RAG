import asyncio
import os
import uuid
from typing import List, Dict, Any

from langsmith import Client
from langsmith.evaluation import aevaluate, LangChainStringEvaluator, EvaluationResult
from langsmith.schemas import Run, Example
from langchain_google_genai import ChatGoogleGenerativeAI

from main import LangGraphAgenticAI
from config import LANGCHAIN_PROJECT

# --- Configuration ---
# The name for the dataset you'll create in LangSmith
DATASET_NAME = "Agentic AI Golden Dataset"

# The name for the evaluation project
EVALUATION_PROJECT_NAME = f"Eval-{LANGCHAIN_PROJECT}-{uuid.uuid4().hex[:8]}"

# --- LangSmith Client ---
# Initialize the LangSmith client
# This automatically picks up the environment variables
client = Client()


async def run_agent(example: Dict[str, Any]) -> Dict[str, Any]:
    """
    Function to run the agent for a single example.
    This is what the evaluator will call for each row in your dataset.
    """
    agent = LangGraphAgenticAI()
    thread_id = f"eval-thread-{uuid.uuid4().hex[:8]}"
    
    final_answer = ""
    # We need to aggregate the streaming response to get the full, final answer
    async for chunk in agent.get_response_stream(example["input"], thread_id):
        if "final_answer" in chunk:
            final_answer = chunk["final_answer"]

    return {"output": final_answer}


def create_evaluators() -> List[LangChainStringEvaluator]:
    """
    Define the evaluators to grade the agent's responses.
    We use AI-assisted evaluators to grade on multiple dimensions using the 'criteria' evaluator.
    """
    # Define the LLM to be used for evaluation. We use Gemini Pro for high-quality grading.
    # This avoids the default dependency on OpenAI's gpt-4.
    eval_llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0)

    # The 'criteria' evaluator uses the specified LLM to grade the output
    # based on a specific question.
    evaluators = [
        # Correctness Evaluator
        LangChainStringEvaluator(
            "criteria",
            config={
                "llm": eval_llm,
                "criteria": {
                    "correctness": "Is the submission factually correct, accurate, and verifiable based on the reference answer provided in the 'output' key?"
                },
            },
        ),
        # Conciseness Evaluator
        LangChainStringEvaluator(
            "criteria",
            config={
                "llm": eval_llm,
                "criteria": {
                    "conciseness": "Is the submission concise and to the point, without unnecessary verbiage?"
                },
            },
        ),
        # Helpfulness Evaluator
        LangChainStringEvaluator(
            "criteria",
            config={
                "llm": eval_llm,
                "criteria": {
                    "helpfulness": "Is the submission helpful, relevant, and directly addresses the user's query from the 'input' key?"
                },
            },
        ),
        # Coherence Evaluator
        LangChainStringEvaluator(
            "criteria",
            config={
                "llm": eval_llm,
                "criteria": {
                    "coherence": "Is the submission coherent, well-structured, and easy to read?"
                },
            },
        ),
    ]
    return evaluators


def print_results(results: EvaluationResult):
    """Print a summary of the evaluation results."""
    print("="*50)
    print("✅ EVALUATION COMPLETE")
    print("="*50)
    
    results_list = results._results

    # Check if results were generated
    if not results_list:
        print("No results were generated. Please check the LangSmith project for errors.")
        return

    # Extract the experiment ID from the first run to build a link
    first_run = results_list[0]
    # Access the run ID from the 'run' object within the result dictionary
    experiment_id = first_run['run'].id
    project_url = f"https://smith.langchain.com/experiments/s/{experiment_id}"
    print(f"📊 View detailed results in LangSmith: {project_url}\n")
    
    # Aggregate and print scores
    summary: Dict[str, List[float]] = {}
    for result in results_list:
        # Scores are in a nested dictionary
        if 'evaluation_results' in result and 'results' in result['evaluation_results']:
            for eval_result in result['evaluation_results']['results']:
                key = eval_result.key
                score = eval_result.score
                if key not in summary:
                    summary[key] = []
                if score is not None:
                    summary[key].append(score)

    if not summary:
        print("No evaluation scores found in the results.")
        return

    print("📊 Evaluation Summary:")
    for key, scores in summary.items():
        if scores:
            avg_score = sum(scores) / len(scores)
            print(f"  - {key}: Average Score = {avg_score:.2f}")
        else:
            print(f"  - {key}: No scores recorded")
    
    print("\n" + "="*50)


async def main():
    """
    Main function to set up and run the evaluation.
    """
    # Create dataset from the CSV file if it doesn't exist
    if not client.has_dataset(dataset_name=DATASET_NAME):
        print(f"Dataset '{DATASET_NAME}' not found. Creating it from CSV...")
        client.upload_csv(
            csv_file="data/langsmith_evaluation_dataset.csv",
            input_keys=["input"],
            output_keys=["output"],
            name=DATASET_NAME,
            description="Golden dataset for evaluating the Agentic AI system.",
        )
        print("✅ Dataset created successfully.")
    else:
        print(f"Found existing dataset: '{DATASET_NAME}'")

    # Define evaluators
    evaluators = create_evaluators()

    # Run the evaluation
    print(f"\n🚀 Running evaluation... project: {EVALUATION_PROJECT_NAME}")
    
    results = await aevaluate(
        run_agent,  # The async function that runs our agent
        data=DATASET_NAME,  # The name of the dataset in LangSmith
        evaluators=evaluators,  # The evaluators to score the results
        experiment_prefix="Agent-Evaluation",  # A prefix for the project name
        max_concurrency=4,  # Run up to 4 evaluations in parallel
    )
    
    # The async aevaluate function returns an object where the results are stored in the ._results attribute
    print_results(results)


if __name__ == "__main__":
    # Ensure you have set the LANGCHAIN environment variables before running
    if not all([os.getenv("LANGCHAIN_TRACING_V2"), os.getenv("LANGCHAIN_API_KEY")]):
        print("❌ Error: LANGCHAIN_TRACING_V2 and LANGCHAIN_API_KEY must be set.")
    else:
        asyncio.run(main()) 