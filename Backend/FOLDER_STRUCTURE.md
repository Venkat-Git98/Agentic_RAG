# Folder Structure Guide

This document provides an overview of the key directories and files in the project, explaining their purpose and contents.

```
/
├── agents/
│   ├── triage_agent.py
│   ├── contextual_answering_agent.py
│   ├── planning_agent.py
│   ├── hyde_agent.py
│   ├── research_orchestrator.py
│   ├── synthesis_agent.py
│   └── memory_agent.py
│
├── data/
│   └── ... (JSON files, CSVs, etc.)
│
├── technical_specification/
│   ├── README.md
│   ├── AGENT_Triage.md
│   └── ... (Other agent docs)
│
├── tools/
│   ├── neo4j_connector.py
│   ├── reranker.py
│   └── ... (Other tool files)
│
├── main.py
├── server.py
├── state.py
├── prompts.py
├── config.py
└── README.md
```

## Key Directories

*   **`/agents`**: This is the core directory containing the logic for each specialized agent in the workflow. Each file corresponds to an agent and defines its `execute` method and interaction with the system state.

*   **`/data`**: Contains static data files used by the system, such as CSVs for evaluation, JSON files for testing, or other data assets required for the knowledge base.

*   **`/technical_specification`**: Houses all detailed technical documentation, including the master architecture overview, the agent-by-agent breakdowns, and other specification documents.

*   **`/tools`**: Contains modules that the agents use to interact with external systems or perform specific, reusable tasks. This includes the `Neo4jConnector` for database queries, the `Reranker` for processing search results, and the `TavilySearchTool` for web searches.

## Key Files

*   **`main.py`**: The main entry point for running the application, particularly for command-line interactions and testing.

*   **`server.py`**: The entry point for running the system as a web service (e.g., via FastAPI). It exposes API endpoints that allow users to interact with the agent workflow.

*   **`state.py`**: Defines the `AgentState` TypedDict. This is a crucial file that specifies the data structure that is passed between all agents in the LangGraph workflow, ensuring data consistency.

*   **`prompts.py`**: A centralized file containing all the complex, multi-line prompts used by the various agents. This separation makes it easier to manage and refine the instructions given to the LLMs.

*   **`config.py`**: Manages configuration settings for the application, such as model names, API keys (often loaded from a `.env` file), and other operational parameters.

*   **`README.md`**: The main, non-technical overview of the project, intended for all users. 