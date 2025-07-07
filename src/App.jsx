import React, { useState, useEffect, useRef, useMemo, useCallback, memo } from 'react';
import { AnimatePresence, motion, useAnimation } from 'framer-motion';
import { ChevronDown, Send, LoaderCircle, Database, Cog, CheckCircle2, XCircle, Search, User, Atom, MessagesSquare, BrainCircuit, Share2, GitBranch, Menu, AlertTriangle, Lightbulb, X, FileCheck, GitCompareArrows, Building2, Undo, Redo } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ReactFlow, MiniMap, Controls, Background, ReactFlowProvider, Handle, Position, NodeResizer, applyNodeChanges, applyEdgeChanges, addEdge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import ELK from 'elkjs/lib/elk.bundled.js';
import useUndo from 'use-undo';


const icons = {
    FileCheck,
    GitCompareArrows,
    Building2,
};

// --- MOCK DATA & HOOKS (Simulating a real backend) ---

const exampleQueries = [
  {
    category: 'Code Compliance',
    icon: FileCheck,
    queries: [
      'What are the fire safety requirements for a new single-family home in Fairfax County?',
      'Is a permit required to build a 150 sq ft deck attached to a house in Richmond?',
      'List the key differences in electrical code for commercial vs. residential buildings in Virginia.',
    ],
  },
  {
    category: 'Comparative Analysis',
    icon: GitCompareArrows,
    queries: [
      'Compare the maximum building height regulations in Arlington County versus Loudoun County.',
      'What are the differences in setback requirements for sheds in Virginia Beach and Chesapeake?',
      'Contrast the energy efficiency code requirements for windows in Northern Virginia vs. the rest of the state.',
    ],
  },
  {
    category: 'Scenario-Based',
    icon: Building2,
    queries: [
      'I want to finish my basement in a 1980s house in Alexandria. What are the egress window requirements I need to be aware of?',
      'Outline the steps and required inspections for converting a garage into a living space in Norfolk.',
      'My client wants to install a solar panel system on their roof in Roanoke. What are the structural load considerations I should review?',
    ],
  },
];

// A more realistic mock of the Vercel AI SDK's useChat hook
const useChat = ({ onFinish, onFirstSubmit }) => {
  const [messages, setMessages] = useState([
    { id: '1', role: 'assistant', content: "Welcome. I am an AI specializing in Virginia's building code regulations. Ask me anything from permit requirements to complex compliance scenarios.", logs: [], thinkingTime: null }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const submitQuery = async (queryText) => {
    if (!queryText.trim() || isLoading) return;

    const startTime = Date.now();

    if (messages.length <= 1) {
        onFirstSubmit?.();
    }

    const userMessage = { id: Date.now().toString(), role: 'user', content: queryText };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    const assistantMessageId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, { id: assistantMessageId, role: 'assistant', content: '', logs: [], thinkingTime: null }]);
    
    try {
      const response = await fetch('https://agenticrag-production.up.railway.app/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_query: queryText,
          thread_id: 'test-session-010',
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Backend error: ${response.status} - ${errorText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const eventMessages = buffer.split('\n\n');
        buffer = eventMessages.pop() || '';

        for (const message of eventMessages) {
          if (!message) continue;

          const eventTypeMatch = message.match(/event: (.*)/);
          const eventType = eventTypeMatch ? eventTypeMatch[1] : 'message';
          
          const dataMatch = message.match(/data: (.*)/s);
          if (!dataMatch) continue;

          const jsonData = dataMatch[1];
          
          try {
            const data = JSON.parse(jsonData);

            if (eventType === 'log') {
              setMessages(prev =>
                prev.map(msg =>
                  msg.id === assistantMessageId
                    ? { ...msg, logs: [...(msg.logs || []), { ...data, id: Date.now() + Math.random() }] }
                    : msg
                )
              );
            } else if (eventType === 'result') {
              const endTime = Date.now();
              const duration = (endTime - startTime) / 1000;
              setMessages(prev =>
                prev.map(msg =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: data.result, thinkingTime: duration }
                    : msg
                )
              );
              if (onFinish) onFinish({ id: assistantMessageId, role: 'assistant', content: data.result });
            }
          } catch (e) {
            console.error("Failed to parse SSE data chunk:", jsonData, e);
          }
        }
      }
    } catch (error) {
      console.error('Error fetching from backend:', error);
       setMessages(prev =>
        prev.map(msg =>
          msg.id === assistantMessageId
            ? { ...msg, content: `An error occurred while contacting the backend: ${error.message}` }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    submitQuery(input);
    setInput('');
  };
  
  const handleInputChange = (e) => setInput(e.target.value);

  return { messages, input, handleInputChange, handleSubmit, isLoading, submitQuery };
};

// --- KNOWLEDGE GRAPH DATA ---
const initialNodes = [
  { id: 'q_perf', type: 'inputNode', position: { x: 400, y: 50 }, data: { label: 'Q4 vs Q3 Performance' } },
  { id: 'q4_sales', type: 'documentNode', position: { x: 150, y: 200 }, data: { label: 'Q4 Sales Report', source: 'sales_q4_final.pdf' } },
  { id: 'q3_sales', type: 'documentNode', position: { x: 650, y: 200 }, data: { label: 'Q3 Sales Report', source: 'sales_q3_final.pdf' } },
  { id: 'new_prod', type: 'entityNode', position: { x: 150, y: 350 }, data: { label: 'Project Titan Launch' } },
  { id: 'analysis', type: 'conceptNode', position: { x: 400, y: 350 }, data: { label: 'Sales Growth Analysis' } },
  { id: 'report', type: 'outputNode', position: { x: 400, y: 500 }, data: { label: 'Synthesized Answer' } },
];

const initialEdges = [
  { id: 'e_q_q4', source: 'q_perf', target: 'q4_sales' },
  { id: 'e_q_q3', source: 'q_perf', target: 'q3_sales' },
  { id: 'e_q4_prod', source: 'q4_sales', target: 'new_prod' },
  { id: 'e_q4_analysis', source: 'q4_sales', target: 'analysis' },
  { id: 'e_q3_analysis', source: 'q3_sales', target: 'analysis' },
  { id: 'e_analysis_report', source: 'analysis', target: 'report' },
];


// --- UI HELPER & THEME COMPONENTS ---

const StatusIndicator = ({ level }) => {
    const statusMap = {
        INFO: { icon: <CheckCircle2 className="w-4 h-4 text-green-400" /> },
        ERROR: { icon: <XCircle className="w-4 h-4 text-red-400" /> },
    };
    const current = statusMap[level];
    if (!current) return null;
    return <div className="flex items-center gap-2">{current.icon}</div>;
};

const LogIcon = ({ level }) => {
    const iconMap = {
        INFO: <Cog className="w-5 h-5 text-gray-400" />,
        ERROR: <XCircle className="w-5 h-5 text-red-400" />,
        WARNING: <AlertTriangle className="w-5 h-5 text-amber-400" />,
    };
    return iconMap[level] || <Cog className="w-5 h-5 text-gray-500" />;
};

const LogEntry = ({ log, isLast }) => {
    const { level, message } = log;
    const titleMatch = message.match(/^--- \\[(.*?)\\]/) || message.match(/^(🧠 [^:]*)/);
    const title = titleMatch ? titleMatch[1].trim() : level;
    const body = message;
    
    return (
      <motion.div
        layout
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, x: -10 }}
        transition={{ duration: 0.3 }}
        className="relative pl-8"
      >
        <div className="absolute left-0 top-1.5 flex items-center justify-center w-6 h-6 bg-gray-800 rounded-full border border-gray-700">
          <LogIcon level={level} />
        </div>
        {!isLast && (
           <div className="absolute left-3 top-8 h-full border-l-2 border-dashed border-gray-700"></div>
        )}
        
        <div className="flex items-start justify-between p-2 rounded-lg ml-4">
            <div className="flex-1">
                <p className="font-semibold text-gray-200 capitalize">{title.replace(/_/g, ' ')}</p>
                <p className="text-sm text-gray-400 mt-1 whitespace-pre-wrap">{body}</p>
            </div>
            <StatusIndicator level={level} />
        </div>
      </motion.div>
    );
};

// --- KNOWLEDGE GRAPH NODE COMPONENTS ---
const NodeWrapper = ({ children, className }) => (
    <motion.div 
        className={`w-52 h-24 p-3 rounded-lg border-2 flex flex-col justify-center shadow-lg backdrop-blur-md transition-all duration-300 hover:shadow-2xl ${className}`}
        whileHover={{ scale: 1.05, y: -5 }}
    >
        {children}
    </motion.div>
);
const knowledgeGraphNodeTypes = {
    inputNode: ({ data }) => <NodeWrapper className="bg-blue-900/30 border-blue-500 hover:shadow-blue-500/20"><p className="font-bold text-blue-200">{data.label}</p></NodeWrapper>,
    documentNode: ({ data }) => <NodeWrapper className="bg-purple-900/30 border-purple-500 hover:shadow-purple-500/20"><p className="font-semibold text-purple-200">{data.label}</p><p className="text-xs text-purple-400 truncate">{data.source}</p></NodeWrapper>,
    entityNode: ({ data }) => <NodeWrapper className="bg-teal-900/30 border-teal-500 hover:shadow-teal-500/20"><p className="font-semibold text-teal-200">{data.label}</p><p className="text-xs text-teal-400">Entity</p></NodeWrapper>,
    conceptNode: ({ data }) => <NodeWrapper className="bg-amber-900/30 border-amber-500 hover:shadow-amber-500/20"><p className="font-semibold text-amber-200">{data.label}</p><p className="text-xs text-amber-400">Concept</p></NodeWrapper>,
    outputNode: ({ data }) => <NodeWrapper className="bg-green-900/30 border-green-500 hover:shadow-green-500/20"><p className="font-bold text-green-200">{data.label}</p></NodeWrapper>,
};

const knowledgeGraphEdgeOptions = {
    type: 'smoothstep',
    style: { stroke: '#4A5568', strokeWidth: 2 },
    markerEnd: { type: 'arrowclosed', color: '#4A5568' },
};


// --- TABS / MAIN VIEW COMPONENTS ---

const ChatTab = () => {
    const chatContainerRef = useRef(null);
    const [isQueryLibraryOpen, setIsQueryLibraryOpen] = useState(false);
    const lightbulbControls = useAnimation();
    const [showInactivityTooltip, setShowInactivityTooltip] = useState(false);
    const inactivityTimer = useRef(null);
    const [queryCategories, setQueryCategories] = useState([]);
    const [initialPrompts, setInitialPrompts] = useState([]);

    const triggerAnimation = useCallback(() => {
        const sequence = async () => {
            await lightbulbControls.start({
                scale: [1, 1.3, 0.8, 1.1, 1],
                rotate: [0, -10, 10, -10, 0],
                transition: { duration: 0.6, ease: "easeInOut" },
                filter: [
                    'drop-shadow(0 0 0px rgba(56, 189, 248, 0))',
                    'drop-shadow(0 0 8px rgba(56, 189, 248, 0.7))',
                    'drop-shadow(0 0 0px rgba(56, 189, 248, 0))',
                ]
            });
        };
        sequence();
    }, [lightbulbControls]);

    const { messages, input, handleInputChange, handleSubmit, isLoading, submitQuery } = useChat({
        onFinish: () => {},
        onFirstSubmit: triggerAnimation
    });

    useEffect(() => {
        const fetchQueries = async () => {
            try {
                const response = await fetch('/queries.json');
                const data = await response.json();
                setQueryCategories(data);

                const allQueries = data.flatMap(category => 
                    category.queries.map(query => ({
                        query,
                        icon: category.icon,
                    }))
                );
                
                const shuffled = allQueries.sort(() => 0.5 - Math.random());
                setInitialPrompts(shuffled.slice(0, 3));

            } catch (error) {
                console.error("Failed to fetch queries:", error);
            }
        };
        fetchQueries();
    }, []);

    const isChatEmpty = messages.length <= 1;

    const resetInactivityTimer = useCallback(() => {
        setShowInactivityTooltip(false);
        clearTimeout(inactivityTimer.current);
        if (!isQueryLibraryOpen && !isChatEmpty) {
            inactivityTimer.current = setTimeout(() => {
                setShowInactivityTooltip(true);
            }, 5000); // 5 seconds
        }
    }, [isQueryLibraryOpen, isChatEmpty]);

    useEffect(() => {
        resetInactivityTimer();
        
        window.addEventListener('mousemove', resetInactivityTimer);
        window.addEventListener('keydown', resetInactivityTimer);
        window.addEventListener('click', resetInactivityTimer);

        return () => {
            clearTimeout(inactivityTimer.current);
            window.removeEventListener('mousemove', resetInactivityTimer);
            window.removeEventListener('keydown', resetInactivityTimer);
            window.removeEventListener('click', resetInactivityTimer);
        };
    }, [resetInactivityTimer]);

    useEffect(() => {
        chatContainerRef.current?.scrollTo({ top: chatContainerRef.current.scrollHeight, behavior: 'smooth' });
    }, [messages]);
    
    const handlePromptClick = (query) => {
        submitQuery(query);
    };

    return (
        <div className="flex flex-col h-full">
             <AnimatePresence>
                {isQueryLibraryOpen && (
                    <QueryLibraryModal
                        categories={queryCategories}
                        onClose={() => setIsQueryLibraryOpen(false)}
                        onSelectQuery={(query) => {
                            handlePromptClick(query);
                            setIsQueryLibraryOpen(false);
                        }}
                    />
                )}
            </AnimatePresence>

            <div className="flex flex-col flex-1 bg-gray-900/50 backdrop-blur-sm rounded-xl border border-gray-700/50 m-4 overflow-hidden">
                <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-6 space-y-6 fancy-scrollbar">
                    <AnimatePresence initial={false}>
                        {messages.map(m => (
                            <ChatMessage key={m.id} message={m} />
                        ))}
                    </AnimatePresence>
                    
                    {isChatEmpty && <InitialPrompts prompts={initialPrompts} onPromptClick={handlePromptClick} />}
                </div>
                <div className="p-4 border-t border-gray-700/50 bg-gray-900/20">
                    <form onSubmit={handleSubmit} className="relative">
                        <div className="relative flex items-center">
                             <AnimatePresence>
                                {showInactivityTooltip && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10, x: -10 }}
                                        animate={{ opacity: 1, y: 0, x: -10 }}
                                        exit={{ opacity: 0, y: 10, x: -10 }}
                                        transition={{ duration: 0.2 }}
                                        className="absolute bottom-full left-0 mb-3 w-max px-3 py-1.5 bg-gray-700/90 text-white text-xs rounded-md shadow-lg pointer-events-none"
                                    >
                                        Example queries to test here
                                    </motion.div>
                                )}
                            </AnimatePresence>
                             <motion.button
                                type="button"
                                title="Explore example queries"
                                onClick={() => setIsQueryLibraryOpen(true)}
                                className="absolute left-3 text-cyan-400 hover:text-cyan-300 transition-colors"
                                animate={lightbulbControls}
                            >
                                <Lightbulb size={20} />
                            </motion.button>
                            <input
                                className="w-full bg-gray-800/80 border border-gray-600/50 rounded-lg py-3 pl-12 pr-14 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 outline-none transition-all"
                                value={input}
                                onChange={handleInputChange}
                                placeholder="Ask a complex question..."
                                disabled={isLoading}
                            />
                            <button type="submit" className="absolute inset-y-0 right-0 flex items-center justify-center w-12 text-gray-400 hover:text-white disabled:text-gray-600 disabled:cursor-not-allowed transition-colors" disabled={isLoading}>
                                {isLoading ? <LoaderCircle size={20} className="animate-spin" /> : <Send size={20} />}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
            <footer className="text-center p-4 text-xs text-gray-500">
                <p>This AI provides guidance, not professional advice. Always consult a licensed expert for critical applications.</p>
            </footer>
        </div>
    );
};

const KnowledgeGraphTab = () => {
    const [nodes, setNodes] = useState(initialNodes);
    const [edges, setEdges] = useState(initialEdges);
    const [selectedNode, setSelectedNode] = useState(null);
    const [isPanelOpen, setIsPanelOpen] = useState(true);

    const onNodeClick = (event, node) => {
        // Simple properties to show, excluding embedding
        const propertiesToShow = Object.entries(node.data.properties || {}).reduce((acc, [key, value]) => {
            if (key !== 'embedding') {
                acc[key] = value;
            }
            return acc;
        }, {});
        setSelectedNode({ ...node.data, properties: propertiesToShow });
    };

    const handleSearch = (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        const chapter = formData.get('chapter');
        console.log('Searching for chapter/subsection:', chapter);
        // Here you would typically fetch data for the new graph
    };

    return (
        <div className="h-full flex bg-gray-900/50 backdrop-blur-sm rounded-xl border border-gray-700/50 m-4 p-4 gap-4">
            <AnimatePresence>
                {isPanelOpen && (
                    <motion.div
                        initial={{ width: 0, opacity: 0, x: -50 }}
                        animate={{ width: 300, opacity: 1, x: 0 }}
                        exit={{ width: 0, opacity: 0, x: -50 }}
                        transition={{ duration: 0.3 }}
                        className="flex flex-col bg-gray-800/60 p-4 rounded-lg border border-gray-700 overflow-hidden"
                    >
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-lg font-bold">Query Graph</h2>
                            <button onClick={() => setIsPanelOpen(false)} className="text-gray-400 hover:text-white">
                                <X size={20} />
                            </button>
                        </div>
                        <form onSubmit={handleSearch} className="flex flex-col gap-4">
                            <input
                                type="text"
                                name="chapter"
                                placeholder="Chapter/Subsection No."
                                className="bg-gray-700/80 border border-gray-600 rounded-md p-2 text-sm focus:ring-2 focus:ring-cyan-500 outline-none"
                            />
                            <button type="submit" className="bg-cyan-600 hover:bg-cyan-700 text-white font-bold py-2 px-4 rounded-md transition-colors">
                                <Search className="w-4 h-4 mr-2 inline-block" />
                                Retrieve Graph
                            </button>
                        </form>
                    </motion.div>
                )}
            </AnimatePresence>

            <div className="flex-1 min-h-0 relative">
                {!isPanelOpen && (
                     <motion.button
                        initial={{ x: -60 }}
                        animate={{ x: 0 }}
                        onClick={() => setIsPanelOpen(true)}
                        className="absolute top-4 left-4 z-10 p-2 bg-gray-800/80 rounded-md border border-gray-700 hover:bg-gray-700"
                        title="Open Query Panel"
                    >
                        <Menu size={20} />
                    </motion.button>
                )}
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodeClick={onNodeClick}
                    nodeTypes={knowledgeGraphNodeTypes}
                    defaultEdgeOptions={knowledgeGraphEdgeOptions}
                    fitView
                 >
                    <Background variant="dots" gap={20} size={1} />
                    <Controls />
                    <MiniMap nodeColor={n => {
                        if (n.type === 'inputNode') return '#2563eb';
                        if (n.type === 'outputNode') return '#16a34a';
                        return '#6b7280';
                    }} />
                 </ReactFlow>
            </div>
            
            <AnimatePresence>
                {selectedNode && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                        onClick={() => setSelectedNode(null)}
                    >
                        <motion.div
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            exit={{ y: 20, opacity: 0 }}
                            className="bg-gray-800 border border-cyan-500/30 rounded-lg shadow-2xl w-full max-w-md p-6 relative"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <button onClick={() => setSelectedNode(null)} className="absolute top-4 right-4 text-gray-400 hover:text-white">
                                <X size={20} />
                            </button>
                            <h3 className="text-xl font-bold text-cyan-400 mb-4">{selectedNode.label}</h3>
                            <div className="space-y-2 text-sm max-h-[60vh] overflow-y-auto fancy-scrollbar pr-2">
                                {selectedNode.properties && Object.entries(selectedNode.properties).map(([key, value]) => (
                                    <div key={key}>
                                        <p className="font-semibold text-gray-300 capitalize">{key.replace(/_/g, ' ')}:</p>
                                        <p className="text-gray-400 bg-gray-900/50 p-2 rounded-md whitespace-pre-wrap">
                                            {typeof value === 'object' ? JSON.stringify(value, null, 2) : value}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};


const elk = new ELK();

const elkOptions = {
    'elk.algorithm': 'layered',
    'elk.direction': 'DOWN',
    'elk.layered.spacing.nodeNodeBetweenLayers': '50',
    'elk.spacing.nodeNode': '50',
    'elk.edgeRouting': 'ORTHOGONAL',
};

// This function will now only be used for laying out the children of a group
const getLayoutedElements = (nodes, edges, options = {}) => {
  const graph = {
    id: 'root',
    layoutOptions: options,
    children: nodes.map(n => ({ ...n, width: n.width || 150, height: n.height || 50 })),
    edges: edges,
  };

  return elk
    .layout(graph)
    .then((layoutedGraph) => ({
      nodes: layoutedGraph.children.map((node) => ({
        ...node,
        position: { x: node.x, y: node.y },
      })),
      edges: layoutedGraph.edges || [],
    }))
    .catch((e) => {
        console.error("ELK layout error:", e);
        return { nodes: [], edges: [] };
    });
};

const nodeExplanations = {
    start: { title: 'User Query', text: "The entry point of the entire workflow. The system is initiated when a user submits a query." },
    triage: { title: 'Triage Agent', text: "Acts as the gatekeeper, performing a rapid initial assessment to determine the most efficient path forward." },
    planning: { title: 'Planning Agent', text: "For complex queries, this agent creates a detailed research plan, breaking down the query and generating hypothetical documents (HyDE)." },
    research: { title: 'Research Orchestrator', text: "Executes the research plan in parallel, using a multi-tier fallback system (Vector -> Graph -> Keyword -> Web) and caches results." },
    validation: { title: 'Thinking Validation Agent', text: "A quality control checkpoint. It assesses if research is sufficient and detects if mathematical calculations are required." },
    synthesis: { title: 'Synthesis Agent', text: "Combines all gathered information into a single, coherent, and structured response, complete with citations and a confidence score." },
    memory: { title: 'Memory Agent', text: "Responsible for the system's long-term memory, saving the Q&A to history and performing analytics." },
    end: { title: 'Final Response', text: "The end point of the workflow, where the final, synthesized answer is delivered to the user." },
    error: { title: 'Error Handler', text: "The system's safety net. It classifies errors and determines the best recovery strategy (retry, fallback, or graceful degradation)." },
    calculation: { title: 'Thinking Calculation Executor', text: "When math is needed, this agent generates and runs Python code in a secure Docker container to perform calculations." },
    placeholder: { title: 'Thinking Placeholder Handler', text: "Ensures a helpful response even when research is incomplete by generating a partial answer with placeholders." },
    A_Pat: { title: 'Pattern Matching', text: "The agent first uses predefined regular expressions to quickly identify simple cases without engaging a costly LLM." },
    A_LLM: { title: 'LLM Classification', text: "If no pattern matches, a large language model classifies the query's intent (Engage, Direct, Clarify, Reject)." },
    A_Route: { title: 'Router', text: "Routes the query to the appropriate next agent based on the classification result." },
    B_Tool: { title: 'Planning Tool', text: "A specialized tool that analyzes the query's intent to decompose it into sub-queries." },
    B_Sub: { title: 'Sub-Queries', text: "The original complex query is broken down into smaller, manageable questions." },
    B_HyDE: { title: 'HyDE Generation', text: "Hypothetical Document Embeddings are generated to prime the research process and improve search relevance." },
    B_Plan: { title: 'Create Research Plan', text: "Sub-queries and HyDE documents are compiled into a structured research plan for the next agent." },
    C_Parallel: { title: 'Parallel Execution', text: "Processes all sub-queries from the research plan simultaneously to speed up the research phase." },
    C_Fallback: { title: 'Multi-tier Fallback', text: "For each sub-query, it attempts to find information using a tiered approach: Vector, then Graph, then Keyword, and finally a Web Search." },
    C_Data: { title: 'Raw Data', text: 'The raw, retrieved data from all search tiers.'},
    C_Rerank: { title: 'Reranker', text: "After gathering raw data, a reranker model improves the relevance and quality of the search results before they are used." },
    C_Cache: { title: 'Sub-query Cache', text: 'To optimize performance, the results of sub-queries are cached in a Redis database.'},
    C_Results: { title: 'Consolidated Research', text: 'All retrieved and reranked information is consolidated into a single package.'},
    D_Assess: { title: 'Assess Sufficiency & Accuracy', text: "Analyzes the research results to determine if they are comprehensive enough to answer the user's query." },
    D_Math: { title: 'Math Detection', text: "Uses a combination of keyword matching, pattern recognition, and an LLM to determine if the user's query requires mathematical calculation." },
    D_Route: { title: 'Route based on Validation', text: 'Routes the workflow to the appropriate next agent based on the validation result.'},
    E_Code: { title: 'Code Generation', text: "An LLM generates Python code to perform the necessary calculations." },
    E_Docker: { title: 'Secure Docker Execution', text: "The generated Python code is executed in a secure, isolated Docker container to prevent potential harm to the system." },
    E_LLM: { title: 'LLM Fallback', text: 'If Docker is unavailable, the agent has a fallback mechanism to use an LLM to perform calculations through a reasoning process.'},
    F_Gaps: { title: 'Gap Analysis', text: "Analyzes the incomplete research results to identify what information is missing." },
    F_Partial: { title: 'Partial Answer', text: 'Generates a partial answer that clearly indicates what information has been found and what is still missing.'},
    F_Plan: { title: 'Enhancement Plan', text: 'Creates a plan for how the research could be enhanced to provide a more complete answer in the future.'},
    G_Combine: { title: 'Combine Information', text: "Takes all available information—sub-query answers, calculation results, and placeholder text—and synthesizes it into a coherent narrative." },
    G_Answer: { title: 'Generate Structured Answer', text: 'Crafts a well-structured, easy-to-read final answer.'},
    G_Cite: { title: 'Source Citations', text: 'Extracts and includes citations for all the sources used, ensuring transparency and verifiability.'},
    G_Conf: { title: 'Confidence Score', text: 'Calculates a confidence score for the final answer, providing a useful metric for assessing quality.'},
    G_Final: { title: 'Final Answer Packet', text: 'The complete package containing the answer, citations, and confidence score.'},
    H_Save: { title: 'Save to History', text: "Saves the user's query and the final answer to the conversation history for long-term memory." },
    H_Analytics: { title: 'Analyze Metrics', text: 'Performs analytics on the conversation, assessing query complexity, response quality, and resource utilization.'},
    I_Analyze: { title: 'Analyze Error', text: 'Classifies the error and assesses its severity.' },
    I_Strategy: { title: 'Determine Strategy', text: 'Determines the best recovery strategy: Retry, Fallback, or Graceful Degradation.' },
};

const architectureNodes = [
    // Manually positioned groups and key nodes for a multi-lane layout
    { id: 'start', type: 'custom', data: { label: 'User Query' }, position: { x: 825, y: 0 }, width: 150, height: 50 },
    { id: 'triage', type: 'group', data: { label: 'Triage Agent' }, position: { x: 600, y: 150 }, style: { width: 300, height: 400 } },
    { id: 'planning', type: 'group', data: { label: 'Planning Agent' }, position: { x: -50, y: 600 }, style: { width: 300, height: 500 } },
    { id: 'research', type: 'group', data: { label: 'Research Orchestrator' }, position: { x: 300, y: 600 }, style: { width: 600, height: 500 } },
    { id: 'validation', type: 'group', data: { label: 'Validation Agent' }, position: { x: 950, y: 600 }, style: { width: 300, height: 300 } },
    { id: 'synthesis', type: 'group', data: { label: 'Synthesis Agent' }, position: { x: 300, y: 1150 }, style: { width: 950, height: 300 } },
    { id: 'memory', type: 'group', data: { label: 'Memory Agent' }, position: { x: 950, y: 950 }, style: { width: 300, height: 300 } },
    { id: 'end', type: 'custom', data: { label: 'Final Response' }, position: { x: 825, y: 1500 }, width: 150, height: 50 },
    
    // Cross-cutting concerns
    { id: 'placeholder', type: 'group', data: { label: 'Placeholder Handler' }, position: { x: -450, y: 300 }, style: { width: 300, height: 400 } },
    { id: 'calculation', type: 'group', data: { label: 'Calculation Executor' }, position: { x: -450, y: 750 }, style: { width: 300, height: 400 } },
    { id: 'error', type: 'group', data: { label: 'Error Handler' }, position: { x: 1300, y: 600 }, style: { width: 300, height: 300 } },
    
    // Child nodes, their positions will be calculated by ELK relative to their parent
    { id: 'A_Pat', type: 'custom', data: { label: 'Pattern Matching' }, parentNode: 'triage', width: 150, height: 50 },
    { id: 'A_LLM', type: 'custom', data: { label: 'LLM Classification' }, parentNode: 'triage', width: 150, height: 50 },
    { id: 'A_Route', type: 'custom', data: { label: 'Route' }, parentNode: 'triage', width: 150, height: 50 },
    { id: 'B_Tool', type: 'custom', data: { label: 'Planning Tool' }, parentNode: 'planning', width: 150, height: 50 },
    { id: 'B_Sub', type: 'custom', data: { label: 'Sub-Queries' }, parentNode: 'planning', width: 150, height: 50 },
    { id: 'B_HyDE', type: 'custom', data: { label: 'HyDE Generation' }, parentNode: 'planning', width: 150, height: 50 },
    { id: 'B_Plan', type: 'custom', data: { label: 'Create Research Plan' }, parentNode: 'planning', width: 150, height: 50 },
    { id: 'C_Parallel', type: 'custom', data: { label: 'Parallel Execution' }, parentNode: 'research', width: 150, height: 50 },
    { id: 'C_Fallback', type: 'custom', data: { label: 'Multi-tier Fallback' }, parentNode: 'research', width: 150, height: 50 },
    { id: 'C_Data', type: 'custom', data: { label: 'Raw Data' }, parentNode: 'research', width: 150, height: 50 },
    { id: 'C_Rerank', type: 'custom', data: { label: 'Reranker' }, parentNode: 'research', width: 150, height: 50 },
    { id: 'C_Cache', type: 'custom', data: { label: 'Sub-query Cache' }, parentNode: 'research', width: 150, height: 50 },
    { id: 'C_Results', type: 'custom', data: { label: 'Consolidated Research' }, parentNode: 'research', width: 150, height: 50 },
    { id: 'D_Assess', type: 'custom', data: { label: 'Assess Sufficiency' }, parentNode: 'validation', width: 150, height: 50 },
    { id: 'D_Math', type: 'custom', data: { label: 'Math Detection' }, parentNode: 'validation', width: 150, height: 50 },
    { id: 'E_Code', type: 'custom', data: { label: 'Code Generation' }, parentNode: 'calculation', width: 150, height: 50 },
    { id: 'E_Docker', type: 'custom', data: { label: 'Secure Docker Execution' }, parentNode: 'calculation', width: 150, height: 50 },
    { id: 'E_LLM', type: 'custom', data: { label: 'LLM Fallback' }, parentNode: 'calculation', width: 150, height: 50 },
    { id: 'F_Gaps', type: 'custom', data: { label: 'Gap Analysis' }, parentNode: 'placeholder', width: 150, height: 50 },
    { id: 'F_Partial', type: 'custom', data: { label: 'Partial Answer' }, parentNode: 'placeholder', width: 150, height: 50 },
    { id: 'F_Plan', type: 'custom', data: { label: 'Enhancement Plan' }, parentNode: 'placeholder', width: 150, height: 50 },
    { id: 'G_Combine', type: 'custom', data: { label: 'Combine Information' }, parentNode: 'synthesis', width: 150, height: 50 },
    { id: 'G_Answer', type: 'custom', data: { label: 'Generate Structured Answer' }, parentNode: 'synthesis', width: 150, height: 50 },
    { id: 'G_Cite', type: 'custom', data: { label: 'Source Citations' }, parentNode: 'synthesis', width: 150, height: 50 },
    { id: 'G_Conf', type: 'custom', data: { label: 'Confidence Score' }, parentNode: 'synthesis', width: 150, height: 50 },
    { id: 'G_Final', type: 'custom', data: { label: 'Final Answer Packet' }, parentNode: 'synthesis', width: 150, height: 50 },
    { id: 'H_Save', type: 'custom', data: { label: 'Save to History' }, parentNode: 'memory', width: 150, height: 50 },
    { id: 'H_Analytics', type: 'custom', data: { label: 'Analyze Metrics' }, parentNode: 'memory', width: 150, height: 50 },
    { id: 'I_Analyze', type: 'custom', data: { label: 'Analyze Error' }, parentNode: 'error', width: 150, height: 50 },
    { id: 'I_Strategy', type: 'custom', data: { label: 'Determine Strategy' }, parentNode: 'error', width: 150, height: 50 },
];

const architectureEdges = [
    // Main Flow
    { id: 'e-start-triage', source: 'start', target: 'triage' },
    { id: 'e-triage-planning', source: 'triage', target: 'planning', label: 'Engage' },
    { id: 'e-planning-research', source: 'planning', target: 'research' },
    { id: 'e-research-validation', source: 'research', target: 'validation' },
    { id: 'e-validation-synthesis', source: 'validation', target: 'synthesis', label: 'Sufficient' },
    { id: 'e-synthesis-memory', source: 'synthesis', target: 'memory' },
    { id: 'e-memory-end', source: 'memory', target: 'end' },
    
    // Conditional / Fallback Paths
    { id: 'e-validation-placeholder', source: 'validation', target: 'placeholder', label: 'Insufficient' },
    { id: 'e-validation-calculation', source: 'validation', target: 'calculation', label: 'Math Needed' },
    { id: 'e-calculation-synthesis', source: 'calculation', target: 'synthesis' },
    { id: 'e-placeholder-synthesis', source: 'placeholder', target: 'synthesis' },

    // Direct to Synthesis
    { id: 'e-triage-synthesis', source: 'triage', target: 'synthesis', label: 'Direct/Clarify' },
    { id: 'e-planning-synthesis', source: 'planning', target: 'synthesis', label: 'Simple Answer' },

    // Connections to Error Handler
    ...['triage', 'planning', 'research', 'validation', 'calculation', 'placeholder', 'synthesis', 'memory'].map(source => ({
      id: `e-${source}-error`, source, target: 'error', type: 'smoothstep', style: { stroke: '#F56565', strokeWidth: 1.5 }, markerEnd: { type: 'arrowclosed', color: '#F56565' }
    })),
    { id: 'e-error-end', source: 'error', target: 'end', label: 'Graceful Degradation', type: 'smoothstep', style: { stroke: '#F56565', strokeWidth: 1.5 }, markerEnd: { type: 'arrowclosed', color: '#F56565' } }
];

const defaultEdgeOptions = {
    type: 'smoothstep',
    style: { stroke: '#06b6d4', strokeWidth: 2 },
    markerEnd: { type: 'arrowclosed', color: '#06b6d4' },
};

const CustomNode = memo(({ data, selected }) => {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="px-4 py-2 shadow-md rounded-md bg-gray-800 border-2 border-cyan-500 text-white text-center"
      >
        <NodeResizer isVisible={selected} minWidth={100} minHeight={30} />
        <Handle type="target" position={Position.Top} />
        {data.label}
        <Handle type="source" position={Position.Bottom} />
      </motion.div>
    );
});

const GroupNode = memo(({ data, selected }) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="bg-gray-800/50 border-2 border-dashed border-gray-600 rounded-lg p-4"
        >
            <NodeResizer isVisible={selected} minWidth={180} minHeight={100} />
            <Handle type="target" position={Position.Top} />
            <div className="text-center font-bold text-cyan-400 mb-2">{data.label}</div>
            <Handle type="source" position={Position.Bottom} />
        </motion.div>
    );
});
  
const nodeTypes = {
    custom: CustomNode,
    group: GroupNode,
};

const ArchitectureTab = () => {
    const [nodes, setNodes] = useState([]);
    const [edges, setEdges] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        setIsLoading(true);
        const topLevelNodes = architectureNodes.filter(n => !n.parentNode);
        const groupNodes = topLevelNodes.filter(n => n.type === 'group');

        const layoutPromises = groupNodes.map(group => {
            const children = architectureNodes.filter(n => n.parentNode === group.id);
            const childEdges = architectureEdges.filter(edge =>
                children.some(c => c.id === edge.source) && children.some(c => c.id === edge.target)
            );
            return getLayoutedElements(children, childEdges, elkOptions);
        });

        Promise.all(layoutPromises).then(layouts => {
            let processedNodes = [...topLevelNodes];

            layouts.forEach((layout, index) => {
                const group = groupNodes[index];
                const groupPosition = group.position;

                const childNodes = layout.nodes.map(node => ({
                    ...node,
                    position: {
                        x: node.position.x + groupPosition.x + 75,
                        y: node.position.y + groupPosition.y + 75
                    }
                }));
                processedNodes = [...processedNodes, ...childNodes];
            });
            
            // Logic to connect edges to groups instead of individual nodes
            const nodeMap = new Map(architectureNodes.map(n => [n.id, n]));
            const processedEdges = architectureEdges.map(edge => {
                const sourceNode = nodeMap.get(edge.source);
                const targetNode = nodeMap.get(edge.target);

                const sourceGroup = sourceNode?.parentNode || edge.source;
                const targetGroup = targetNode?.parentNode || edge.target;
                
                return { ...edge, source: sourceGroup, target: targetGroup };
            }).filter(edge => edge.source !== edge.target);

            const uniqueEdges = Array.from(new Map(processedEdges.map(e => [`${e.source}->${e.target}`, e])).values());

            setNodes(processedNodes);
            setEdges(uniqueEdges);
            setIsLoading(false);
        });
    }, []);

    const [selectedNode, setSelectedNode] = useState(null);

    const onNodeClick = (event, node) => {
        if (nodeExplanations[node.id]) {
            setSelectedNode(nodeExplanations[node.id]);
        }
    };
    
    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-full">
                <LoaderCircle className="w-10 h-10 animate-spin text-cyan-500" />
            </div>
        );
    }

    return (
      <ReactFlowProvider>
        <div className="h-full grid grid-cols-1 md:grid-cols-3 gap-4 p-4">
            <div className="md:col-span-2 flex flex-col bg-gray-900/50 backdrop-blur-sm rounded-xl border border-gray-700/50 overflow-hidden">
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodeClick={onNodeClick}
                    nodeTypes={nodeTypes}
                    defaultEdgeOptions={defaultEdgeOptions}
                    fitView
                >
                    <Background />
                    <Controls />
                    <MiniMap />
                </ReactFlow>
            </div>
            <div className="flex flex-col bg-gray-900/50 backdrop-blur-sm rounded-xl border border-gray-700/50 p-4">
                <h2 className="text-lg font-bold mb-4 flex items-center gap-2"><BrainCircuit size={22}/> Component Details</h2>
                <div className="flex-1 bg-gray-900/70 p-4 rounded-lg overflow-y-auto fancy-scrollbar">
                    <AnimatePresence mode="wait">
                    {selectedNode ? (
                        <motion.div 
                            key={selectedNode.title}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                        >
                            <h3 className="text-xl font-bold text-cyan-400 mb-2">{selectedNode.title}</h3>
                            <p className="text-gray-300 leading-relaxed">{selectedNode.text}</p>
                        </motion.div>
                    ) : (
                        <div className="flex items-center justify-center h-full text-gray-500">
                           <p>Select a component to learn more.</p>
                        </div>
                    )}
                    </AnimatePresence>
                </div>
            </div>
        </div>
      </ReactFlowProvider>
    );
};


export default function App() {
    const [activeTab, setActiveTab] = useState('chat');

    const TabButton = ({ id, label, icon: Icon }) => (
        <button
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg transition-all duration-200 outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 ${activeTab === id ? 'bg-cyan-600/80 text-white' : 'text-gray-300 hover:bg-gray-800/50'}`}
        >
            <Icon size={16} />
            {label}
        </button>
    );

    const renderTabContent = () => {
        switch (activeTab) {
            case 'chat': return <ChatTab />;
            case 'graph': return <KnowledgeGraphTab />;
            case 'architecture': return <ArchitectureTab />;
            default: return null;
        }
    };

    return (
        <main className="h-screen w-screen flex flex-col bg-transparent text-gray-200 font-sans antialiased">
            <header className="flex-shrink-0 bg-black/30 backdrop-blur-lg border-b border-gray-800/50 p-3 grid grid-cols-3 items-center z-10">
                <div className="flex items-center gap-2 justify-self-start">
                    <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-lg flex items-center justify-center">
                        <Atom size={20} className="text-white"/>
                    </div>
                    <h1 className="text-lg font-bold text-white">Compliance Agentic AI</h1>
                </div>
                <nav className="hidden md:flex items-center gap-2 p-1 bg-gray-900/50 rounded-lg border border-gray-700/50 justify-self-center">
                   <TabButton id="chat" label="Chat" icon={MessagesSquare} />
                   <TabButton id="graph" label="Knowledge Graph" icon={Share2} />
                   <TabButton id="architecture" label="Architecture" icon={GitBranch} />
                </nav>
                <div />
            </header>
            <div className="flex-1 min-h-0">
                 <AnimatePresence mode="wait">
                    <motion.div
                        key={activeTab}
                        initial={{ opacity: 0, y: 15 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -15 }}
                        transition={{ duration: 0.25 }}
                        className="h-full"
                    >
                        {renderTabContent()}
                    </motion.div>
                </AnimatePresence>
            </div>
        </main>
    );
} 

const ChatMessage = ({ message }) => {
    const { role, content, logs, thinkingTime } = message;
    const isUser = role === 'user';
    const Icon = isUser ? User : Atom;
    const [isThinkingOpen, setIsThinkingOpen] = useState(false);

    const hasLogs = !isUser && logs && logs.length > 0;

    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={`flex items-start gap-3 ${isUser ? 'justify-end' : ''}`}
        >
            {!isUser && (
                <div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center flex-shrink-0 mt-1">
                    <Icon className="w-5 h-5 text-gray-400" />
                </div>
            )}
            <div className={`flex flex-col w-full ${isUser ? 'items-end' : 'items-start'}`}>
                <div className={`p-4 rounded-lg max-w-[85%] ${isUser ? 'bg-cyan-600/80' : 'bg-gray-700/60'}`}>
                     {isUser ? (
                        <p className="text-white whitespace-pre-wrap">{content}</p>
                    ) : (
                        <div className="prose prose-sm prose-invert max-w-none">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {content || ''}
                            </ReactMarkdown>
                            {!content && <LoaderCircle className="animate-spin" />}
                        </div>
                    )}
                </div>
                {hasLogs && (
                    <div className="mt-2 w-full max-w-[85%] flex items-center gap-4">
                        <button
                            onClick={() => setIsThinkingOpen(!isThinkingOpen)}
                            className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200 transition-colors"
                        >
                            <BrainCircuit className="w-4 h-4 text-cyan-400" />
                            <span>Show thinking</span>
                            <ChevronDown className={`w-4 h-4 transition-transform ${isThinkingOpen ? 'transform rotate-180' : ''}`} />
                        </button>
                        {thinkingTime && (
                            <span className="text-xs text-gray-500">
                                Thought for {thinkingTime.toFixed(1)}s
                            </span>
                        )}
                        <AnimatePresence>
                            {isThinkingOpen && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0, y: -10 }}
                                    animate={{ opacity: 1, height: 'auto', y: 0 }}
                                    exit={{ opacity: 0, height: 0, y: -10 }}
                                    transition={{ duration: 0.3 }}
                                    className="mt-2 pl-4 border-l-2 border-gray-700/50"
                                >
                                    <div className="space-y-4 pt-2">
                                        {logs.map((log, index) => (
                                            <LogEntry
                                                key={log.id}
                                                log={log}
                                                isLast={index === logs.length - 1}
                                            />
                                        ))}
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                )}
            </div>
        </motion.div>
    );
}; 

const InitialPrompts = ({ prompts, onPromptClick }) => (
    <div className="w-full">
        <h2 className="text-center text-sm text-gray-500 mb-4">Here are a few ideas to start:</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {prompts.map((prompt, i) => {
                const Icon = icons[prompt.icon];
                return (
                     <div key={i} className="bg-gray-800/50 p-4 rounded-lg border border-gray-700/50 hover:border-cyan-500/50 transition-colors cursor-pointer flex flex-col" onClick={() => onPromptClick(prompt.query)}>
                        <div className="mb-3">
                            <Icon className="w-6 h-6 text-cyan-400" />
                        </div>
                        <p className="text-sm text-gray-400">{prompt.query}</p>
                    </div>
                )
            })}
        </div>
    </div>
);

const QueryLibraryModal = ({ categories, onClose, onSelectQuery }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.95, y: 20 }}
        transition={{ duration: 0.2, ease: 'easeOut' }}
        className="relative w-full max-w-2xl max-h-[80vh] bg-gray-900 border border-cyan-500/30 rounded-2xl shadow-2xl flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex-shrink-0 p-6 flex items-center justify-between border-b border-gray-700/50">
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <Lightbulb className="text-cyan-400" />
            Prompt Library
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <X size={24} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-6 space-y-6 fancy-scrollbar">
          {categories.map((category) => (
            <div key={category.category}>
              <h3 className="text-lg font-semibold text-cyan-400 mb-3">{category.category}</h3>
              <div className="space-y-3">
                {category.queries.map((query) => (
                  <div
                    key={query}
                    onClick={() => onSelectQuery(query)}
                    className="p-4 bg-gray-800/70 rounded-lg border border-gray-700 hover:border-cyan-500 transition-all duration-200 cursor-pointer text-gray-300 hover:text-white"
                  >
                    {query}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
};
