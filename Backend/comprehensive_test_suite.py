import asyncio
import json
import datetime
import uuid
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

from main import LangGraphAgenticAI

class ComprehensiveTestSuite:
    def __init__(self, test_file_path):
        self.test_queries = self._load_test_queries(test_file_path)
        self.results = []
        self.start_time = None
        self.end_time = None

    def _load_test_queries(self, test_file_path):
        console = Console()
        try:
            with open(test_file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            console.print(f"[bold red]Error: Test queries file not found at '{test_file_path}'[/bold red]")
            return []
        except json.JSONDecodeError:
            console.print(f"[bold red]Error: Could not decode JSON from '{test_file_path}'[/bold red]")
            return []

    async def run(self):
        console = Console()
        if not self.test_queries:
            console.print("[bold yellow]No test queries to run.[/bold yellow]")
            return

        self.start_time = datetime.datetime.now()
        console.print(f"[bold green]Starting comprehensive test suite at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}[/bold green]")

        with Progress(console=console) as progress:
            task = progress.add_task("[cyan]Running test suite...[/cyan]", total=len(self.test_queries))
            for test_case in self.test_queries:
                query = test_case["query"]
                test_id = test_case["test_id"]
                progress.update(task, description=f"[cyan]Running {test_id}...[/cyan]")

                try:
                    agent_instance = LangGraphAgenticAI()
                    final_state = await agent_instance.invoke_for_test_async(query, f"session_{test_id}")

                    # Clean up state for cleaner logs
                    if "explicit_input_prompts" in final_state:
                        del final_state["explicit_input_prompts"]
                    if "original_query" in final_state: # Redundant
                        del final_state["original_query"]

                    result = {
                        "test_id": test_id,
                        "description": test_case["description"],
                        "query": query,
                        "final_answer": final_state.get("final_answer", "N/A"),
                        "full_trace": final_state,
                        "status": "Success" if final_state.get("final_answer") else "Failure"
                    }
                except Exception as e:
                    console.print(f"\n[bold red]CRITICAL FAILURE in test {test_id}: {e}[/bold red]")
                    result = {
                        "test_id": test_id,
                        "description": test_case["description"],
                        "query": query,
                        "final_answer": "CRITICAL FAILURE",
                        "full_trace": {"error": str(e)},
                        "status": "Critical Failure"
                    }
                
                self.results.append(result)
                progress.advance(task)

        self.end_time = datetime.datetime.now()
        self._print_summary()
        self._save_results()

    def _print_summary(self):
        console = Console()
        table = Table(title="Test Suite Summary")
        table.add_column("Test ID", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Query", style="magenta")

        success_count = 0
        failure_count = 0
        for result in self.results:
            status_style = "green" if "Success" in result['status'] else "red"
            table.add_row(result['test_id'], f"[{status_style}]{result['status']}[/{status_style}]", result['query'])
            if "Success" in result['status']:
                success_count += 1
            else:
                failure_count += 1
        
        console.print(table)
        duration = self.end_time - self.start_time
        console.print(f"\n[bold]Total Tests: {len(self.results)}[/bold]")
        console.print(f"[bold green]Successes: {success_count}[/bold green]")
        console.print(f"[bold red]Failures: {failure_count}[/bold red]")
        console.print(f"[bold]Total Duration: {duration}[/bold]")

    def _save_results(self):
        console = Console()
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        output_filename = f"test_results_with_trace_{timestamp}.json"
        with open(output_filename, 'w') as f:
            json.dump(self.results, f, indent=4)
        console.print(f"\n[bold]Results with full trace saved to [cyan]{output_filename}[/cyan][/bold]")

if __name__ == '__main__':
    suite = ComprehensiveTestSuite('experimentation_phase/testing_files/testing_suite.json')
    asyncio.run(suite.run()) 