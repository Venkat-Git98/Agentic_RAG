# Research Orchestrator Agent

## Purpose

The `ResearchOrchestrator` is the master research engine of the system. It is responsible for taking the detailed research plan and executing it with high performance and resilience to retrieve all necessary information from various data sources.

## Core Functions

1.  **Parallel Execution:**
    *   The orchestrator processes all sub-queries from the research plan concurrently. This parallel approach dramatically reduces the total time required to gather information.

2.  **Resilient Retrieval Cascade:**
    *   For each sub-query, the orchestrator employs a sophisticated, multi-step fallback strategy to maximize the chance of finding relevant information. It attempts the following retrieval methods in order:
        1.  **Direct/Math Retrieval:** It first attempts a targeted lookup in **Neo4j**, ideal for finding specific, known entities like "Section 1607.12.1" or "Equation 16-7".
        2.  **Vector Search:** If a direct hit is not found, it performs a semantic search in **Neo4j** using the hypothetical document from the `HydeAgent`. This finds conceptually related content.
        3.  **Keyword Search:** If vector search is insufficient, it falls back to a traditional keyword-based search against the **Neo4j** knowledge graph.
        4.  **Web Search:** If all internal knowledge base searches are exhausted, it uses the **Tavily** tool as a final safety net to search the public web.

3.  **Context Validation and Expansion:**
    *   All retrieved information is passed to the `ThinkingValidationAgent` to ensure it is relevant to the sub-query.
    *   If the context is deemed highly relevant, the orchestrator can perform a **Graph Expansion** step, querying **Neo4j** to find directly connected nodes (e.g., related tables or diagrams) to enrich the context even further.

4.  **Error Handling:**
    *   The orchestrator is designed to be resilient. If any single sub-query fails to find sufficient information after exhausting the entire retrieval cascade, it is handled gracefully. An error is logged, and a placeholder is created, allowing the other parallel tasks to complete without a total system failure.

## Downstream Routing

*   Once all parallel sub-query tasks are complete (either with success or a handled error), the aggregated set of results is passed to the `SynthesisAgent`. 