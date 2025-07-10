import React, { useState } from 'react';
import VisNetwork from './VisNetwork';
import { architectureNodes, architectureEdges } from './ArchitectureData';
import { detailedArchitectureNodes, detailedArchitectureEdges } from './DetailedArchitectureData';
import { motion } from 'framer-motion';
import { Network, GitMerge } from 'lucide-react';

const ArchitectureTab = ({ onNodeClick }) => {
  const [isDetailedView, setIsDetailedView] = useState(false);

  const nodes = isDetailedView ? detailedArchitectureNodes : architectureNodes;
  const edges = isDetailedView ? detailedArchitectureEdges : architectureEdges;

  // Add the full description to the title for hover-over tooltips
  const nodesWithTitles = nodes.map(node => ({
    ...node,
    title: `<b>${node.label.replace('\\n', ' ')}</b><br><hr style="margin: 4px 0; border-color: #4b5563;">${node.description || 'No details available.'}`
  }));

  const ViewToggle = () => (
    <div className="absolute top-4 left-4 z-10 bg-gray-900/70 backdrop-blur-md p-1 rounded-lg border border-gray-700/50 flex items-center gap-1">
      <button 
        onClick={() => setIsDetailedView(false)}
        className={`px-3 py-1.5 text-xs font-medium rounded-md flex items-center gap-2 transition-colors ${!isDetailedView ? 'bg-cyan-600 text-white' : 'text-gray-300 hover:bg-gray-800'}`}
      >
        <Network size={14} />
        Simple
      </button>
      <button 
        onClick={() => setIsDetailedView(true)}
        className={`px-3 py-1.5 text-xs font-medium rounded-md flex items-center gap-2 transition-colors ${isDetailedView ? 'bg-cyan-600 text-white' : 'text-gray-300 hover:bg-gray-800'}`}
      >
        <GitMerge size={14} />
        Detailed
      </button>
    </div>
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -15 }}
      transition={{ duration: 0.25 }}
      className="h-full relative"
    >
      <ViewToggle />
      <VisNetwork
        nodes={nodesWithTitles}
        edges={edges}
        onNodeClick={onNodeClick}
        isHierarchical={true}
      />
    </motion.div>
  );
};

export default ArchitectureTab; 