# LangSmith Trace Analysis & Debugging Guide

Congratulations on successfully integrating LangSmith! This guide will teach you how to analyze the traces you are now collecting to debug issues and understand your agent's cognitive process.

---

## **Understanding the LangSmith Trace View**

When you click on a trace, you'll see a waterfall view. This is the timeline of your agent's execution. Each bar represents a "run" – a self-contained operation with its own inputs, outputs, and duration.

*   **Parent Run (Top Bar):** This is the entire `app.astream` call. Its duration is the total response time.
*   **Nested Runs:** These are the individual agents, tools, and LLM calls that were executed as part of the overall run.

---

## **Workflow for Analyzing a Complex Trace**

Let's use the query you just ran as an example. Find that trace in your project and follow along.

### **Step 1: Top-Down Analysis (The "What")**

1.  **Start with the Parent Run:** Look at the total duration. Is it what you expected?
2.  **Examine the Main Agent Runs:** You will see runs for each major component of your graph, likely in this order:
    *   `TriageAgent`
    *   `PlanningAgent`
    *   `ResearchOrchestrator`
    *   `SynthesisAgent`
    Identify which of these top-level runs took the most time. This immediately tells you where the biggest performance bottlenecks are.

### **Step 2: Deep Dive into the `ResearchOrchestrator` (The "Why")**

The `ResearchOrchestrator` is the most complex part of your system. This is where you'll spend most of your debugging time.

1.  **Click to Expand:** Click on the `ResearchOrchestrator` run in the waterfall view.
2.  **View Sub-Queries:** You will see the parallel sub-queries that were executed. If you used the parallel tool, they will appear nested under a `ParallelResearchTool` run.
3.  **Inspect a Single Sub-Query:** Click on one of the sub-query runs. Now you can see the magic:
    *   **Retrieval Step:** Look for the tool call to your Neo4j database.
        *   **Inputs:** You'll see the exact Cypher query that was generated and executed. Is it correct?
        *   **Outputs:** You'll see the raw data retrieved from the graph. Is it relevant to the sub-query?
    *   **Reranking Step:** Look for the `CohereReranker` run.
        *   **Inputs:** See the documents that were passed to the reranker.
        *   **Outputs:** See the documents that came out, along with their new `relevance_score`. Did the reranker correctly prioritize the most relevant documents?
    *   **Validation Step:** Look for the `ThinkingValidationAgent` run.
        *   **Inputs:** This agent receives the reranked, validated context.
        *   **Outputs:** Check the `relevance_score` and `reasoning`. This is how you'll know if the context for a sub-query was good enough to proceed.

### **Step 3: Analyze LLM Calls (The "How")**

For any agent that calls an LLM (like the `PlanningAgent` or `SynthesisAgent`), you can get granular details.

1.  **Click on an LLM Call:** In the trace, these are typically labeled with the model name (e.g., `ChatGoogleGenerativeAI`).
2.  **Inspect the Prompt & Response:**
    *   **Inputs:** You will see the full, formatted prompt that was sent to the model. This is invaluable for prompt engineering. If the model gave a bad response, the problem is often in the prompt it received.
    *   **Outputs:** See the raw text or JSON that the model returned.
    *   **Settings:** View the `temperature`, `model_name`, and other settings used for that specific call.
    *   **Token Usage:** See exactly how many prompt and completion tokens were used, which is critical for cost monitoring.

---

## **Example Debugging Scenario: A Bad Answer**

Imagine a user reports that the agent gave an answer that missed key details.

**Your Debugging Workflow:**

1.  **Find the Trace:** Use the `thread_id` from the user's session to find the exact trace in LangSmith.
2.  **Check the `SynthesisAgent`:**
    *   **Input:** Look at the `sub_query_answers` that were passed into it. Is the missing information absent from this context? If yes, the problem happened *before* synthesis.
    *   **Prompt:** Look at the prompt sent to the synthesis model. Did it correctly instruct the model to include all details?
3.  **Investigate the `ResearchOrchestrator`:** If the context was bad, this is the culprit.
    *   Did one of the sub-queries fail to retrieve the right documents?
    *   Did the reranker push the important documents to the bottom?
    *   Did the `ThinkingValidationAgent` incorrectly approve low-quality context?
4.  **Inspect the `PlanningAgent`:** If the research plan itself was flawed (e.g., it didn't create a sub-query for the missing information), the issue started here. Check the prompt that generated the plan.

---

## **Next Steps: Practice**

The best way to learn is by doing. Take a few of the recent traces in your project and go through this analysis workflow. Try to answer these questions for each trace:

*   What was the most time-consuming step?
*   Was the context retrieved from the knowledge graph relevant?
*   Did the final answer accurately reflect the context that was retrieved?

Once you are comfortable with this analysis process, let me know, and we will proceed to **Phase 4: Automated Evaluations**. 