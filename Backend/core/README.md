# 🧠 Core System Components

This directory contains the fundamental components that power the LangGraph agentic workflow system, including state management, workflow orchestration, and advanced thinking capabilities.

## 📁 Directory Overview

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| **state.py** | Workflow state management | Type-safe state definition, state transitions |
| **thinking_workflow.py** | Main workflow orchestration | Agent routing, conditional edges |
| **conversation_manager.py** | Conversation context handling | Memory management, Redis integration |
| **thinking_logger.py** | Reasoning transparency | Multi-level thinking modes |
| **cognitive_flow.py** | Cognitive process tracking | Real-time agent decision logging |
| **thinking_messages.py** | Thinking output formatting | Structured reasoning display |
| **cognitive_flow_agent_wrapper.py** | Agent instrumentation | Automatic cognitive logging |

## 🎯 Core Components

### State Management (`state.py`)

The heart of the workflow system, defining the data structure that flows through all agents.

**AgentState Structure**:
```python
class AgentState(TypedDict):
    # Query Information
    user_query: str                    # Original user question
    thread_id: str                     # Conversation session ID
    
    # Agent Decisions
    triage_classification: str         # Query type classification
    needs_research: bool              # Research requirement flag
    research_plan: List[ResearchTask] # Structured research tasks
    
    # Retrieved Information
    retrieved_contexts: List[RetrievedContext]  # Search results
    web_search_results: List[Dict]              # Web findings
    
    # Memory Components
    conversation_history: str          # Recent exchanges
    structured_memory: Dict[str, Any]  # Extracted facts
    memory_summary: str               # Narrative overview
    
    # Response
    final_answer: str                 # Generated response
    confidence_score: float           # Answer confidence
    
    # Metadata
    execution_log: List[ExecutionLog] # Agent execution trace
    quality_metrics: QualityMetrics   # Performance metrics
    error_state: Optional[ErrorInfo]  # Error information
```

**Key Types**:

```python
class RetrievedContext(TypedDict):
    source: str          # 'vector_search', 'graph', 'web'
    query: str           # Sub-query that prompted retrieval
    uid: str             # Unique identifier
    title: Optional[str] # Document/section title
    text: str           # Main content
    metadata: Dict      # Additional metadata

class ExecutionLog(TypedDict):
    agent_name: str
    timestamp: str
    input_summary: str
    output_summary: str
    execution_time_ms: float
    success: bool
    error_message: Optional[str]
```

**State Helpers**:
```python
def create_initial_state(user_query: str, context: str, 
                        conversation_manager, debug: bool) -> AgentState:
    """Initialize state with query and context"""
    
def log_agent_execution(state: AgentState, agent_name: str, 
                       start_time: float, success: bool):
    """Add execution log entry to state"""
```

---

### Workflow Orchestration (`thinking_workflow.py`)

Implements the LangGraph workflow with conditional routing and agent coordination.

**Key Components**:

```python
class ThinkingAgenticWorkflow:
    def __init__(self, debug_mode: bool = True, 
                 thinking_mode: bool = True,
                 thinking_detail_mode: ThinkingMode = ThinkingMode.SIMPLE):
        # Initialize workflow with agents and routing
        
    def _build_workflow_graph(self) -> StateGraph:
        # Define agent nodes and edges
        workflow = StateGraph(AgentState)
        
        # Add agents
        workflow.add_node("triage", TriageAgent())
        workflow.add_node("planning", PlanningAgent())
        # ... more agents
        
        # Define routing
        workflow.add_conditional_edges(
            "triage",
            self._route_after_triage,
            routing_map
        )
```

**Routing Logic**:

```python
def _route_after_triage(state: AgentState) -> str:
    """Determine next agent based on triage classification"""
    classification = state["triage_classification"]
    
    if classification == "simple_response":
        return "finish"
    elif classification == "contextual_clarification":
        return "contextual_answering"
    elif classification == "direct_retrieval":
        return "research"
    else:
        return "planning"
```

**Workflow Paths**:
1. **Simple Path**: Triage → Direct Response
2. **Contextual Path**: Triage → Contextual → Response
3. **Research Path**: Triage → Planning → Hyde → Research → Synthesis → Memory
4. **Error Path**: Any Agent → Error Handler → Graceful Response

---

### Conversation Manager (`conversation_manager.py`)

Handles conversation state persistence and context management using Redis.

**Core Features**:
- Thread-based conversation tracking
- Redis-backed persistence
- Memory window management
- Context payload generation

**Key Methods**:

```python
class ConversationManager:
    def __init__(self, thread_id: str, redis_client=None):
        self.thread_id = thread_id
        self.redis_client = redis_client
        self.ttl = 7200  # 2 hour TTL
        
    def add_user_message(self, message: str):
        """Add user message to history"""
        
    def add_assistant_message(self, message: str):
        """Add assistant response to history"""
        
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Retrieve conversation history"""
        
    def get_contextual_payload(self) -> str:
        """Generate context string for agents"""
        
    def update_structured_memory(self, memory_dict: Dict):
        """Update extracted facts"""
```

**Memory Structure**:
```python
{
    "conversation": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ],
    "structured_memory": {
        "user_goals": ["..."],
        "key_facts": {...},
        "resolved_questions": [...]
    },
    "summary": "Brief narrative of conversation"
}
```

---

### Thinking Logger (`thinking_logger.py`)

Provides transparent reasoning visibility with multiple detail levels.

**Thinking Modes**:
```python
class ThinkingMode(Enum):
    DISABLED = "disabled"   # No thinking output
    SIMPLE = "simple"       # Basic decisions only
    DETAILED = "detailed"   # Full reasoning trace
    DEBUG = "debug"        # Include internal state
```

**Usage Pattern**:
```python
class ThinkingLogger:
    def __init__(self, mode: ThinkingMode = ThinkingMode.SIMPLE):
        self.mode = mode
        self.thoughts = []
        
    def log_decision(self, decision: str, reasoning: str = None):
        """Log a key decision point"""
        
    def log_analysis(self, analysis: str, data: Dict = None):
        """Log analytical thinking"""
        
    def log_plan(self, plan: List[str]):
        """Log multi-step planning"""
        
    def get_thinking_summary(self) -> str:
        """Generate formatted thinking output"""
```

**Thinking Mixin**:
```python
class ThinkingMixin:
    """Mixin to add thinking capabilities to agents"""
    
    def think(self, thought: str):
        """Log a thought in the thinking process"""
        
    def think_decision(self, decision: str, options: List[str]):
        """Log a decision with alternatives"""
```

---

### Cognitive Flow (`cognitive_flow.py`)

Tracks the cognitive process flow through agents in real-time.

**Key Features**:
- Real-time agent transition tracking
- Decision point logging
- Cognitive state visualization

```python
class CognitiveFlowLogger:
    def __init__(self, output_queue: asyncio.Queue):
        self.output_queue = output_queue
        self.flow_state = CognitiveFlowState()
        
    async def log_agent_entry(self, agent_name: str, 
                             input_summary: str):
        """Log agent activation"""
        
    async def log_agent_decision(self, agent_name: str, 
                                decision: str, reasoning: str):
        """Log key decision"""
        
    async def log_agent_exit(self, agent_name: str, 
                            output_summary: str):
        """Log agent completion"""
```

**Flow Visualization**:
```
Triage Agent → [Classification: complex_research]
     ↓
Planning Agent → [Created 3 sub-tasks]
     ↓
Research Orchestrator → [Executing parallel searches]
     ↓
Synthesis Agent → [Combining 15 sources]
     ↓
Memory Agent → [Updated context]
```

---

### Agent Wrapper (`cognitive_flow_agent_wrapper.py`)

Automatically instruments agents with cognitive flow logging.

```python
class CognitiveFlowAgentWrapper:
    def __init__(self, agent: BaseLangGraphAgent, 
                 logger: CognitiveFlowLogger):
        self.agent = agent
        self.logger = logger
        
    def execute(self, state: AgentState) -> AgentState:
        # Log entry
        self.logger.log_agent_entry(
            self.agent.agent_name,
            summarize_input(state)
        )
        
        # Execute agent
        result = self.agent.execute(state)
        
        # Log exit
        self.logger.log_agent_exit(
            self.agent.agent_name,
            summarize_output(result)
        )
        
        return result
```

## 🔄 State Flow Example

```python
# 1. Initialize State
initial_state = create_initial_state(
    user_query="What are the requirements for emergency exits?",
    context_payload="Previous discussion about building codes",
    conversation_manager=conv_manager,
    debug_mode=True
)

# 2. Workflow Execution
workflow = ThinkingAgenticWorkflow(
    thinking_mode=True,
    thinking_detail_mode=ThinkingMode.DETAILED
)

# 3. Process Through Agents
final_state = await workflow.run(
    user_query=initial_state["user_query"],
    context_payload=initial_state["context_payload"],
    conversation_manager=conv_manager,
    thread_id="session-123"
)

# 4. Access Results
answer = final_state["final_answer"]
thinking = final_state["thinking_log"]
metrics = final_state["quality_metrics"]
```

## 🧪 Testing Core Components

### State Testing
```python
def test_state_initialization():
    state = create_initial_state("test query", "", None, True)
    assert state["user_query"] == "test query"
    assert state["execution_log"] == []
```

### Workflow Testing
```python
async def test_workflow_routing():
    workflow = ThinkingAgenticWorkflow()
    state = {"triage_classification": "simple_response"}
    next_node = workflow._route_after_triage(state)
    assert next_node == "finish"
```

### Memory Testing
```python
def test_conversation_manager():
    manager = ConversationManager("test-thread")
    manager.add_user_message("Hello")
    manager.add_assistant_message("Hi there!")
    history = manager.get_conversation_history()
    assert len(history) == 2
```

## 📊 Performance Considerations

### State Size Management
- Limit conversation history to recent N exchanges
- Compress large retrieved contexts
- Clear intermediate results after synthesis

### Workflow Optimization
- Use conditional edges to skip unnecessary agents
- Implement early termination for simple queries
- Cache agent decisions for similar queries

### Memory Efficiency
- Set appropriate Redis TTLs
- Implement memory cleanup routines
- Use lazy loading for large contexts

## 🔧 Configuration

### Environment Variables
```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_TTL=7200

# Thinking Mode
THINKING_MODE=detailed
ENABLE_COGNITIVE_FLOW=true

# Performance
MAX_PARALLEL_AGENTS=5
AGENT_TIMEOUT_SECONDS=30
```

### Workflow Customization
```python
# Custom workflow with specific agents
custom_workflow = StateGraph(AgentState)
custom_workflow.add_node("custom_agent", CustomAgent())
custom_workflow.add_edge("triage", "custom_agent")
```

## 📚 Best Practices

1. **State Immutability**: Never modify state in-place
2. **Error Propagation**: Always check error_state before processing
3. **Logging Discipline**: Use appropriate thinking detail levels
4. **Memory Management**: Clean up large state objects
5. **Testing Coverage**: Test all routing paths
6. **Performance Monitoring**: Track agent execution times

## 🚀 Quick Start

```python
from core.thinking_workflow import create_thinking_agentic_workflow
from core.conversation_manager import ConversationManager

# Initialize workflow
workflow = create_thinking_agentic_workflow(
    debug=True,
    thinking_mode=True,
    thinking_detail_mode=ThinkingMode.SIMPLE
)

# Create conversation manager
conv_manager = ConversationManager("user-session-123")

# Run query
response = await workflow.run(
    user_query="What are the requirements for emergency lighting?",
    conversation_manager=conv_manager,
    thread_id="user-session-123"
)

print(response["final_answer"])
```