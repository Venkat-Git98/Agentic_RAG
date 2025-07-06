import json
import subprocess
import sys
from datetime import datetime
import time
import os
import argparse

def run_test_suite(test_id_to_run=None):
    """
    Reads the test suite, runs each test case against the main agent script,
    and saves the detailed results.
    """
    try:
        with open('testing_suite.json', 'r') as f:
            test_cases = json.load(f)
    except FileNotFoundError:
        print("ERROR: testing_suite.json not found. Please ensure the file exists.")
        return
    except json.JSONDecodeError:
        print("ERROR: Could not decode testing_suite.json. Please check for syntax errors.")
        return

    if test_id_to_run:
        test_cases = [tc for tc in test_cases if tc.get("test_id") == test_id_to_run]
        if not test_cases:
            print(f"ERROR: Test case with ID '{test_id_to_run}' not found in testing_suite.json.")
            return

    total_tests = len(test_cases)
    print(f"Found {total_tests} test cases. Starting the test run...")
    print("="*80)

    all_results = []
    start_time = time.time()

    for i, test_case in enumerate(test_cases, 1):
        test_id = test_case.get("test_id", f"unnamed-test-{i}")
        query = test_case.get("query")

        if not query:
            print(f"SKIPPING Test {i}/{total_tests} ({test_id}): No query found.")
            continue

        print(f"RUNNING Test {i}/{total_tests}: {test_id}...")
        print(f"  Query: {query}")

        try:
            # Execute the main.py script as a subprocess
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            process = subprocess.Popen(
                [sys.executable, 'main.py', '--query', query],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                env=env
            )
            
            # Get the output
            stdout, stderr = process.communicate(timeout=180) # 3-minute timeout per test

            if process.returncode != 0:
                print(f"  ERROR for Test {i}/{total_tests} ({test_id}). Return code: {process.returncode}")
                print(f"  Stderr: {stderr}")

            # Store the result
            result_data = {
                "test_case": test_case,
                "execution_timestamp": datetime.now().isoformat(),
                "status": "passed" if process.returncode == 0 else "failed",
                "stdout": stdout,
                "stderr": stderr
            }
            all_results.append(result_data)
            print(f"  COMPLETED Test {i}/{total_tests} ({test_id})")

        except subprocess.TimeoutExpired:
            print(f"  TIMEOUT for Test {i}/{total_tests} ({test_id}). Test took too long.")
            result_data = {
                "test_case": test_case,
                "execution_timestamp": datetime.now().isoformat(),
                "status": "timeout",
                "stdout": "",
                "stderr": "Test execution timed out after 3 minutes."
            }
            all_results.append(result_data)
        except Exception as e:
            print(f"  CRITICAL ERROR for Test {i}/{total_tests} ({test_id}): {e}")
            result_data = {
                "test_case": test_case,
                "execution_timestamp": datetime.now().isoformat(),
                "status": "critical_error",
                "stdout": "",
                "stderr": str(e)
            }
            all_results.append(result_data)
        
        print("-" * 40)

    end_time = time.time()
    total_duration = end_time - start_time

    # Save the results to a file
    with open('test_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)

    print("="*80)
    print("Test run complete.")
    print(f"Total tests executed: {total_tests}")
    print(f"Total duration: {total_duration:.2f} seconds")
    print("Results have been saved to test_results.json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the AI agent test suite.")
    parser.add_argument('--test_id', type=str, help='Run a single test case by its ID.')
    args = parser.parse_args()

    run_test_suite(args.test_id)