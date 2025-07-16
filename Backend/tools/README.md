# 🛠️ Tools Directory Documentation

This directory contains reusable tools and utilities that agents use to perform specific tasks such as information retrieval, search operations, and data processing.

## 📚 Tool Overview

| Tool | Purpose | Key Features |
|------|---------|--------------|
| **Neo4j Connector** | Graph database operations | Vector search, graph traversal, keyword search |
| **Reranker** | Result relevance optimization | Cohere-based reranking, score normalization |
| **Web Search Tool** | Real-time information retrieval | Tavily API integration |
| **Planning Tool** | Research plan generation | Task decomposition, dependency management |
| **Hyde Tool** | Hypothetical answer generation | Retrieval enhancement |
| **Synthesis Tool** | Information combination | Multi-source integration |
| **Parallel Research Tool** | Concurrent search execution | Async operations, result aggregation |
| **Equation Detector** | Mathematical content extraction | Formula parsing, variable detection |
| **Keyword Retrieval Tool** | Exact match searching | Fuzzy matching, relevance scoring |
| **Direct Retrieval Queries** | Optimized single lookups | Fast targeted searches |
| **Image Utils** | Image processing utilities | Base64 encoding, format conversion |

## 🔍 Core Tools

### Neo4j Connector (`neo4j_connector.py`)

The central hub for all knowledge graph operations, providing multiple search strategies and data retrieval methods.

**Key Classes**:
```python
class Neo4jConnector:
    def __init__(self):
        # Initialize connection to Neo4j database
        
    async def similarity_search(self, query: str, top_k: int = 5) -> List[Dict]:
        # Vector similarity search using embeddings
        
    async def graph_search(self, start_node_id: str, max_depth: int = 2) -> List[Dict]:
        # Traverse graph relationships from starting node
        
    async def keyword_search(self, query: str, top_k: int = 5) -> List[Dict]:
        # Full-text search with fuzzy matching
        
    async def hybrid_search(self, query: str, top_k: int = 10) -> List[Dict]:
        # Combined vector + keyword search with reranking
```

**Search Strategies**:

1. **Vector Search**:
   - Uses sentence-transformers embeddings
   - Cosine similarity matching
   - Best for semantic queries

2. **Graph Search**:
   - Traverses relationships (CONTAINS, REFERENCES, etc.)
   - Retrieves connected context
   - Ideal for comprehensive information

3. **Keyword Search**:
   - Full-text indexing
   - Fuzzy matching with thresholds
   - Perfect for exact terms

4. **Hybrid Search**:
   - Combines vector and keyword
   - Reranks with Cohere
   - Optimal for complex queries

**Usage Example**:
```python
connector = Neo4jConnector()
results = await connector.hybrid_search(
    "emergency exit requirements",
    top_k=10
)
```

---

### Reranker (`reranker.py`)

Optimizes search results using Cohere's reranking model for improved relevance.

**Key Features**:
- Relevance scoring
- Result deduplication
- Score normalization
- Metadata preservation

**Implementation**:
```python
class Reranker:
    def __init__(self):
        self.cohere_client = cohere.Client(api_key=COHERE_API_KEY)
        
    def rerank(self, query: str, documents: List[str], top_k: int = 5) -> List[Dict]:
        # Rerank documents by relevance to query
        response = self.cohere_client.rerank(
            model='rerank-english-v3.0',
            query=query,
            documents=documents,
            top_n=top_k
        )
        return self._format_results(response)
```

---

### Web Search Tool (`web_search_tool.py`)

Provides real-time web search capabilities using the Tavily API.

**Features**:
- Current information retrieval
- Multiple result formats
- Source credibility filtering
- Content extraction

**Usage**:
```python
def web_search_tavily(query: str, max_results: int = 5) -> List[Dict]:
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    results = tavily_client.search(
        query=query,
        search_depth="advanced",
        max_results=max_results
    )
    return format_web_results(results)
```

---

### Parallel Research Tool (`parallel_research_tool.py`)

Executes multiple search operations concurrently for maximum efficiency.

**Key Capabilities**:
- Async task execution
- Dependency resolution
- Result aggregation
- Error isolation

**Architecture**:
```python
class ParallelResearchTool:
    async def execute_research_plan(self, tasks: List[Dict]) -> List[Dict]:
        # Group independent tasks
        independent_tasks = [t for t in tasks if not t.get("depends_on")]
        
        # Execute in parallel
        results = await asyncio.gather(*[
            self._execute_single_task(task) 
            for task in independent_tasks
        ], return_exceptions=True)
        
        # Handle dependent tasks
        dependent_results = await self._execute_dependent_tasks(
            tasks, results
        )
        
        return self._aggregate_results(results + dependent_results)
```

**Execution Flow**:
1. Parse research plan
2. Identify dependencies
3. Execute independent tasks in parallel
4. Process dependent tasks sequentially
5. Aggregate and deduplicate results

---

### Equation Detector (`equation_detector.py`)

Specialized tool for extracting and parsing mathematical content from text.

**Features**:
- Formula detection
- Variable extraction
- Unit identification
- LaTeX conversion

**Core Methods**:
```python
class EquationDetector:
    def detect_equations(self, text: str) -> List[Dict]:
        # Find mathematical expressions
        equations = []
        
        # Pattern matching for formulas
        formula_patterns = [
            r'[A-Z]\s*=\s*[^\.]+',  # Simple equations
            r'\$\$[^$]+\$\$',       # LaTeX blocks
            r'\\\[[^\]]+\\\]'       # Display math
        ]
        
        for pattern in formula_patterns:
            matches = re.findall(pattern, text)
            equations.extend(self._parse_matches(matches))
            
        return equations
        
    def extract_variables(self, equation: str) -> Dict[str, Any]:
        # Parse variables and their descriptions
        variables = {}
        # Complex parsing logic here
        return variables
```

---

### Planning Tool (`planning_tool.py`)

Generates structured research plans from complex queries.

**Planning Strategy**:
```python
def create_research_plan(query: str, context: Dict) -> List[Dict]:
    # Analyze query components
    components = analyze_query_structure(query)
    
    # Generate sub-queries
    tasks = []
    for component in components:
        task = {
            "sub_query": component["question"],
            "search_type": determine_search_type(component),
            "priority": assess_priority(component),
            "depends_on": identify_dependencies(component, tasks)
        }
        tasks.append(task)
        
    return optimize_task_order(tasks)
```

---

### Hyde Tool (`hyde_tool.py`)

Generates hypothetical answers to improve retrieval accuracy.

**Process**:
1. Analyze user query
2. Generate plausible answer
3. Use answer for similarity search
4. Return enhanced results

**Implementation**:
```python
def generate_hyde_response(query: str, llm_model) -> str:
    prompt = f"""
    Generate a detailed, factual answer to this question:
    {query}
    
    Even if you're not certain, provide a comprehensive response
    that would likely contain the key terms and concepts.
    """
    
    return llm_model.invoke(prompt)
```

## 🔧 Tool Integration

### Creating New Tools

Follow this template for new tools:

```python
# tool_name.py
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ToolName:
    """
    Brief description of the tool's purpose.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize tool with configuration."""
        self.config = config or {}
        self._setup()
        
    def _setup(self):
        """Perform any necessary setup."""
        pass
        
    def execute(self, input_data: Any) -> Any:
        """
        Main execution method.
        
        Args:
            input_data: Input parameters for the tool
            
        Returns:
            Tool execution results
        """
        try:
            # Tool logic here
            result = self._process(input_data)
            return result
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            raise
            
    def _process(self, data: Any) -> Any:
        """Internal processing logic."""
        pass
```

### Tool Configuration

Tools can be configured via environment variables or config objects:

```python
# config.py
TOOL_CONFIG = {
    "neo4j": {
        "uri": os.getenv("NEO4J_URI"),
        "auth": (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    },
    "reranker": {
        "model": "rerank-english-v3.0",
        "top_k_default": 5
    },
    "web_search": {
        "max_results_default": 10,
        "search_depth": "advanced"
    }
}
```

## 📊 Performance Optimization



### Async Operations

Tools use async/await for concurrent operations:

```python
async def parallel_search(queries: List[str]) -> List[Dict]:
    tasks = [search_single(q) for q in queries]
    results = await asyncio.gather(*tasks)
    return results
```

## 🧪 Testing Tools

Each tool should have comprehensive tests:

```python
# test_tool_name.py
import pytest
from tools.tool_name import ToolName

@pytest.fixture
def tool():
    return ToolName()

def test_basic_functionality(tool):
    result = tool.execute("test input")
    assert result is not None

@pytest.mark.asyncio
async def test_async_operation(tool):
    result = await tool.async_execute("test")
    assert len(result) > 0
```

## 📈 Monitoring & Metrics

Tools track various metrics:

- Execution time
- Success/failure rates
- Cache hit rates
- API usage
- Error frequencies

Access metrics via:
```python
tool.get_metrics()
# Returns: {"executions": 100, "avg_time": 0.5, "errors": 2}
```

## 🔌 Tool Dependencies

```
Base Infrastructure:
├── Neo4j Database
├── Redis Cache
├── Cohere API
├── Tavily API
└── Google Gemini API

Python Dependencies:
├── neo4j (Graph DB client)
├── sentence-transformers (Embeddings)
├── cohere (Reranking)
├── tavily-python (Web search)
├── tiktoken (Token counting)
└── thefuzz (Fuzzy matching)
```

