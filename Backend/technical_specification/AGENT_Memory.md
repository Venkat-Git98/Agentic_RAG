# Memory Agent

## Purpose

The `MemoryAgent` is the final agent in the workflow. It is responsible for persisting the results of the interaction, ensuring the system can learn from its work and maintain conversational context.

## Core Functions

1.  **Performance Caching:**
    *   If the `SynthesisAgent` flagged the final answer as high-quality, this agent's first job is to store that answer in the **Redis performance cache**.
    *   This "Prompt Caching" ensures that if the same query is asked again, it can be answered almost instantly by the `TriageAgent`.

2.  **Session Management:**
    *   Regardless of whether the answer was cached, the agent's second job is to update the user's current conversation history.
    *   It saves the user's most recent query and the system's final answer to the **Redis session store**. This provides the necessary short-term context for the `ContextualAnsweringAgent` to handle follow-up questions.

## Downstream Routing

*   The `MemoryAgent` is the final cognitive step. After it completes its tasks, the final answer is delivered to the user, and the workflow run concludes. 