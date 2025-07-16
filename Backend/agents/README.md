# 🤖 Agent Directory Documentation

This directory contains all specialized agent implementations for the LangGraph-based agentic AI system. Each agent is designed with a single responsibility and communicates through a standardized state interface.

## 📋 Agent Overview

| Agent | Purpose | Key Features |
|-------|---------|--------------|
| **Triage Agent** | Query classification & routing | Intent detection, complexity assessment |
| **Contextual Answering Agent** | Handle follow-up questions | Context-aware responses |
| **Planning Agent** | Decompose complex queries | Multi-step research plans |
| **Hyde Agent** | Generate hypothetical answers | Improved retrieval accuracy |
| **Research Orchestrator** | Execute parallel research | Multi-source information gathering |
| **Synthesis Agent** | Combine research results | Coherent answer generation |
| **Memory Agent** | Update conversation state | Context preservation |
| **Error Handler** | Manage failures gracefully | Fallback strategies |
| **Retrieval Strategy Agent** | Optimize search approaches | Dynamic strategy selection |

## 🏗️ Base Agent Architecture

All agents inherit from `BaseLangGraphAgent` which provides:

```python
class BaseLangGraphAgent(ABC):
    def __init__(self, model_tier: str = "tier_2", agent_name: Optional[str] = None):
        # Initialize with LLM model tier and logging
        
    @abstractmethod
    def execute(self, state: AgentState) -> AgentState:
        # Main execution method - must be implemented by each agent
        
    def _execute_with_logging(self, state: AgentState) -> AgentState:
        # Wrapper that adds execution logging and error handling
```

### Model Tiers

- **Tier 1**: Premium models (Gemini 1.5 Pro) for complex reasoning
- **Tier 2**: Efficient models (Gemini 1.5 Flash) for routine tasks

## 🔍 Agent Specifications

### Triage Agent (`triage_agent.py`)

**Purpose**: Analyze incoming queries and route to appropriate workflow

**Key Methods**:
```python
def execute(self, state: AgentState) -> AgentState:
    # Classifies query into: simple_response, contextual_clarification, 
    # direct_retrieval, or complex_research
```

**Classification Logic**:
- **Simple Response**: Greetings, clarifications, general info
- **Contextual Clarification**: Follow-up questions requiring context
- **Direct Retrieval**: Single-document lookup queries
- **Complex Research**: Multi-faceted questions needing planning

---

### Planning Agent (`planning_agent.py`)

**Purpose**: Break down complex queries into executable research tasks

**Key Features**:
- Identifies information requirements
- Creates dependency graph for tasks
- Prioritizes research operations
- Detects calculation needs

**Output Format**:
```python
{
    "sub_query": "What is the wind load calculation formula?",
    "search_type": "vector",
    "priority": "high",
    "depends_on": [],
    "requires_calculation": true
}
```

---

### Research Orchestrator (`research_orchestrator.py`)

**Purpose**: Execute research plan with maximum efficiency

**Key Capabilities**:
- **Parallel Execution**: Run independent searches simultaneously
- **Multi-Strategy Search**: Vector, graph, keyword, and web search
- **Result Aggregation**: Combine findings from multiple sources
- **Quality Filtering**: Remove duplicates and low-relevance results

**Research Flow**:
1. Parse research plan
2. Group independent tasks
3. Execute in parallel batches
4. Aggregate and deduplicate
5. Rank by relevance

---

### Hyde Agent (`hyde_agent.py`)

**Purpose**: Generate hypothetical answers to improve retrieval

**How It Works**:
1. Takes user query
2. Generates plausible answer
3. Uses answer for similarity search
4. Improves retrieval precision

**Example**:
```python
Query: "What are the requirements for emergency exits?"
Hyde Output: "Emergency exits must be clearly marked, have a minimum width 
of 36 inches, open outward, and remain unlocked during occupancy..."
```

---

### Synthesis Agent (`synthesis_agent.py`)

**Purpose**: Transform research results into coherent answers

**Key Responsibilities**:
- Information integration
- Contradiction resolution
- Source attribution
- Mathematical formatting
- Answer validation

**Quality Checks**:
```python
def _validate_answer(self, answer: str, state: AgentState) -> bool:
    # Check completeness
    # Verify source coverage
    # Ensure factual consistency
    # Validate calculations
```

**Enhanced Version**: `EnhancedSynthesisAgent` adds:
- Multi-pass synthesis
- Confidence scoring
- Answer refinement

---

### Memory Agent (`memory_agent.py`)

**Purpose**: Maintain conversation context and extract key information

**Memory Types**:
1. **Conversation History**: Recent exchanges
2. **Structured Memory**: JSON-formatted facts
3. **Summary Memory**: Narrative overview

**Update Process**:
```python
def execute(self, state: AgentState) -> AgentState:
    # Update conversation history
    # Extract new facts to structured memory
    # Regenerate summary if needed
    # Manage memory size limits
```

---

### Contextual Answering Agent (`contextual_answering_agent.py`)

**Purpose**: Handle follow-up questions using conversation context

**Key Features**:
- Context relevance detection
- Answer generation from memory
- Fallback to research if needed

**Decision Flow**:
```
Has sufficient context? → Generate answer
                      ↓
                   Needs more info? → Route to planning
```

---

### Error Handler (`error_handler.py`)

**Purpose**: Graceful failure management and recovery

**Error Types Handled**:
- API failures
- Timeout errors
- Invalid responses
- Resource limitations
- Unexpected exceptions

**Recovery Strategies**:
1. Retry with backoff
2. Fallback to simpler approach
3. Provide partial answer
4. Clear error messaging

---

### Retrieval Strategy Agent (`retrieval_strategy_agent.py`)

**Purpose**: Dynamically select optimal retrieval strategies

**Strategy Selection Factors**:
- Query type and complexity
- Available data sources
- Performance requirements
- Previous success rates

**Available Strategies**:
- **Vector Search**: Semantic similarity
- **Graph Traversal**: Relationship-based
- **Keyword Search**: Exact matching
- **Hybrid**: Combined approaches

## 📊 Agent Communication

### State Interface

All agents communicate through the `AgentState` object:

```python
class AgentState(TypedDict):
    # Input
    user_query: str
    thread_id: str
    
    # Processing
    triage_classification: str
    research_plan: List[Dict]
    retrieved_contexts: List[Dict]
    
    # Output
    final_answer: str
    quality_metrics: Dict
    
    # Memory
    conversation_history: str
    structured_memory: Dict
    
    # Tracking
    execution_log: List[Dict]
    error_state: Optional[Dict]
```

### Execution Pattern

```python
# Standard agent execution
state = agent.execute(state)

# With error handling
try:
    state = agent._execute_with_logging(state)
except Exception as e:
    state = error_handler.execute(state)
```

## 🧪 Testing Agents

Each agent should have corresponding tests:

```python
def test_agent_basic_functionality():
    agent = SpecificAgent()
    state = create_test_state()
    result = agent.execute(state)
    assert result["expected_field"] is not None

def test_agent_error_handling():
    # Test graceful failure
    pass
```

## 🔧 Creating New Agents

To add a new agent:

1. **Inherit from BaseLangGraphAgent**:
```python
from agents.base_agent import BaseLangGraphAgent

class NewAgent(BaseLangGraphAgent):
    def __init__(self):
        super().__init__(model_tier="tier_2", agent_name="NewAgent")
```

2. **Implement execute method**:
```python
def execute(self, state: AgentState) -> AgentState:
    # Your agent logic here
    return state
```

3. **Add to workflow**:
```python
# In thinking_workflow.py
workflow.add_node("new_agent", NewAgent())
```

4. **Define routing logic**:
```python
workflow.add_conditional_edges(
    "previous_agent",
    route_to_new_agent,
    {"new_agent": "new_agent", "other": "other_agent"}
)
```

## 📈 Performance Considerations

### Optimization Tips

1. **Use appropriate model tiers**: Tier 2 for simple tasks
2. **Implement caching**: Cache expensive operations
3. **Parallel execution**: Use asyncio for concurrent operations
4. **Early termination**: Stop when sufficient info gathered
5. **Batch operations**: Group similar tasks

### Monitoring

Each agent logs:
- Execution time
- Token usage
- Success/failure status
- Key decisions made

Access logs via:
```python
state["execution_log"]
```

## 🔗 Agent Dependencies

```
base_agent.py
    ↓
triage_agent.py → planning_agent.py → hyde_agent.py
                          ↓
                  research_orchestrator.py
                          ↓
                    synthesis_agent.py
                          ↓
                     memory_agent.py
```

## 📚 Additional Resources

- [Base Agent Implementation](base_agent.py)
- [State Management](../core/state.py)
- [Workflow Configuration](../core/thinking_workflow.py)
- [Testing Guidelines](../TESTING_STRATEGY.md)