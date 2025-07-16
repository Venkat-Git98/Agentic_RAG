# 🤖 Agent Directory Documentation

This directory contains all specialized agent implementations for the LangGraph-based agentic AI system. Each agent is a Python class that inherits from `BaseLangGraphAgent` and is designed with a single, focused responsibility.

## 📋 Agent Overview

| Agent Class | Filename | Purpose |
| :--- | :--- | :--- |
| `TriageAgent` | `triage_agent.py` | Performs initial query classification and routing. |
| `ContextualAnsweringAgent` | `contextual_answering_agent.py` | Handles direct follow-up questions using conversation context. |
| `PlanningAgent` | `planning_agent.py` | Decomposes complex queries into a multi-step research plan. |
| `HydeAgent` | `hyde_agent.py` | Generates hypothetical documents to improve retrieval accuracy. |
| `ResearchOrchestrator` | `research_orchestrator.py` | Manages the execution of the research plan, including parallel retrieval and validation. |
| `SynthesisAgent` | `synthesis_agent.py` | Synthesizes a final, coherent answer from the collected research. |
| `MemoryAgent` | `memory_agent.py` | Updates the conversation history and state at the end of a workflow. |
| `ErrorHandler` | `error_handler.py` | Manages workflow failures, retries, and graceful degradation. |
| `RetrievalStrategyAgent` | `retrieval_strategy_agent.py` | Determines the optimal retrieval strategy for a given sub-query. |
| `RouterAgent` | `router_agent.py`| A simple agent for routing between other agents (less used in the current workflow). |

---

## 🏗️ Base Agent Architecture

All agents inherit from the abstract base class `BaseLangGraphAgent` found in `agents/base_agent.py`. This provides a consistent structure and a set of common functionalities.

**Core Structure**:
```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseLangGraphAgent(ABC):
    
    def __init__(self, model_tier: str, agent_name: Optional[str] = None):
        # ... initializes logger and LLM model ...

    async def __call__(self, state: AgentState) -> AgentState:
        # Main entry point with logging, error handling, and state updates.

    @abstractmethod
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        # Core logic to be implemented by each specific agent.
        # It returns a dictionary of values to be updated in the state.
        pass
```

### Key Principles of the Base Agent:
- **State-Driven**: Agents operate on and return a shared `AgentState` object. The `execute` method's return dictionary is merged back into the state.
- **Asynchronous**: All agents are designed to be `async` to support non-blocking operations.
- **Error Handling**: The `__call__` method includes a generic `try...except` block that catches errors, logs them, and updates the `error_state` field.
- **Model Tiering**: Agents can be initialized with a `"tier_1"` (e.g., Gemini 1.5 Pro) or `"tier_2"` (e.g., Gemini 1.5 Flash) model to balance performance and cost.

---

## 🔍 Key Agent Specifications

### `TriageAgent`
- **Purpose**: Acts as the initial gatekeeper. It analyzes the user's query and the conversation context to decide the most efficient path.
- **Key Logic**: Uses an LLM with a detailed prompt (`TRIAGE_PROMPT`) to classify the query into categories like `simple_response`, `contextual_clarification`, `direct_retrieval`, or `complex_research`. It also checks a Redis-based query cache for previously answered questions.
- **Output**: Updates the state with `triage_classification`, `rewritten_query`, and `triage_reasoning`.

### `PlanningAgent`
- **Purpose**: Decomposes a complex query into a structured, multi-step research plan.
- **Key Logic**: Leverages the `PlanningTool` to generate a list of sub-queries. It can detect if a query requires a mathematical calculation and flag it in the state using the `math_calculation_needed` key.
- **Output**: A `research_plan` list in the `AgentState`. Each item in the list is a dictionary representing a research task.

### `ResearchOrchestrator`
- **Purpose**: The workhorse of the research process. It takes the `research_plan` and executes it.
- **Key Logic**:
    - Can run sub-queries sequentially or in parallel based on the `USE_PARALLEL_EXECUTION` config flag.
    - For each sub-query, it calls the `RetrievalStrategyAgent` to determine the best way to find information.
    - It executes the chosen retrieval strategy (e.g., vector search, keyword search) with a series of fallback mechanisms.
    - It uses the `ThinkingValidationAgent` to check the quality of retrieved context.
- **Output**: A `sub_query_answers` list, where each item contains the sub-query, the retrieved answer, and metadata about the retrieval process.

### `SynthesisAgent`
- **Purpose**: Constructs the final, polished answer for the user.
- **Key Logic**: Takes the list of `sub_query_answers` and uses the `SynthesisTool` (which calls an LLM with `SYNTHESIS_PROMPT`) to weave them into a single, coherent response. It also extracts source citations.
- **Caching**: If the generated answer is of high quality, this agent stores it in the Redis query cache for future use.
- **Output**: The `final_answer`, `source_citations`, and `confidence_score` in the `AgentState`.

### `ErrorHandler`
- **Purpose**: To make the workflow resilient. It's triggered when any agent in the graph fails.
- **Key Logic**: Analyzes the `error_state` to determine if the error is recoverable. It can trigger a `retry` (by resetting the workflow to a previous step) or a `graceful_degradation` (by providing a fallback response to the user).
- **Output**: Modifies the `current_step` and `workflow_status` to control the flow after an error.

## ⛓️ Agent Interaction
Agents do not call each other directly. They communicate and are orchestrated through the `LangGraph` workflow defined in `core/thinking_workflow.py`. The workflow directs the `AgentState` object from one agent to the next based on the output of the previous agent and the conditional logic defined in the graph.