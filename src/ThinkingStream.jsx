import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BrainCircuit, CheckCircle, AlertTriangle, Workflow } from 'lucide-react';

const LogIcon = ({ level }) => {
  switch (level) {
    case 'INFO':
      return <CheckCircle className="w-4 h-4 text-green-400" />;
    case 'ERROR':
      return <AlertTriangle className="w-4 h-4 text-red-400" />;
    case 'AGENT':
        return <BrainCircuit className="w-4 h-4 text-purple-400" />;
    default:
      return <Workflow className="w-4 h-4 text-blue-400" />;
  }
};

const ThinkingStream = ({ logs }) => {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  if (!logs || logs.length === 0) {
    return null;
  }

  return (
    <motion.div 
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.3 }}
      className="bg-gray-800/50 border border-gray-700 rounded-lg mx-4 mb-4 overflow-hidden"
    >
      <div className="p-3 border-b border-gray-700">
        <h3 className="text-sm font-semibold text-gray-200 flex items-center">
            <BrainCircuit className="w-5 h-5 mr-2 text-purple-400" />
            Live Thinking Process
        </h3>
      </div>
      <div ref={scrollRef} className="max-h-48 overflow-y-auto p-3 text-xs font-mono">
        <AnimatePresence>
          {logs.map((log, index) => (
            <motion.div
              key={log.id || index}
              layout
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
              className="flex items-start py-1.5 text-gray-300"
            >
              <LogIcon level={log.level} />
              <span className="ml-3 flex-1 whitespace-pre-wrap">
                {typeof log.message === 'string' ? log.message : JSON.stringify(log.message, null, 2)}
              </span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

export default ThinkingStream; 