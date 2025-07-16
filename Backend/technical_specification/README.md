# Technical Architecture & Agent Specifications

This document provides an in-depth technical analysis of the LangGraph-based multi-agent AI system architecture, detailing the design decisions, agent behaviors, and system workflows.

## System Architecture Overview

The system implements a **Directed Acyclic Graph (DAG)** workflow using LangGraph, where specialized agents process information through a stateful pipeline. Each agent is designed with a single responsibility, enabling modular development and testing.

### High-Level Architecture

```
User Query → API Layer → LangGraph Workflow → Response Stream
                              ↓
                    [Agent Pipeline]
                    Triage → Planning → Research → Synthesis
                              ↓            ↓          ↓
                           Memory    Knowledge    Caching
```

### Key Architectural Decisions

1. **Agent Specialization**: Each agent focuses on one cognitive task
2. **Stateful Workflow**: Maintains context throughout processing
3. **Parallel Execution**: Research tasks run concurrently
4. **Streaming Response**: Real-time feedback via Server-Sent Events
5. **Thinking Transparency**: Optional detailed reasoning logs

## Core Design Principles

### 1. Separation of Concerns
- **Agents**: Handle specific cognitive tasks
- **Tools**: Provide reusable functionality
- **State**: Manages data flow between agents
- **Workflow**: Orchestrates agent execution

### 2. Fail-Safe Design
- Error boundaries at each agent
- Graceful degradation strategies
- Comprehensive error tracking
- Fallback mechanisms for critical paths

### 3. Performance First
- Redis caching for frequent queries
- Parallel research execution
- Lazy loading of resources
- Efficient state management

### 4. Observability
- Detailed execution logs
- LangSmith integration
- Thinking mode for transparency
- Performance metrics tracking

## Agent Specifications

### 🔍 Triage Agent
**Purpose**: Initial query classification and routing

**Key Responsibilities**:
- Classify queries into categories (simple, contextual, research-needed)
- Extract key entities and intent
- Determine routing path
- Handle error states

**Classification Types**:
- `simple_response`: Direct answers without retrieval
- `contextual_clarification`: Requires conversation context
- `direct_retrieval`: Single document lookup
- `complex_research`: Multi-step research needed

**Implementation**: `agents/triage_agent.py`

---

### 📋 Planning Agent
**Purpose**: Decompose complex queries into research sub-tasks

**Key Responsibilities**:
- Break down multi-faceted questions
- Create ordered research plan
- Identify calculation requirements
- Determine retrieval strategies

**Output Structure**:
```python
{
    "sub_query": "Specific research question",
    "search_type": "vector|graph|keyword|web",
    "priority": "high|medium|low",
    "depends_on": ["previous_task_ids"]
}
```

**Implementation**: `agents/planning_agent.py`

---

### 🔬 Research Orchestrator
**Purpose**: Execute research plan with parallel operations

**Key Responsibilities**:
- Execute multiple searches concurrently
- Coordinate different retrieval strategies
- Handle mathematical extraction
- Manage research dependencies

**Retrieval Strategies**:
1. **Vector Search**: Semantic similarity
2. **Graph Traversal**: Related concepts
3. **Keyword Search**: Exact matches
4. **Web Search**: Real-time information

**Implementation**: `agents/research_orchestrator.py`

---

### ✨ Synthesis Agent
**Purpose**: Combine research into coherent response

**Key Responsibilities**:
- Merge information from multiple sources
- Resolve contradictions
- Format mathematical content
- Generate citations
- Ensure answer completeness

**Quality Checks**:
- Source verification
- Contradiction resolution
- Completeness validation
- Format consistency

**Implementation**: `agents/synthesis_agent.py`

---

### 🧠 Memory Agent
**Purpose**: Update conversation and structured memory

**Key Responsibilities**:
- Update conversation history
- Extract key facts to structured memory
- Generate narrative summaries
- Manage context windows

**Memory Types**:
1. **Conversation Memory**: Recent exchanges
2. **Structured Memory**: Key facts as JSON
3. **Summary Memory**: Narrative overview

**Implementation**: `agents/memory_agent.py`

## Workflow Orchestration





### Conditional Routing Logic

```python
def route_after_triage(state):
    classification = state["triage_classification"]
    if classification == "simple_response":
        return "finish"
    elif classification == "contextual_clarification":
        return "contextual_answering"
    else:
        return "planning"
```

### Parallel Research Execution

The Research Orchestrator implements sophisticated parallel execution:

```python
async def execute_parallel_research(tasks):
    results = await asyncio.gather(*[
        execute_search(task) for task in tasks
        if task["depends_on"] is None
    ])
    # Process dependent tasks after prerequisites
```

## State Management

### AgentState Structure

```python
class AgentState(TypedDict):
    # Core query information
    user_query: str
    thread_id: str
    
    # Agent outputs
    triage_classification: str
    research_plan: List[ResearchTask]
    retrieved_contexts: List[RetrievedContext]
    final_answer: str
    
    # Memory components
    conversation_history: str
    structured_memory: Dict[str, Any]
    
    # Execution tracking
    execution_log: List[ExecutionLog]
    quality_metrics: QualityMetrics
    
    # Error handling
    error_state: Optional[ErrorInfo]
```

### State Transitions

1. **Initialization**: Create state from user query
2. **Agent Processing**: Each agent updates relevant fields
3. **Validation**: Ensure state consistency
4. **Persistence**: Save to Redis for session continuity

## Data Infrastructure

### Neo4j Knowledge Graph

**Schema Design**:
```cypher
(Document)-[:CONTAINS]->(Section)-[:HAS_CONTENT]->(Chunk)
(Section)-[:REFERENCES]->(Table|Figure|Equation)
(Chunk)-[:SIMILAR_TO {score: float}]->(Chunk)
```

**Indexing Strategy**:
- Full-text search on content
- Vector embeddings for similarity
- Relationship traversal for context

### Redis Caching Layer

**Cache Types**:
1. **Query Cache**: Complete responses
2. **Research Cache**: Intermediate results
3. **Session Cache**: Conversation state
4. **Embedding Cache**: Vector representations

**TTL Strategy**:
- Query responses: 24 hours
- Research results: 1 hour
- Session data: 2 hours
- Embeddings: 7 days

## Advanced Features

### Mathematical Processing

The system includes sophisticated mathematical capabilities:

1. **Formula Extraction**: Identifies equations in text
2. **Variable Mapping**: Extracts parameters and values
3. **Calculation Engine**: Executes mathematical operations
4. **Step-by-Step Solutions**: Provides detailed explanations

### Thinking Mode

Enables transparent reasoning visibility:

```python
class ThinkingMode(Enum):
    DISABLED = "disabled"
    SIMPLE = "simple"      # Basic decision logs
    DETAILED = "detailed"  # Full reasoning trace
    DEBUG = "debug"        # Include internal state
```

### Quality Assurance

Built-in quality metrics:
- **Retrieval Relevance**: Cosine similarity scores
- **Answer Completeness**: Coverage of query aspects
- **Source Reliability**: Citation quality
- **Response Coherence**: Logical consistency

## Performance Optimizations

### 1. Parallel Processing
- Concurrent research execution
- Async tool operations
- Batch embedding generation

### 2. Caching Strategy
- Multi-level cache hierarchy
- Intelligent cache invalidation
- Preemptive cache warming

### 3. Resource Management
- Connection pooling for databases
- Lazy model loading
- Memory-efficient state handling

### 4. Query Optimization
- Semantic query expansion
- Result reranking
- Early termination for simple queries

## Monitoring & Debugging

### LangSmith Integration

Track execution with detailed traces:
```python
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "agentic-ai-backend"
```

### Performance Metrics

Key metrics tracked:
- Agent execution times
- Cache hit rates
- Retrieval accuracy
- Token usage
- Error frequencies

### Debug Tools

1. **Thinking Logger**: Detailed reasoning traces
2. **State Inspector**: Examine workflow state
3. **Query Analyzer**: Breakdown query processing
4. **Performance Profiler**: Identify bottlenecks

## Agent Communication Protocol

Agents communicate through standardized interfaces:

```python
class BaseAgent(ABC):
    @abstractmethod
    async def execute(self, state: AgentState) -> AgentState:
        """Process state and return updated state"""
        pass
```

### Message Passing

- **Input Validation**: Type checking and schema validation
- **Output Contracts**: Guaranteed state updates
- **Error Propagation**: Standardized error format
- **Logging Protocol**: Consistent execution logs

