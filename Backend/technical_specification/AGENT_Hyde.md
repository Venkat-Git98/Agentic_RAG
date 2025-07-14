# Hyde Agent

## Purpose

The `HydeAgent` (Hypothetical Document Embeddings) is a specialized agent designed to improve the quality and accuracy of the information retrieval process. It does this by creating idealized documents that help guide the search algorithms.

## Core Functions

1.  **Hypothetical Document Generation:**
    *   The agent receives the `research_plan` (a list of sub-queries) from the `PlanningAgent`.
    *   For each individual sub-query, it uses a Tier-1 Language Model to generate a short, hypothetical document. This document is a concise, well-structured paragraph that *looks like* the perfect answer to that sub-query.

2.  **Search Enhancement:**
    *   These hypothetical documents are not shown to the user. Instead, they are passed along with the original sub-queries to the `ResearchOrchestrator`.
    *   During the vector search phase, the orchestrator uses the *embedding* (a numerical representation) of this idealized document—rather than the sub-query itself—to find actual content in the **Neo4j** database that is conceptually similar. This technique significantly improves the relevance of search results.

## Downstream Routing

Like the `PlanningAgent`, the `HydeAgent` has a linear path:
*   The enriched research plan, now containing a hypothetical document for each sub-query, is passed directly to the `ResearchOrchestrator` to begin the execution of the research. 