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
    label: '🤖\nTriage Agent\n(Gemini Flash)',
    group: 'agent',
    description: "The first agent that analyzes the user query using Gemini Flash for rapid classification. It performs an initial assessment to determine the query's nature and routing path. Execution time: 1-3 seconds."
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
    label: '🤖\nPlanning Agent\n(Gemini Pro)',
    group: 'agent',
    description: "If the query is valid, the Planning Agent takes over using Gemini Pro for complex reasoning. It analyzes the query in depth to generate a strategic plan with HyDE sub-query generation. Execution time: 2-5 seconds."
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

  // Level 3: Research - THE CROWN JEWEL
  {
    id: 'researchOrchestrator',
    label: '🔄\nResearch Orchestrator\n🚀 PARALLEL EXECUTION\n4-6x Performance Boost',
    group: 'orchestrator',
    description: "THE CROWN JEWEL: This component manages parallel execution of research sub-queries using asyncio.gather(). Revolutionary performance improvement: 60-90 seconds → 10-15 seconds for 6 sub-queries. Each sub-query runs independently with full fallback chain support."
  },
  {
    id: 'parallelProcessing',
    label: '⚡\nParallel Sub-Query\nProcessing',
    group: 'process',
    description: "Multiple sub-queries execute simultaneously using true async parallel processing. Each sub-query gets its own fallback chain execution with error isolation - failed queries don't affect others."
  },
  {
    id: 'fallbackChain',
    label: 'Intelligent\nFallback Chain\n💾→🔍→🕸️→🔤→🌐',
    group: 'process',
    description: "Sequential fallback strategy: Redis Cache (60-70% hit rate) → Vector Search → Neo4j Graph → Keyword Search → Web Search. Each level provides increasingly comprehensive retrieval methods."
  },
  {
    id: 'mathEnhancement',
    label: '🧮\nMathematical Enhancement\n69 Math Nodes\n118 Tables, 49 Diagrams',
    group: 'augment',
    description: "Sophisticated mathematical content detection and enhancement. Detects equation references (e.g., 'Equation 16-7'), retrieves LaTeX content from 69 Math nodes, and integrates tables/diagrams with proper formatting."
  },
  {
    id: 'validationAgent',
    label: '🔬\nThinking Validation Agent\n1-10 Quality Scoring',
    group: 'agent',
    description: "Assesses the quality and sufficiency of gathered information using a 1-10 relevance scale (6.0+ threshold). Also performs critical mathematical calculation detection to determine if computational augmentation is needed."
  },

  // Level 4: Validation Decision
  {
    id: 'validationDecision',
    label: 'Quality Assessment\n& Math Detection',
    group: 'decision',
    description: "The most critical routing decision. Mathematical calculation needs take absolute priority. Otherwise, the path is determined by research quality assessment and sufficiency analysis."
  },

  // Level 5: Augmentation (Conditional)
  {
    id: 'calculationExecutor',
    label: '🧮\nCalculation Executor\nDocker Container',
    group: 'augment',
    description: "Activated ONLY when mathematical calculations are detected. Performs complex computations using secure Docker containers or mathematical libraries. Results are integrated back into the research context."
  },
  {
    id: 'placeholderHandler',
    label: '📝\nPlaceholder Handler\nGraceful Degradation',
    group: 'augment',
    description: "Activated when research is insufficient. Generates placeholder content and crafts partial answers while acknowledging gaps in available information. Ensures graceful degradation."
  },

  // Level 6: Synthesis & Memory
  {
    id: 'synthesisAgent',
    label: '📝\nSynthesis Agent\n(Gemini Pro)\nMaster Integration',
    group: 'agent',
    description: "The final assembly point using Gemini Pro for high-quality synthesis. Integrates all available information (research, calculations, placeholders) into a coherent answer. Manages citations and calculates confidence scores."
  },
  {
    id: 'memoryAgent',
    label: '💾\nMemory Agent\nRedis + File Backup',
    group: 'agent',
    description: "Persists conversation history and interaction details to Redis for real-time access plus file system backup for reliability. Handles dual-storage architecture and session management."
  },
  {
    id: 'endSuccess',
    label: 'End:\nSuccess\nQuality Validated',
    group: 'end',
    description: "The workflow successfully completes with quality validation, having stored the interaction in dual storage (Redis + file backup) and provided a comprehensive final answer to the user."
  },

  // Error Handling
  {
    id: 'errorHandling',
    label: '🚨\nError Handling\nGraceful Recovery',
    group: 'error',
    description: "Comprehensive error classification and recovery system with multiple strategies: fallback execution, exponential backoff retry, and graceful degradation. Ensures 99%+ system reliability."
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
  { from: 'planningDecision', to: 'researchOrchestrator', label: 'Research Plan' },
  { from: 'planningDecision', to: 'synthesisAgent', label: 'Direct Retrieval' },
  { from: 'planningDecision', to: 'endSimple', label: 'Simple Answer' },

  // Research Flow - Enhanced with Parallel Processing
  { from: 'researchOrchestrator', to: 'parallelProcessing' },
  { from: 'parallelProcessing', to: 'fallbackChain' },
  { from: 'fallbackChain', to: 'mathEnhancement' },
  { from: 'mathEnhancement', to: 'validationAgent' },
  { from: 'validationAgent', to: 'validationDecision' },

  // Validation Flow
  { from: 'validationDecision', to: 'calculationExecutor', label: 'Math Required' },
  { from: 'validationDecision', to: 'placeholderHandler', label: 'Insufficient Data' },
  { from: 'validationDecision', to: 'synthesisAgent', label: 'Quality Approved' },

  // Augmentation to Synthesis
  { from: 'calculationExecutor', to: 'synthesisAgent' },
  { from: 'placeholderHandler', to: 'synthesisAgent' },

  // Finalization Flow
  { from: 'synthesisAgent', to: 'memoryAgent' },
  { from: 'memoryAgent', to: 'endSuccess' },

  // Error Handling Flow
  { from: 'researchOrchestrator', to: 'errorHandling', label: 'Error' },
  { from: 'synthesisAgent', to: 'errorHandling', label: 'Error' },
  { from: 'errorHandling', to: 'fallbackChain', label: 'Recovery' },
  { from: 'errorHandling', to: 'synthesisAgent', label: 'Graceful Degradation' },
];

// Horizontal Architecture Layout - Optimized for Left-to-Right Flow
export const horizontalArchitectureNodes = [
  // Column 1: Input
  { 
    id: 'userQuery', 
    label: 'User Query\n🧑‍💻', 
    group: 'input', 
    x: 0, y: 0, fixed: true,
    description: "The starting point of the entire agentic workflow. User submits a Virginia building code query that triggers the sophisticated AI processing pipeline."
  },
  
  // Column 2: Triage
  { 
    id: 'triageAgent', 
    label: '🤖 Triage Agent\n(Gemini Flash)\n⚡ 1-3s', 
    group: 'agent', 
    x: 250, y: 0, fixed: true,
    description: "Fast query classification using Gemini Flash. Analyzes query complexity and determines optimal routing path. Lightning-fast execution in 1-3 seconds."
  },
  { 
    id: 'triageDecision', 
    label: 'Classification\nDecision', 
    group: 'decision', 
    x: 500, y: 0, fixed: true,
    description: "Critical decision point that routes queries based on complexity: Engage for complex queries, Clarify for ambiguous ones, Reject for out-of-scope."
  },
  
  // Column 2 Endpoints
  { 
    id: 'endClarify', 
    label: 'End:\nClarify', 
    group: 'end', 
    x: 500, y: -150, fixed: true,
    description: "Workflow terminates with clarification request when query is too vague or ambiguous for processing."
  },
  { 
    id: 'endReject', 
    label: 'End:\nReject', 
    group: 'end', 
    x: 500, y: 150, fixed: true,
    description: "Workflow terminates when query is out-of-scope, inappropriate, or outside the AI's knowledge domain."
  },
  
  // Column 3: Planning
  { 
    id: 'planningAgent', 
    label: '🤖 Planning Agent\n(Gemini Pro)\n⚡ 2-5s', 
    group: 'agent', 
    x: 750, y: 0, fixed: true,
    description: "Strategic planning using Gemini Pro for complex reasoning. Generates HyDE sub-queries and determines optimal research strategy. Execution time: 2-5 seconds."
  },
  { 
    id: 'planningDecision', 
    label: 'Strategy\nSelection', 
    group: 'decision', 
    x: 1000, y: 0, fixed: true,
    description: "Strategic routing based on query complexity: Simple for direct answers, Research for complex multi-step processing."
  },
  { 
    id: 'endSimple', 
    label: 'End:\nSimple', 
    group: 'end', 
    x: 1000, y: 150, fixed: true,
    description: "Workflow terminates with simple direct answer when no complex research is required."
  },
  
  // Column 4: Research Orchestrator - THE CROWN JEWEL
  { 
    id: 'researchOrchestrator', 
    label: '🔄 Research Orchestrator\n🚀 PARALLEL EXECUTION\n4-6x Speedup\n⚡ 10-15s', 
    group: 'orchestrator', 
    x: 1250, y: 0, fixed: true,
    description: "THE CROWN JEWEL: Revolutionary parallel execution engine using asyncio.gather(). Achieves 4-6x performance boost: 60-90 seconds → 10-15 seconds for 6 sub-queries."
  },
  { 
    id: 'parallelProcessing', 
    label: '⚡ Parallel\nSub-Queries', 
    group: 'process', 
    x: 1500, y: 0, fixed: true,
    description: "Multiple sub-queries execute simultaneously with true async parallel processing. Each sub-query gets independent fallback chain execution with error isolation."
  },
  
  // Column 5: Processing Chain
  { 
    id: 'fallbackChain', 
    label: 'Fallback Chain\n💾→🔍→🕸️→🔤→🌐', 
    group: 'process', 
    x: 1750, y: 0, fixed: true,
    description: "Intelligent sequential fallback: Redis Cache (60-70% hit rate) → Vector Search → Neo4j Graph → Keyword Search → Web Search. Ensures comprehensive information retrieval."
  },
  { 
    id: 'mathEnhancement', 
    label: '🧮 Math Enhancement\n69 Math Nodes\n118 Tables, 49 Diagrams', 
    group: 'augment', 
    x: 2000, y: 0, fixed: true,
    description: "Sophisticated mathematical content detection and enhancement. Processes equation references, retrieves LaTeX from 69 Math nodes, integrates 118 tables and 49 diagrams."
  },
  
  // Column 6: Validation
  { 
    id: 'validationAgent', 
    label: '🔬 Validation Agent\n1-10 Quality Score\n⚡ Thinking Mode', 
    group: 'agent', 
    x: 2250, y: 0, fixed: true,
    description: "Quality assessment using 1-10 relevance scale (6.0+ threshold). Includes mathematical calculation detection and thinking-enhanced validation process."
  },
  { 
    id: 'validationDecision', 
    label: 'Quality &\nMath Check', 
    group: 'decision', 
    x: 2500, y: 0, fixed: true,
    description: "Critical routing decision. Mathematical calculations take absolute priority, otherwise routes based on quality assessment and sufficiency analysis."
  },
  
  // Column 7: Augmentation
  { 
    id: 'calculationExecutor', 
    label: '🧮 Calculation\nExecutor\nDocker Container', 
    group: 'augment', 
    x: 2750, y: -100, fixed: true,
    description: "Activated only for mathematical calculations. Performs complex computations using secure Docker containers for safety and isolation."
  },
  { 
    id: 'placeholderHandler', 
    label: '📝 Placeholder\nHandler\nGraceful Degradation', 
    group: 'augment', 
    x: 2750, y: 100, fixed: true,
    description: "Activated when research is insufficient. Generates partial answers with gap acknowledgment, ensuring graceful degradation rather than failure."
  },
  
  // Column 8: Synthesis
  { 
    id: 'synthesisAgent', 
    label: '📝 Synthesis Agent\n(Gemini Pro)\nMaster Integration', 
    group: 'agent', 
    x: 3000, y: 0, fixed: true,
    description: "Final assembly using Gemini Pro for high-quality synthesis. Integrates all information sources, manages citations, calculates confidence scores."
  },
  
  // Column 9: Memory & Success
  { 
    id: 'memoryAgent', 
    label: '💾 Memory Agent\nRedis + File Backup', 
    group: 'agent', 
    x: 3250, y: 0, fixed: true,
    description: "Dual storage architecture: Redis for real-time access plus file system backup for reliability. Handles conversation state and session management."
  },
  { 
    id: 'endSuccess', 
    label: 'End: Success\n✅ Quality Validated\n💾 Memory Stored', 
    group: 'end', 
    x: 3500, y: 0, fixed: true,
    description: "Successful workflow completion with quality validation. Interaction stored in dual storage (Redis + file backup) and comprehensive answer provided."
  },
  
  // Error Handling (bottom flow)
  { 
    id: 'errorHandling', 
    label: '🚨 Error Handling\nGraceful Recovery\n99%+ Reliability', 
    group: 'error', 
    x: 2000, y: 200, fixed: true,
    description: "Comprehensive error classification and recovery system. Multiple strategies: fallback execution, exponential backoff retry, graceful degradation. 99%+ reliability."
  },
];

export const horizontalArchitectureEdges = [
  // Main Flow (Left to Right)
  { from: 'userQuery', to: 'triageAgent', label: 'Submit Query' },
  { from: 'triageAgent', to: 'triageDecision', label: 'Analyze' },
  { from: 'triageDecision', to: 'endClarify', label: 'Clarify' },
  { from: 'triageDecision', to: 'endReject', label: 'Reject' },
  { from: 'triageDecision', to: 'planningAgent', label: 'Engage' },
  
  { from: 'planningAgent', to: 'planningDecision', label: 'Plan' },
  { from: 'planningDecision', to: 'endSimple', label: 'Simple' },
  { from: 'planningDecision', to: 'researchOrchestrator', label: 'Research' },
  
  { from: 'researchOrchestrator', to: 'parallelProcessing', label: 'Parallel Exec' },
  { from: 'parallelProcessing', to: 'fallbackChain', label: 'Process' },
  { from: 'fallbackChain', to: 'mathEnhancement', label: 'Enhance' },
  { from: 'mathEnhancement', to: 'validationAgent', label: 'Validate' },
  
  { from: 'validationAgent', to: 'validationDecision', label: 'Assess' },
  { from: 'validationDecision', to: 'calculationExecutor', label: 'Math Required' },
  { from: 'validationDecision', to: 'placeholderHandler', label: 'Insufficient' },
  { from: 'validationDecision', to: 'synthesisAgent', label: 'Approved' },
  
  { from: 'calculationExecutor', to: 'synthesisAgent', label: 'Compute' },
  { from: 'placeholderHandler', to: 'synthesisAgent', label: 'Partial' },
  
  { from: 'synthesisAgent', to: 'memoryAgent', label: 'Synthesize' },
  { from: 'memoryAgent', to: 'endSuccess', label: 'Store' },
  
  // Error Handling Flow
  { from: 'researchOrchestrator', to: 'errorHandling', label: 'Error', dashes: true },
  { from: 'synthesisAgent', to: 'errorHandling', label: 'Error', dashes: true },
  { from: 'errorHandling', to: 'fallbackChain', label: 'Recover', dashes: true },
  { from: 'errorHandling', to: 'synthesisAgent', label: 'Degrade', dashes: true },
]; 

// Executive Professional Design - Optimized for Executive Presentations
export const executiveArchitectureNodes = [
  // Stage 1: Input & Analysis
  {
    id: 'userInput',
    label: '📋\nUser Query\nSubmission',
    group: 'input-executive',
    x: 0, y: 0, fixed: true,
    level: 1,
    stage: 'Input',
    description: "Executive Summary: Initial user query submission that triggers the AI workflow pipeline."
  },
  {
    id: 'intelligentTriage',
    label: '🧠\nIntelligent Triage\nAI Classification',
    group: 'agent-executive',
    x: 300, y: 0, fixed: true,
    level: 1,
    stage: 'Analysis',
    description: "Executive Summary: AI-powered query analysis with 95% accuracy classification in under 3 seconds."
  },

  // Stage 2: Strategic Planning
  {
    id: 'strategicPlanning',
    label: '📋\nStrategic Planning\nResearch Strategy',
    group: 'planning-executive',
    x: 600, y: 0, fixed: true,
    level: 2,
    stage: 'Planning',
    description: "Executive Summary: Advanced AI generates comprehensive research strategy with HyDE methodology."
  },

  // Stage 3: Research Engine - THE CROWN JEWEL
  {
    id: 'researchEngine',
    label: '🚀\nParallel Research Engine\n4-6x Performance Boost\nTHE CROWN JEWEL',
    group: 'crown-jewel',
    x: 900, y: 0, fixed: true,
    level: 3,
    stage: 'Research',
    description: "Executive Summary: Revolutionary parallel processing engine delivering 4-6x performance improvement. Industry-leading 10-15 second response time."
  },

  // Stage 4: Quality Assurance
  {
    id: 'qualityValidation',
    label: '🔬\nQuality Validation\n10-Point Scoring',
    group: 'validation-executive',
    x: 1200, y: 0, fixed: true,
    level: 4,
    stage: 'Validation',
    description: "Executive Summary: Rigorous quality assessment with 10-point scoring system ensuring 6.0+ threshold compliance."
  },

  // Stage 5: Final Assembly
  {
    id: 'masterSynthesis',
    label: '📝\nMaster Synthesis\nFinal Assembly',
    group: 'synthesis-executive',
    x: 1500, y: 0, fixed: true,
    level: 5,
    stage: 'Output',
    description: "Executive Summary: High-quality response synthesis with citations, confidence scoring, and comprehensive final answer."
  },

  // Supporting Infrastructure (Bottom Row)
  {
    id: 'mathematicalEngine',
    label: '🧮\nMathematical Engine\n69 Math Nodes\n118 Tables',
    group: 'infrastructure',
    x: 450, y: 200, fixed: true,
    level: 0,
    stage: 'Infrastructure',
    description: "Supporting Infrastructure: Advanced mathematical content processing with 69 equation nodes and 118 data tables."
  },
  {
    id: 'knowledgeGraph',
    label: '🕸️\nKnowledge Graph\nNeo4j Database',
    group: 'infrastructure',
    x: 750, y: 200, fixed: true,
    level: 0,
    stage: 'Infrastructure',
    description: "Supporting Infrastructure: Comprehensive knowledge graph with 98% hierarchical connectivity and vector embeddings."
  },
  {
    id: 'memorySystem',
    label: '💾\nMemory System\nRedis + Backup',
    group: 'infrastructure',
    x: 1050, y: 200, fixed: true,
    level: 0,
    stage: 'Infrastructure',
    description: "Supporting Infrastructure: Dual-storage architecture with Redis for real-time access and file backup for reliability."
  },

  // Success Metrics (Top Row)
  {
    id: 'performanceMetrics',
    label: '📊\nPerformance\n10-15s Response\n99%+ Reliability',
    group: 'metrics',
    x: 1800, y: 0, fixed: true,
    level: 6,
    stage: 'Metrics',
    description: "Success Metrics: Industry-leading performance with 10-15 second response time and 99%+ system reliability."
  }
];

export const executiveArchitectureEdges = [
  // Main Executive Flow
  { from: 'userInput', to: 'intelligentTriage', label: 'Submit', color: { color: '#3b82f6' } },
  { from: 'intelligentTriage', to: 'strategicPlanning', label: 'Analyze', color: { color: '#3b82f6' } },
  { from: 'strategicPlanning', to: 'researchEngine', label: 'Execute', color: { color: '#f59e0b' } },
  { from: 'researchEngine', to: 'qualityValidation', label: 'Validate', color: { color: '#f59e0b' } },
  { from: 'qualityValidation', to: 'masterSynthesis', label: 'Synthesize', color: { color: '#10b981' } },
  { from: 'masterSynthesis', to: 'performanceMetrics', label: 'Deliver', color: { color: '#10b981' } },

  // Infrastructure Support (Dashed lines)
  { from: 'mathematicalEngine', to: 'researchEngine', dashes: [5,5], color: { color: '#6b7280' } },
  { from: 'knowledgeGraph', to: 'researchEngine', dashes: [5,5], color: { color: '#6b7280' } },
  { from: 'memorySystem', to: 'masterSynthesis', dashes: [5,5], color: { color: '#6b7280' } },
]; 

// Modern Flat Design - Minimalist Professional
export const modernFlatNodes = [
  { 
    id: 'input', 
    label: 'User\nInput', 
    group: 'flat-input', 
    x: 0, y: 0, fixed: true,
    description: "Clean, minimalist input interface for user query submission. Ultra-modern flat design approach."
  },
  { 
    id: 'process', 
    label: 'AI\nProcessing', 
    group: 'flat-process', 
    x: 400, y: 0, fixed: true,
    description: "Streamlined AI processing component with intelligent triage and planning. Simplified for clarity."
  },
  { 
    id: 'research', 
    label: 'Research\nEngine', 
    group: 'flat-research', 
    x: 800, y: 0, fixed: true,
    description: "Powerful research engine with parallel processing capabilities. Core intelligence component."
  },
  { 
    id: 'output', 
    label: 'Final\nOutput', 
    group: 'flat-output', 
    x: 1200, y: 0, fixed: true,
    description: "Clean, professional output delivery with synthesis and quality validation."
  },
];

export const modernFlatEdges = [
  { from: 'input', to: 'process', color: { color: '#3b82f6' }, width: 3 },
  { from: 'process', to: 'research', color: { color: '#3b82f6' }, width: 3 },
  { from: 'research', to: 'output', color: { color: '#3b82f6' }, width: 3 },
];

// Swimlane Process Design - Professional Business Process
export const swimlaneNodes = [
  // Lane 1: User Interface
  { 
    id: 'userQuery', 
    label: 'User Query', 
    group: 'lane-user', 
    x: 0, y: 0, fixed: true,
    description: "User Interface Lane: Initial query submission point for user interactions."
  },
  { 
    id: 'userResult', 
    label: 'Final Result', 
    group: 'lane-user', 
    x: 1400, y: 0, fixed: true,
    description: "User Interface Lane: Final result delivery to the user with complete answer."
  },
  
  // Lane 2: AI Agents
  { 
    id: 'triageAgent', 
    label: 'Triage Agent', 
    group: 'lane-agents', 
    x: 200, y: 150, fixed: true,
    description: "AI Agents Lane: Initial query classification and routing agent."
  },
  { 
    id: 'planningAgent', 
    label: 'Planning Agent', 
    group: 'lane-agents', 
    x: 500, y: 150, fixed: true,
    description: "AI Agents Lane: Strategic research planning and sub-query generation."
  },
  { 
    id: 'researchAgent', 
    label: 'Research Agent', 
    group: 'lane-agents', 
    x: 800, y: 150, fixed: true,
    description: "AI Agents Lane: Parallel research orchestrator with 4-6x performance boost."
  },
  { 
    id: 'synthesisAgent', 
    label: 'Synthesis Agent', 
    group: 'lane-agents', 
    x: 1100, y: 150, fixed: true,
    description: "AI Agents Lane: Final answer synthesis and quality assurance."
  },
  
  // Lane 3: Data Processing
  { 
    id: 'dataRetrieval', 
    label: 'Data Retrieval', 
    group: 'lane-data', 
    x: 350, y: 300, fixed: true,
    description: "Data Processing Lane: Information retrieval from knowledge graph and vector search."
  },
  { 
    id: 'mathProcessing', 
    label: 'Math Processing', 
    group: 'lane-data', 
    x: 650, y: 300, fixed: true,
    description: "Data Processing Lane: Mathematical content enhancement with 69 math nodes."
  },
  { 
    id: 'qualityCheck', 
    label: 'Quality Check', 
    group: 'lane-data', 
    x: 950, y: 300, fixed: true,
    description: "Data Processing Lane: Quality validation with 10-point scoring system."
  },
];

export const swimlaneEdges = [
  { from: 'userQuery', to: 'triageAgent' },
  { from: 'triageAgent', to: 'planningAgent' },
  { from: 'planningAgent', to: 'researchAgent' },
  { from: 'planningAgent', to: 'dataRetrieval' },
  { from: 'researchAgent', to: 'mathProcessing' },
  { from: 'mathProcessing', to: 'qualityCheck' },
  { from: 'researchAgent', to: 'synthesisAgent' },
  { from: 'qualityCheck', to: 'synthesisAgent' },
  { from: 'synthesisAgent', to: 'userResult' },
];

// Technical Architecture Design - Microservice Style
export const technicalArchNodes = [
  // API Gateway
  { 
    id: 'apiGateway', 
    label: 'API Gateway\nQuery Interface', 
    group: 'tech-gateway', 
    x: 0, y: 0, fixed: true,
    description: "Technical Architecture: Main entry point handling HTTP/REST requests with load balancing and authentication."
  },
  
  // Microservices
  { 
    id: 'triageService', 
    label: 'Triage\nMicroservice', 
    group: 'tech-service', 
    x: 300, y: -100, fixed: true,
    description: "Technical Architecture: Containerized microservice for query classification using Gemini Flash LLM."
  },
  { 
    id: 'planningService', 
    label: 'Planning\nMicroservice', 
    group: 'tech-service', 
    x: 300, y: 100, fixed: true,
    description: "Technical Architecture: Strategic planning microservice with HyDE methodology and Gemini Pro integration."
  },
  { 
    id: 'researchService', 
    label: 'Research\nOrchestrator', 
    group: 'tech-orchestrator', 
    x: 600, y: 0, fixed: true,
    description: "Technical Architecture: Core orchestration service managing parallel async execution with 4-6x performance improvement."
  },
  { 
    id: 'synthesisService', 
    label: 'Synthesis\nMicroservice', 
    group: 'tech-service', 
    x: 900, y: 0, fixed: true,
    description: "Technical Architecture: Final assembly microservice handling response synthesis and quality validation."
  },
  
  // Databases
  { 
    id: 'neo4jDB', 
    label: 'Neo4j\nKnowledge Graph', 
    group: 'tech-database', 
    x: 450, y: 200, fixed: true,
    description: "Technical Architecture: Graph database with 69 math nodes, 118 tables, and vector embeddings using Cypher queries."
  },
  { 
    id: 'redisCache', 
    label: 'Redis\nCache Layer', 
    group: 'tech-cache', 
    x: 750, y: 200, fixed: true,
    description: "Technical Architecture: High-performance in-memory cache with 60-70% hit rate for fast retrieval."
  },
  
  // External Services
  { 
    id: 'webSearch', 
    label: 'Web Search\nAPI', 
    group: 'tech-external', 
    x: 600, y: -200, fixed: true,
    description: "Technical Architecture: External Tavily web search API integration for comprehensive information retrieval."
  },
];

export const technicalArchEdges = [
  { from: 'apiGateway', to: 'triageService', label: 'HTTP/REST' },
  { from: 'apiGateway', to: 'planningService', label: 'HTTP/REST' },
  { from: 'triageService', to: 'researchService', label: 'Async' },
  { from: 'planningService', to: 'researchService', label: 'Async' },
  { from: 'researchService', to: 'synthesisService', label: 'gRPC' },
  { from: 'researchService', to: 'neo4jDB', label: 'Cypher', dashes: true },
  { from: 'researchService', to: 'redisCache', label: 'Redis Protocol', dashes: true },
  { from: 'researchService', to: 'webSearch', label: 'HTTPS', dashes: true },
];

// Design Configuration Object
export const designOptions = {
  executive: {
    name: "Executive Dashboard",
    complexity: 7,
    description: "Clean, professional design optimized for executive presentations",
    nodes: "executiveArchitectureNodes",
    edges: "executiveArchitectureEdges",
    pros: ["Executive-friendly", "Clear visual hierarchy", "Performance focused"],
    cons: ["Less technical detail", "May oversimplify complex processes"]
  },
  
  modernFlat: {
    name: "Modern Flat Design",
    complexity: 3,
    description: "Minimalist, ultra-clean design with modern aesthetics",
    nodes: "modernFlatNodes", 
    edges: "modernFlatEdges",
    pros: ["Very clean", "Easy to understand", "Modern look"],
    cons: ["Oversimplified", "May lack detail for technical users"]
  },
  
  swimlane: {
    name: "Swimlane Process",
    complexity: 6,
    description: "Professional business process design with clear role separation",
    nodes: "swimlaneNodes",
    edges: "swimlaneEdges", 
    pros: ["Clear role separation", "Business-friendly", "Professional"],
    cons: ["Requires more space", "May be complex for simple workflows"]
  },
  
  technicalArch: {
    name: "Technical Architecture",
    complexity: 9,
    description: "Detailed microservice architecture with technical precision",
    nodes: "technicalArchNodes",
    edges: "technicalArchEdges",
    pros: ["Highly technical", "Accurate representation", "Developer-friendly"],
    cons: ["Complex for non-technical users", "May overwhelm stakeholders"]
  },
  
  horizontal: {
    name: "Horizontal Timeline",
    complexity: 5,
    description: "Left-to-right workflow with timeline progression",
    nodes: "horizontalArchitectureNodes",
    edges: "horizontalArchitectureEdges",
    pros: ["Natural reading flow", "Timeline clarity", "Comprehensive"],
    cons: ["Requires wide screen", "Medium complexity"]
  },
  
  traditional: {
    name: "Traditional Vertical",
    complexity: 4,
    description: "Classic top-down hierarchical design",
    nodes: "architectureNodes", 
    edges: "architectureEdges",
    pros: ["Familiar structure", "Hierarchical clarity", "Compact"],
    cons: ["Traditional look", "Less modern appeal"]
  },

  "C4 Model Architecture": {
    description: "Complete C4 Model software architecture with all 4 levels (Context, Container, Component, Code)",
    complexity: 10,
    category: "Software Engineering Standard",
    layout: "horizontal",
    pros: ["Complete software engineering standard", "4-level detail hierarchy", "Professional notation", "Industry standard"],
    cons: ["Complex to understand", "Requires technical knowledge"]
  },

  "Agentic AI Flow": {
    description: "Professional agentic AI system flow - Simple: core agents & Redis, Detailed: complete process",
    complexity: 7,
    category: "AI/ML Engineering",
    layout: "horizontal",
    pros: ["Professional design", "Clear agent flow", "Redis integration", "Dual complexity levels"],
    cons: ["Technical domain", "AI/ML knowledge helpful"]
  },

  "professionalFlow": {
    name: "Professional Agentic Flow",
    complexity: 8,
    standard: "AI/ML Engineering Standard",
    description: "A polished, professional diagram inspired by your design, with icons and a clean layout.",
    nodes: "professionalFlowNodes",
    edges: "professionalFlowEdges",
    pros: ["Visually appealing", "Professional icons & colors", "Clear, spacious layout"],
    cons: ["Abstracted details", "Focus on aesthetics"]
  },
}; 

// C4 Model Architecture design with all four levels
export const c4ModelArchitecture = {
  // Level 1: System Context
  context: {
    nodes: [
      // External Entities
      {
        id: 'end_users',
        label: 'End Users\n(Researchers, Engineers)',
        x: 100,
        y: 100,
        size: 60,
        shape: 'box',
        font: { size: 14, color: '#2c3e50', multi: true },
        color: { 
          background: '#3498db', 
          border: '#2980b9',
          highlight: { background: '#5dade2', border: '#2980b9' }
        },
        borderWidth: 3,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 8 }
      },
      {
        id: 'agentic_rag_system',
        label: '🏗️ Virginia Building Code\nAgentic RAG System\n\n🚀 4-6x Parallel Performance\n📊 69 Math, 118 Tables, 49 Diagrams\n🎯 Quality Score 6.0+ Threshold',
        x: 400,
        y: 300,
        size: 100,
        shape: 'box',
        font: { size: 16, color: '#ffffff', multi: true, bold: true },
        color: { 
          background: '#e74c3c', 
          border: '#c0392b',
          highlight: { background: '#ec7063', border: '#c0392b' }
        },
        borderWidth: 4,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.4)', size: 12 }
      },
      {
        id: 'building_code_db',
        label: 'Virginia Building Code\nDatabase\n(External)',
        x: 700,
        y: 100,
        size: 60,
        shape: 'cylinder',
        font: { size: 14, color: '#2c3e50', multi: true },
        color: { 
          background: '#95a5a6', 
          border: '#7f8c8d',
          highlight: { background: '#bdc3c7', border: '#7f8c8d' }
        },
        borderWidth: 3,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 8 }
      },
      {
        id: 'external_apis',
        label: 'External APIs\n& Services',
        x: 700,
        y: 500,
        size: 50,
        shape: 'hexagon',
        font: { size: 14, color: '#2c3e50', multi: true },
        color: { 
          background: '#f39c12', 
          border: '#e67e22',
          highlight: { background: '#f7dc6f', border: '#e67e22' }
        },
        borderWidth: 3,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 8 }
      }
    ],
    edges: [
      {
        id: 'users_to_system',
        from: 'end_users',
        to: 'agentic_rag_system',
        label: 'Query Building Codes\n[HTTPS/REST]',
        color: { color: '#3498db' },
        width: 3,
        arrows: { to: { enabled: true, scaleFactor: 1.2 } },
        font: { size: 12, color: '#2c3e50', background: '#ffffff' }
      },
      {
        id: 'system_to_db',
        from: 'agentic_rag_system',
        to: 'building_code_db',
        label: 'Retrieve Code Data\n[API Calls]',
        color: { color: '#e74c3c' },
        width: 3,
        arrows: { to: { enabled: true, scaleFactor: 1.2 } },
        font: { size: 12, color: '#2c3e50', background: '#ffffff' }
      },
      {
        id: 'system_to_apis',
        from: 'agentic_rag_system',
        to: 'external_apis',
        label: 'External Integrations\n[REST/GraphQL]',
        color: { color: '#f39c12' },
        width: 3,
        arrows: { to: { enabled: true, scaleFactor: 1.2 } },
        font: { size: 12, color: '#2c3e50', background: '#ffffff' }
      }
    ]
  },

  // Level 2: Container Diagram
  container: {
    nodes: [
      // Frontend Container
      {
        id: 'frontend_app',
        label: '⚛️ Frontend Application\n\nReact + Vite\n• Interactive UI\n• Real-time Updates\n• Architecture Visualization',
        x: 200,
        y: 100,
        size: 80,
        shape: 'box',
        font: { size: 14, color: '#ffffff', multi: true, bold: true },
        color: { 
          background: '#61dafb', 
          border: '#21a6c4',
          highlight: { background: '#87e8ff', border: '#21a6c4' }
        },
        borderWidth: 4,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 10 }
      },
      
      // LangGraph Orchestrator Container  
      {
        id: 'langgraph_orchestrator',
        label: '🦜 LangGraph Agent Orchestrator\n\n🚀 THE CROWN JEWEL\nParallel Execution Engine\n• Triage → Planning → Research\n• 4-6x Performance Boost\n• Mathematical Enhancement\n• Quality Validation',
        x: 500,
        y: 300,
        size: 120,
        shape: 'box',
        font: { size: 16, color: '#ffffff', multi: true, bold: true },
        color: { 
          background: '#8e44ad', 
          border: '#6c3483',
          highlight: { background: '#bb8fce', border: '#6c3483' }
        },
        borderWidth: 5,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.4)', size: 15 }
      },

      // Neo4j Knowledge Graph
      {
        id: 'neo4j_db',
        label: '🗄️ Neo4j Knowledge Graph\n\n📊 69 Math Nodes\n📋 118 Table Nodes\n📈 49 Diagram Nodes\n🔗 Complex Relationships',
        x: 800,
        y: 200,
        size: 90,
        shape: 'cylinder',
        font: { size: 14, color: '#ffffff', multi: true, bold: true },
        color: { 
          background: '#4CAF50', 
          border: '#388E3C',
          highlight: { background: '#81C784', border: '#388E3C' }
        },
        borderWidth: 4,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 10 }
      },

      // Redis Cache
      {
        id: 'redis_cache',
        label: '🔴 Redis Cache\n\nMemory & Session Store\n• Agent State\n• Fast Retrieval\n• Performance Optimization',
        x: 200,
        y: 500,
        size: 70,
        shape: 'cylinder',
        font: { size: 14, color: '#ffffff', multi: true, bold: true },
        color: { 
          background: '#dc382d', 
          border: '#a51a0e',
          highlight: { background: '#e57373', border: '#a51a0e' }
        },
        borderWidth: 4,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 10 }
      },

      // File Backup System
      {
        id: 'file_backup',
        label: '📁 File Backup System\n\nDual Storage Architecture\n• Persistent Storage\n• Data Recovery\n• Backup & Restore',
        x: 800,
        y: 500,
        size: 70,
        shape: 'cylinder',
        font: { size: 14, color: '#2c3e50', multi: true, bold: true },
        color: { 
          background: '#95a5a6', 
          border: '#7f8c8d',
          highlight: { background: '#bdc3c7', border: '#7f8c8d' }
        },
        borderWidth: 4,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 10 }
      },

      // Gemini AI Services
      {
        id: 'gemini_ai',
        label: '✨ Google Gemini AI\n\n🧠 Gemini Pro & Flash\n• Advanced Reasoning\n• Multi-modal Processing\n• High Performance LLM',
        x: 500,
        y: 600,
        size: 90,
        shape: 'hexagon',
        font: { size: 14, color: '#ffffff', multi: true, bold: true },
        color: { 
          background: '#4285f4', 
          border: '#1a73e8',
          highlight: { background: '#7baaf7', border: '#1a73e8' }
        },
        borderWidth: 4,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 10 }
      }
    ],
    edges: [
      {
        id: 'frontend_to_orchestrator',
        from: 'frontend_app',
        to: 'langgraph_orchestrator',
        label: 'User Queries\n[REST API/WebSocket]',
        color: { color: '#61dafb' },
        width: 4,
        arrows: { to: { enabled: true, scaleFactor: 1.2 } },
        font: { size: 12, color: '#2c3e50', background: '#ffffff' }
      },
      {
        id: 'orchestrator_to_neo4j',
        from: 'langgraph_orchestrator',
        to: 'neo4j_db',
        label: 'Graph Queries\n[Cypher/Bolt]',
        color: { color: '#8e44ad' },
        width: 4,
        arrows: { to: { enabled: true, scaleFactor: 1.2 } },
        font: { size: 12, color: '#2c3e50', background: '#ffffff' }
      },
      {
        id: 'orchestrator_to_redis',
        from: 'langgraph_orchestrator',
        to: 'redis_cache',
        label: 'Memory Storage\n[Redis Protocol]',
        color: { color: '#dc382d' },
        width: 4,
        arrows: { to: { enabled: true, scaleFactor: 1.2 } },
        font: { size: 12, color: '#2c3e50', background: '#ffffff' }
      },
      {
        id: 'orchestrator_to_gemini',
        from: 'langgraph_orchestrator',
        to: 'gemini_ai',
        label: 'LLM Requests\n[API Calls]',
        color: { color: '#4285f4' },
        width: 4,
        arrows: { to: { enabled: true, scaleFactor: 1.2 } },
        font: { size: 12, color: '#2c3e50', background: '#ffffff' }
      },
      {
        id: 'orchestrator_to_backup',
        from: 'langgraph_orchestrator',
        to: 'file_backup',
        label: 'Data Persistence\n[File I/O]',
        color: { color: '#95a5a6' },
        width: 3,
        arrows: { to: { enabled: true, scaleFactor: 1.2 } },
        font: { size: 12, color: '#2c3e50', background: '#ffffff' }
      }
    ]
  },

  // Level 3: Component Diagram (LangGraph Orchestrator Internal Structure)
  component: {
    nodes: [
      // Triage Agent
      {
        id: 'triage_agent',
        label: '🎯 Triage Agent\n\nQuery Classification\n• Intent Analysis\n• Complexity Assessment\n• Route Planning\n⏱️ 1-3 seconds',
        x: 150,
        y: 100,
        size: 70,
        shape: 'ellipse',
        font: { size: 12, color: '#ffffff', multi: true, bold: true },
        color: { 
          background: '#e67e22', 
          border: '#d35400',
          highlight: { background: '#f39c12', border: '#d35400' }
        },
        borderWidth: 3,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 8 }
      },

      // Planning Agent  
      {
        id: 'planning_agent',
        label: '📋 Planning Agent\n\nExecution Strategy\n• Task Decomposition\n• Resource Allocation\n• Workflow Design\n⏱️ 2-5 seconds',
        x: 400,
        y: 100,
        size: 70,
        shape: 'ellipse',
        font: { size: 12, color: '#ffffff', multi: true, bold: true },
        color: { 
          background: '#3498db', 
          border: '#2980b9',
          highlight: { background: '#5dade2', border: '#2980b9' }
        },
        borderWidth: 3,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 8 }
      },

      // Research Orchestrator (THE CROWN JEWEL)
      {
        id: 'research_orchestrator',
        label: '🚀 Research Orchestrator\n\n⭐ THE CROWN JEWEL ⭐\nParallel Execution Engine\n• Sub-query Generation\n• Parallel Processing\n• Result Coordination\n• 4-6x Performance Boost\n⏱️ 10-15 seconds',
        x: 650,
        y: 200,
        size: 110,
        shape: 'star',
        font: { size: 14, color: '#ffffff', multi: true, bold: true },
        color: { 
          background: '#8e44ad', 
          border: '#6c3483',
          highlight: { background: '#bb8fce', border: '#6c3483' }
        },
        borderWidth: 5,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.4)', size: 15 }
      },

      // Parallel Coordinator
      {
        id: 'parallel_coordinator',
        label: '⚡ Parallel Coordinator\n\nasyncio.gather()\n• Concurrent Execution\n• Load Balancing\n• Result Synchronization',
        x: 900,
        y: 100,
        size: 80,
        shape: 'diamond',
        font: { size: 12, color: '#ffffff', multi: true, bold: true },
        color: { 
          background: '#f39c12', 
          border: '#e67e22',
          highlight: { background: '#f7dc6f', border: '#e67e22' }
        },
        borderWidth: 4,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 10 }
      },

      // Mathematical Enhancement Pipeline
      {
        id: 'math_enhancement',
        label: '🔢 Mathematical Enhancement\n\nEquation Processing\n• Pattern Detection\n• LaTeX Rendering\n• Math Node Retrieval\n📊 69 Math Nodes',
        x: 150,
        y: 350,
        size: 80,
        shape: 'box',
        font: { size: 12, color: '#ffffff', multi: true, bold: true },
        color: { 
          background: '#e74c3c', 
          border: '#c0392b',
          highlight: { background: '#ec7063', border: '#c0392b' }
        },
        borderWidth: 4,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 10 }
      },

      // Validation Agent
      {
        id: 'validation_agent',
        label: '✅ Validation Agent\n\nQuality Control\n• Relevance Scoring\n• Accuracy Check\n• 6.0+ Threshold\n• Error Detection',
        x: 400,
        y: 350,
        size: 75,
        shape: 'ellipse',
        font: { size: 12, color: '#ffffff', multi: true, bold: true },
        color: { 
          background: '#27ae60', 
          border: '#229954',
          highlight: { background: '#58d68d', border: '#229954' }
        },
        borderWidth: 3,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 8 }
      },

      // Synthesis Agent
      {
        id: 'synthesis_agent',
        label: '🔄 Synthesis Agent\n\nResult Integration\n• Content Merging\n• Coherence Check\n• Final Assembly\n• Response Generation',
        x: 650,
        y: 400,
        size: 75,
        shape: 'ellipse',
        font: { size: 12, color: '#ffffff', multi: true, bold: true },
        color: { 
          background: '#9b59b6', 
          border: '#8e44ad',
          highlight: { background: '#d2b4de', border: '#8e44ad' }
        },
        borderWidth: 3,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 8 }
      },

      // Memory Agent
      {
        id: 'memory_agent',
        label: '🧠 Memory Agent\n\nContext Management\n• Session Storage\n• History Tracking\n• State Persistence\n• Redis Integration',
        x: 900,
        y: 350,
        size: 75,
        shape: 'ellipse',
        font: { size: 12, color: '#ffffff', multi: true, bold: true },
        color: { 
          background: '#dc382d', 
          border: '#a51a0e',
          highlight: { background: '#e57373', border: '#a51a0e' }
        },
        borderWidth: 3,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 8 }
      },

      // Quality Scoring System
      {
        id: 'quality_scoring',
        label: '📊 Quality Scoring System\n\nRelevance Metrics\n• 1-10 Scale Scoring\n• Threshold: 6.0+\n• Performance Monitoring\n• Quality Assurance',
        x: 400,
        y: 550,
        size: 80,
        shape: 'triangle',
        font: { size: 12, color: '#ffffff', multi: true, bold: true },
        color: { 
          background: '#34495e', 
          border: '#2c3e50',
          highlight: { background: '#5d6d7e', border: '#2c3e50' }
        },
        borderWidth: 4,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 10 }
      }
    ],
    edges: [
      {
        id: 'triage_to_planning',
        from: 'triage_agent',
        to: 'planning_agent',
        label: 'Classified Query',
        color: { color: '#e67e22' },
        width: 3,
        arrows: { to: { enabled: true, scaleFactor: 1.2 } },
        font: { size: 10, color: '#2c3e50', background: '#ffffff' }
      },
      {
        id: 'planning_to_research',
        from: 'planning_agent',
        to: 'research_orchestrator',
        label: 'Execution Plan',
        color: { color: '#3498db' },
        width: 4,
        arrows: { to: { enabled: true, scaleFactor: 1.2 } },
        font: { size: 10, color: '#2c3e50', background: '#ffffff' }
      },
      {
        id: 'research_to_parallel',
        from: 'research_orchestrator',
        to: 'parallel_coordinator',
        label: 'Parallel Tasks',
        color: { color: '#8e44ad' },
        width: 4,
        arrows: { to: { enabled: true, scaleFactor: 1.2 } },
        font: { size: 10, color: '#2c3e50', background: '#ffffff' }
      },
      {
        id: 'research_to_math',
        from: 'research_orchestrator',
        to: 'math_enhancement',
        label: 'Math Processing',
        color: { color: '#e74c3c' },
        width: 3,
        arrows: { to: { enabled: true, scaleFactor: 1.2 } },
        font: { size: 10, color: '#2c3e50', background: '#ffffff' }
      },
      {
        id: 'parallel_to_validation',
        from: 'parallel_coordinator',
        to: 'validation_agent',
        label: 'Results',
        color: { color: '#f39c12' },
        width: 3,
        arrows: { to: { enabled: true, scaleFactor: 1.2 } },
        font: { size: 10, color: '#2c3e50', background: '#ffffff' }
      },
      {
        id: 'validation_to_synthesis',
        from: 'validation_agent',
        to: 'synthesis_agent',
        label: 'Validated Data',
        color: { color: '#27ae60' },
        width: 3,
        arrows: { to: { enabled: true, scaleFactor: 1.2 } },
        font: { size: 10, color: '#2c3e50', background: '#ffffff' }
      },
      {
        id: 'synthesis_to_memory',
        from: 'synthesis_agent',
        to: 'memory_agent',
        label: 'State Update',
        color: { color: '#9b59b6' },
        width: 3,
        arrows: { to: { enabled: true, scaleFactor: 1.2 } },
        font: { size: 10, color: '#2c3e50', background: '#ffffff' }
      },
      {
        id: 'validation_to_quality',
        from: 'validation_agent',
        to: 'quality_scoring',
        label: 'Quality Metrics',
        color: { color: '#27ae60' },
        width: 3,
        arrows: { to: { enabled: true, scaleFactor: 1.2 } },
        font: { size: 10, color: '#2c3e50', background: '#ffffff' }
      }
    ]
  },

  // Level 4: Code Diagram (Implementation Details)
  code: {
    nodes: [
      // Core Classes
      {
        id: 'langgraph_core',
        label: '📦 LangGraph Core\n\nStateGraph Class\n+ state: Dict\n+ nodes: List[Node]\n+ edges: List[Edge]\n+ execute()\n+ parallel_invoke()',
        x: 200,
        y: 100,
        size: 80,
        shape: 'box',
        font: { size: 11, color: '#2c3e50', multi: true, family: 'monospace' },
        color: { 
          background: '#ecf0f1', 
          border: '#34495e',
          highlight: { background: '#d5dbdb', border: '#34495e' }
        },
        borderWidth: 2,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.2)', size: 5 }
      },
      
      {
        id: 'agent_base',
        label: '🤖 BaseAgent\n\nextends BaseAgent\n+ process(query: str)\n+ validate(result: Dict)\n+ update_state(state: Dict)\n- llm_client: GeminiClient',
        x: 500,
        y: 100,
        size: 80,
        shape: 'box',
        font: { size: 11, color: '#2c3e50', multi: true, family: 'monospace' },
        color: { 
          background: '#fff3cd', 
          border: '#856404',
          highlight: { background: '#fefefe', border: '#856404' }
        },
        borderWidth: 2,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.2)', size: 5 }
      },

      {
        id: 'gemini_client',
        label: '🧠 GeminiClient\n\n+ model: str\n+ api_key: str\n+ generate(prompt: str)\n+ async_invoke()\n+ batch_process()',
        x: 800,
        y: 100,
        size: 75,
        shape: 'box',
        font: { size: 11, color: '#2c3e50', multi: true, family: 'monospace' },
        color: { 
          background: '#d4edda', 
          border: '#155724',
          highlight: { background: '#f1fdf4', border: '#155724' }
        },
        borderWidth: 2,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.2)', size: 5 }
      },

      // Specific Agent Implementations
      {
        id: 'triage_impl',
        label: '🎯 TriageAgent\n\nextends BaseAgent\n+ classify_intent()\n+ assess_complexity()\n+ route_query()',
        x: 200,
        y: 300,
        size: 70,
        shape: 'box',
        font: { size: 11, color: '#2c3e50', multi: true, family: 'monospace' },
        color: { 
          background: '#fdeaa7', 
          border: '#fdcb6e',
          highlight: { background: '#fef9e6', border: '#fdcb6e' }
        },
        borderWidth: 2,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.2)', size: 5 }
      },

      {
        id: 'research_impl',
        label: '🚀 ResearchOrchestrator\n\nextends BaseAgent\n+ generate_subqueries()\n+ async parallel_search()\n+ coordinate_results()\n+ asyncio.gather()',
        x: 500,
        y: 300,
        size: 90,
        shape: 'box',
        font: { size: 11, color: '#2c3e50', multi: true, family: 'monospace' },
        color: { 
          background: '#e17055', 
          border: '#d63031',
          highlight: { background: '#fab1a0', border: '#d63031' }
        },
        borderWidth: 3,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 8 }
      },

      {
        id: 'neo4j_service',
        label: '🗄️ Neo4jService\n\n+ driver: Driver\n+ query(cypher: str)\n+ create_nodes()\n+ find_relationships()\n+ math_node_search()',
        x: 800,
        y: 300,
        size: 75,
        shape: 'cylinder',
        font: { size: 11, color: '#2c3e50', multi: true, family: 'monospace' },
        color: { 
          background: '#81ecec', 
          border: '#00b894',
          highlight: { background: '#b2fcfc', border: '#00b894' }
        },
        borderWidth: 2,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.2)', size: 5 }
      },

      // Utility Classes
      {
        id: 'quality_scorer',
        label: '📊 QualityScorer\n\n+ score_relevance()\n+ threshold: float = 6.0\n+ validate_quality()\n+ generate_metrics()',
        x: 200,
        y: 500,
        size: 75,
        shape: 'box',
        font: { size: 11, color: '#2c3e50', multi: true, family: 'monospace' },
        color: { 
          background: '#fd79a8', 
          border: '#e84393',
          highlight: { background: '#ff97b7', border: '#e84393' }
        },
        borderWidth: 2,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.2)', size: 5 }
      },

      {
        id: 'math_processor',
        label: '🔢 MathProcessor\n\n+ detect_equations()\n+ latex_render()\n+ extract_patterns()\n+ enhance_content()',
        x: 500,
        y: 500,
        size: 75,
        shape: 'box',
        font: { size: 11, color: '#2c3e50', multi: true, family: 'monospace' },
        color: { 
          background: '#a29bfe', 
          border: '#6c5ce7',
          highlight: { background: '#ccc5ff', border: '#6c5ce7' }
        },
        borderWidth: 2,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.2)', size: 5 }
      }
    ],
    edges: [
      {
        id: 'core_to_base',
        from: 'langgraph_core',
        to: 'agent_base',
        label: 'uses',
        color: { color: '#2c3e50' },
        width: 2,
        arrows: { to: { enabled: true, scaleFactor: 1.0 } },
        font: { size: 9, color: '#2c3e50' }
      },
      {
        id: 'base_to_gemini',
        from: 'agent_base',
        to: 'gemini_client',
        label: 'depends on',
        color: { color: '#27ae60' },
        width: 2,
        arrows: { to: { enabled: true, scaleFactor: 1.0 } },
        font: { size: 9, color: '#2c3e50' }
      },
      {
        id: 'triage_extends',
        from: 'triage_impl',
        to: 'agent_base',
        label: 'extends',
        color: { color: '#3498db' },
        width: 2,
        arrows: { to: { enabled: true, scaleFactor: 1.0 } },
        font: { size: 9, color: '#2c3e50' },
        dashes: [5, 5]
      },
      {
        id: 'research_extends',
        from: 'research_impl',
        to: 'agent_base',
        label: 'extends',
        color: { color: '#e74c3c' },
        width: 3,
        arrows: { to: { enabled: true, scaleFactor: 1.0 } },
        font: { size: 9, color: '#2c3e50' },
        dashes: [5, 5]
      },
      {
        id: 'research_to_neo4j',
        from: 'research_impl',
        to: 'neo4j_service',
        label: 'queries',
        color: { color: '#00b894' },
        width: 2,
        arrows: { to: { enabled: true, scaleFactor: 1.0 } },
        font: { size: 9, color: '#2c3e50' }
      },
      {
        id: 'quality_to_base',
        from: 'quality_scorer',
        to: 'agent_base',
        label: 'validates',
        color: { color: '#e84393' },
        width: 2,
        arrows: { to: { enabled: true, scaleFactor: 1.0 } },
        font: { size: 9, color: '#2c3e50' }
      },
      {
        id: 'math_to_research',
        from: 'math_processor',
        to: 'research_impl',
        label: 'enhances',
        color: { color: '#6c5ce7' },
        width: 2,
        arrows: { to: { enabled: true, scaleFactor: 1.0 } },
        font: { size: 9, color: '#2c3e50' }
      }
    ]
  }
}

// C4 Model System Architecture - Professional Engineering Standard
export const c4ModelNodes = [
  // Context Level - External Systems and Users
  {
    id: 'user',
    label: 'Building Code\nSpecialist\n[Person]',
    group: 'c4-person',
    x: 0, y: 0, fixed: true,
    description: "External Actor: Building code specialist submitting technical queries requiring expert-level analysis."
  },
  {
    id: 'system',
    label: 'Agentic RAG System\n[Software System]\nVirginia Building Code AI Assistant',
    group: 'c4-system',
    x: 500, y: 0, fixed: true,
    description: "Core System: Advanced multi-agent RAG system providing expert-level building code analysis with mathematical processing capabilities."
  },
  {
    id: 'knowledge-source',
    label: 'Virginia Building Code\nDocumentation\n[External System]',
    group: 'c4-external',
    x: 1000, y: 0, fixed: true,
    description: "External Data Source: Official Virginia building code documentation with mathematical equations, tables, and regulatory content."
  },

  // Container Level - Major Technical Building Blocks
  {
    id: 'api-gateway',
    label: 'API Gateway\n[Container: Node.js]\nRequest routing & authentication',
    group: 'c4-container',
    x: 200, y: 200, fixed: true,
    description: "Container: High-performance API gateway handling request routing, load balancing, and authentication using Node.js runtime."
  },
  {
    id: 'orchestrator',
    label: 'Research Orchestrator\n[Container: Python]\nParallel execution engine',
    group: 'c4-orchestrator',
    x: 500, y: 200, fixed: true,
    description: "Container: Core orchestration service implementing asyncio parallel execution with 4-6x performance optimization using Python/LangGraph."
  },
  {
    id: 'knowledge-graph',
    label: 'Knowledge Graph\n[Container: Neo4j]\n69 Math nodes, 118 Tables',
    group: 'c4-database',
    x: 800, y: 200, fixed: true,
    description: "Container: Graph database storing structured building code content with mathematical equations, tables, and hierarchical relationships."
  },

  // Component Level - Internal Components
  {
    id: 'triage-service',
    label: 'Triage Agent\n[Component]\nGemini Flash classification',
    group: 'c4-component',
    x: 100, y: 350, fixed: true,
    description: "Component: Fast query classification service using Gemini Flash for sub-3-second response time with 95% accuracy."
  },
  {
    id: 'planning-service',
    label: 'Planning Agent\n[Component]\nHyDE methodology',
    group: 'c4-component',
    x: 300, y: 350, fixed: true,
    description: "Component: Strategic planning service generating hypothetical documents and sub-queries using advanced HyDE methodology."
  },
  {
    id: 'math-processor',
    label: 'Mathematical Processor\n[Component]\nEquation detection & LaTeX',
    group: 'c4-component',
    x: 500, y: 350, fixed: true,
    description: "Component: Specialized mathematical content processor detecting equations, rendering LaTeX, and integrating tabular data."
  },
  {
    id: 'validation-engine',
    label: 'Validation Engine\n[Component]\n10-point quality scoring',
    group: 'c4-component',
    x: 700, y: 350, fixed: true,
    description: "Component: Quality assurance engine implementing 10-point relevance scoring with 6.0+ threshold validation."
  },
  {
    id: 'synthesis-engine',
    label: 'Synthesis Engine\n[Component]\nGemini Pro integration',
    group: 'c4-component',
    x: 900, y: 350, fixed: true,
    description: "Component: Final assembly engine using Gemini Pro for high-quality response synthesis with citation management."
  }
];

export const c4ModelEdges = [
  // Context Level Relationships
  { from: 'user', to: 'system', label: 'Submits technical queries\n[HTTPS]' },
  { from: 'system', to: 'knowledge-source', label: 'Retrieves code documentation\n[API/File System]' },
  
  // Container Level Communication
  { from: 'system', to: 'api-gateway', label: 'Routes requests' },
  { from: 'api-gateway', to: 'orchestrator', label: 'gRPC/HTTP' },
  { from: 'orchestrator', to: 'knowledge-graph', label: 'Cypher queries' },
  
  // Component Level Interactions
  { from: 'api-gateway', to: 'triage-service', label: 'Async message' },
  { from: 'triage-service', to: 'planning-service', label: 'Classification result' },
  { from: 'planning-service', to: 'orchestrator', label: 'Research plan' },
  { from: 'orchestrator', to: 'math-processor', label: 'Parallel execution' },
  { from: 'math-processor', to: 'validation-engine', label: 'Enhanced content' },
  { from: 'validation-engine', to: 'synthesis-engine', label: 'Validated data' },
  { from: 'synthesis-engine', to: 'user', label: 'Final response', dashes: true }
];

// Data Flow Diagram (DFD) - Classic Structured Analysis
export const dfdNodes = [
  // External Entities (Squares)
  {
    id: 'user-entity',
    label: 'Building Code\nSpecialist',
    group: 'dfd-entity',
    x: 0, y: 200, fixed: true,
    description: "External Entity: Building code specialist requiring technical analysis and regulatory compliance information."
  },
  {
    id: 'code-repository',
    label: 'Virginia Code\nRepository',
    group: 'dfd-entity',
    x: 1200, y: 200, fixed: true,
    description: "External Entity: Official repository containing Virginia building code documents, equations, and regulatory tables."
  },

  // Processes (Circles)
  {
    id: 'process-1',
    label: '1.0\nQuery\nClassification',
    group: 'dfd-process',
    x: 200, y: 200, fixed: true,
    description: "Process 1.0: Intelligent query classification using AI to determine complexity and routing requirements."
  },
  {
    id: 'process-2',
    label: '2.0\nResearch\nOrchestration',
    group: 'dfd-process',
    x: 400, y: 200, fixed: true,
    description: "Process 2.0: Parallel research orchestration managing multiple information retrieval streams with performance optimization."
  },
  {
    id: 'process-3',
    label: '3.0\nMathematical\nProcessing',
    group: 'dfd-process',
    x: 600, y: 200, fixed: true,
    description: "Process 3.0: Specialized mathematical content processing including equation detection and LaTeX rendering."
  },
  {
    id: 'process-4',
    label: '4.0\nQuality\nValidation',
    group: 'dfd-process',
    x: 800, y: 200, fixed: true,
    description: "Process 4.0: Comprehensive quality validation using 10-point scoring system with threshold compliance checking."
  },
  {
    id: 'process-5',
    label: '5.0\nResponse\nSynthesis',
    group: 'dfd-process',
    x: 1000, y: 200, fixed: true,
    description: "Process 5.0: Final response synthesis integrating all processed information with citation management."
  },

  // Data Stores (Open rectangles)
  {
    id: 'cache-store',
    label: 'D1 | Redis Cache\n60-70% hit rate',
    group: 'dfd-datastore',
    x: 400, y: 50, fixed: true,
    description: "Data Store D1: High-performance Redis cache providing 60-70% hit rate for frequently accessed content."
  },
  {
    id: 'graph-store',
    label: 'D2 | Knowledge Graph\n69 Math nodes, 118 Tables',
    group: 'dfd-datastore',
    x: 600, y: 50, fixed: true,
    description: "Data Store D2: Neo4j knowledge graph containing 69 mathematical nodes and 118 structured tables with hierarchical relationships."
  },
  {
    id: 'memory-store',
    label: 'D3 | Conversation Memory\nDual storage architecture',
    group: 'dfd-datastore',
    x: 800, y: 50, fixed: true,
    description: "Data Store D3: Dual storage architecture using Redis for real-time access and file backup for persistence."
  }
];

export const dfdEdges = [
  // Data flows from external entities
  { from: 'user-entity', to: 'process-1', label: 'Query submission' },
  { from: 'process-5', to: 'user-entity', label: 'Technical response' },
  { from: 'process-2', to: 'code-repository', label: 'Content request' },
  { from: 'code-repository', to: 'process-2', label: 'Code documentation' },

  // Process to process flows
  { from: 'process-1', to: 'process-2', label: 'Classification result' },
  { from: 'process-2', to: 'process-3', label: 'Raw content' },
  { from: 'process-3', to: 'process-4', label: 'Enhanced content' },
  { from: 'process-4', to: 'process-5', label: 'Validated data' },

  // Data store interactions
  { from: 'process-2', to: 'cache-store', label: 'Cache lookup' },
  { from: 'cache-store', to: 'process-2', label: 'Cached results' },
  { from: 'process-2', to: 'graph-store', label: 'Graph query' },
  { from: 'graph-store', to: 'process-3', label: 'Mathematical content' },
  { from: 'process-5', to: 'memory-store', label: 'Store conversation' },
  { from: 'memory-store', to: 'process-1', label: 'Context retrieval' }
];

// Event-Driven Architecture - Modern Microservices Pattern
export const eventDrivenNodes = [
  // Event Producers
  {
    id: 'api-gateway-event',
    label: 'API Gateway\n[Event Producer]\nHTTP → Events',
    group: 'eda-producer',
    x: 0, y: 200, fixed: true,
    description: "Event Producer: API Gateway converting HTTP requests into domain events for downstream processing."
  },

  // Event Bus/Message Broker
  {
    id: 'event-bus',
    label: 'Event Bus\n[Message Broker]\nAsync Communication',
    group: 'eda-bus',
    x: 300, y: 200, fixed: true,
    description: "Event Bus: Central message broker enabling asynchronous communication between microservices with guaranteed delivery."
  },

  // Event Consumers/Services
  {
    id: 'triage-consumer',
    label: 'Triage Service\n[Event Consumer]\nQuery classification events',
    group: 'eda-consumer',
    x: 150, y: 350, fixed: true,
    description: "Event Consumer: Triage service consuming query events and publishing classification results for downstream processing."
  },
  {
    id: 'research-consumer',
    label: 'Research Service\n[Event Consumer]\nParallel execution events',
    group: 'eda-consumer',
    x: 450, y: 350, fixed: true,
    description: "Event Consumer: Research orchestrator consuming research events and managing parallel sub-query execution."
  },
  {
    id: 'math-consumer',
    label: 'Math Service\n[Event Consumer]\nMathematical processing events',
    group: 'eda-consumer',
    x: 150, y: 50, fixed: true,
    description: "Event Consumer: Mathematical processing service handling equation detection and LaTeX rendering events."
  },
  {
    id: 'synthesis-consumer',
    label: 'Synthesis Service\n[Event Consumer]\nResponse assembly events',
    group: 'eda-consumer',
    x: 450, y: 50, fixed: true,
    description: "Event Consumer: Synthesis service consuming validation events and producing final response assembly."
  },

  // Event Stores
  {
    id: 'event-store',
    label: 'Event Store\n[Persistence]\nEvent sourcing',
    group: 'eda-store',
    x: 600, y: 200, fixed: true,
    description: "Event Store: Persistent event log enabling event sourcing, replay capabilities, and audit trail maintenance."
  }
];

export const eventDrivenEdges = [
  // Event flow patterns
  { from: 'api-gateway-event', to: 'event-bus', label: 'QuerySubmitted\n[Event]' },
  { from: 'event-bus', to: 'triage-consumer', label: 'QuerySubmitted' },
  { from: 'triage-consumer', to: 'event-bus', label: 'QueryClassified\n[Event]' },
  { from: 'event-bus', to: 'research-consumer', label: 'QueryClassified' },
  { from: 'research-consumer', to: 'event-bus', label: 'ResearchCompleted\n[Event]' },
  { from: 'event-bus', to: 'math-consumer', label: 'ResearchCompleted' },
  { from: 'math-consumer', to: 'event-bus', label: 'MathProcessed\n[Event]' },
  { from: 'event-bus', to: 'synthesis-consumer', label: 'MathProcessed' },
  { from: 'synthesis-consumer', to: 'event-bus', label: 'ResponseReady\n[Event]' },
  
  // Event persistence
  { from: 'event-bus', to: 'event-store', label: 'Persist events' },
  { from: 'event-store', to: 'event-bus', label: 'Event replay' }
];

// Network Topology Diagram - Infrastructure Engineering Standard
export const networkTopologyNodes = [
  // Network Edge/DMZ
  {
    id: 'load-balancer',
    label: 'Load Balancer\n[F5/NGINX]\nHA Proxy',
    group: 'network-edge',
    x: 0, y: 200, fixed: true,
    description: "Network Edge: High-availability load balancer distributing traffic across multiple application instances with SSL termination."
  },
  {
    id: 'firewall',
    label: 'Firewall\n[Security Gateway]\nIngress/Egress Rules',
    group: 'network-security',
    x: 200, y: 100, fixed: true,
    description: "Network Security: Next-generation firewall implementing ingress/egress rules, DPI, and threat detection."
  },

  // Application Tier
  {
    id: 'app-cluster',
    label: 'Application Cluster\n[Kubernetes]\n3x Pods, Auto-scaling',
    group: 'network-compute',
    x: 400, y: 200, fixed: true,
    description: "Compute Tier: Kubernetes cluster with 3-pod configuration, horizontal auto-scaling, and rolling deployments."
  },
  {
    id: 'api-mesh',
    label: 'Service Mesh\n[Istio/Envoy]\nMicroservices Communication',
    group: 'network-mesh',
    x: 600, y: 200, fixed: true,
    description: "Service Mesh: Istio/Envoy proxy handling microservice communication, traffic management, and observability."
  },

  // Data Tier
  {
    id: 'primary-db',
    label: 'Primary Database\n[Neo4j Cluster]\nMaster Node',
    group: 'network-database',
    x: 400, y: 350, fixed: true,
    description: "Data Tier: Neo4j primary database cluster node handling write operations with ACID compliance."
  },
  {
    id: 'replica-db',
    label: 'Read Replica\n[Neo4j]\nRead-only Slaves',
    group: 'network-database',
    x: 600, y: 350, fixed: true,
    description: "Data Tier: Neo4j read replica nodes providing read scaling and disaster recovery capabilities."
  },
  {
    id: 'cache-cluster',
    label: 'Cache Cluster\n[Redis Sentinel]\n3-node HA',
    group: 'network-cache',
    x: 500, y: 450, fixed: true,
    description: "Cache Tier: Redis Sentinel cluster with 3-node high availability and automatic failover."
  },

  // Monitoring & Observability
  {
    id: 'monitoring',
    label: 'Monitoring Stack\n[Prometheus/Grafana]\nMetrics & Alerting',
    group: 'network-monitoring',
    x: 800, y: 200, fixed: true,
    description: "Observability: Prometheus metrics collection with Grafana dashboards and PagerDuty alerting integration."
  }
];

export const networkTopologyEdges = [
  // Traffic flow
  { from: 'load-balancer', to: 'firewall', label: 'HTTPS/443', color: { color: '#dc2626' } },
  { from: 'firewall', to: 'app-cluster', label: 'Filtered traffic', color: { color: '#059669' } },
  { from: 'app-cluster', to: 'api-mesh', label: 'gRPC/HTTP', color: { color: '#3b82f6' } },
  
  // Data access
  { from: 'api-mesh', to: 'primary-db', label: 'Write ops\nCypher', color: { color: '#7c3aed' } },
  { from: 'api-mesh', to: 'replica-db', label: 'Read ops\nCypher', color: { color: '#7c3aed' }, dashes: true },
  { from: 'api-mesh', to: 'cache-cluster', label: 'Cache lookup\nRedis Protocol', color: { color: '#ea580c' } },
  
  // Replication
  { from: 'primary-db', to: 'replica-db', label: 'Replication\nStreaming', color: { color: '#6b7280' } },
  
  // Monitoring
  { from: 'app-cluster', to: 'monitoring', label: 'Metrics\nPrometheus', color: { color: '#10b981' }, dashes: true },
  { from: 'primary-db', to: 'monitoring', label: 'DB Metrics', color: { color: '#10b981' }, dashes: true },
  { from: 'cache-cluster', to: 'monitoring', label: 'Cache Metrics', color: { color: '#10b981' }, dashes: true }
];

// UML Component Diagram - Software Engineering Standard
export const umlComponentNodes = [
  // Presentation Layer
  {
    id: 'web-interface',
    label: '<<component>>\nWeb Interface\n[React Frontend]',
    group: 'uml-component',
    x: 100, y: 50, fixed: true,
    description: "UML Component: React-based web interface providing user interaction capabilities with responsive design."
  },
  {
    id: 'api-facade',
    label: '<<component>>\nAPI Facade\n[REST Gateway]',
    group: 'uml-component',
    x: 400, y: 50, fixed: true,
    description: "UML Component: API facade implementing REST endpoints and request/response transformation."
  },

  // Business Logic Layer
  {
    id: 'triage-component',
    label: '<<component>>\nTriage Engine\n[Classification Service]',
    group: 'uml-component',
    x: 100, y: 200, fixed: true,
    description: "UML Component: Query classification engine implementing intelligent routing algorithms."
  },
  {
    id: 'orchestrator-component',
    label: '<<component>>\nResearch Orchestrator\n[Parallel Execution Engine]',
    group: 'uml-orchestrator',
    x: 400, y: 200, fixed: true,
    description: "UML Component: Core orchestration engine managing parallel sub-query execution with performance optimization."
  },
  {
    id: 'synthesis-component',
    label: '<<component>>\nSynthesis Engine\n[Response Assembly]',
    group: 'uml-component',
    x: 700, y: 200, fixed: true,
    description: "UML Component: Response synthesis engine combining multiple information sources with citation management."
  },

  // Data Access Layer
  {
    id: 'graph-repository',
    label: '<<component>>\nGraph Repository\n[Neo4j Data Access]',
    group: 'uml-repository',
    x: 100, y: 350, fixed: true,
    description: "UML Component: Data access component implementing Neo4j graph database operations with Cypher queries."
  },
  {
    id: 'cache-repository',
    label: '<<component>>\nCache Repository\n[Redis Data Access]',
    group: 'uml-repository',
    x: 400, y: 350, fixed: true,
    description: "UML Component: Cache access component managing Redis operations with TTL and eviction policies."
  },
  {
    id: 'web-repository',
    label: '<<component>>\nWeb Repository\n[External API Access]',
    group: 'uml-repository',
    x: 700, y: 350, fixed: true,
    description: "UML Component: External API access component handling web search and third-party integrations."
  },

  // Interfaces
  {
    id: 'llm-interface',
    label: '<<interface>>\nLLM Provider\n[Gemini Pro/Flash]',
    group: 'uml-interface',
    x: 400, y: 100, fixed: true,
    description: "UML Interface: LLM provider interface abstracting Gemini Pro/Flash API interactions."
  }
];

export const umlComponentEdges = [
  // Presentation to Business Logic
  { from: 'web-interface', to: 'api-facade', label: '<<uses>>' },
  { from: 'api-facade', to: 'triage-component', label: '<<uses>>' },
  { from: 'api-facade', to: 'orchestrator-component', label: '<<uses>>' },
  
  // Business Logic Dependencies
  { from: 'triage-component', to: 'llm-interface', label: '<<requires>>' },
  { from: 'orchestrator-component', to: 'llm-interface', label: '<<requires>>' },
  { from: 'synthesis-component', to: 'llm-interface', label: '<<requires>>' },
  
  // Data Access Dependencies
  { from: 'orchestrator-component', to: 'graph-repository', label: '<<uses>>' },
  { from: 'orchestrator-component', to: 'cache-repository', label: '<<uses>>' },
  { from: 'orchestrator-component', to: 'web-repository', label: '<<uses>>' },
  { from: 'synthesis-component', to: 'cache-repository', label: '<<uses>>' },
  
  // Component Assembly
  { from: 'orchestrator-component', to: 'synthesis-component', label: '<<delegates>>' }
];

// Infrastructure as Code (IaC) Pattern - DevOps Engineering
export const iacNodes = [
  // Infrastructure Definition
  {
    id: 'terraform-main',
    label: 'main.tf\n[Terraform]\nInfrastructure Definition',
    group: 'iac-terraform',
    x: 100, y: 100, fixed: true,
    description: "IaC Definition: Main Terraform configuration defining complete infrastructure stack with provider dependencies."
  },
  {
    id: 'kubernetes-manifests',
    label: 'k8s-manifests/\n[YAML]\nDeployment Specs',
    group: 'iac-k8s',
    x: 400, y: 100, fixed: true,
    description: "IaC Definition: Kubernetes YAML manifests defining deployments, services, ingress, and configuration maps."
  },
  {
    id: 'helm-charts',
    label: 'helm-charts/\n[Helm]\nPackage Manager',
    group: 'iac-helm',
    x: 700, y: 100, fixed: true,
    description: "IaC Definition: Helm charts providing templated Kubernetes deployments with environment-specific values."
  },

  // CI/CD Pipeline
  {
    id: 'github-actions',
    label: 'github-actions/\n[Workflow]\nCI/CD Pipeline',
    group: 'iac-cicd',
    x: 100, y: 250, fixed: true,
    description: "IaC Pipeline: GitHub Actions workflow implementing CI/CD pipeline with automated testing and deployment."
  },
  {
    id: 'docker-compose',
    label: 'docker-compose.yml\n[Container]\nLocal Development',
    group: 'iac-docker',
    x: 400, y: 250, fixed: true,
    description: "IaC Definition: Docker Compose configuration for local development environment with service dependencies."
  },

  // Deployed Infrastructure
  {
    id: 'aws-vpc',
    label: 'AWS VPC\n[Cloud Infrastructure]\nNetwork Foundation',
    group: 'iac-cloud',
    x: 100, y: 400, fixed: true,
    description: "Cloud Infrastructure: AWS VPC providing network foundation with subnets, security groups, and routing."
  },
  {
    id: 'eks-cluster',
    label: 'EKS Cluster\n[Managed Kubernetes]\nContainer Orchestration',
    group: 'iac-cloud',
    x: 400, y: 400, fixed: true,
    description: "Cloud Infrastructure: AWS EKS cluster providing managed Kubernetes with auto-scaling and monitoring."
  },
  {
    id: 'rds-neo4j',
    label: 'RDS/Neo4j\n[Managed Database]\nData Persistence',
    group: 'iac-cloud',
    x: 700, y: 400, fixed: true,
    description: "Cloud Infrastructure: Managed database services providing Neo4j graph database with backup and monitoring."
  }
];

export const iacEdges = [
  // Infrastructure Definition Flow
  { from: 'terraform-main', to: 'aws-vpc', label: 'terraform apply', color: { color: '#7c3aed' } },
  { from: 'terraform-main', to: 'eks-cluster', label: 'provisions', color: { color: '#7c3aed' } },
  { from: 'terraform-main', to: 'rds-neo4j', label: 'creates', color: { color: '#7c3aed' } },
  
  // Deployment Flow
  { from: 'kubernetes-manifests', to: 'eks-cluster', label: 'kubectl apply', color: { color: '#3b82f6' } },
  { from: 'helm-charts', to: 'eks-cluster', label: 'helm install', color: { color: '#059669' } },
  
  // CI/CD Flow
  { from: 'github-actions', to: 'docker-compose', label: 'test locally', color: { color: '#ea580c' } },
  { from: 'github-actions', to: 'helm-charts', label: 'deploy', color: { color: '#ea580c' } },
  
  // Local Development
  { from: 'docker-compose', to: 'kubernetes-manifests', label: 'dev → staging', color: { color: '#6b7280' }, dashes: true }
];

// Add new engineering options
export const advancedEngineeringOptions = {
  networkTopology: {
    name: "Network Topology Diagram",
    complexity: 10,
    standard: "Network Engineering Standard",
    description: "Professional network topology showing infrastructure, security, and data flow patterns",
    nodes: "networkTopologyNodes",
    edges: "networkTopologyEdges", 
    pros: ["Infrastructure clarity", "Security visualization", "Operations focused"],
    cons: ["High technical complexity", "Infrastructure specific"]
  },
  
  umlComponent: {
    name: "UML Component Diagram",
    complexity: 9,
    standard: "Software Engineering UML Standard",
    description: "Industry-standard UML component diagram showing software architecture and dependencies",
    nodes: "umlComponentNodes",
    edges: "umlComponentEdges",
    pros: ["UML standard", "Clear dependencies", "Software architecture focus"],
    cons: ["Requires UML knowledge", "Software-centric view"]
  },
  
  infrastructureAsCode: {
    name: "Infrastructure as Code (IaC)",
    complexity: 10,
    standard: "DevOps Engineering Standard",
    description: "Modern DevOps pattern showing infrastructure definition, CI/CD, and cloud deployment",
    nodes: "iacNodes",
    edges: "iacEdges",
    pros: ["Modern DevOps practice", "Cloud-native approach", "Automation focused"],
    cons: ["DevOps expertise required", "Cloud-specific implementation"]
  }
};

// Update engineering design options
export const engineeringDesignOptions = {
  monoDark: {
    name: "Monochromatic Dark",
    complexity: 8,
    standard: "Professional Standard",
    description: "A professional, high-contrast dark theme with accent colors for clarity.",
    nodes: "monoDarkNodes",
    edges: "monoDarkEdges",
    pros: ["Modern dark mode aesthetic", "High-contrast & readable", "Strategic color use"],
    cons: ["Minimalist style", "May not suit all preferences"]
  },
  c4Model: {
    name: "C4 Model Architecture",
    complexity: 10,
    standard: "Software Engineering Standard",
    description: "Industry-standard C4 model showing Context, Containers, and Components with proper engineering notation",
    nodes: "c4ModelNodes",
    edges: "c4ModelEdges",
    pros: ["Industry standard", "Clear abstraction levels", "Professional documentation"],
    cons: ["High complexity", "Requires technical knowledge"]
  },
  
  dataFlowDiagram: {
    name: "Data Flow Diagram (DFD)",
    complexity: 9,
    standard: "Structured Analysis Standard", 
    description: "Classic structured analysis DFD showing processes, data stores, and external entities",
    nodes: "dfdNodes",
    edges: "dfdEdges",
    pros: ["Structured analysis standard", "Clear data flow", "Academic/professional recognition"],
    cons: ["Traditional approach", "Complex for non-technical users"]
  },
  
  eventDrivenArch: {
    name: "Event-Driven Architecture",
    complexity: 9,
    standard: "Modern Microservices Standard",
    description: "Modern microservices architecture showing event producers, consumers, and message brokers",
    nodes: "eventDrivenNodes", 
    edges: "eventDrivenEdges",
    pros: ["Modern architecture pattern", "Scalable design", "Industry best practice"],
    cons: ["High complexity", "Requires distributed systems knowledge"]
  },

  agenticFlow: {
    name: "Agentic AI Process Flow",
    complexity: 7,
    standard: "AI/ML Engineering Standard",
    description: "Professional agentic AI system flow - Simple view shows core agents & Redis integration, Detailed view shows complete process",
    nodes: "agenticFlowNodes",
    edges: "agenticFlowEdges",
    pros: ["Clean agent workflow", "Shows Redis integration", "Professional design", "Simple & detailed views"],
    cons: ["Requires AI/ML knowledge", "Technical system"]
  },

  "professionalFlow": {
    name: "Professional Agentic Flow",
    complexity: 8,
    standard: "AI/ML Engineering Standard",
    description: "A polished, professional diagram inspired by your design, with icons and a clean layout.",
    nodes: "professionalFlowNodes",
    edges: "professionalFlowEdges",
    pros: ["Visually appealing", "Professional icons & colors", "Clear, spacious layout"],
    cons: ["Abstracted details", "Focus on aesthetics"]
  },

  ...advancedEngineeringOptions
}; 

// Comprehensive Agentic AI Flow Diagram - Complete End-to-End Process
export const agenticFlowNodes = [
  // 1. User Input Stage
  {
    id: 'user_input',
    label: '👤 User Query\n\n"Load calculation for\n20-foot beam?"',
    x: 100,
    y: 300,
    size: 50,
    shape: 'box',
    font: { size: 12, color: '#ffffff', multi: true, bold: true },
    color: { 
      background: '#3498db', 
      border: '#2980b9',
      highlight: { background: '#5dade2', border: '#2980b9' }
    },
    borderWidth: 3,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 8 },
    fixed: { x: true, y: true }
  },

  // 2. Triage Agent
  {
    id: 'triage_agent',
    label: '🎯 TRIAGE\n\n🧠 Gemini Flash\n⚡ Classification\n⏱️ 1-3s',
    x: 250,
    y: 300,
    size: 45,
    shape: 'ellipse',
    font: { size: 11, color: '#ffffff', multi: true, bold: true },
    color: { 
      background: '#e67e22', 
      border: '#d35400',
      highlight: { background: '#f39c12', border: '#d35400' }
    },
    borderWidth: 3,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 8 },
    fixed: { x: true, y: true }
  },

  // 3. Planning Agent
  {
    id: 'planning_agent',
    label: '📋 PLANNING\n\n🧠 Gemini Pro\n🎯 HyDE Method\n⏱️ 2-5s',
    x: 400,
    y: 300,
    size: 45,
    shape: 'ellipse',
    font: { size: 11, color: '#ffffff', multi: true, bold: true },
    color: { 
      background: '#3498db', 
      border: '#2980b9',
      highlight: { background: '#5dade2', border: '#2980b9' }
    },
    borderWidth: 3,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 8 },
    fixed: { x: true, y: true }
  },

  // 4. Research Orchestrator - THE CROWN JEWEL
  {
    id: 'research_orchestrator',
    label: '🚀 ORCHESTRATOR\n\n⭐ CROWN JEWEL ⭐\n🔥 PARALLEL ENGINE\n\n4-6x Speed Boost\n⏱️ 10-15s',
    x: 600,
    y: 300,
    size: 70,
    shape: 'star',
    font: { size: 12, color: '#ffffff', multi: true, bold: true },
    color: { 
      background: '#8e44ad', 
      border: '#6c3483',
      highlight: { background: '#bb8fce', border: '#6c3483' }
    },
    borderWidth: 4,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.4)', size: 12 },
    fixed: { x: true, y: true }
  },

  // 5. Parallel Stream 1 - Top
  {
    id: 'parallel_stream_1',
    label: '⚡ Stream 1\n\n🔍 Math Search\n📊 Equations',
    x: 800,
    y: 200,
    size: 40,
    shape: 'diamond',
    font: { size: 10, color: '#ffffff', multi: true, bold: true },
    color: { 
      background: '#f39c12', 
      border: '#e67e22',
      highlight: { background: '#f7dc6f', border: '#e67e22' }
    },
    borderWidth: 3,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 6 },
    fixed: { x: true, y: true }
  },

  // 6. Parallel Stream 2 - Middle
  {
    id: 'parallel_stream_2',
    label: '⚡ Stream 2\n\n🏗️ Table Search\n📏 Standards',
    x: 800,
    y: 300,
    size: 40,
    shape: 'diamond',
    font: { size: 10, color: '#ffffff', multi: true, bold: true },
    color: { 
      background: '#27ae60', 
      border: '#229954',
      highlight: { background: '#58d68d', border: '#229954' }
    },
    borderWidth: 3,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 6 },
    fixed: { x: true, y: true }
  },

  // 7. Parallel Stream 3 - Bottom
  {
    id: 'parallel_stream_3',
    label: '⚡ Stream 3\n\n🏠 Code Search\n📈 Diagrams',
    x: 800,
    y: 400,
    size: 40,
    shape: 'diamond',
    font: { size: 10, color: '#ffffff', multi: true, bold: true },
    color: { 
      background: '#e74c3c', 
      border: '#c0392b',
      highlight: { background: '#ec7063', border: '#c0392b' }
    },
    borderWidth: 3,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 6 },
    fixed: { x: true, y: true }
  },

  // 8. Neo4j Knowledge Graph
  {
    id: 'neo4j_knowledge_graph',
    label: '🗄️ NEO4J GRAPH\n\n📊 69 Math Nodes\n📋 118 Tables\n📈 49 Diagrams',
    x: 1000,
    y: 300,
    size: 55,
    shape: 'cylinder',
    font: { size: 11, color: '#ffffff', multi: true, bold: true },
    color: { 
      background: '#4CAF50', 
      border: '#388E3C',
      highlight: { background: '#81C784', border: '#388E3C' }
    },
    borderWidth: 3,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 10 },
    fixed: { x: true, y: true }
  },

  // 9. Mathematical Enhancement
  {
    id: 'math_enhancement',
    label: '🔢 MATH ENHANCE\n\n🧮 Equation Detection\n📐 LaTeX Render\n\n"W = (DL + LL) × L²/8"',
    x: 1200,
    y: 200,
    size: 50,
    shape: 'box',
    font: { size: 10, color: '#ffffff', multi: true, bold: true },
    color: { 
      background: '#9b59b6', 
      border: '#8e44ad',
      highlight: { background: '#d2b4de', border: '#8e44ad' }
    },
    borderWidth: 3,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 8 },
    fixed: { x: true, y: true }
  },

  // 10. Quality Validation
  {
    id: 'validation_engine',
    label: '✅ VALIDATION\n\n🎯 10-Point Score\n📏 Threshold: 6.0+\n\nScore: 8.7/10 ✅',
    x: 1200,
    y: 300,
    size: 50,
    shape: 'hexagon',
    font: { size: 10, color: '#ffffff', multi: true, bold: true },
    color: { 
      background: '#27ae60', 
      border: '#229954',
      highlight: { background: '#58d68d', border: '#229954' }
    },
    borderWidth: 3,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 8 },
    fixed: { x: true, y: true }
  },

  // 11. Synthesis Agent
  {
    id: 'synthesis_agent',
    label: '🔄 SYNTHESIS\n\n🧠 Gemini Pro\n📝 Assembly\n✨ Final Check',
    x: 1200,
    y: 400,
    size: 45,
    shape: 'ellipse',
    font: { size: 10, color: '#ffffff', multi: true, bold: true },
    color: { 
      background: '#e74c3c', 
      border: '#c0392b',
      highlight: { background: '#ec7063', border: '#c0392b' }
    },
    borderWidth: 3,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 8 },
    fixed: { x: true, y: true }
  },

  // 12. Memory Agent
  {
    id: 'memory_agent',
    label: '🧠 MEMORY\n\n🔴 Redis Cache\n💾 Session Storage\n⚡ 60-70% Hit Rate',
    x: 1400,
    y: 250,
    size: 40,
    shape: 'ellipse',
    font: { size: 9, color: '#ffffff', multi: true, bold: true },
    color: { 
      background: '#dc382d', 
      border: '#a51a0e',
      highlight: { background: '#e57373', border: '#a51a0e' }
    },
    borderWidth: 3,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 6 },
    fixed: { x: true, y: true }
  },

  // 13. File Backup
  {
    id: 'file_backup',
    label: '📁 BACKUP\n\n💾 Dual Storage\n🔄 Persistence\n🛡️ Recovery',
    x: 1400,
    y: 350,
    size: 35,
    shape: 'cylinder',
    font: { size: 9, color: '#2c3e50', multi: true, bold: true },
    color: { 
      background: '#95a5a6', 
      border: '#7f8c8d',
      highlight: { background: '#bdc3c7', border: '#7f8c8d' }
    },
    borderWidth: 2,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 6 },
    fixed: { x: true, y: true }
  },

  // 14. Response Assembly
  {
    id: 'response_assembly',
    label: '📤 ASSEMBLY\n\n✨ Final Compilation\n📊 Calculations\n📋 Citations',
    x: 1600,
    y: 300,
    size: 45,
    shape: 'box',
    font: { size: 10, color: '#ffffff', multi: true, bold: true },
    color: { 
      background: '#34495e', 
      border: '#2c3e50',
      highlight: { background: '#5d6d7e', border: '#2c3e50' }
    },
    borderWidth: 3,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 8 },
    fixed: { x: true, y: true }
  },

  // 15. User Response
  {
    id: 'user_response',
    label: '👤 FINAL RESPONSE\n\n"20-foot beam:\n📐 W = (DL+LL)×L²/8\n📊 Table R502.5.1(1)"\n\n✅ Total: 15-20s',
    x: 1800,
    y: 300,
    size: 55,
    shape: 'box',
    font: { size: 11, color: '#ffffff', multi: true, bold: true },
    color: { 
      background: '#3498db', 
      border: '#2980b9',
      highlight: { background: '#5dade2', border: '#2980b9' }
    },
    borderWidth: 3,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 10 },
    fixed: { x: true, y: true }
  },

  // 16. Performance Metrics
  {
    id: 'performance_metrics',
    label: '📊 METRICS\n\n🚀 4-6x Speed\n⏱️ 60s → 15s\n🎯 Score: 8.7/10\n🔥 85% Efficiency',
    x: 600,
    y: 150,
    size: 45,
    shape: 'triangle',
    font: { size: 9, color: '#ffffff', multi: true, bold: true },
    color: { 
      background: '#f39c12', 
      border: '#e67e22',
      highlight: { background: '#f7dc6f', border: '#e67e22' }
    },
    borderWidth: 3,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 6 },
    fixed: { x: true, y: true }
  }
];

export const agenticFlowEdges = [
  // Main Flow Path
  {
    id: 'user_to_triage',
    from: 'user_input',
    to: 'triage_agent',
    label: 'Query',
    color: { color: '#3498db' },
    width: 3,
    arrows: { to: { enabled: true, scaleFactor: 1.2 } },
    font: { size: 10, color: '#2c3e50', background: '#ffffff' }
  },
  {
    id: 'triage_to_planning',
    from: 'triage_agent',
    to: 'planning_agent',
    label: 'Classified:\n"Structural Calc"',
    color: { color: '#e67e22' },
    width: 3,
    arrows: { to: { enabled: true, scaleFactor: 1.2 } },
    font: { size: 9, color: '#2c3e50', background: '#ffffff' }
  },
  {
    id: 'planning_to_orchestrator',
    from: 'planning_agent',
    to: 'research_orchestrator',
    label: 'Plan:\n3 Streams',
    color: { color: '#3498db' },
    width: 4,
    arrows: { to: { enabled: true, scaleFactor: 1.3 } },
    font: { size: 9, color: '#2c3e50', background: '#ffffff' }
  },

  // Parallel Stream Branches
  {
    id: 'orchestrator_to_stream1',
    from: 'research_orchestrator',
    to: 'parallel_stream_1',
    label: 'Math\nSearch',
    color: { color: '#f39c12' },
    width: 2,
    arrows: { to: { enabled: true, scaleFactor: 1.0 } },
    font: { size: 8, color: '#2c3e50', background: '#ffffff' }
  },
  {
    id: 'orchestrator_to_stream2',
    from: 'research_orchestrator',
    to: 'parallel_stream_2',
    label: 'Table\nSearch',
    color: { color: '#27ae60' },
    width: 2,
    arrows: { to: { enabled: true, scaleFactor: 1.0 } },
    font: { size: 8, color: '#2c3e50', background: '#ffffff' }
  },
  {
    id: 'orchestrator_to_stream3',
    from: 'research_orchestrator',
    to: 'parallel_stream_3',
    label: 'Code\nSearch',
    color: { color: '#e74c3c' },
    width: 2,
    arrows: { to: { enabled: true, scaleFactor: 1.0 } },
    font: { size: 8, color: '#2c3e50', background: '#ffffff' }
  },

  // Knowledge Graph Access
  {
    id: 'stream1_to_neo4j',
    from: 'parallel_stream_1',
    to: 'neo4j_knowledge_graph',
    label: 'Math Nodes',
    color: { color: '#f39c12' },
    width: 2,
    arrows: { to: { enabled: true, scaleFactor: 1.0 } },
    font: { size: 8, color: '#2c3e50', background: '#ffffff' }
  },
  {
    id: 'stream2_to_neo4j',
    from: 'parallel_stream_2',
    to: 'neo4j_knowledge_graph',
    label: 'Table Nodes',
    color: { color: '#27ae60' },
    width: 2,
    arrows: { to: { enabled: true, scaleFactor: 1.0 } },
    font: { size: 8, color: '#2c3e50', background: '#ffffff' }
  },
  {
    id: 'stream3_to_neo4j',
    from: 'parallel_stream_3',
    to: 'neo4j_knowledge_graph',
    label: 'Diagram Nodes',
    color: { color: '#e74c3c' },
    width: 2,
    arrows: { to: { enabled: true, scaleFactor: 1.0 } },
    font: { size: 8, color: '#2c3e50', background: '#ffffff' }
  },

  // Processing Pipeline
  {
    id: 'neo4j_to_math',
    from: 'neo4j_knowledge_graph',
    to: 'math_enhancement',
    label: '69 Equations',
    color: { color: '#9b59b6' },
    width: 2,
    arrows: { to: { enabled: true, scaleFactor: 1.0 } },
    font: { size: 8, color: '#2c3e50', background: '#ffffff' }
  },
  {
    id: 'neo4j_to_validation',
    from: 'neo4j_knowledge_graph',
    to: 'validation_engine',
    label: '237 Nodes',
    color: { color: '#27ae60' },
    width: 3,
    arrows: { to: { enabled: true, scaleFactor: 1.1 } },
    font: { size: 8, color: '#2c3e50', background: '#ffffff' }
  },
  {
    id: 'neo4j_to_synthesis',
    from: 'neo4j_knowledge_graph',
    to: 'synthesis_agent',
    label: 'Raw Content',
    color: { color: '#e74c3c' },
    width: 2,
    arrows: { to: { enabled: true, scaleFactor: 1.0 } },
    font: { size: 8, color: '#2c3e50', background: '#ffffff' }
  },

  // Enhancement and Validation Flow
  {
    id: 'math_to_validation',
    from: 'math_enhancement',
    to: 'validation_engine',
    label: 'LaTeX\nRendered',
    color: { color: '#9b59b6' },
    width: 2,
    arrows: { to: { enabled: true, scaleFactor: 1.0 } },
    font: { size: 8, color: '#2c3e50', background: '#ffffff' }
  },
  {
    id: 'validation_to_synthesis',
    from: 'validation_engine',
    to: 'synthesis_agent',
    label: 'Score 8.7/10',
    color: { color: '#27ae60' },
    width: 3,
    arrows: { to: { enabled: true, scaleFactor: 1.1 } },
    font: { size: 8, color: '#2c3e50', background: '#ffffff' }
  },

  // Memory and Storage
  {
    id: 'synthesis_to_memory',
    from: 'synthesis_agent',
    to: 'memory_agent',
    label: 'Context',
    color: { color: '#dc382d' },
    width: 2,
    arrows: { to: { enabled: true, scaleFactor: 1.0 } },
    font: { size: 8, color: '#2c3e50', background: '#ffffff' }
  },
  {
    id: 'synthesis_to_backup',
    from: 'synthesis_agent',
    to: 'file_backup',
    label: 'Backup',
    color: { color: '#95a5a6' },
    width: 1,
    arrows: { to: { enabled: true, scaleFactor: 0.8 } },
    font: { size: 7, color: '#2c3e50', background: '#ffffff' }
  },

  // Final Assembly and Delivery
  {
    id: 'synthesis_to_assembly',
    from: 'synthesis_agent',
    to: 'response_assembly',
    label: 'Final Content',
    color: { color: '#34495e' },
    width: 3,
    arrows: { to: { enabled: true, scaleFactor: 1.2 } },
    font: { size: 9, color: '#2c3e50', background: '#ffffff' }
  },
  {
    id: 'memory_to_assembly',
    from: 'memory_agent',
    to: 'response_assembly',
    label: 'Session',
    color: { color: '#dc382d' },
    width: 1,
    arrows: { to: { enabled: true, scaleFactor: 0.8 } },
    font: { size: 7, color: '#2c3e50', background: '#ffffff' },
    dashes: [3, 3]
  },
  {
    id: 'assembly_to_user',
    from: 'response_assembly',
    to: 'user_response',
    label: 'Complete\nResponse',
    color: { color: '#3498db' },
    width: 4,
    arrows: { to: { enabled: true, scaleFactor: 1.3 } },
    font: { size: 10, color: '#2c3e50', background: '#ffffff' }
  },

  // Performance Metrics Connection
  {
    id: 'orchestrator_to_metrics',
    from: 'research_orchestrator',
    to: 'performance_metrics',
    label: 'Metrics',
    color: { color: '#f39c12' },
    width: 1,
    arrows: { to: { enabled: true, scaleFactor: 0.8 } },
    font: { size: 7, color: '#2c3e50', background: '#ffffff' },
    dashes: [3, 3]
  }
]; 

// Simplified Agentic AI Flow - Clean Professional Design for Simple View
export const simpleAgenticFlowNodes = [
  // 1. User Input
  {
    id: 'user_input',
    label: '👤 User Query',
    x: 100,
    y: 300,
    size: 35,
    shape: 'box',
    font: { size: 12, color: '#ffffff', bold: true },
    color: { 
      background: '#2c3e50', 
      border: '#1a252f',
      highlight: { background: '#34495e', border: '#1a252f' }
    },
    borderWidth: 2,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.2)', size: 4 },
    fixed: { x: true, y: true }
  },

  // 2. Triage Agent
  {
    id: 'triage_agent',
    label: '🎯 Triage Agent\n\nClassification',
    x: 280,
    y: 300,
    size: 35,
    shape: 'ellipse',
    font: { size: 11, color: '#ffffff', bold: true, multi: true },
    color: { 
      background: '#3498db', 
      border: '#2980b9',
      highlight: { background: '#5dade2', border: '#2980b9' }
    },
    borderWidth: 2,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.2)', size: 4 },
    fixed: { x: true, y: true }
  },

  // 3. Planning Agent
  {
    id: 'planning_agent',
    label: '📋 Planning Agent\n\nStrategy & HyDE',
    x: 460,
    y: 300,
    size: 35,
    shape: 'ellipse',
    font: { size: 11, color: '#ffffff', bold: true, multi: true },
    color: { 
      background: '#3498db', 
      border: '#2980b9',
      highlight: { background: '#5dade2', border: '#2980b9' }
    },
    borderWidth: 2,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.2)', size: 4 },
    fixed: { x: true, y: true }
  },

  // 4. Research Orchestrator - Crown Jewel
  {
    id: 'research_orchestrator',
    label: '🚀 Research Orchestrator\n\n⭐ PARALLEL ENGINE ⭐\n4-6x Speed Boost',
    x: 680,
    y: 300,
    size: 50,
    shape: 'star',
    font: { size: 12, color: '#ffffff', bold: true, multi: true },
    color: { 
      background: '#8e44ad', 
      border: '#6c3483',
      highlight: { background: '#bb8fce', border: '#6c3483' }
    },
    borderWidth: 3,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 6 },
    fixed: { x: true, y: true }
  },

  // 5. Neo4j Knowledge Graph
  {
    id: 'neo4j_graph',
    label: '🗄️ Neo4j Knowledge Graph\n\n237 Total Nodes\n69 Math • 118 Tables • 49 Diagrams',
    x: 920,
    y: 300,
    size: 45,
    shape: 'cylinder',
    font: { size: 11, color: '#ffffff', bold: true, multi: true },
    color: { 
      background: '#27ae60', 
      border: '#229954',
      highlight: { background: '#58d68d', border: '#229954' }
    },
    borderWidth: 2,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.2)', size: 5 },
    fixed: { x: true, y: true }
  },

  // 6. Redis Cache & Memory
  {
    id: 'redis_memory',
    label: '🔴 Redis Cache & Memory\n\nSession Management\nConversation History\n60-70% Hit Rate',
    x: 920,
    y: 180,
    size: 40,
    shape: 'diamond',
    font: { size: 10, color: '#ffffff', bold: true, multi: true },
    color: { 
      background: '#e74c3c', 
      border: '#c0392b',
      highlight: { background: '#ec7063', border: '#c0392b' }
    },
    borderWidth: 2,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.2)', size: 4 },
    fixed: { x: true, y: true }
  },

  // 7. Synthesis Agent
  {
    id: 'synthesis_agent',
    label: '🔄 Synthesis Agent\n\nResponse Assembly\nQuality Assurance',
    x: 1160,
    y: 300,
    size: 35,
    shape: 'ellipse',
    font: { size: 11, color: '#ffffff', bold: true, multi: true },
    color: { 
      background: '#3498db', 
      border: '#2980b9',
      highlight: { background: '#5dade2', border: '#2980b9' }
    },
    borderWidth: 2,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.2)', size: 4 },
    fixed: { x: true, y: true }
  },

  // 8. Final Response
  {
    id: 'final_response',
    label: '📤 Final Response\n\nComplete Answer',
    x: 1340,
    y: 300,
    size: 35,
    shape: 'box',
    font: { size: 11, color: '#ffffff', bold: true, multi: true },
    color: { 
      background: '#2c3e50', 
      border: '#1a252f',
      highlight: { background: '#34495e', border: '#1a252f' }
    },
    borderWidth: 2,
    shadow: { enabled: true, color: 'rgba(0,0,0,0.2)', size: 4 },
    fixed: { x: true, y: true }
  }
];

export const simpleAgenticFlowEdges = [
  // Main Agent Flow
  {
    id: 'user_to_triage',
    from: 'user_input',
    to: 'triage_agent',
    label: 'Query',
    color: { color: '#2c3e50' },
    width: 2,
    arrows: { to: { enabled: true, scaleFactor: 1.0 } },
    font: { size: 10, color: '#2c3e50', background: '#ffffff' }
  },
  {
    id: 'triage_to_planning',
    from: 'triage_agent',
    to: 'planning_agent',
    label: 'Intent',
    color: { color: '#3498db' },
    width: 2,
    arrows: { to: { enabled: true, scaleFactor: 1.0 } },
    font: { size: 10, color: '#2c3e50', background: '#ffffff' }
  },
  {
    id: 'planning_to_orchestrator',
    from: 'planning_agent',
    to: 'research_orchestrator',
    label: 'Strategy',
    color: { color: '#3498db' },
    width: 3,
    arrows: { to: { enabled: true, scaleFactor: 1.1 } },
    font: { size: 10, color: '#2c3e50', background: '#ffffff' }
  },
  {
    id: 'orchestrator_to_neo4j',
    from: 'research_orchestrator',
    to: 'neo4j_graph',
    label: 'Parallel Queries',
    color: { color: '#8e44ad' },
    width: 3,
    arrows: { to: { enabled: true, scaleFactor: 1.1 } },
    font: { size: 10, color: '#2c3e50', background: '#ffffff' }
  },
  {
    id: 'neo4j_to_synthesis',
    from: 'neo4j_graph',
    to: 'synthesis_agent',
    label: 'Retrieved Data',
    color: { color: '#27ae60' },
    width: 2,
    arrows: { to: { enabled: true, scaleFactor: 1.0 } },
    font: { size: 10, color: '#2c3e50', background: '#ffffff' }
  },
  {
    id: 'synthesis_to_response',
    from: 'synthesis_agent',
    to: 'final_response',
    label: 'Final Answer',
    color: { color: '#3498db' },
    width: 3,
    arrows: { to: { enabled: true, scaleFactor: 1.1 } },
    font: { size: 10, color: '#2c3e50', background: '#ffffff' }
  },

  // Redis Integration Connections
  {
    id: 'orchestrator_to_redis',
    from: 'research_orchestrator',
    to: 'redis_memory',
    label: 'Cache Check',
    color: { color: '#e74c3c' },
    width: 2,
    arrows: { to: { enabled: true, scaleFactor: 1.0 } },
    font: { size: 9, color: '#2c3e50', background: '#ffffff' },
    dashes: [3, 3]
  },
  {
    id: 'redis_to_synthesis',
    from: 'redis_memory',
    to: 'synthesis_agent',
    label: 'Context',
    color: { color: '#e74c3c' },
    width: 2,
    arrows: { to: { enabled: true, scaleFactor: 1.0 } },
    font: { size: 9, color: '#2c3e50', background: '#ffffff' },
    dashes: [3, 3]
  },
  {
    id: 'synthesis_to_redis',
    from: 'synthesis_agent',
    to: 'redis_memory',
    label: 'Store Session',
    color: { color: '#e74c3c' },
    width: 1,
    arrows: { to: { enabled: true, scaleFactor: 0.8 } },
    font: { size: 8, color: '#2c3e50', background: '#ffffff' },
    dashes: [3, 3]
  }
];

// =================================================================================
// Professional Agentic AI Flow (Based on User's Visual Design)
// =================================================================================

export const professionalFlowNodes = [
  // 1. User Input
  {
    id: 'user_input',
    label: '👤  User Query',
    x: 0,
    y: 300,
    size: 40,
    shape: 'box',
    font: { size: 14, color: '#e0e0e0', bold: true },
    color: { 
      background: '#2c3e50', 
      border: '#1a252f',
      highlight: { background: '#34495e', border: '#1a252f' }
    },
    borderWidth: 2,
    fixed: { x: true, y: true }
  },

  // 2. Triage Agent
  {
    id: 'triage_agent',
    label: '🎯  Triage Agent\n\nClassification',
    x: 220,
    y: 300,
    size: 45,
    shape: 'ellipse',
    font: { size: 14, color: '#ffffff', bold: true, multi: true, align: 'center' },
    color: { 
      background: '#e67e22', 
      border: '#d35400',
      highlight: { background: '#f39c12', border: '#d35400' }
    },
    borderWidth: 2,
    fixed: { x: true, y: true }
  },

  // 3. Planning Agent
  {
    id: 'planning_agent',
    label: '📋  Planning Agent\n\nStrategy & HyDE',
    x: 440,
    y: 300,
    size: 45,
    shape: 'ellipse',
    font: { size: 14, color: '#ffffff', bold: true, multi: true, align: 'center' },
    color: { 
      background: '#3498db', 
      border: '#2980b9',
      highlight: { background: '#5dade2', border: '#2980b9' }
    },
    borderWidth: 2,
    fixed: { x: true, y: true }
  },

  // 4. Research Orchestrator - Star
  {
    id: 'research_orchestrator_star',
    label: '', // Label is handled by the text node below
    x: 680,
    y: 300,
    size: 55,
    shape: 'star',
    color: { 
      background: '#8e44ad', 
      border: '#6c3483',
      highlight: { background: '#bb8fce', border: '#6c3483' }
    },
    borderWidth: 3,
    fixed: { x: true, y: true }
  },

  // 4a. Research Orchestrator - Text Label
  {
    id: 'research_orchestrator_label',
    label: '🚀 Research Orchestrator\n\n⭐ PARALLEL ENGINE ⭐\n4-6x Speed Boost',
    x: 680,
    y: 420, // Positioned below the star
    shape: 'text',
    font: { size: 13, color: '#e0e0e0', multi: true, align: 'center', bold: true },
    fixed: { x: true, y: true }
  },

  // 5. Neo4j Knowledge Graph
  {
    id: 'neo4j_graph',
    label: '🗄️  Neo4j Knowledge Graph\n\n237 Total Nodes\n69 Math • 118 Tables • 49 Diagrams',
    x: 950,
    y: 300,
    size: 60,
    shape: 'ellipse',
    font: { size: 14, color: '#ffffff', bold: true, multi: true, align: 'center' },
    color: { 
      background: '#27ae60', 
      border: '#229954',
      highlight: { background: '#58d68d', border: '#229954' }
    },
    borderWidth: 3,
    fixed: { x: true, y: true }
  },

  // 6. Redis Cache & Memory
  {
    id: 'redis_memory',
    label: '🔴  Redis Cache & Memory\n\nSession Management\nConversation History\n60-70% Hit Rate',
    x: 950,
    y: 120, // Positioned above Neo4j
    size: 50,
    shape: 'diamond',
    font: { size: 13, color: '#ffffff', bold: true, multi: true, align: 'center' },
    color: { 
      background: '#e74c3c', 
      border: '#c0392b',
      highlight: { background: '#ec7063', border: '#c0392b' }
    },
    borderWidth: 3,
    fixed: { x: true, y: true }
  },

  // 7. Synthesis Agent
  {
    id: 'synthesis_agent',
    label: '🔄  Synthesis Agent\n\nResponse Assembly\nQuality Assurance',
    x: 1220,
    y: 300,
    size: 45,
    shape: 'ellipse',
    font: { size: 14, color: '#ffffff', bold: true, multi: true, align: 'center' },
    color: { 
      background: '#3498db', 
      border: '#2980b9',
      highlight: { background: '#5dade2', border: '#2980b9' }
    },
    borderWidth: 2,
    fixed: { x: true, y: true }
  },

  // 8. Final Response
  {
    id: 'final_response',
    label: '📤  Final Response\n\nComplete Answer',
    x: 1420,
    y: 300,
    size: 40,
    shape: 'box',
    font: { size: 14, color: '#e0e0e0', bold: true, multi: true, align: 'center' },
    color: { 
      background: '#2c3e50', 
      border: '#1a252f',
      highlight: { background: '#34495e', border: '#1a252f' }
    },
    borderWidth: 2,
    fixed: { x: true, y: true }
  }
];

export const professionalFlowEdges = [
  // Main Agent Flow
  { from: 'user_input', to: 'triage_agent', label: 'Query', color: { color: '#5dade2' }, width: 2, arrows: 'to' },
  { from: 'triage_agent', to: 'planning_agent', label: 'Intent', color: { color: '#5dade2' }, width: 2, arrows: 'to' },
  { from: 'planning_agent', to: 'research_orchestrator_star', label: 'Strategy', color: { color: '#5dade2' }, width: 3, arrows: 'to' },
  { from: 'research_orchestrator_star', to: 'neo4j_graph', label: 'Parallel Queries', color: { color: '#bb8fce' }, width: 3, arrows: 'to' },
  { from: 'neo4j_graph', to: 'synthesis_agent', label: 'Retrieved Data', color: { color: '#58d68d' }, width: 2, arrows: 'to' },
  { from: 'synthesis_agent', to: 'final_response', label: 'Final Answer', color: { color: '#5dade2' }, width: 3, arrows: 'to' },

  // Redis Integration Connections
  { from: 'research_orchestrator_star', to: 'redis_memory', label: 'Cache Check', color: { color: '#ec7063' }, width: 2, arrows: 'to', dashes: [5, 5] },
  { from: 'redis_memory', to: 'synthesis_agent', label: 'Context', color: { color: '#ec7063' }, width: 2, arrows: 'to', dashes: [5, 5] },
  { from: 'synthesis_agent', to: 'redis_memory', label: 'Store Session', color: { color: '#ec7063' }, width: 1, arrows: 'to', dashes: [5, 5] }
];

// =================================================================================
// Corporate Standard Design (v3 - Professional & Clean)
// =================================================================================
export const corporateDesignNodes = [
  // 1. User Input
  {
    id: 'user_input',
    label: '👤\n\nUser Query',
    x: 0,
    y: 300,
    shape: 'box',
    font: { size: 14, color: '#343a40', multi: true, align: 'center' },
    color: { background: '#ffffff', border: '#ced4da', highlight: { background: '#e9ecef', border: '#adb5bd' } },
    borderWidth: 2,
    fixed: { x: true, y: true },
    widthConstraint: { minimum: 120, maximum: 120 },
    heightConstraint: { minimum: 80, maximum: 80 }
  },

  // 2. Triage Agent
  {
    id: 'triage_agent',
    label: '🎯\n\nTriage Agent',
    x: 250,
    y: 300,
    shape: 'ellipse',
    font: { size: 14, color: '#ffffff', multi: true, align: 'center' },
    color: { background: '#007bff', border: '#0056b3', highlight: { background: '#3395ff', border: '#0056b3' } },
    borderWidth: 2,
    fixed: { x: true, y: true },
    widthConstraint: { minimum: 100, maximum: 100 },
  },

  // 3. Planning Agent
  {
    id: 'planning_agent',
    label: '📋\n\nPlanning Agent',
    x: 500,
    y: 300,
    shape: 'ellipse',
    font: { size: 14, color: '#ffffff', multi: true, align: 'center' },
    color: { background: '#007bff', border: '#0056b3', highlight: { background: '#3395ff', border: '#0056b3' } },
    borderWidth: 2,
    fixed: { x: true, y: true },
    widthConstraint: { minimum: 100, maximum: 100 },
  },

  // 4. Research Orchestrator
  {
    id: 'research_orchestrator',
    label: '🚀\n\nResearch Orchestrator\n(Parallel Engine)',
    x: 750,
    y: 300,
    shape: 'box',
    font: { size: 14, color: '#ffffff', multi: true, align: 'center', bold: true },
    color: { background: '#6f42c1', border: '#5a3d92', highlight: { background: '#8a63d2', border: '#5a3d92' } },
    borderWidth: 3,
    fixed: { x: true, y: true },
    widthConstraint: { minimum: 150, maximum: 150 },
    heightConstraint: { minimum: 100, maximum: 100 }
  },

  // 5. Data Layer (Group Box)
  {
    id: 'data_layer',
    label: 'Data & Caching Layer',
    x: 1050,
    y: 220,
    shape: 'box',
    shapeProperties: { borderRadius: 4 },
    font: { size: 16, color: '#6c757d', align: 'center' },
    color: { background: 'rgba(233, 236, 239, 0.5)', border: '#dee2e6' },
    borderWidth: 2,
    fixed: { x: true, y: true },
    widthConstraint: { minimum: 220, maximum: 220 },
    heightConstraint: { minimum: 250, maximum: 250 }
  },
  
  // 5a. Neo4j Knowledge Graph
  {
    id: 'neo4j_graph',
    label: '🗄️\n\nNeo4j Graph',
    x: 1050,
    y: 300,
    shape: 'database',
    font: { size: 14, color: '#ffffff', multi: true, align: 'center' },
    color: { background: '#28a745', border: '#1e7e34', highlight: { background: '#48b461', border: '#1e7e34' } },
    borderWidth: 2,
    fixed: { x: true, y: true },
    widthConstraint: { minimum: 120, maximum: 120 },
  },

  // 5b. Redis Cache
  {
    id: 'redis_memory',
    label: '🔴\n\nRedis Cache',
    x: 1050,
    y: 420,
    shape: 'database',
    font: { size: 14, color: '#ffffff', multi: true, align: 'center' },
    color: { background: '#dc3545', border: '#b02a37', highlight: { background: '#e45665', border: '#b02a37' } },
    borderWidth: 2,
    fixed: { x: true, y: true },
    widthConstraint: { minimum: 120, maximum: 120 },
  },

  // 6. Synthesis Agent
  {
    id: 'synthesis_agent',
    label: '🔄\n\nSynthesis Agent',
    x: 1350,
    y: 300,
    shape: 'ellipse',
    font: { size: 14, color: '#ffffff', multi: true, align: 'center' },
    color: { background: '#007bff', border: '#0056b3', highlight: { background: '#3395ff', border: '#0056b3' } },
    borderWidth: 2,
    fixed: { x: true, y: true },
    widthConstraint: { minimum: 100, maximum: 100 },
  },

  // 7. Final Response
  {
    id: 'final_response',
    label: '📤\n\nFinal Response',
    x: 1600,
    y: 300,
    shape: 'box',
    font: { size: 14, color: '#343a40', multi: true, align: 'center' },
    color: { background: '#ffffff', border: '#ced4da', highlight: { background: '#e9ecef', border: '#adb5bd' } },
    borderWidth: 2,
    fixed: { x: true, y: true },
    widthConstraint: { minimum: 120, maximum: 120 },
    heightConstraint: { minimum: 80, maximum: 80 }
  }
];

export const corporateDesignEdges = [
  { from: 'user_input', to: 'triage_agent', color: { color: '#6c757d' }, width: 2.5, arrows: 'to', smooth: { type: 'cubicBezier' } },
  { from: 'triage_agent', to: 'planning_agent', color: { color: '#6c757d' }, width: 2.5, arrows: 'to', smooth: { type: 'cubicBezier' } },
  { from: 'planning_agent', to: 'research_orchestrator', color: { color: '#6c757d' }, width: 2.5, arrows: 'to', smooth: { type: 'cubicBezier' } },
  { from: 'research_orchestrator', to: 'neo4j_graph', label: 'Data Retrieval', font: { align: 'top' }, color: { color: '#28a745' }, width: 2.5, arrows: 'to', smooth: { type: 'cubicBezier' } },
  { from: 'research_orchestrator', to: 'redis_memory', label: 'Cache Check', font: { align: 'bottom' }, color: { color: '#dc3545' }, width: 2, arrows: 'to', dashes: [10, 5], smooth: { type: 'cubicBezier' } },
  { from: 'neo4j_graph', to: 'synthesis_agent', color: { color: '#6c757d' }, width: 2.5, arrows: 'to', smooth: { type: 'cubicBezier' } },
  { from: 'redis_memory', to: 'synthesis_agent', label: 'Context', font: { align: 'top' }, color: { color: '#dc3545' }, width: 2, arrows: 'to', dashes: [10, 5], smooth: { type: 'cubicBezier' } },
  { from: 'synthesis_agent', to: 'final_response', color: { color: '#6c757d' }, width: 2.5, arrows: 'to', smooth: { type: 'cubicBezier' } }
];

// =================================================================================
// Monochromatic Dark Mode Design (v4 - Professional & High-Contrast)
// =================================================================================
export const monoDarkNodes = [
  // 1. User Input
  {
    id: 'user_input',
    label: '👤\n\nUser Query',
    x: 0,
    y: 300,
    shape: 'box',
    font: { size: 14, color: '#e9ecef', multi: true, align: 'center' },
    color: { background: '#212529', border: '#ced4da', highlight: { background: '#343a40', border: '#ffffff' } },
    borderWidth: 2,
    fixed: { x: true, y: true },
    widthConstraint: { minimum: 120, maximum: 120 },
    heightConstraint: { minimum: 80, maximum: 80 }
  },

  // 2. Triage Agent
  {
    id: 'triage_agent',
    label: '🎯\n\nTriage Agent',
    x: 250,
    y: 300,
    shape: 'ellipse',
    font: { size: 14, color: '#e9ecef', multi: true, align: 'center' },
    color: { background: '#212529', border: '#007bff', highlight: { background: '#343a40', border: '#3395ff' } },
    borderWidth: 3,
    fixed: { x: true, y: true },
    widthConstraint: { minimum: 100, maximum: 100 },
  },

  // 3. Planning Agent
  {
    id: 'planning_agent',
    label: '📋\n\nPlanning Agent',
    x: 500,
    y: 300,
    shape: 'ellipse',
    font: { size: 14, color: '#e9ecef', multi: true, align: 'center' },
    color: { background: '#212529', border: '#007bff', highlight: { background: '#343a40', border: '#3395ff' } },
    borderWidth: 3,
    fixed: { x: true, y: true },
    widthConstraint: { minimum: 100, maximum: 100 },
  },

  // 4. Research Orchestrator
  {
    id: 'research_orchestrator',
    label: '🚀\n\nResearch Orchestrator\n(Parallel Engine)',
    x: 750,
    y: 300,
    shape: 'box',
    font: { size: 14, color: '#e9ecef', multi: true, align: 'center', bold: true },
    color: { background: '#212529', border: '#6f42c1', highlight: { background: '#343a40', border: '#8a63d2' } },
    borderWidth: 4,
    fixed: { x: true, y: true },
    widthConstraint: { minimum: 150, maximum: 150 },
    heightConstraint: { minimum: 100, maximum: 100 }
  },
  
  // 5. Neo4j Knowledge Graph
  {
    id: 'neo4j_graph',
    label: '🗄️\n\nNeo4j Graph',
    x: 1050,
    y: 220,
    shape: 'database',
    font: { size: 14, color: '#e9ecef', multi: true, align: 'center' },
    color: { background: '#212529', border: '#28a745', highlight: { background: '#343a40', border: '#48b461' } },
    borderWidth: 3,
    fixed: { x: true, y: true },
    widthConstraint: { minimum: 120, maximum: 120 },
  },

  // 6. Redis Cache
  {
    id: 'redis_memory',
    label: '🔴\n\nRedis Cache',
    x: 1050,
    y: 380,
    shape: 'database',
    font: { size: 14, color: '#e9ecef', multi: true, align: 'center' },
    color: { background: '#212529', border: '#dc3545', highlight: { background: '#343a40', border: '#e45665' } },
    borderWidth: 3,
    fixed: { x: true, y: true },
    widthConstraint: { minimum: 120, maximum: 120 },
  },

  // 7. Synthesis Agent
  {
    id: 'synthesis_agent',
    label: '🔄\n\nSynthesis Agent',
    x: 1350,
    y: 300,
    shape: 'ellipse',
    font: { size: 14, color: '#e9ecef', multi: true, align: 'center' },
    color: { background: '#212529', border: '#007bff', highlight: { background: '#343a40', border: '#3395ff' } },
    borderWidth: 3,
    fixed: { x: true, y: true },
    widthConstraint: { minimum: 100, maximum: 100 },
  },

  // 8. Final Response
  {
    id: 'final_response',
    label: '📤\n\nFinal Response',
    x: 1600,
    y: 300,
    shape: 'box',
    font: { size: 14, color: '#e9ecef', multi: true, align: 'center' },
    color: { background: '#212529', border: '#ced4da', highlight: { background: '#343a40', border: '#ffffff' } },
    borderWidth: 2,
    fixed: { x: true, y: true },
    widthConstraint: { minimum: 120, maximum: 120 },
    heightConstraint: { minimum: 80, maximum: 80 }
  }
];

export const monoDarkEdges = [
  { from: 'user_input', to: 'triage_agent', color: { color: '#6c757d' }, width: 2.5, arrows: 'to', smooth: { type: 'cubicBezier' } },
  { from: 'triage_agent', to: 'planning_agent', color: { color: '#6c757d' }, width: 2.5, arrows: 'to', smooth: { type: 'cubicBezier' } },
  { from: 'planning_agent', to: 'research_orchestrator', color: { color: '#6c757d' }, width: 2.5, arrows: 'to', smooth: { type: 'cubicBezier' } },
  { from: 'research_orchestrator', to: 'neo4j_graph', label: 'Data Retrieval', font: { color: '#e9ecef', strokeColor: '#212529', align: 'top' }, color: { color: '#28a745' }, width: 2.5, arrows: 'to', smooth: { type: 'cubicBezier' } },
  { from: 'research_orchestrator', to: 'redis_memory', label: 'Cache Check', font: { color: '#e9ecef', strokeColor: '#212529', align: 'bottom' }, color: { color: '#dc3545' }, width: 2, arrows: 'to', dashes: [10, 5], smooth: { type: 'cubicBezier' } },
  { from: 'neo4j_graph', to: 'synthesis_agent', color: { color: '#6c757d' }, width: 2.5, arrows: 'to', smooth: { type: 'cubicBezier' } },
  { from: 'redis_memory', to: 'synthesis_agent', label: 'Context', font: { color: '#e9ecef', strokeColor: '#212529', align: 'top' }, color: { color: '#dc3545' }, width: 2, arrows: 'to', dashes: [10, 5], smooth: { type: 'cubicBezier' } },
  { from: 'synthesis_agent', to: 'final_response', color: { color: '#6c757d' }, width: 2.5, arrows: 'to', smooth: { type: 'cubicBezier' } }
];