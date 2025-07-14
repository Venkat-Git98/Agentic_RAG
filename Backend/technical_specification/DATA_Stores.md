# Data Stores: Redis & Neo4j

The AI agent's advanced capabilities are supported by a robust data infrastructure consisting of two specialized databases: Redis and Neo4j. Each serves a distinct but critical purpose.

## Redis: The High-Speed Memory Hub

Redis is an in-memory database known for its exceptional speed. In this system, it acts as the agent's "short-term memory" and performance-enhancing cache.

*   **Role:** High-speed caching and session management.
*   **Key Functions:**
    1.  **Performance Cache (Prompt Caching):** When the system generates a high-quality answer to a complex question, the final response is stored in Redis. When a new query comes in, the `TriageAgent` checks this cache first. If a match is found, the system can return a validated answer in milliseconds, bypassing the entire research workflow.
    2.  **Session Store:** Redis is also used to store the history of each user's current conversation. This provides the short-term context needed for the `ContextualAnsweringAgent` to handle follow-up questions accurately.

## Neo4j: The Permanent Knowledge Graph

Neo4j is a graph database that serves as the system's "long-term memory" and expert knowledge base. It is specifically designed to store and query highly connected data, making it ideal for the Virginia Building Code.

*   **Role:** Deep, structured knowledge storage.
*   **Key Functions:**
    1.  **Relational Knowledge:** Unlike traditional databases, Neo4j stores not just the text of the building code but also the intricate **relationships** between its parts. For example, it knows that a specific paragraph in "Section 1607" references "Table 1607.1" and relies on "Equation 16-7".
    2.  **Complex Querying:** This relational structure allows the `ResearchOrchestrator` to perform sophisticated queries. It can ask for "the section that defines live load and all the tables and equations it references," a query that would be impossible for standard databases.
    3.  **Graph Expansion:** When a relevant piece of information is found, the orchestrator can query Neo4j to find all directly connected nodes, automatically enriching the research context with related tables, diagrams, and formulas. 