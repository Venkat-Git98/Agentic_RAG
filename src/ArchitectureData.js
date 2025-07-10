export const architectureNodes = [
  // Level 0: Input
  {
    id: 'userQuery',
    label: 'User Query',
    group: 'input',
    description: "The process begins with a query submitted by the user. This is the primary input that triggers the entire agentic workflow."
  },

  // Level 1: Triage
  {
    id: 'triageAgent',
    label: '🤖\nTriage Agent',
    group: 'agent',
    description: "The first agent that analyzes the user query. It performs an initial classification to determine the query's nature and how to proceed. It uses a combination of pattern matching for simple cases and an LLM for complex classification."
  },
  {
    id: 'triageDecision',
    label: 'Query\nClassification',
    group: 'decision',
    description: "A critical decision point based on the Triage Agent's analysis. The workflow branches here based on whether the query is valid, requires clarification, or should be rejected."
  },
  {
    id: 'endClarify',
    label: 'End:\nClarify',
    group: 'end',
    description: "The workflow terminates if the query is too vague. The system asks the user for more details before it can proceed."
  },
  {
    id: 'endReject',
    label: 'End:\nReject',
    group: 'end',
    description: "The workflow terminates if the query is off-topic, inappropriate, or outside the AI's scope of knowledge."
  },

  // Level 2: Planning
  {
    id: 'planningAgent',
    label: '🤖\nPlanning Agent',
    group: 'agent',
    description: "If the query is valid, the Planning Agent takes over. It analyzes the query in depth to generate a strategic plan. This can range from a simple direct data fetch to a complex multi-step research plan."
  },
  {
    id: 'planningDecision',
    label: 'Strategy\nGeneration',
    group: 'decision',
    description: "The decision point following the planning phase. The workflow can branch to direct answer synthesis, full-scale research, or end if a simple answer is sufficient."
  },
    {
    id: 'endSimple',
    label: 'End:\nSimple Answer',
    group: 'end',
    description: "The workflow terminates if the Planning Agent can provide a direct, simple answer without needing to perform extensive research."
  },

  // Level 3: Research
  {
    id: 'researchOrchestrator',
    label: '🔄\nResearch Orchestrator',
    group: 'orchestrator',
    description: "This component manages the execution of the research plan. It processes sub-queries in parallel and includes a sophisticated fallback chain to ensure the most relevant information is found."
  },
  {
    id: 'fallbackChain',
    label: 'Internal\nFallback Chain',
    group: 'process',
    description: "A sequential process to find information. It starts with the most efficient methods (Cache, Vector Search) and progressively uses more comprehensive ones (Graph, Keyword, Web Search) if initial attempts fail."
  },
  {
    id: 'validationAgent',
    label: '🔬\nValidation Agent',
    group: 'agent',
    description: "After research, this agent assesses the quality and sufficiency of the gathered information. It also performs a critical check to detect if any mathematical calculations are required to answer the query."
  },

  // Level 4: Validation Decision
  {
    id: 'validationDecision',
    label: 'Assess Research\n& Detect Math',
    group: 'decision',
    description: "The most critical routing decision. The presence of required mathematical calculations takes absolute priority. Otherwise, the path is determined by whether the research results are sufficient."
  },

  // Level 5: Augmentation (Conditional)
  {
    id: 'calculationExecutor',
    label: '🧮\nCalculation Executor',
    group: 'augment',
    description: "This component is activated ONLY if the Validation Agent detects a need for math. It performs the necessary calculations, which can range from simple library calls to complex execution in a secure Docker container. The results are then appended to the research context."
  },
  {
    id: 'placeholderHandler',
    label: '📝\nPlaceholder Handler',
    group: 'augment',
    description: "This component is activated if research is found to be insufficient. It generates placeholder content and crafts a partial answer, acknowledging the gaps in the available information."
  },

  // Level 6: Synthesis & Memory
  {
    id: 'synthesisAgent',
    label: '📝\nSynthesis Agent',
    group: 'agent',
    description: "The final assembly point. This agent integrates all available information (research, calculations, placeholders) into a single, coherent answer. It also manages citations and calculates a final confidence score."
  },
  {
    id: 'memoryAgent',
    label: '💾\nMemory Agent',
    group: 'agent',
    description: "The last step in the process. This agent persists the conversation history and interaction details to Redis for long-term memory and potential future optimizations. It also handles logging and analytics."
  },
    {
    id: 'endSuccess',
    label: 'End:\nSuccess',
    group: 'end',
    description: "The workflow successfully completes, having stored the interaction in memory and provided the final answer to the user."
  },
];

export const architectureEdges = [
  // Triage Flow
  { from: 'userQuery', to: 'triageAgent' },
  { from: 'triageAgent', to: 'triageDecision' },
  { from: 'triageDecision', to: 'planningAgent', label: 'Engage' },
  { from: 'triageDecision', to: 'endClarify', label: 'Clarify' },
  { from: 'triageDecision', to: 'endReject', label: 'Reject' },

  // Planning Flow
  { from: 'planningAgent', to: 'planningDecision' },
  { from: 'planningDecision', to: 'researchOrchestrator', label: 'Research' },
  { from: 'planningDecision', to: 'synthesisAgent', label: 'Direct' },
  { from: 'planningDecision', to: 'endSimple', label: 'Simple' },

  // Research Flow
  { from: 'researchOrchestrator', to: 'fallbackChain' },
  { from: 'fallbackChain', to: 'validationAgent' },
  { from: 'validationAgent', to: 'validationDecision' },

  // Validation Flow
  { from: 'validationDecision', to: 'calculationExecutor', label: 'Math Needed' },
  { from: 'validationDecision', to: 'placeholderHandler', label: 'Needs Correction' },
  { from: 'validationDecision', to: 'synthesisAgent', label: 'Sufficient' },

  // Augmentation to Synthesis
  { from: 'calculationExecutor', to: 'synthesisAgent' },
  { from: 'placeholderHandler', to: 'synthesisAgent' },

  // Finalization Flow
  { from: 'synthesisAgent', to: 'memoryAgent' },
  { from: 'memoryAgent', to: 'endSuccess' },
]; 