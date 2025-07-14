# Contextual Answering Agent

## Purpose

The `ContextualAnsweringAgent` serves as a "fast path" in the workflow, designed to handle simple, conversational follow-up questions efficiently. Its goal is to provide a quick and accurate response without engaging the full, resource-intensive research pipeline.

## Core Functions

1.  **Contextual Analysis:**
    *   This agent is activated when the `TriageAgent` classifies a query as a `contextual_clarification`.
    *   It retrieves the recent conversation history from the **Redis session store**.

2.  **LLM-Powered Response Generation:**
    *   It uses a powerful Tier-1 Language Model, providing it with both the user's current follow-up question and the retrieved conversation history.
    *   The prompt strictly instructs the LLM to answer the question *only* if the information is present in the provided context.

3.  **Success/Failure Determination:**
    *   The LLM's response indicates whether it was able to formulate an answer from the context (`"answerable": true`) or not.

## Downstream Routing

The agent's decision dictates the next step in the workflow:

*   **On Success:** If an answer is generated, it is passed directly to the `SynthesisAgent` to be formatted as the final response. The main research path is skipped entirely.
*   **On Failure:** If the context is insufficient, the agent signals a failure. The workflow then re-routes the query to the `PlanningAgent` to initiate a full research process, ensuring that even failed contextual queries are still answered correctly. 