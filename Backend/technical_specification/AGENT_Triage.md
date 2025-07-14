# Triage Agent

## Purpose

The `TriageAgent` is the initial entry point and intelligent router for the entire system. Its primary responsibility is to analyze the incoming user query and determine the most efficient workflow path, preventing unnecessary processing for simple or previously answered questions.

## Core Functions

1.  **Cache Retrieval:**
    *   Upon receiving a query, the agent's first action is to check a high-speed **Redis cache**.
    *   It looks for an exact match to a previously answered question. If a match is found, it proceeds to the validation step.

2.  **Cache Validation:**
    *   If a cached answer is retrieved, it is not returned immediately. Instead, it is passed to a `ThinkingValidationAgent`.
    *   This validation step ensures the cached answer is still relevant and meets quality standards. If the score is high (e.g., >= 7/10), the cached answer is returned directly to the user, and the workflow terminates for maximum efficiency.

3.  **Query Classification:**
    *   If the cache check results in a miss or the validation fails, the query is passed to a Tier-2 Language Model.
    *   The LLM classifies the query into one of several categories:
        *   `complex_research`: The query is complex and requires a full, multi-step research plan.
        *   `direct_retrieval`: The query can likely be answered by a single, direct lookup in the knowledge graph.
        *   `contextual_clarification`: The query is a follow-up to the previous turn and can be answered using conversation history.

## Downstream Routing

Based on the classification result, the `TriageAgent` routes the state to the appropriate next agent:
*   **To `PlanningAgent` & `HydeAgent`:** For `complex_research`.
*   **To `ContextualAnsweringAgent`:** For `contextual_clarification`.
*   **To `ResearchOrchestrator`:** For `direct_retrieval` (skipping the planning phase). 