export const detailedArchitectureNodes = [
  // --- Core Agents ---
  { id: 'triageAgent', label: '🤖\nTriage Agent\n(Gemini Flash)', group: 'agent', description: "Fast query classification using Gemini Flash. Execution time: 1-3 seconds." },
  { id: 'planningAgent', label: '🤖\nPlanning Agent\n(Gemini Pro)', group: 'agent', description: "Strategic planning with HyDE sub-query generation using Gemini Pro. Execution time: 2-5 seconds." },
  { id: 'researchOrchestrator', label: '🔄\nResearch Orchestrator\n🚀 PARALLEL ENGINE', group: 'orchestrator', description: "THE CROWN JEWEL: Manages parallel execution of research sub-queries using asyncio.gather(). Revolutionary 4-6x performance boost." },
  { id: 'validationAgent', label: '🔬\nThinking Validation Agent\n1-10 Quality Scoring', group: 'agent', description: "Quality assessment with 1-10 relevance scoring (6.0+ threshold) and mathematical calculation detection." },
  { id: 'synthesisAgent', label: '📝\nSynthesis Agent\n(Gemini Pro)', group: 'agent', description: "Master integration using Gemini Pro for high-quality synthesis with citation management and confidence scoring." },
  { id: 'memoryAgent', label: '💾\nMemory Agent\nRedis + File Backup', group: 'agent', description: "Dual storage architecture: Redis for real-time access, file system for reliability backup." },

  // --- Entry & Exit ---
  { id: 'userQuery', label: 'User Query\nVirginia Building Code', group: 'input', description: "Starting point for all Virginia building code queries." },
  { id: 'endSuccess', label: 'End\n(Success)\nQuality Validated', group: 'end', description: "Successful completion with quality validation and dual storage persistence." },

  // --- Triage Internals ---
  { id: 'triagePatternScreen', label: 'Pattern\nScreening\n⚡ Fast Check', group: 'sub-process', description: "Lightning-fast pattern matching for simple rejection or direct retrieval patterns." },
  { id: 'triageLlm', label: 'LLM\nClassification\n🧠 Complex Analysis', group: 'sub-process-llm', description: "For complex queries, Gemini Flash determines final classification (Engage, Clarify, Reject)." },
  { id: 'triageDecision', label: 'Route\nDecision', group: 'decision-small', description: "Primary routing decision based on triage analysis." },
  { id: 'endClarify', label: 'End\n(Clarify)', group: 'end', description: "Request for user clarification on ambiguous queries." },
  { id: 'endReject', label: 'End\n(Reject)', group: 'end', description: "Rejection of out-of-scope or inappropriate queries." },

  // --- Planning Internals ---
  { id: 'planningAnalysis', label: 'Query\nComplexity Analysis\n📊 Deep Assessment', group: 'sub-process', description: "Deep analysis of query complexity to determine optimal strategy approach." },
  { id: 'planningDecision', label: 'Strategy\nSelection', group: 'decision-small', description: "Strategic routing based on complexity analysis." },
  { id: 'planningHyde', label: 'HyDE Sub-Query\nGeneration\n📝 Parallel Plan', group: 'sub-process-llm', description: "Generates multi-step research plan with hypothetical document embeddings for enhanced parallel retrieval." },
  { id: 'planningDirectRetrieval', label: 'Direct Entity\nRetrieval\n⚡ Fast Lookup', group: 'sub-process', description: "Directly fetches specific, known entities from the Neo4j knowledge graph." },
  { id: 'endSimple', label: 'End\n(Simple Answer)', group: 'end', description: "Simple answer termination without complex research." },

  // --- Parallel Research System ---
  { id: 'parallelCoordinator', label: 'Parallel Execution\nCoordinator\n🚀 asyncio.gather()', group: 'sub-process', description: "Coordinates parallel execution of multiple sub-queries using asyncio.gather() for 4-6x speedup." },
  { id: 'subQuery1', label: 'Sub-Query 1\n⚡ Async Processing', group: 'sub-process', description: "Independent parallel processing with full fallback chain and error isolation." },
  { id: 'subQuery2', label: 'Sub-Query 2\n⚡ Async Processing', group: 'sub-process', description: "Independent parallel processing with full fallback chain and error isolation." },
  { id: 'subQueryN', label: 'Sub-Query N\n⚡ Async Processing', group: 'sub-process', description: "Independent parallel processing with full fallback chain and error isolation." },

  // --- Enhanced Fallback Chain ---
  { id: 'researchCache', label: 'Redis Cache\nCheck\n💾 60-70% Hit Rate', group: 'sub-process-io', description: "Checks Redis cache for previously computed results. High hit rate provides significant performance boost." },
  { id: 'researchVector', label: 'Vector Search\n🔍 Semantic Similarity', group: 'fallback', description: "Primary retrieval using semantic vector search with embedding similarity matching." },
  { id: 'researchGraph', label: 'Neo4j Graph\nSearch\n🕸️ Mathematical Context', group: 'fallback', description: "Advanced graph traversal with CONTAINS/REFERENCES relationships for mathematical content discovery." },
  { id: 'researchKeyword', label: 'Keyword Search\n🔤 Traditional Matching', group: 'fallback', description: "Traditional keyword-based search as tertiary fallback method." },
  { id: 'researchWeb', label: 'Web Search\n🌐 Tavily API', group: 'fallback-web', description: "Final fallback to external web search using Tavily API when all internal methods fail." },
  { id: 'researchCollect', label: 'Result Collection\n📊 Quality Assessment', group: 'sub-process', description: "Collects and aggregates results from all parallel sub-queries with quality assessment." },

  // --- Mathematical Enhancement System ---
  { id: 'equationDetector', label: 'Equation Pattern\nDetection\n🔍 Regex Matching', group: 'sub-process', description: "Advanced pattern detection for equations (e.g., 'Equation 16-7', 'Eq. 16.7') and section references." },
  { id: 'mathNodeRetrieval', label: 'Math Node\nRetrieval\n📊 69 Math Nodes', group: 'sub-process-io', description: "Retrieves mathematical content from 69 Math nodes with UID patterns like '1605.2-math-1'." },
  { id: 'latexProcessor', label: 'LaTeX Content\nProcessing\n📝 Formula Rendering', group: 'sub-process', description: "Processes LaTeX mathematical content with proper subscripts, superscripts, and equation formatting." },
  { id: 'tableIntegration', label: 'Table & Diagram\nIntegration\n📋 118 Tables, 49 Diagrams', group: 'sub-process', description: "Integrates structured data from 118 tables and 49 diagrams with proper formatting preservation." },

  // --- Validation Internals ---
  { id: 'validationQuality', label: 'Quality\nAssessment\n🎯 1-10 Scoring', group: 'sub-process', description: "Evaluates research quality using 1-10 relevance scale with 6.0+ acceptance threshold." },
  { id: 'validationMath', label: 'Mathematical\nNeed Detection\n🧮 Calculation Analysis', group: 'sub-process-llm', description: "Uses LLM to detect if mathematical calculations are required for complete answer." },
  { id: 'validationDecision', label: 'Validation\nRouting', group: 'decision-small', description: "Critical routing based on quality assessment and mathematical needs analysis." },

  // --- Augmentation ---
  { id: 'calculationExecutor', label: '🧮\nCalculation Executor\nDocker Container', group: 'augment', description: "Performs complex mathematical computations using secure Docker containers for safety and isolation." },
  { id: 'placeholderHandler', label: '📝\nPlaceholder Handler\nGraceful Degradation', group: 'augment', description: "Generates partial answers with gap acknowledgment when research is incomplete." },

  // --- Enhanced Error Handling ---
  { id: 'errorHandler', label: '🚨\nError Classification\n& Recovery Manager', group: 'error', description: "Sophisticated error classification with multiple recovery strategies and 99%+ reliability." },
  { id: 'errorFallback', label: 'Fallback\nStrategy Execution\n🔄 Alternative Paths', group: 'error-sub', description: "Executes alternative retrieval paths when primary methods fail." },
  { id: 'errorRetry', label: 'Exponential\nBackoff Retry\n⏱️ Smart Waiting', group: 'error-sub', description: "Intelligent retry with exponential backoff for transient failures like API quota limits." },
  { id: 'errorDegrade', label: 'Graceful\nDegradation\n⬇️ Best Effort', group: 'error-sub', description: "Proceeds with partial data to provide best-effort response when full recovery isn't possible." },
  
  // --- Performance Monitoring ---
  { id: 'performanceMonitor', label: 'Performance\nMonitoring\n📊 Real-time Metrics', group: 'sub-process', description: "Tracks execution times, cache hit rates, and quality metrics for system optimization." },
  { id: 'qualityMetrics', label: 'Quality Metrics\nTracking\n✅ Success Rates', group: 'sub-process', description: "Monitors quality scores, confidence levels, and user satisfaction metrics." },
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
  
  // Research Flow - Parallel Processing
  { from: 'researchOrchestrator', to: 'parallelCoordinator' },
  { from: 'parallelCoordinator', to: 'subQuery1' },
  { from: 'parallelCoordinator', to: 'subQuery2' },
  { from: 'parallelCoordinator', to: 'subQueryN' },
  
  // Individual Fallback Chains for Each Sub-Query
  { from: 'subQuery1', to: 'researchCache' },
  { from: 'researchCache', to: 'researchVector', label: 'miss' },
  { from: 'researchCache', to: 'equationDetector', label: 'hit' },
  { from: 'researchVector', to: 'researchGraph', label: 'fallback' },
  { from: 'researchVector', to: 'equationDetector', label: 'success' },
  { from: 'researchGraph', to: 'researchKeyword', label: 'fallback' },
  { from: 'researchGraph', to: 'equationDetector', label: 'success' },
  { from: 'researchKeyword', to: 'researchWeb', label: 'fallback' },
  { from: 'researchKeyword', to: 'equationDetector', label: 'success' },
  { from: 'researchWeb', to: 'equationDetector' },
  
  // Mathematical Enhancement Flow
  { from: 'equationDetector', to: 'mathNodeRetrieval' },
  { from: 'mathNodeRetrieval', to: 'latexProcessor' },
  { from: 'latexProcessor', to: 'tableIntegration' },
  { from: 'tableIntegration', to: 'researchCollect' },
  { from: 'researchCollect', to: 'performanceMonitor' },
  { from: 'performanceMonitor', to: 'validationAgent' },

  // Validation Flow with Quality Metrics
  { from: 'validationAgent', to: 'validationQuality' },
  { from: 'validationQuality', to: 'validationMath' },
  { from: 'validationMath', to: 'qualityMetrics' },
  { from: 'qualityMetrics', to: 'validationDecision' },
  { from: 'validationDecision', to: 'calculationExecutor', label: 'Math Required' },
  { from: 'validationDecision', to: 'placeholderHandler', label: 'Insufficient Quality' },
  { from: 'validationDecision', to: 'synthesisAgent', label: 'Quality Approved' },

  // Augmentation to Synthesis
  { from: 'calculationExecutor', to: 'synthesisAgent' },
  { from: 'placeholderHandler', to: 'synthesisAgent' },

  // Finalization Flow
  { from: 'synthesisAgent', to: 'memoryAgent' },
  { from: 'memoryAgent', to: 'endSuccess' },

  // Enhanced Error Handling Flow
  { from: 'parallelCoordinator', to: 'errorHandler', label: 'execution error' },
  { from: 'synthesisAgent', to: 'errorHandler', label: 'synthesis error' },
  { from: 'validationAgent', to: 'errorHandler', label: 'validation error' },
  { from: 'errorHandler', to: 'errorFallback', label: 'processing error' },
  { from: 'errorHandler', to: 'errorRetry', label: 'transient error' },
  { from: 'errorHandler', to: 'errorDegrade', label: 'max retries reached' },
  { from: 'errorFallback', to: 'researchWeb' },
  { from: 'errorRetry', to: 'parallelCoordinator' },
  { from: 'errorDegrade', to: 'synthesisAgent' },
]; 