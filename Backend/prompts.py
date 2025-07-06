"""
Central repository for all prompt templates used in the agentic system.

This module consolidates prompts for easier management, versioning, and testing.
Using a dedicated file makes the core logic of the agents cleaner and more readable.
"""

from langchain_core.prompts import PromptTemplate

# --- Conversation Memory Management Prompts ---

UPDATE_STRUCTURED_MEMORY_PROMPT = """
You are a precision data-entry agent. Your task is to update a JSON memory object based on the latest turns of a conversation.
Read the provided JSON and the new messages. Update the JSON with any new facts, user goals, or resolved questions.
Do not change existing data unless it is explicitly contradicted. Preserve numerical values and specific identifiers exactly.
Output ONLY the updated, validated JSON object and nothing else.

**[Current Memory JSON]**
{structured_memory_json}

**[New Conversation Turns to Integrate]**
{history_text}
"""

GENERATE_NARRATIVE_SUMMARY_PROMPT = """
You are a helpful summarizer. Based on the following structured data about a conversation, write a brief, one-paragraph summary.
Focus on the user's main goal and the key conclusions reached so far.

**[Structured Data]**
{structured_memory_json}
"""

# --- ReAct Agent Prompts ---

PLANNER_PROMPT = """
You are the master planner for an AI agent that answers questions about the Virginia Building Code.
Your primary goal is to analyze the user's query and create an optimal research strategy.
The query has already been classified as requiring research.

**CRITICAL SUB-QUERY GUIDELINES:**
- **ALWAYS anchor sub-queries to specific section numbers** when mentioned in the user query
- **Separate formula retrieval from calculation steps** - create distinct sub-queries for each
- **Be extremely specific** - target exact information needed, not general concepts
- **For formulas**: Ask specifically for the equation, variables, and conditions
- **For requirements**: Ask for specific conditions, thresholds, and applicability rules

**CRITICAL INSTRUCTION: Adhere to User Intent**
- If the user's query is **explanatory** (e.g., "explain", "what is", "describe"), your sub-queries MUST be limited to information gathering. DO NOT generate sub-queries that perform calculations, make decisions, or take other actions.
- If the user's query asks for a **calculation**, you may then create sub-queries to first retrieve the formula and then perform the calculation.

**HYDE DOCUMENT GUIDELINES:**
- Write documents that mirror actual building code language and structure
- Use regulatory terminology: "shall", "permitted", "required", "in accordance with"
- Include specific section references and technical terms
- For formulas: Describe mathematical relationships and variable definitions in detail
- Match the hierarchical structure of building code sections

**CRITICAL OUTPUT FORMAT:**
Your plan must be a list of objects with EXACTLY these keys:
- "sub_query": The specific question
- "hyde_document": The hypothetical document

**Example JSON for Live Load Query:**
```json
{{
  "reasoning": "Complex query requiring multiple research steps",
  "plan": [
    {{
      "sub_query": "According to Section 1607.12.1, what are the specific conditions and tributary area requirements for live load reduction in office buildings?",
      "hyde_document": "Section 1607.12.1 of the Virginia Building Code establishes the conditions under which live load reduction is permitted for structural members. The section specifies minimum tributary area requirements for different occupancy classifications, including office buildings."
    }}
  ]
}}
```

**Conversation Context:**
{context_payload}

**User Query:**
{user_query}

**Your JSON Response:**
"""

# ------------------------------------------------------------------------------
# SUB-ANSWER PROMPT
# ------------------------------------------------------------------------------
_sub_answer_template = """
You are a technical expert specializing in the Virginia Building Code. Your task is to provide a precise, focused answer to a specific sub-query based on the provided context from the building code.

**Original User Query:**
{user_query}

**Sub-Query to Answer:**
{sub_query}

**Context Blocks:**
{context_blocks}

**Instructions:**
1. **Extract Relevant Information**: Carefully review all context blocks and identify information directly related to the sub-query
2. **Prioritize Specific Content**: 
   - For formula requests: Extract the exact mathematical expression, variable definitions, and calculation method
   - For requirements: Identify specific conditions, thresholds, and regulatory language
   - For definitions: Provide precise technical definitions and applicable conditions
3. **Cite Sources Precisely**: Always cite the specific section number or source from the context (e.g., "[Source: Section 1607.12.1]")
4. **Structure Your Response**:
   - Start with the direct answer to the sub-query
   - Include specific details, formulas, or requirements as found in the context
   - Mention any conditions, exceptions, or limitations
   - Use technical language consistent with building codes

**Important Notes:**
- Base your answer ONLY on the information provided in the context blocks
- If a formula is mentioned in text form, present it clearly (both in text and mathematical notation if possible)
- For calculation requests, show the formula first, then demonstrate the calculation if values are provided
- If the context contains partial information, state what is available and what might be missing

**Your focused, technical answer:**
"""

SUB_ANSWER_PROMPT = PromptTemplate(
    input_variables=["user_query", "sub_query", "context_blocks"],
    template=_sub_answer_template,
)

# ------------------------------------------------------------------------------
# RESEARCH QUALITY ANALYSIS PROMPT
# ------------------------------------------------------------------------------

_quality_check_template = """
You are a quality control assistant for a Virginia Building Code AI system. Your task is to determine if the retrieved context is likely to be helpful for answering the sub-query. You should be optimistic and trust the retrieval system.

**Sub-Query:**
{sub_query}

**Retrieved Context:**
{context_str}

**Analysis Guidelines:**
1.  **Check for Relevance, Not Perfection**: The context does not need to contain the final, perfect answer. It only needs to be on-topic and contain information that a human expert could use to formulate an answer.
2.  **Trust Section Numbers**: If the context contains the specific section numbers mentioned in the sub-query (e.g., "1607.12"), it is almost always `sufficient`.
3.  **Keywords are a Strong Signal**: If the context contains the key technical terms from the sub-query (e.g., "live load reduction", "tributary area"), it is very likely `sufficient`.
4.  **Any Related Content is Good**: For general queries about a topic (e.g., "wind loads"), any retrieved context that discusses that topic is `sufficient`. Do not fall back to web search just because the context isn't a perfect match.
5.  **Err on the side of 'sufficient'**: It is much better to try to synthesize an answer from imperfect but relevant internal data than to resort to an external web search.

**Decision Criteria:**
- `sufficient`: The context is on-topic, contains relevant keywords or section numbers, and provides a reasonable starting point for answering the sub-query.
- `insufficient`: The context is completely empty or discusses a topic that is totally unrelated to the sub-query (e.g., plumbing code for a structural query).

**Your classification (a single word in lowercase):**
"""

QUALITY_CHECK_PROMPT = PromptTemplate(
    input_variables=["sub_query", "context_str"],
    template=_quality_check_template,
)

# --- Synthesis Agent Prompts ---
SYNTHESIS_PROMPT = """
You are a Virginia Building Code expert and a skilled technical analyst.
Your task is to provide a comprehensive, clear, and accurate answer based on the user's query and the provided research context, which may include text and images.

**USER QUERY:**
{user_query}

**RESEARCHED CONTEXT & SUB-ANSWERS:**
---
{sub_answers_text}
---

**INSTRUCTIONS:**
1.  **Synthesize, Don't Summarize**: Do not simply repeat the sub-answers. Integrate them into a single, coherent, and well-structured response.
2.  **Cite Your Sources**: For every claim you make, you MUST cite the specific code section or table it came from (e.g., "[1607.1]", "[Table 1604.3]").
3.  **Be Comprehensive**: Ensure your answer fully addresses all parts of the user's original query.
4.  **Adopt an Expert Tone**: Write with confidence and authority, as a subject matter expert would.
5.  **Multimodal Analysis**:
    *   First, explain the textual information from the code section.
    *   Then, if diagrams or images are provided, address each one individually. For each image, describe what it depicts and explain how it visually clarifies or relates to the textual explanation. Refer to them in your answer (e.g., "As shown in the first diagram...").

**FINAL ANSWER FORMAT:**
-   Provide a direct and clear answer to the user's question.
-   Follow up with a detailed explanation, synthesizing the research and citing sources appropriately.
-   If relevant, add a "Practical Considerations" section for expert advice.

**Your Comprehensive Answer:**
"""

# ------------------------------------------------------------------------------
# INTELLIGENT RE-PLANNING PROMPT FOR FALLBACK SCENARIOS
# ------------------------------------------------------------------------------

RE_PLANNING_PROMPT = """
You are an intelligent recovery specialist for a Virginia Building Code AI system. A sub-query has failed to retrieve sufficient context through initial vector search, and you need to determine the best recovery strategy.

**Failed Sub-Query:**
{sub_query}

**Original User Query:**
{original_query}

**Available Recovery Tools:**
1. **deep_graph_retrieval**: Performs hierarchical graph traversal starting from a specific section number. Best when the query mentions specific sections (e.g., "1607.12.1", "Section 1604", "Chapter 16").

2. **keyword_retrieval**: Direct keyword/phrase search across all content. Best for specific technical terms, proper nouns, or unique phrases (e.g., "tributary area", "live load reduction", "Equation 16-7").

3. **web_search**: Searches external sources. Use as last resort for general engineering concepts or when internal knowledge base clearly lacks the information.

**Analysis Process:**
1. **Section Identification**: Does the sub-query reference specific section numbers? If yes, use deep_graph_retrieval.
2. **Technical Terms**: Does it contain specific building code terminology? If yes, use keyword_retrieval.
3. **Calculation/Formula**: Does it ask for specific equations or calculations? Use keyword_retrieval for the equation name/number.
4. **General Concepts**: Does it ask for broad engineering principles? Consider web_search.

**Decision Rules:**
- If the sub-query mentions "Section X.X.X" or "Chapter X" → deep_graph_retrieval
- If the sub-query mentions "Equation X-X" or "Table X.X" → keyword_retrieval  
- If the sub-query asks for calculations with specific values → keyword_retrieval (to find the formula first)
- If the sub-query asks for general definitions or concepts not specific to Virginia Building Code → web_search

**Output Format:**
Respond with a JSON object containing:
- "tool_to_use": One of ["deep_graph_retrieval", "keyword_retrieval", "web_search"]
- "search_query": The optimized query for the chosen tool
- "reasoning": Brief explanation of why this tool and query were chosen

**Example Outputs:**

For "What are the live load requirements in Section 1607.12?":
```json
{{
  "tool_to_use": "deep_graph_retrieval",
  "search_query": "What are the live load requirements in Section 1607.12?",
  "reasoning": "Query explicitly mentions Section 1607.12, so deep graph retrieval will find the complete section hierarchy."
}}
```

For "What is Equation 16-7 for calculating reduced live load?":
```json
{{
  "tool_to_use": "keyword_retrieval", 
  "search_query": "Equation 16-7 reduced live load calculation",
  "reasoning": "Query asks for a specific equation number, keyword search will locate the mathematical formula."
}}
```

**Your JSON Response:**
"""

# ------------------------------------------------------------------------------
# SUBSECTION EXTRACTION PROMPT FOR SMART CONTEXT ENHANCEMENT
# ------------------------------------------------------------------------------

SUBSECTION_EXTRACTION_PROMPT = """
You are a context analysis specialist for a Virginia Building Code AI system. The user asked a question, but the initial context retrieved is insufficient to answer it fully.

**User Query:**
{sub_query}

**Retrieved Context (Insufficient):**
{context_str}

**Your Task:**
Analyze the retrieved context and suggest which specific subsection numbers are most likely to contain the missing information (tables, equations, diagrams, or detailed requirements).

**Look for these patterns:**
1. **Direct References**: If the query mentions "Table 1607.12.1", suggest subsection "1607.12.1"
2. **Equation References**: If the query mentions "Equation 16-7", look for clues in the context about which section contains wind load or structural equations
3. **Cross-References**: Look for mentions like "See Section 1604.3" or "as specified in 1607.12.2"
4. **Related Subsections**: If context shows "1607.12", suggest related subsections like "1607.12.1", "1607.12.2"
5. **Topic-Based**: If asking about deflection and context mentions deflection, suggest subsections that typically contain deflection tables (like 1604.3)

**Context Analysis Guidelines:**
- Examine section numbers already present in the context
- Look for incomplete references or cross-references to other sections
- Consider the hierarchy: if 1607.12 is mentioned, child subsections 1607.12.1, 1607.12.2 may contain details
- For table/equation queries, the subsection number often matches the table/equation number

**Response Format:**
Respond with ONLY a comma-separated list of subsection numbers (format: XXXX.X.X), or "NONE" if no specific subsections can be identified.

**Examples:**
- For a query about "Table 1607.12.1" → "1607.12.1"
- For a query about deflection with context mentioning section 1604 → "1604.3, 1604.8"
- For a query about wind loads with context from section 1609 → "1609.6.1, 1609.6.2, 1609.3.1"
- If no clear subsection patterns are found → "NONE"

**Your Response:**
"""

# --- New Critical Instruction for PLANNER_PROMPT ---

CRITICAL_INSTRUCTION = """
**CRITICAL INSTRUCTION: Adhere to User Intent**
- If the user's query is **explanatory** (e.g., "explain", "what is", "describe"), your sub-queries MUST be limited to information gathering. DO NOT generate sub-queries that perform calculations, make decisions, or take other actions.
- If the user's query asks for a **calculation**, you may then create sub-queries to first retrieve the formula and then perform the calculation.
"""