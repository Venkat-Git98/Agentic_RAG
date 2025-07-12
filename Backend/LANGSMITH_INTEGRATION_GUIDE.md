# LangSmith Integration Guide

This guide provides a step-by-step process for activating and verifying the LangSmith integration with your agentic AI system.

---

## **Phase 1: Environment Configuration (Now Complete)**

The codebase has been updated to support LangSmith tracing. To activate it, you must configure the following environment variables in your deployment environment (e.g., a local `.env` file or your Railway project settings).

```bash
# 1. Enable LangSmith Tracing (Master Switch)
LANGCHAIN_TRACING_V2="true"

# 2. Set Your LangSmith API Key
# Get this from your LangSmith account settings page.
LANGCHAIN_API_KEY="ls__..."

# 3. Set Your LangSmith Project Name
# This will help you organize traces. Choose a meaningful name.
LANGCHAIN_PROJECT="Agentic-AI-Production"

# 4. (Optional) Ensure the endpoint is set (usually not needed)
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
```

---

## **Phase 2: Verification (Your Turn)**

Follow these steps to ensure that traces are being captured correctly.

### **Step 2.1: Run a Test Query**

After setting the environment variables and restarting your application, send a test query to your API. It is best to use a complex query that will trigger a full research workflow.

**Example `curl` command:**
```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
           "message": "What is the difference between the live load requirements for a residential balcony and a commercial parking garage?",
           "thread_id": "langsmith_test_01"
         }'
```

### **Step 2.2: Verify in the LangSmith UI**

1.  **Log in to your LangSmith account.**
2.  Navigate to the project you specified in the `LANGCHAIN_PROJECT` environment variable (e.g., "Agentic-AI-Production").
3.  You should see a new trace appear at the top of the list for the query you just ran.

### **What to Look For in the Trace:**

*   **A Full Waterfall View:** The main trace should show the total run time.
*   **Component Runs:** You should see nested runs for each agent (`TriageAgent`, `PlanningAgent`, `ResearchOrchestrator`, etc.).
*   **LLM & Tool Calls:** Click into the `ResearchOrchestrator` run. You should see the individual LLM calls for planning and the tool calls to your Neo4j database.
*   **Metadata:** On the left-hand side of the trace view, under the "Metadata" tab, you should see the `user_id` and `thread_id` that you passed in your API call. This confirms that metadata propagation is working.

![Example LangSmith Trace](https://blog.langchain.dev/content/images/2023/10/Screenshot-2023-10-17-at-1.56.28-PM.png)
*(Image for illustrative purposes)*

---

## **Next Steps**

Once you have successfully verified that traces are appearing in LangSmith, please let me know. We can then proceed to the next phases:

*   **Phase 3: Deep Debugging and Analysis:** I can guide you on how to interpret complex traces to debug issues.
*   **Phase 4: Automated Evaluations:** I can help you set up a dataset and define evaluators to continuously monitor your agent's quality. 