export const detailedArchitectureNodes = [
  // --- Core Agents ---
  { id: 'triageAgent', label: '🤖\nTriage Agent', group: 'agent' },
  { id: 'planningAgent', label: '🤖\nPlanning Agent', group: 'agent' },
  { id: 'researchOrchestrator', label: '🔄\nResearch Orchestrator', group: 'orchestrator' },
  { id: 'validationAgent', label: '🔬\nValidation Agent', group: 'agent' },
  { id: 'synthesisAgent', label: '📝\nSynthesis Agent', group: 'agent' },
  { id: 'memoryAgent', label: '💾\nMemory Agent', group: 'agent' },

  // --- Entry & Exit ---
  { id: 'userQuery', label: 'User Query', group: 'input' },
  { id: 'endSuccess', label: 'End\n(Success)', group: 'end' },

  // --- Triage Internals ---
  { id: 'triagePatternScreen', label: 'Pattern\nScreening', group: 'sub-process', description: "Fast check for simple rejection or direct retrieval patterns." },
  { id: 'triageLlm', label: 'LLM\nClassification', group: 'sub-process-llm', description: "For complex queries, an LLM determines the final classification (Engage, Clarify, Reject)." },
  { id: 'triageDecision', label: 'Route', group: 'decision-small' },
  { id: 'endClarify', label: 'End\n(Clarify)', group: 'end' },
  { id: 'endReject', label: 'End\n(Reject)', group: 'end' },

  // --- Planning Internals ---
  { id: 'planningAnalysis', label: 'Query\nAnalysis', group: 'sub-process', description: "Deep analysis of the query to determine the best strategy." },
  { id: 'planningDecision', label: 'Route', group: 'decision-small' },
  { id: 'planningHyde', label: 'Create Sub-Queries\n(HyDE)', group: 'sub-process-llm', description: "Generates a multi-step research plan with hypothetical document embeddings for enhanced retrieval." },
  { id: 'planningDirectRetrieval', label: 'Retrieve\nEntity', group: 'sub-process', description: "Directly fetches a specific, known entity from the knowledge graph." },
  { id: 'endSimple', label: 'End\n(Simple Answer)', group: 'end' },

  // --- Research Internals (Fallback Chain) ---
  { id: 'researchCache', label: 'Cache\nCheck', group: 'sub-process-io', description: "Checks Redis cache for previously computed results to this sub-query." },
  { id: 'researchVector', label: 'Vector\nSearch', group: 'fallback', description: "Primary retrieval method using semantic vector search." },
  { id: 'researchGraph', label: 'Graph\nSearch', group: 'fallback', description: "Secondary search on the knowledge graph if vector search fails." },
  { id: 'researchKeyword', label: 'Keyword\nSearch', group: 'fallback', description: "Tertiary search using traditional keyword matching." },
  { id: 'researchWeb', label: 'Web\nSearch', group: 'fallback-web', description: "Final fallback to a web search engine if all internal methods fail." },
  { id: 'researchCollect', label: 'Collect\nResults', group: 'sub-process' },

  // --- Validation Internals ---
  { id: 'validationQuality', label: 'Assess\nQuality', group: 'sub-process', description: "Evaluates the sufficiency and relevance of the research results." },
  { id: 'validationMath', label: 'Detect\nMath', group: 'sub-process-llm', description: "Uses an LLM to detect if mathematical calculations are needed." },
  { id: 'validationDecision', label: 'Route', group: 'decision-small' },

  // --- Augmentation ---
  { id: 'calculationExecutor', label: '🧮\nCalculation Executor', group: 'augment', description: "Performs complex math via Docker or libraries." },
  { id: 'placeholderHandler', label: '📝\nPlaceholder Handler', group: 'augment', description: "Generates partial answers if research is incomplete." },

  // --- Error Handling ---
  { id: 'errorHandler', label: '🚨\nError Handler', group: 'error', description: "Centralized error handling mechanism." },
  { id: 'errorFallback', label: 'Fallback\nStrategy', group: 'error-sub', description: "Executes a fallback path (e.g., trying web search)." },
  { id: 'errorRetry', label: 'Wait &\nRetry', group: 'error-sub', description: "Waits for a period (e.g., for API quota reset) and retries the step." },
  { id: 'errorDegrade', label: 'Graceful\nDegradation', group: 'error-sub', description: "Proceeds with partial data to provide a best-effort response." },
];

export const detailedArchitectureEdges = [
  // Entry
  { from: 'userQuery', to: 'triageAgent' },
  { from: 'triageAgent', to: 'triagePatternScreen' },
  
  // Triage Flow
  { from: 'triagePatternScreen', to: 'triageLlm', label: 'if complex' },
  { from: 'triageLlm', to: 'triageDecision' },
  { from: 'triagePatternScreen', to: 'triageDecision', label: 'if simple' },
  { from: 'triageDecision', to: 'planningAgent', label: 'Engage' },
  { from: 'triageDecision', to: 'endClarify', label: 'Clarify' },
  { from: 'triageDecision', to: 'endReject', label: 'Reject' },
  
  // Planning Flow
  { from: 'planningAgent', to: 'planningAnalysis' },
  { from: 'planningAnalysis', to: 'planningDecision' },
  { from: 'planningDecision', to: 'planningHyde', label: 'Research' },
  { from: 'planningHyde', to: 'researchOrchestrator' },
  { from: 'planningDecision', to: 'planningDirectRetrieval', label: 'Direct' },
  { from: 'planningDirectRetrieval', to: 'synthesisAgent' },
  { from: 'planningDecision', to: 'endSimple', label: 'Simple' },
  
  // Research Flow
  { from: 'researchOrchestrator', to: 'researchCache' },
  { from: 'researchCache', to: 'researchVector', label: 'miss' },
  { from: 'researchCache', to: 'researchCollect', label: 'hit' },
  { from: 'researchVector', to: 'researchGraph', label: 'fallback' },
  { from: 'researchGraph', to: 'researchKeyword', label: 'fallback' },
  { from: 'researchKeyword', to: 'researchWeb', label: 'fallback' },
  { from: 'researchWeb', to: 'researchCollect' },
  { from: 'researchVector', to: 'researchCollect', label: 'success' },
  { from: 'researchGraph', to: 'researchCollect', label: 'success' },
  { from: 'researchKeyword', to: 'researchCollect', label: 'success' },
  { from: 'researchCollect', to: 'validationAgent' },

  // Validation Flow
  { from: 'validationAgent', to: 'validationQuality' },
  { from: 'validationQuality', to: 'validationMath' },
  { from: 'validationMath', to: 'validationDecision' },
  { from: 'validationDecision', to: 'calculationExecutor', label: 'Math Needed' },
  { from: 'validationDecision', to: 'placeholderHandler', label: 'Insufficient' },
  { from: 'validationDecision', to: 'synthesisAgent', label: 'Sufficient' },

  // Augmentation to Synthesis
  { from: 'calculationExecutor', to: 'synthesisAgent' },
  { from: 'placeholderHandler', to: 'synthesisAgent' },

  // Finalization Flow
  { from: 'synthesisAgent', to: 'memoryAgent' },
  { from: 'memoryAgent', to: 'endSuccess' },

  // Error Handling Flow
  { from: 'researchOrchestrator', to: 'errorHandler', astyle: 'error' },
  { from: 'synthesisAgent', to: 'errorHandler', astyle: 'error' },
  { from: 'errorHandler', to: 'errorFallback', label: 'processing\nerror' },
  { from: 'errorHandler', to: 'errorRetry', label: 'quota or\nnetwork error' },
  { from: 'errorHandler', to: 'errorDegrade', label: 'max retries\nreached' },
  { from: 'errorFallback', to: 'researchWeb' },
  { from: 'errorDegrade', to: 'synthesisAgent' },
]; 