export const userFlowNodes = [
  // User Input
  { id: 'user_query', label: 'User Query', x: 0, y: -800, fixed: true, shape: 'ellipse', group: 'input' },

  // Stage 1: Triage & Early Exit
  { id: 'triage_agent', label: 'Triage Agent', x: 0, y: -650, fixed: true, shape: 'box', group: 'agent' },
  { id: 'validate_cache', label: 'Validate Cached Answer', x: 0, y: -550, fixed: true, shape: 'box', group: 'agent' },
  { id: 'is_valid_cache', label: 'Is Valid?\n(Score >= 7)', x: 0, y: -400, fixed: true, shape: 'diamond', group: 'decision' },
  { id: 'final_answer_redis', label: 'Final Answer from Redis', x: 200, y: -300, fixed: true, shape: 'box', group: 'output' },
  { id: 'classify_query', label: 'Classify Query', x: -200, y: -300, fixed: true, shape: 'box', group: 'agent' },
  { id: 'route_by_classification', label: 'Route by Classification', x: -200, y: -150, fixed: true, shape: 'diamond', group: 'decision' },
  { id: 'redis_cache', label: 'Redis Cache & Sessions', x: 400, y: -600, fixed: true, shape: 'database', group: 'database' },

  // Contextual Path
  { id: 'contextual_agent', label: 'Contextual Answering Agent', x: -600, y: -50, fixed: true, shape: 'box', group: 'agent' },
  { id: 'answerable_from_context', label: 'Answerable from Context?', x: -600, y: 50, fixed: true, shape: 'diamond', group: 'decision' },

  // Complex Research Path
  { id: 'planning_agent', label: 'Planning Agent', x: -400, y: 50, fixed: true, shape: 'box', group: 'agent' },
  { id: 'hyde_agent', label: 'Hyde Agent', x: -400, y: 150, fixed: true, shape: 'box', group: 'agent' },
  { id: 'start_parallel_research', label: 'Start Parallel Research', x: -400, y: 250, fixed: true, shape: 'box', group: 'agent' },
  { id: 'for_each_subquery', label: 'For Each Subquery', x: -400, y: 350, fixed: true, shape: 'diamond', group: 'decision' },
  { id: 'select_strategy', label: 'Select Strategy', x: -400, y: 450, fixed: true, shape: 'box', group: 'agent' },
  
  // Research Orchestrator
  { id: 'initial_strategy', label: 'Initial Strategy', x: -800, y: 600, fixed: true, shape: 'box', group: 'agent' },
  { id: 'sufficient_answer_1', label: 'Sufficient Answer?', x: -800, y: 700, fixed: true, shape: 'diamond', group: 'decision' },
  { id: 'vector_search_1', label: 'Vector Search', x: -600, y: 700, fixed: true, shape: 'box', group: 'agent' },
  { id: 'sufficient_answer_2', label: 'Sufficient Answer?', x: -600, y: 800, fixed: true, shape: 'diamond', group: 'decision' },
  { id: 'keyword_search_1', label: 'Keyword Search', x: -400, y: 800, fixed: true, shape: 'box', group: 'agent' },
  { id: 'sufficient_answer_3', label: 'Sufficient Answer?', x: -400, y: 900, fixed: true, shape: 'diamond', group: 'decision' },
  { id: 'web_search', label: 'Web Search Tavily', x: -200, y: 900, fixed: true, shape: 'box', group: 'agent' },
  { id: 'sufficient_answer_4', label: 'Sufficient Answer?', x: -200, y: 1000, fixed: true, shape: 'diamond', group: 'decision' },
  { id: 'reranker', label: 'Reranker (Cohere Rankers)', x: -800, y: 1100, fixed: true, shape: 'box', group: 'agent' },
  { id: 'validate_context', label: 'Validate Context', x: -600, y: 1100, fixed: true, shape: 'box', group: 'agent' },
  { id: 'is_context_relevant', label: 'Is the context Relevant?', x: -600, y: 1200, fixed: true, shape: 'diamond', group: 'decision' },
  { id: 'aggregate_results', label: 'Aggregate All Results', x: -600, y: 1400, fixed: true, shape: 'box', group: 'agent' },
  { id: 'super_targeted_retrieval', label: 'Super Targeted Retrieval (Hierarchical Retrieval)', x: 0, y: 1100, fixed: true, shape: 'box', group: 'agent' },
  { id: 'neo4j_expansion', label: 'Neo4j Graph Expansion', x: 200, y: 750, fixed: true, shape: 'database', group: 'database' },

  // Synthesis Stage
  { id: 'synthesis_agent', label: 'Synthesis Agent', x: 800, y: -300, fixed: true, shape: 'box', group: 'agent' },
  { id: 'calculation_needed', label: 'Calculation Needed?', x: 800, y: -200, fixed: true, shape: 'diamond', group: 'decision' },
  { id: 'enhanced_calculation', label: 'Enhanced Calculation', x: 700, y: -100, fixed: true, shape: 'box', group: 'agent' },
  { id: 'standard_synthesis', label: 'Standard Synthesis', x: 900, y: -100, fixed: true, shape: 'box', group: 'agent' },
  { id: 'is_answer_high_quality', label: 'Is Answer High Quality?', x: 800, y: 0, fixed: true, shape: 'diamond', group: 'decision' },
  { id: 'memory_agent_update', label: 'Memory Agent (Update Conversation)', x: 700, y: 100, fixed: true, shape: 'box', group: 'agent' },
  { id: 'prompt_caching', label: 'Prompt Caching', x: 900, y: 100, fixed: true, shape: 'box', group: 'agent' },
  { id: 'final_answer', label: 'Final Answer', x: 800, y: 250, fixed: true, shape: 'box', group: 'output' },
];

export const userFlowEdges = [
  // Stage 1
  { from: 'user_query', to: 'triage_agent', id: 'e1' },
  { from: 'triage_agent', to: 'validate_cache', id: 'e2' },
  { from: 'validate_cache', to: 'is_valid_cache', id: 'e3' },
  { from: 'is_valid_cache', to: 'final_answer_redis', label: 'Yes', id: 'e4' },
  { from: 'is_valid_cache', to: 'classify_query', label: 'No', id: 'e5' },
  { from: 'classify_query', to: 'route_by_classification', id: 'e6' },
  { from: 'triage_agent', to: 'redis_cache', label: 'Check Cache for queries', id: 'e7' },
  { from: 'validate_cache', to: 'redis_cache', label: 'Cache Hit', id: 'e8', dashes: true },
  { from: 'route_by_classification', to: 'redis_cache', label: 'Cache Miss', id: 'e9', dashes: true },
  
  // Routing
  { from: 'route_by_classification', to: 'contextual_agent', label: 'Contextual Clarification', id: 'e10' },
  { from: 'route_by_classification', to: 'planning_agent', label: 'Complex Research', id: 'e11' },

  // Contextual Flow
  { from: 'contextual_agent', to: 'answerable_from_context', id: 'e12' },
  { from: 'answerable_from_context', to: 'synthesis_agent', label: 'Yes', id: 'e13' },
  { from: 'answerable_from_context', to: 'planning_agent', label: 'No, Need More Info', id: 'e14' },
  
  // Planning Flow
  { from: 'planning_agent', to: 'hyde_agent', id: 'e15' },
  { from: 'hyde_agent', to: 'start_parallel_research', id: 'e16' },
  { from: 'start_parallel_research', to: 'for_each_subquery', id: 'e17' },
  { from: 'for_each_subquery', to: 'select_strategy', id: 'e18' },
  { from: 'select_strategy', to: 'initial_strategy', id: 'e19' },

  // Research Orchestrator Flow
  { from: 'initial_strategy', to: 'sufficient_answer_1', id: 'e20' },
  { from: 'sufficient_answer_1', to: 'reranker', label: 'Yes', id: 'e21' },
  { from: 'sufficient_answer_1', to: 'vector_search_1', label: 'No', id: 'e22' },
  { from: 'vector_search_1', to: 'sufficient_answer_2', id: 'e23' },
  { from: 'sufficient_answer_2', to: 'reranker', label: 'Yes', id: 'e24' },
  { from: 'sufficient_answer_2', to: 'keyword_search_1', label: 'No', id: 'e25' },
  { from: 'keyword_search_1', to: 'sufficient_answer_3', id: 'e26' },
  { from: 'sufficient_answer_3', to: 'reranker', label: 'Yes', id: 'e27' },
  { from: 'sufficient_answer_3', to: 'web_search', label: 'No', id: 'e28' },
  { from: 'web_search', to: 'sufficient_answer_4', id: 'e29' },
  { from: 'sufficient_answer_4', to: 'reranker', label: 'Yes', id: 'e30' },
  { from: 'sufficient_answer_4', to: 'super_targeted_retrieval', label: 'No', id: 'e31' },
  { from: 'reranker', to: 'validate_context', id: 'e32' },
  { from: 'validate_context', to: 'is_context_relevant', id: 'e33' },
  { from: 'is_context_relevant', to: 'aggregate_results', label: 'Yes', id: 'e34' },
  { from: 'is_context_relevant', to: 'initial_strategy', label: 'No', id: 'e35' }, // Loop back
  { from: 'aggregate_results', to: 'synthesis_agent', id: 'e36' },
  { from: 'vector_search_1', to: 'neo4j_expansion', id: 'e37' },
  { from: 'keyword_search_1', to: 'neo4j_expansion', id: 'e38' },
  
  // Synthesis Flow
  { from: 'synthesis_agent', to: 'calculation_needed', id: 'e39' },
  { from: 'calculation_needed', to: 'enhanced_calculation', label: 'Yes', id: 'e40' },
  { from: 'calculation_needed', to: 'standard_synthesis', label: 'No', id: 'e41' },
  { from: 'enhanced_calculation', to: 'is_answer_high_quality', id: 'e42' },
  { from: 'standard_synthesis', to: 'is_answer_high_quality', id: 'e43' },
  { from: 'is_answer_high_quality', to: 'prompt_caching', label: 'Yes', id: 'e44' },
  { from: 'is_answer_high_quality', to: 'memory_agent_update', label: 'No', id: 'e45' },
  { from: 'prompt_caching', to: 'final_answer', id: 'e46' },
  { from: 'memory_agent_update', to: 'final_answer', id: 'e47' },
];

export const clusterData = {
    'stage1_cluster': {
        label: 'Stage 1: Triage & Early Exit',
        nodes: ['triage_agent', 'validate_cache', 'is_valid_cache', 'final_answer_redis', 'classify_query', 'route_by_classification']
    },
    'research_orchestrator_cluster': {
        label: 'Research Orchestrator Agent',
        nodes: ['initial_strategy', 'sufficient_answer_1', 'vector_search_1', 'sufficient_answer_2', 'keyword_search_1', 'sufficient_answer_3', 'web_search', 'sufficient_answer_4', 'reranker', 'validate_context', 'is_context_relevant', 'aggregate_results', 'super_targeted_retrieval', 'neo4j_expansion']
    },
    'synthesis_cluster': {
        label: 'Synthesis Agent',
        nodes: ['synthesis_agent', 'calculation_needed', 'enhanced_calculation', 'standard_synthesis', 'is_answer_high_quality', 'memory_agent_update', 'prompt_caching', 'final_answer']
    }
}; 