# Planning Agent

## Purpose

The `PlanningAgent` acts as the primary strategist for the research workflow. When a user's query is too complex for a simple or direct answer, this agent's job is to deconstruct it into a logical, step-by-step plan that the `ResearchOrchestrator` can execute.

## Core Functions

1.  **Query Decomposition:**
    *   The agent receives the user's query and any existing conversational context.
    *   It uses a Tier-1 Language Model to analyze the query and break it down into a series of smaller, self-contained sub-queries. This ensures that each research step is focused and targeted.
    *   The output is a structured list of these sub-queries, which forms the `research_plan`.

2.  **Calculation Detection:**
    *   A key function of this agent is to analyze the query for keywords and patterns that indicate a need for mathematical calculation (e.g., "calculate", "what is the value of", "using equation 16-7").
    *   If a calculation is detected, it sets a `MATH_CALCULATION_NEEDED` flag in the workflow's state. This flag is used by the `SynthesisAgent` later to choose a specialized response format.

## Downstream Routing

The `PlanningAgent` has a single, linear downstream path:
*   The `research_plan` it generates is passed directly to the `HydeAgent` for the next step in the research preparation phase. 