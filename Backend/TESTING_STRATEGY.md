# Testing Strategy

This document outlines the testing strategy for the AI agent, covering different types of test cases designed to ensure the system's accuracy, robustness, and efficiency.

## 1. Unit Tests

*   **Purpose:** To verify the functionality of individual, isolated components.
*   **Scope:**
    *   **Tool Tests:** Each module in the `/tools` directory should have unit tests to confirm it functions correctly (e.g., does `Neo4jConnector` successfully connect and run a simple query?).
    *   **Agent Logic Tests:** Test helper functions within agents that do not require a full workflow run (e.g., does the calculation detection regex in the `PlanningAgent` correctly identify mathematical queries?).

## 2. Integration Tests

*   **Purpose:** To test the interaction and data flow between connected components.
*   **Scope:**
    *   **Agent-to-Tool:** Test the direct interaction between an agent and the tools it uses (e.g., does the `ResearchOrchestrator` correctly call the `Neo4jConnector` and process its output?).
    *   **Agent-to-Agent:** Verify the data transfer between two sequential agents (e.g., does the `PlanningAgent` produce a `research_plan` that the `HydeAgent` can correctly interpret?).

## 3. End-to-End (E2E) Workflow Tests

*   **Purpose:** To test the entire agentic workflow from input to output, simulating a real user query. These are the most important tests for ensuring overall system quality.
*   **Scope:** These tests are built around specific query types that target different paths in the architecture.

### E2E Test Case Categories:

*   **Cache Hit Test:**
    *   **Description:** Run a complex query twice.
    *   **Expected Behavior:** The first run should take a significant amount of time and involve the full research pipeline. The second run should be nearly instantaneous (<1s) and show in the logs that the answer was retrieved from the cache.

*   **Contextual Follow-up Test:**
    *   **Description:** Ask an initial, broad question. Then, ask a follow-up question that relies on the first answer (e.g., "And what about the requirements for the handrail?").
    *   **Expected Behavior:** The second query should be routed through the `ContextualAnsweringAgent` and answered correctly without initiating a new research plan.

*   **Simple Direct Retrieval Test:**
    *   **Description:** Ask a question that can be answered by a single, direct lookup (e.g., "What is Section 1607.12?").
    *   **Expected Behavior:** The `TriageAgent` should classify this as `direct_retrieval`. The workflow should skip the `PlanningAgent` and `HydeAgent` and go straight to the `ResearchOrchestrator`.

*   **Complex Research Test:**
    *   **Description:** Ask a broad, multi-faceted question (e.g., "What are all the live load requirements for residential balconies?").
    *   **Expected Behavior:** The system should engage the full pipeline: `PlanningAgent` should create multiple sub-queries, `HydeAgent` should generate documents, and `ResearchOrchestrator` should execute a parallel search.

*   **Calculation-Based Test:**
    *   **Description:** Ask a question that requires a formula and calculation (e.g., "Using Equation 16-7, calculate the reduced live load for a tributary area of 500 sq ft.").
    *   **Expected Behavior:** The `PlanningAgent` should set the `MATH_CALCULATION_NEEDED` flag. The `SynthesisAgent` should use its specialized "enhanced calculation" path to provide a step-by-step answer.

*   **Fallback and Resilience Test:**
    *   **Description:** Formulate a query that is known to not exist in the **Neo4j** knowledge base but is answerable via a web search.
    *   **Expected Behavior:** The logs should show the `ResearchOrchestrator` attempting and failing the Neo4j retrieval steps, and then successfully finding an answer using the **Tavily** web search tool. 