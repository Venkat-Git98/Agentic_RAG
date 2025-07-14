# Synthesis Agent

## Purpose

The `SynthesisAgent` acts as the final author for the system. Its primary role is to take the potentially fragmented collection of verified research data from the `ResearchOrchestrator` and weave it into a single, cohesive, and human-readable final answer.

## Core Functions

1.  **Answer Generation:**
    *   The agent receives the full set of sub-query answers and the original user query.
    *   It uses a powerful Tier-1 Language Model to synthesize this information, creating a comprehensive response that directly addresses the user's initial question.

2.  **Specialized Calculation Path:**
    *   The agent first checks for the `MATH_CALCULATION_NEEDED` flag set by the `PlanningAgent`.
    *   If the flag is `True`, it uses a specialized "enhanced calculation" prompt. This instructs the LLM to format the answer in a step-by-step manner, clearly explaining any formulas, variables, and the final numerical result.
    *   If the flag is `False`, it proceeds with the standard synthesis process.

3.  **Quality Assessment & Caching:**
    *   After generating the answer, the agent performs a quality check.
    *   If the answer is deemed high-quality (based on factors like length, confidence, and citation presence), it is passed to the `MemoryAgent` with instructions to store it in the **Redis performance cache** (Prompt Caching).

## Downstream Routing

*   After the synthesis and quality check are complete, the final answer and caching instruction are passed to the `MemoryAgent` for the final step of the workflow. 