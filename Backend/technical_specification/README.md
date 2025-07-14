# System Architecture & Technical Specifications

This document provides a detailed technical overview of the multi-agent AI system, its components, and its operational workflow.

## Master Architecture Diagram

The following diagram illustrates the complete, end-to-end flow of the system, from initial user query to the final response.

![Master Architecture Diagram](User%20Flow%20Diagram%20for%20FigJam%20(Community)%20(2).jpg)

## Architectural Overview

The system is designed as a stateful, multi-agent workflow orchestrated by LangGraph. This architecture allows for a clear separation of concerns, where each agent performs a highly specialized task. The flow is not strictly linear; it contains conditional routing and parallel processing to handle a variety of query types efficiently and robustly.

The core components are:

1.  **Workflow Engine (LangGraph):** Manages the state and directs the flow of data between agents.
2.  **Specialized Agents:** Individual Python classes that perform the cognitive work (e.g., Triage, Planning, Research).
3.  **Data Infrastructure:** External systems providing memory and knowledge, primarily **Redis** for caching and session management, and **Neo4j** as the long-term knowledge graph.

## Detailed Agent Descriptions

For a granular breakdown of each agent's purpose, functions, and interactions, please refer to the specific documentation files below:

*   [Triage Agent](./AGENT_Triage.md)
*   [Contextual Answering Agent](./AGENT_ContextualAnswering.md)
*   [Planning Agent](./AGENT_Planning.md)
*   [Hyde Agent](./AGENT_Hyde.md)
*   [Research Orchestrator Agent](./AGENT_ResearchOrchestrator.md)
*   [Synthesis Agent](./AGENT_Synthesis.md)
*   [Memory Agent](./AGENT_Memory.md)
*   [Data Stores (Redis & Neo4j)](./DATA_Stores.md) 