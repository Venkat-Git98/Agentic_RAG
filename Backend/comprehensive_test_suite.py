import asyncio
import json
import uuid
from datetime import datetime
import pandas as pd
from rich.console import Console
from rich.table import Table

from main import LangGraphAgenticAI
from conversation_manager import ConversationManager
from config import redis_client

console = Console()

class ComprehensiveTestSuite:
    def __init__(self, test_queries_file):
        self.test_queries_file = test_queries_file
        self.test_queries = self._load_test_queries()
        self.results = []

    def _load_test_queries(self):
        with open(self.test_queries_file, 'r') as f:
            return json.load(f)

    def _print_summary(self):
        df = pd.DataFrame(self.results)

        # --- Save results to a file ---
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_filename = f"test_results_{timestamp}.json"
        try:
            with open(results_filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=4)
            console.print(f"\n[bold green]📊 Test results saved to {results_filename}[/bold green]")
        except Exception as e:
            console.print(f"\n[bold red]Error saving results to file: {e}[/bold red]")

        
        table = Table(title=f"Comprehensive Test Suite Results ({timestamp})")
        table.add_column("Test ID", style="cyan")
        table.add_column("Description", style="magenta")
        table.add_column("Query", style="magenta")
        table.add_column("Final Answer", style="green")
        table.add_column("Status", style="bold")
        
        for _, row in df.iterrows():
            status = "✅" if row['status'] == 'Success' else "❌"
            table.add_row(
                row['test_id'],
                row['description'],
                row['query'],
                row['final_answer'],
                status
            )
            
        console.print(table)

    async def run_tests(self):
        ai_system = LangGraphAgenticAI()

        for test in self.test_queries:
            thread_id = f"test-session-{uuid.uuid4()}"
            
            console.print(f"[bold blue]Running test case: {test['test_id']} - {test['description']}[/bold blue]")
            
            try:
                final_answer = ""
                async for chunk in ai_system.get_response_stream(test['query'], thread_id):
                    if "final_answer" in chunk:
                        final_answer = chunk["final_answer"]

                self.results.append({
                    'test_id': test['test_id'],
                    'description': test['description'],
                    'query': test['query'],
                    'final_answer': final_answer,
                    'status': 'Success'
                })

            except Exception as e:
                console.print(f"[bold red]Test case failed: {test['test_id']}[/bold red]")
                console.print(f"Error: {e}")
                self.results.append({
                    'test_id': test['test_id'],
                    'description': test['description'],
                    'query': test['query'],
                    'final_answer': 'N/A',
                    'status': 'Failure'
                })
        
        self._print_summary()

if __name__ == '__main__':
    suite = ComprehensiveTestSuite('experimentation_phase/testing_files/testing_suite.json')
    asyncio.run(suite.run_tests()) 