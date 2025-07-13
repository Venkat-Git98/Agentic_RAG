import React, { useState, useEffect, useRef, useMemo, useCallback, memo } from 'react';
import { AnimatePresence, motion, useAnimation } from 'framer-motion';
import { ChevronDown, Send, LoaderCircle, Database, Cog, CheckCircle2, XCircle, Search, User, Atom, MessagesSquare, BrainCircuit, Share2, GitBranch, Menu, AlertTriangle, Lightbulb, X, FileCheck, GitCompareArrows, Building2, Workflow, PlusCircle, Users, Pencil } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import VisNetwork from './VisNetwork';
import { DataSet } from 'vis-data';
import ArchitectureTab from './ArchitectureTab';
import ThinkingStream from './ThinkingStream'; // Import the new component

const getOrCreateUserId = () => {
    let userId = localStorage.getItem('agentic-compliance-user-id');
    if (!userId) {
        userId = crypto.randomUUID();
        localStorage.setItem('agentic-compliance-user-id', userId);
    }
    console.log('User ID:', userId);
    return userId;
};

const icons = {
    FileCheck,
    GitCompareArrows,
    Building2,
};

// --- SESSION MANAGEMENT HOOK ---
const useSessionManager = () => {
    const [activeSessionId, setActiveSessionId] = useState(null);
    const [sessions, setSessions] = useState([]); // Array of { id: string, name: string }

    useEffect(() => {
        // Migration logic from old format to new format
        let storedSessions = JSON.parse(localStorage.getItem('agentic-compliance-sessions') || 'null');
        const oldStoredIds = JSON.parse(localStorage.getItem('agentic-compliance-user-ids') || 'null');

        if (!storedSessions && oldStoredIds) {
            // Migrate from old format
            storedSessions = oldStoredIds.map((id, index) => ({
                id,
                name: `Session ${index + 1}`
            }));
            localStorage.setItem('agentic-compliance-sessions', JSON.stringify(storedSessions));
            localStorage.removeItem('agentic-compliance-user-ids'); // Clean up old key
        } else if (!storedSessions) {
            storedSessions = [];
        }

        let activeId = localStorage.getItem('agentic-compliance-active-user-id');

        // If no sessions, create a new one.
        if (storedSessions.length === 0) {
            const newId = crypto.randomUUID();
            const newSession = { id: newId, name: 'Default Session' };
            storedSessions = [newSession];
            activeId = newId;
            localStorage.setItem('agentic-compliance-sessions', JSON.stringify(storedSessions));
            localStorage.setItem('agentic-compliance-active-user-id', activeId);
        }

        // Validate activeId
        if (!activeId || !storedSessions.some(s => s.id === activeId)) {
            activeId = storedSessions[0].id;
            localStorage.setItem('agentic-compliance-active-user-id', activeId);
        }
        
        setActiveSessionId(activeId);
        setSessions(storedSessions);
    }, []);

    const updateSessions = (newSessions) => {
        setSessions(newSessions);
        localStorage.setItem('agentic-compliance-sessions', JSON.stringify(newSessions));
    };

    const createNewSession = useCallback(() => {
        const newId = crypto.randomUUID();
        const newSession = {
            id: newId,
            name: `Session ${sessions.length + 1}`
        };
        const updatedSessions = [...sessions, newSession];
        
        updateSessions(updatedSessions);
        localStorage.setItem('agentic-compliance-active-user-id', newId);
        setActiveSessionId(newId);
    }, [sessions]);

    const switchSession = useCallback((sessionId) => {
        if (sessions.some(s => s.id === sessionId)) {
            localStorage.setItem('agentic-compliance-active-user-id', sessionId);
            setActiveSessionId(sessionId);
        } else {
            console.error("Attempted to switch to a non-existent session ID:", sessionId);
        }
    }, [sessions]);

    const renameSession = useCallback((sessionId, newName) => {
        const updatedSessions = sessions.map(session =>
            session.id === sessionId ? { ...session, name: newName } : session
        );
        updateSessions(updatedSessions);
    }, [sessions]);

    return { activeSessionId, sessions, createNewSession, switchSession, renameSession };
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

const useChat = ({ userId, onFinish, onFirstSubmit }) => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isHistoryLoading, setIsHistoryLoading] = useState(true);
    const hasFlashedWelcome = useRef(new Set());
  
    useEffect(() => {
      const fetchHistory = async () => {
          if (!userId) return;
          console.log('Fetching history for userId:', userId);
          setIsHistoryLoading(true);
          
          try {
              const response = await fetch(`https://agenticrag-production.up.railway.app/history?userId=${encodeURIComponent(userId)}`);
              console.log('History response status:', response.status);
              console.log('History response ok:', response.ok);

              if (response.ok) {
                  const historyData = await response.json();
                  console.log('History data received:', historyData);
                  // Check for the nested 'data' property as per the API spec
                  if (historyData && historyData.data && historyData.data.length > 0) {
                      console.log('Setting messages from history:', historyData.data);
                      setMessages(historyData.data);
                  } else {
                      if (!hasFlashedWelcome.current.has(userId)) {
                          setMessages([
                              { id: '1', role: 'assistant', content: "Welcome. I am an AI specializing in Virginia's building code regulations. Ask me anything from permit requirements to complex compliance scenarios.", logs: [], thinkingTime: null }
                          ]);
                          hasFlashedWelcome.current.add(userId);
                      } else {
                          setMessages([]);
                      }
                  }
              } else {
                  console.error('History response not ok. Status:', response.status);
                  const errorText = await response.text();
                  console.error('Error response body:', errorText);
                   setMessages([
                      { id: '1', role: 'assistant', content: "Welcome. I am an AI specializing in Virginia's building code regulations. Ask me anything from permit requirements to complex compliance scenarios.", logs: [], thinkingTime: null }
                  ]);
              }
          } catch (error) {
              console.error("Failed to fetch chat history:", error);
              console.error("Error details:", {
                  name: error.name,
                  message: error.message,
                  stack: error.stack
              });
              setMessages([
                  { id: '1', role: 'assistant', content: "Welcome. I am an AI specializing in Virginia's building code regulations. Ask me anything from permit requirements to complex compliance scenarios.", logs: [], thinkingTime: null }
              ]);
          } finally {
              setIsHistoryLoading(false);
          }
      };

      fetchHistory();
    }, [userId]);
  
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
            thread_id: userId,
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
  
          let currentEventType = 'message'; // Start with a default type

          for (const message of eventMessages) {
            if (!message) continue;
  
            const eventTypeMatch = message.match(/event: (.*)/);
            if (eventTypeMatch) {
                currentEventType = eventTypeMatch[1];
            }
            
            const dataMatch = message.match(/data: (.*)/s);
            if (!dataMatch) continue;
  
            const jsonData = dataMatch[1];
            
            try {
              const data = JSON.parse(jsonData);
  
              if (currentEventType === 'log') {
                setMessages(prev =>
                  prev.map(msg =>
                    msg.id === assistantMessageId
                      ? { ...msg, logs: [...(msg.logs || []), { ...data, id: Date.now() + Math.random() }] }
                      : msg
                  )
                );
              } else if (currentEventType === 'message') {
                  // This handles the character-by-character streaming
                  setMessages(prev =>
                      prev.map(msg =>
                          msg.id === assistantMessageId
                              ? { ...msg, content: (msg.content || '') + (data.token || '') }
                              : msg
                      )
                  );
              } else if (currentEventType === 'result') {
                const endTime = Date.now();
                const duration = (endTime - startTime) / 1000;
                // This sets the final, clean content from the backend
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
  
    return { messages, input, handleInputChange, handleSubmit, isLoading, submitQuery, isHistoryLoading };
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
        className={`w-56 h-auto p-4 rounded-xl border-2 flex flex-col justify-center shadow-lg backdrop-blur-md transition-all duration-300 hover:shadow-2xl ${className}`}
        whileHover={{ scale: 1.05, y: -5 }}
    >
        {children}
    </motion.div>
);

const knowledgeGraphNodeTypes = {
    inputnode: ({ data }) => <NodeWrapper className="bg-blue-900/40 border-blue-500"><p className="font-bold text-blue-200">{data.label}</p></NodeWrapper>,
    documentnode: ({ data }) => <NodeWrapper className="bg-purple-900/40 border-purple-500"><p className="font-semibold text-purple-200">{data.label}</p><p className="text-xs text-purple-400 truncate">{data.source}</p></NodeWrapper>,
    entitynode: ({ data }) => <NodeWrapper className="bg-teal-900/40 border-teal-500"><p className="font-semibold text-teal-200">{data.label}</p><p className="text-xs text-teal-400">{data.group || 'Entity'}</p></NodeWrapper>,
    conceptnode: ({ data }) => <NodeWrapper className="bg-amber-900/40 border-amber-500"><p className="font-semibold text-amber-200">{data.label}</p><p className="text-xs text-amber-400">Concept</p></NodeWrapper>,
    chapternode: ({ data }) => <NodeWrapper className="bg-indigo-900/40 border-indigo-500"><p className="font-bold text-xl text-indigo-200">{data.label}</p><p className="text-xs text-indigo-400">Chapter</p></NodeWrapper>,
    sectionnode: ({ data }) => <NodeWrapper className="bg-gray-700/40 border-gray-500"><p className="font-semibold text-gray-200">{data.label}</p><p className="text-xs text-gray-400">Section</p></NodeWrapper>,
    subsectionnode: ({ data }) => <NodeWrapper className="bg-gray-600/40 border-gray-400"><p className="font-semibold text-gray-300">{data.label}</p><p className="text-xs text-gray-500">Subsection</p></NodeWrapper>,
    tablenode: ({ data }) => <NodeWrapper className="bg-pink-900/40 border-pink-500"><p className="font-mono text-pink-200">{data.label}</p><p className="text-xs text-pink-400">Table</p></NodeWrapper>,
    diagramnode: ({ data }) => <NodeWrapper className="bg-orange-900/40 border-orange-500"><p className="font-mono text-orange-200">{data.label}</p><p className="text-xs text-orange-400">Diagram</p></NodeWrapper>,
    mathnode: ({ data }) => <NodeWrapper className="bg-lime-900/40 border-lime-500"><p className="font-mono text-lime-200">{data.label}</p><p className="text-xs text-lime-400">Math</p></NodeWrapper>,
    standardnode: ({ data }) => <NodeWrapper className="bg-cyan-900/40 border-cyan-500"><p className="font-semibold text-cyan-200">{data.label}</p><p className="text-xs text-cyan-400">Standard</p></NodeWrapper>,
};

const knowledgeGraphEdgeOptions = {
    type: 'smoothstep',
    style: { stroke: '#60a5fa', strokeWidth: 1.5, opacity: 0.6 },
    markerEnd: { type: 'arrowclosed', color: '#60a5fa' },
};


// --- TABS / MAIN VIEW COMPONENTS ---

const ChatTab = ({ messages, input, handleInputChange, handleSubmit, isLoading, submitQuery, isHistoryLoading }) => {
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

const useForceLayout = (nodes, edges) => {
    const [layoutedNodes, setLayoutedNodes] = useState([]);
    
    useEffect(() => {
        if (nodes.length === 0) {
            setLayoutedNodes([]);
            return;
        }

        const simulationNodes = nodes.map(n => ({ ...n }));

        const simulation = forceSimulation(simulationNodes)
            .force('link', forceLink(edges).id(d => d.id).distance(200).strength(0.1))
            .force('charge', forceManyBody().strength(-1000))
            .force('center', forceCenter(450, 450))
            .force('collide', forceCollide().radius(d => (d.width || 150) / 2 + 20).strength(0.8))
            .stop();

        simulation.tick(300); // Run simulation synchronously to get a good initial layout

        setLayoutedNodes(simulation.nodes());

    }, [nodes, edges]);

    return layoutedNodes;
};

const KnowledgeGraphTab = ({ nodes, edges, onNodeClick, handleSearch, isLoading, error, isPanelOpen, setIsPanelOpen }) => {
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
                                defaultValue="1607"
                            />
                            <button type="submit" className="bg-cyan-600 hover:bg-cyan-700 text-white font-bold py-2 px-4 rounded-md transition-colors disabled:opacity-50" disabled={isLoading}>
                                {isLoading ? <LoaderCircle className="w-4 h-4 mr-2 inline-block animate-spin" /> : <Search className="w-4 h-4 mr-2 inline-block" />}
                                Retrieve Graph
                            </button>
                        </form>
                    </motion.div>
                )}
            </AnimatePresence>
            
            <div className="flex-1 min-h-0 relative bg-gray-900/40 rounded-lg border border-gray-800/60">
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
                
                {isLoading && (
                    <div className="absolute inset-0 flex items-center justify-center z-20 bg-gray-900/50">
                        <LoaderCircle className="w-10 h-10 animate-spin text-cyan-500" />
                    </div>
                )}

                {error && (
                    <div className="absolute inset-0 flex flex-col items-center justify-center z-20 p-4 text-center">
                        <AlertTriangle className="w-10 h-10 text-red-500 mb-4" />
                        <p className="text-red-400 font-semibold">Could not load Knowledge Graph</p>
                        <p className="text-gray-400 text-sm mt-1">{error}</p>
                    </div>
                )}
                
                {!isLoading && !error && nodes.length === 0 && (
                    <div className="absolute inset-0 flex items-center justify-center text-gray-500">
                        <p>Enter a chapter or subsection to visualize the Knowledge Graph.</p>
                    </div>
                )}

                 {nodes.length > 0 && !isLoading && !error && (
                    <VisNetwork nodes={nodes} edges={edges} onNodeClick={onNodeClick} />
                )}
            </div>
        </div>
    );
};


export default function App() {
    const [activeTab, setActiveTab] = useState('chat');
    const { activeSessionId, sessions, createNewSession, switchSession, renameSession } = useSessionManager();

    const { messages, input, handleInputChange, handleSubmit, isLoading, submitQuery, isHistoryLoading } = useChat({
        userId: activeSessionId,
        onFinish: () => {},
        onFirstSubmit: () => {} // This can be re-wired if needed
    });

    // State lifted from KnowledgeGraphTab
    const [graphNodes, setGraphNodes] = useState([]);
    const [graphEdges, setGraphEdges] = useState([]);
    const [selectedNode, setSelectedNode] = useState(null);
    const [isPanelOpen, setIsPanelOpen] = useState(true);
    const [isLoadingGraph, setIsLoadingGraph] = useState(false);
    const [graphError, setGraphError] = useState(null);
    const initialQueryFired = useRef(false);

    const onNodeClick = (event, node) => {
        // eslint-disable-next-line no-unused-vars
        const { embedding, ...properties } = node;
        setSelectedNode({ properties: properties || {} });
    };

    const handleSearchGraph = useCallback(async (query) => {
        if (!query || !activeSessionId) return;

        setIsLoadingGraph(true);
        setGraphError(null);
        
        try {
            const response = await fetch(`https://agenticrag-production.up.railway.app/api/knowledge-graph?query=${encodeURIComponent(query)}&userId=${encodeURIComponent(activeSessionId)}`);
            if (!response.ok) throw new Error(`API Error: ${response.status} - ${await response.text()}`);
            
            const graphData = await response.json();
            if (!graphData.nodes || !graphData.edges) throw new Error("Invalid data from API.");

            const visNodes = graphData.nodes.map(apiNode => {
                // eslint-disable-next-line no-unused-vars
                const { embedding, ...restOfData } = apiNode.data;
                return {
                    id: String(apiNode.id),
                    label: `${apiNode.type}: ${apiNode.id}`,
                    title: `<b>${restOfData.label}</b><br>Type: ${apiNode.type}<br>ID: ${apiNode.id}`,
                    group: apiNode.type,
                    ...restOfData
                }
            });

            const visEdges = graphData.edges.map(e => ({
                id: e.id,
                from: e.source,
                to: e.target,
                label: e.label,
                arrows: 'to'
            }));
            
            setGraphNodes(visNodes);
            setGraphEdges(visEdges);
        } catch (e) {
            console.error("Failed to fetch or process knowledge graph:", e);
            setGraphError(e.message || "Failed to load graph.");
        } finally {
            setIsLoadingGraph(false);
        }
    }, [activeSessionId]);

    const handleSearchSubmit = (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        const chapter = formData.get('chapter');
        handleSearchGraph(chapter);
    };

    useEffect(() => {
        if (activeTab === 'graph' && !initialQueryFired.current && graphNodes.length === 0) {
            initialQueryFired.current = true;
            handleSearchGraph('1607');
        }
    }, [activeTab, handleSearchGraph, graphNodes.length]);


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
            case 'chat': return (
                <ChatTab 
                    messages={messages}
                    input={input}
                    handleInputChange={handleInputChange}
                    handleSubmit={handleSubmit}
                    isLoading={isLoading}
                    submitQuery={submitQuery}
                    isHistoryLoading={isHistoryLoading}
                />
            );
            case 'graph': return (
                <KnowledgeGraphTab
                    nodes={graphNodes}
                    edges={graphEdges}
                    onNodeClick={onNodeClick}
                    handleSearch={handleSearchSubmit}
                    isLoading={isLoadingGraph}
                    error={graphError}
                    isPanelOpen={isPanelOpen}
                    setIsPanelOpen={setIsPanelOpen}
                />
            );
            case 'architecture': return <ArchitectureTab onNodeClick={onNodeClick} />;
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
                <div className="justify-self-end pr-4">
                    <SessionControls 
                        activeSessionId={activeSessionId}
                        sessions={sessions}
                        onSwitch={switchSession}
                        onCreate={createNewSession}
                        onRename={renameSession}
                    />
                </div>
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
            <AnimatePresence>
                {selectedNode && (
                        <motion.div 
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                        onClick={() => setSelectedNode(null)}
                    >
                        <motion.div
                            className="bg-gray-800 border border-cyan-500/30 rounded-lg shadow-2xl w-full max-w-md p-6 relative"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <button onClick={() => setSelectedNode(null)} className="absolute top-4 right-4 text-gray-400 hover:text-white">
                                <X size={20} />
                            </button>
                            <h3 className="text-xl font-bold text-cyan-400 mb-4">{selectedNode.properties.label}</h3>
                            <div className="space-y-2 text-sm max-h-[60vh] overflow-y-auto fancy-scrollbar pr-2">
                                 {selectedNode.properties && Object.entries(selectedNode.properties).map(([key, value]) => {
                                    if (key === 'embedding') return null;
                                    return (
                                        <div key={key}>
                                            <p className="font-semibold text-gray-300 capitalize">{key.replace(/_/g, ' ')}:</p>
                                            <p className="text-gray-400 bg-gray-900/50 p-2 rounded-md whitespace-pre-wrap">
                                                {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                                            </p>
                        </div>
                                    )
                                })}
                            </div>
                        </motion.div>
                    </motion.div>
                    )}
                    </AnimatePresence>
        </main>
    );
} 

const SessionControls = ({ activeSessionId, sessions, onSwitch, onCreate, onRename }) => {
    const [isOpen, setIsOpen] = useState(false);
    const wrapperRef = useRef(null);
    const [editingSessionId, setEditingSessionId] = useState(null);
    const [editingName, setEditingName] = useState('');
    const inputRef = useRef(null);


    useEffect(() => {
        function handleClickOutside(event) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [wrapperRef]);
    
    useEffect(() => {
        if (editingSessionId && inputRef.current) {
            inputRef.current.focus();
            inputRef.current.select();
        }
    }, [editingSessionId]);

    const handleStartEditing = (session) => {
        setEditingSessionId(session.id);
        setEditingName(session.name);
    };

    const handleFinishEditing = () => {
        if (editingSessionId && editingName.trim()) {
            onRename(editingSessionId, editingName.trim());
        }
        setEditingSessionId(null);
        setEditingName('');
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            handleFinishEditing();
        } else if (e.key === 'Escape') {
            setEditingSessionId(null);
            setEditingName('');
        }
    };

    if (!activeSessionId) return null;

    const activeSession = sessions.find(s => s.id === activeSessionId);

    return (
        <div className="flex items-center gap-3">
             <button
                onClick={onCreate}
                className="flex items-center gap-2 text-sm px-3 py-2 bg-gray-800/60 border border-gray-700 rounded-lg hover:bg-gray-700/80 transition-colors"
                title="Start New Chat Session"
            >
                <PlusCircle size={16} />
                New Chat
            </button>
            <div className="relative" ref={wrapperRef}>
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className="flex items-center gap-2 text-sm px-3 py-2 bg-gray-800/60 border border-gray-700 rounded-lg hover:bg-gray-700/80 transition-colors w-48"
                >
                    <Users size={16} />
                    <span className="truncate flex-1 text-left">{activeSession ? activeSession.name : '...'}</span>
                    <ChevronDown size={16} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
                </button>
                <AnimatePresence>
                    {isOpen && (
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="absolute right-0 mt-2 w-64 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-20"
                        >
                            <div className="p-2 space-y-1">
                                {sessions.map(session => (
                                    <div
                                        key={session.id}
                                        className={`w-full flex items-center justify-between text-left px-3 py-2 text-sm rounded-md transition-colors group ${
                                            session.id === activeSessionId
                                                ? 'bg-cyan-600 text-white'
                                                : 'text-gray-300 hover:bg-gray-700/60'
                                        }`}
                                    >
                                        {editingSessionId === session.id ? (
                                            <input
                                                ref={inputRef}
                                                type="text"
                                                value={editingName}
                                                onChange={(e) => setEditingName(e.target.value)}
                                                onBlur={handleFinishEditing}
                                                onKeyDown={handleKeyDown}
                                                className="bg-transparent w-full outline-none border-b border-cyan-400"
                                            />
                                        ) : (
                                            <button
                                                onClick={() => {
                                                    onSwitch(session.id);
                                                    setIsOpen(false);
                                                }}
                                                className="flex-1 truncate text-left"
                                            >
                                                {session.name}
                                            </button>
                                        )}

                                        {editingSessionId !== session.id && (
                                            <button
                                                onClick={() => handleStartEditing(session)}
                                                className="p-1 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-white transition-opacity"
                                                title="Rename session"
                                            >
                                                <Pencil size={14} />
                                            </button>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

const ChatMessage = ({ message }) => {
  const [showThinking, setShowThinking] = useState(false);
  const { role, content, logs, thinkingTime } = message;
  const isAssistant = role === 'assistant';
  const isGenerating = isAssistant && !thinkingTime && content === '';
  const hasLogs = logs && logs.length > 0;
  const isUser = role === 'user';
  const Icon = isUser ? User : Atom;

  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } }
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="mb-6"
    >
      <div className={`flex items-start gap-4 ${isUser ? 'justify-end' : ''}`}>
        {!isUser && (
          <div className="w-9 h-9 rounded-full bg-gray-700 flex items-center justify-center flex-shrink-0">
            <Icon className="w-5 h-5 text-gray-300" />
          </div>
        )}

        <div className={`w-full max-w-[85%] ${isUser ? 'order-1' : ''}`}>
          <motion.div
            layout
            className={`px-4 py-3 rounded-2xl ${
              isUser
                ? 'bg-blue-600 text-white rounded-br-none'
                : 'bg-gray-700 text-gray-200 rounded-bl-none'
            }`}
          >
            <div className="prose prose-sm prose-invert max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  a: ({ node, ...props }) => <a {...props} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline" />,
                }}
              >
                {content || (isAssistant ? '...' : '')}
              </ReactMarkdown>
            </div>
          </motion.div>

          {isAssistant && !isGenerating && thinkingTime && (
            <div className="mt-2 text-xs text-gray-500 flex items-center">
              <BrainCircuit className="w-4 h-4 mr-1.5" />
              <span>Thinking time: {thinkingTime.toFixed(2)}s</span>
              {hasLogs && (
                <button
                  onClick={() => setShowThinking(!showThinking)}
                  className="ml-4 font-medium text-gray-400 hover:text-white transition-colors flex items-center"
                >
                  {showThinking ? 'Hide Thinking' : 'Show Thinking'}
                  <ChevronDown className={`w-4 h-4 ml-1 transition-transform ${showThinking ? 'rotate-180' : ''}`} />
                </button>
              )}
            </div>
          )}
        </div>

        {isUser && (
          <div className="w-9 h-9 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0 order-2">
            <Icon className="w-5 h-5 text-white" />
          </div>
        )}
      </div>

      <AnimatePresence>
        {isGenerating && hasLogs && <ThinkingStream logs={logs} />}
      </AnimatePresence>
      
      <AnimatePresence>
        {showThinking && hasLogs && (
           <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="pl-12 mt-2"
          >
             <div className="bg-gray-800/50 border border-gray-700 rounded-lg">
                <pre className="p-4 text-xs text-gray-300 whitespace-pre-wrap font-mono overflow-x-auto">
                  {logs.map((log, i) => (
                    <div key={i} className="flex items-start py-1">
                      <LogIcon level={log.level} />
                      <span className="ml-2 flex-1">
                        {typeof log.message === 'string' ? log.message : JSON.stringify(log.message, null, 2)}
                      </span>
                    </div>
                  ))}
                </pre>
            </div>
           </motion.div>
        )}
      </AnimatePresence>
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
