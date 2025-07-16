# 🛠️ Tools Directory Documentation

This directory contains reusable, modular tools that agents use to perform specific, concrete tasks such as information retrieval, search operations, and data processing. Tools are typically wrapped by agents to be included in the `LangGraph` workflow.

## 📚 Tool Overview

| Tool Class | Filename | Purpose | Key Method |
| :--- | :--- | :--- | :--- |
| `Neo4jConnector` | `neo4j_connector.py` | Singleton for all knowledge graph operations. | `execute_query`, `vector_search` |
| `Reranker` | `reranker.py` | Optimizes search results using Cohere's rerank model. | `async rerank()` |
| `TavilySearchTool` | `web_search_tool.py` | Performs real-time web searches using the Tavily API. | `__call__()` |
| `ParallelResearchTool` | `parallel_research_tool.py`| Executes a research plan with parallel operations. | `__call__()` |
| `EquationDetector` | `equation_detector.py` | Extracts and resolves mathematical content from text. | `resolve_equation_references()` |
| `PlanningTool` | `planning_tool.py` | Decomposes a complex query into a structured research plan. | `__call__()` |
| `HydeTool` | `hyde_tool.py` | Generates a hypothetical document to improve search retrieval. | `__call__()` |
| `KeywordRetrievalTool`| `keyword_retrieval_tool.py`| Performs relevance-scored keyword search using Neo4j's full-text index. | `async __call__()` |
| `SynthesisTool` | `synthesis_tool.py` | Synthesizes a final answer from a collection of sub-query answers. | `__call__()` |
| `FinishTool` | `finish_tool.py` | Signals the end of the agent's work. | `__call__()` |

---

## 🔍 Core Tools In-Depth

### `Neo4jConnector`

This class is the central hub for all knowledge graph interactions. It's implemented as a singleton to manage the database driver efficiently.

**Key Methods**:
```python
class Neo4jConnector:
    @classmethod
    def get_driver(cls):
        # Gets the singleton Neo4j driver instance.

    @staticmethod
    def execute_query(query: str, parameters: dict = None) -> list:
        # Executes a raw Cypher query.

    @staticmethod
    def vector_search(embedding: list, top_k: int = 1) -> list[dict]:
        # Performs a vector search and expands context using graph relationships.
```

**Retrieval Strategies**:
The connector facilitates multiple retrieval strategies through its query methods:
1.  **Vector Search**: Finds the best semantic match and retrieves its full context.
2.  **Direct Lookup**: Fetches specific nodes or subgraphs using functions like `get_gold_standard_context()` or `get_full_subsection_context_by_id()`.
3.  **Keyword Search**: Leveraged by `KeywordRetrievalTool` which calls `execute_query` with a `db.index.fulltext.queryNodes` Cypher query.

---

### `Reranker`

Improves the relevance of search results by using the powerful Cohere Rerank API.

**Key Features**:
- Asynchronous reranking for non-blocking I/O.
- Graceful fallback to return original documents if the API call fails.
- Processes a list of document dictionaries.

**Core Method**:
```python
class Reranker:
    async def rerank(self, query: str, documents: List[Dict[str, Any]], top_n: int = 3) -> List[Dict[str, Any]]:
        # Reranks a list of documents against a query.
```

---

### `TavilySearchTool`

Provides agents with the ability to search the live web, essential for finding up-to-date information or external standards not present in the local knowledge base.

**Features**:
- Inherits from `BaseTool` for ReAct agent compatibility.
- Uses Tavily's "advanced" search depth for comprehensive results.
- Includes a direct answer from Tavily in the formatted output.

**Core Method**:
```python
class TavilySearchTool(BaseTool):
    def __call__(self, query: str) -> Dict[str, str]:
        # Executes the search via a POST request to the Tavily API.
```

---

### `ParallelResearchTool`

Orchestrates the execution of a research plan, processing multiple sub-queries concurrently for maximum efficiency. It's a key component for performance.

**Key Capabilities**:
- Uses an internal `RetrievalStrategyAgent` to decide the best retrieval method for each sub-query.
- Employs `asyncio` to run independent retrieval tasks in parallel.
- Leverages the `EquationDetector` to enhance retrieval for mathematical queries.

**Core Method**:
```python
class ParallelResearchTool(BaseTool):
    # Note: The main logic is async, but the __call__ is a sync wrapper
    # to satisfy the BaseTool interface.
    def __call__(self, plan: List[Dict[str, str]], original_query: str) -> Dict[str, List[Dict[str, Any]]]:
        # Runs the async logic to process the plan in parallel.
```

---

### `EquationDetector`

A specialized utility for handling the complexities of mathematical and technical content within the building code.

**Features**:
- Detects references to equations, tables, and sections using regex patterns.
- Infers context by linking equation numbers (e.g., "Eq. 16-7") to their likely chapter (e.g., Chapter 16).
- Provides methods to retrieve mathematical content directly from the knowledge graph.

**Core Method**:
```python
class EquationDetector:
    def resolve_equation_references(self, text: str) -> Dict[str, Any]:
        # Aggregates all detected references (equations, tables, sections)
        # into a single structured dictionary.
```

---

### `PlanningTool`

The strategic component responsible for creating a research plan. It decomposes a single complex query into multiple, targeted sub-queries that the `ParallelResearchTool` can execute.

**Features**:
- Inherits from `BaseTool`.
- Uses different internal prompts depending on whether the query is for research or a specific calculation.
- Generates a JSON object containing a "reasoning" string and a "plan" list.

**Core Method**:
```python
class PlanningTool(BaseTool):
    def __call__(self, query: str, context_payload: str) -> dict:
        # Selects a prompt (strategist or specialist) and uses an LLM
        # to generate the structured research plan.
```

---

### `HydeTool`

Implements the Hypothetical Document Embeddings technique. It generates a fake, "ideal" document that perfectly answers a sub-query. This hypothetical document is then used for semantic search, often yielding more relevant results than the sub-query alone.

**Core Method**:
```python
class HydeTool(BaseTool):
    def __call__(self, sub_query: str) -> str:
        # Uses a specialized LLM prompt to generate a single-paragraph
        # hypothetical document that mimics the style of the building code.
```

---

## 🔧 Tool Integration & Usage

### Creating New Tools
New tools should inherit from `react_agent.base_tool.BaseTool` if they are to be used within the ReAct agent framework (though this seems to be a legacy pattern in this codebase).

**Template**:
```python
from react_agent.base_tool import BaseTool
from typing import Any

class MyNewTool(BaseTool):
    name: str = "my_new_tool"
    description: str = "A description of what my new tool does."

    def __init__(self):
        # Initialization logic here
        pass

    def __call__(self, input: Any) -> Any:
        # Main execution logic here
        return "result"
```

### Async vs. Sync Tools
The codebase contains a mix of `async` and `sync` tools. Tools inheriting from `BaseTool` often have a synchronous `__call__` method, which may internally run an `async` function using `asyncio.run()`. Newer or I/O-bound tools like `Reranker` are designed to be fully `async`.

## 🧪 Testing Tools
Each tool should have a corresponding test file in the `tests/` directory (if such a directory were to be created). Tests should cover both successful execution and failure cases.

**Example Test Structure**:
```python
import pytest
from tools.my_new_tool import MyNewTool

@pytest.fixture
def tool():
    return MyNewTool()

def test_basic_functionality(tool):
    result = tool("some input")
    assert result == "result"

def test_error_handling(tool):
    with pytest.raises(ValueError):
        tool("invalid input")
```

