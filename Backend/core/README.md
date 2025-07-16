# 🧠 Core System Components Documentation

This directory contains the fundamental components that power the LangGraph agentic workflow system, including state management, workflow orchestration, conversation context, and the cognitive logging framework.

## 📁 Directory Overview

| Component | Filename | Purpose |
| :--- | :--- | :--- |
| **State Management** | `state.py` | Defines the `AgentState` TypedDict that flows through the graph. |
| **Workflow Orchestration** | `thinking_workflow.py` | Constructs the `LangGraph` StateGraph and defines agent routing logic. |
| **Conversation Manager** | `conversation_manager.py`| Handles conversation history, memory, and context persistence using Redis. |
| **Cognitive Logging** | `cognitive_flow.py` | Provides the data structures for logging the agent's thinking process. |
| **Agent Wrapper** | `cognitive_flow_agent_wrapper.py` | Injects cognitive logging into each agent automatically. |
| **Thinking Logger** | `thinking_logger.py` | A human-readable, stream-of-consciousness style logger (less used now). |
| **Thinking Messages** | `thinking_messages.py` | A collection of pre-defined "thinking" messages for the cognitive wrapper. |

---

## 🎯 Core Components In-Depth

### State Management (`state.py`)
This file is the single source of truth for the data structure that is passed between all agents in the workflow.

**`AgentState` TypedDict**:
The `AgentState` is a large `TypedDict` that contains dozens of optional and required keys that agents read from and write to. It is the primary data-passing mechanism.

**Key `TypedDict` Structures**:
```python
class ExecutionLog(TypedDict):
    """Individual agent execution log entry"""
    agent_name: str
    timestamp: str
    input_summary: str
    output_summary: str
    execution_time_ms: float
    success: bool
    error_message: Optional[str]

class RetrievedContext(TypedDict):
    """A unified structure for holding retrieved context from any source."""
    source: str
    query: str
    uid: str
    title: Optional[str]
    text: str
    metadata: Dict[str, Any]

class AgentState(TypedDict):
    # This is a simplified view. See the source file for all ~40 keys.
    user_query: str
    context_payload: str
    current_step: Literal[...]
    workflow_status: Literal[...]
    triage_classification: Optional[Literal[...]]
    research_plan: Optional[List[Dict[str, str]]]
    sub_query_answers: Optional[List[Dict[str, str]]]
    final_answer: Optional[str]
    error_state: Optional[Dict[str, Any]]
    execution_log: List[ExecutionLog]
    cognitive_flow_messages: List[Dict[str, Any]]
```

**Helper Functions**:
- `create_initial_state(...)`: Factory function to construct the initial state for a new workflow run.
- `log_agent_execution(...)`: Appends a new `ExecutionLog` entry to the state.

---

### Workflow Orchestration (`thinking_workflow.py`)
This module builds and compiles the `LangGraph` `StateGraph` that defines the entire agentic process.

**`ThinkingAgenticWorkflow` Class**:
This class is responsible for setting up the agent nodes and the conditional edges that route the `AgentState` between them.

**Core Logic**:
```python
class ThinkingAgenticWorkflow:
    def _build_workflow_graph(self) -> StateGraph:
        """Build the workflow graph with our new agent architecture."""
        workflow = StateGraph(AgentState)
        
        # All agent nodes are wrapped to inject cognitive logging
        workflow.add_node(
            "triage", 
            CognitiveFlowAgentWrapper(TriageAgent(), self.cognitive_flow_logger)
        )
        # ... other agents are added similarly ...
        
        workflow.set_entry_point("triage")
        
        # Conditional edges determine the next step based on state
        workflow.add_conditional_edges(
            "triage",
            self._route_after_triage,
            {
                "planning": "planning",
                "research": "research",
                "contextual_answering": "contextual_answering",
                "finish": END,
                "error": "error_handler"
            }
        )
        # ... more edges ...
        
        return workflow
```

**Routing Functions**:
The `_route_after_triage` function inspects the `triage_classification` key in the `AgentState` to decide which agent should run next. This is the primary mechanism for conditional logic in the workflow.

---

### Conversation Manager (`conversation_manager.py`)
This class provides a persistent, long-term memory for conversations, using Redis as the primary backend with a file-based backup.

**Key Features**:
- **Hybrid Memory**: Manages both a `full_history` of messages and a `StructuredMemory` object (a Pydantic model) that an LLM updates with key facts.
- **Context Payloads**: The `get_contextual_payload` method generates the rich context string that agents use, combining the structured memory, a running summary, and the most recent messages.
- **Persistence**: Automatically saves the entire conversation state to Redis and a local JSON file after each new message.

**Core Methods**:
```python
class ConversationManager:
    def __init__(self, conversation_id: str, redis_client: redis.Redis, ...):
        # Loads state from Redis or a backup file on initialization.
    
    def add_message(self, role: Literal["user", "assistant"], content: str):
        # Adds a message and persists the new state.

    def get_contextual_payload(self) -> str:
        # Generates the context string for the agent workflow.
```

---

### Cognitive Logging Framework
This framework provides the real-time "thinking" messages streamed to the frontend.

- **`cognitive_flow.py`**: Defines the `CognitiveFlowLogger` class. Its `log_step` method is the core function for sending a thinking message to the streaming queue.
    ```python
    class CognitiveFlowLogger:
        async def log_step(self, agent_name: str, status: Literal["WORKING", "DONE", "ERROR"], message: str, state: Optional[AgentState] = None):
            # Puts the message onto the asyncio.Queue for streaming
            await self.queue.put({"cognitive_message": message})
    ```

- **`cognitive_flow_agent_wrapper.py`**: Defines the `CognitiveFlowAgentWrapper`. This class is crucial as it wraps every agent in the workflow. Its `__call__` method intercepts the execution, sends a pre-defined "thinking" message from `thinking_messages.py`, runs the actual agent, and then sends a "done" message. This automates the thinking process visibility.
    ```python
    class CognitiveFlowAgentWrapper:
        async def __call__(self, state: AgentState) -> Dict[str, Any]:
            # 1. Log a pre-defined "WORKING" message
            # 2. Execute the wrapped agent: result = await self.agent(state)
            # 3. Log a "DONE" message
            # 4. Return the result
    ```
- **`thinking_messages.py`**: A simple dictionary mapping agent names to lists of possible "thinking" messages, adding variety to the frontend display.
- **`thinking_logger.py`**: A legacy, more complex logger that is less central to the current streaming implementation but still part of the codebase. It provides more granular, hierarchical logging capabilities.