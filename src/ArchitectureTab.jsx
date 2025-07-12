import React, { useState } from 'react';
import VisNetwork from './VisNetwork';
import { 
  architectureNodes, architectureEdges, 
  horizontalArchitectureNodes, horizontalArchitectureEdges,
  executiveArchitectureNodes, executiveArchitectureEdges,
  modernFlatNodes, modernFlatEdges,
  swimlaneNodes, swimlaneEdges,
  technicalArchNodes, technicalArchEdges,
  c4ModelNodes, c4ModelEdges,
  c4ModelArchitecture,
  agenticFlowNodes, agenticFlowEdges,
  simpleAgenticFlowNodes, simpleAgenticFlowEdges,
  professionalFlowNodes, professionalFlowEdges, // <-- Import new professional flow
  corporateDesignNodes, corporateDesignEdges, // <-- Import new corporate design
  monoDarkNodes, monoDarkEdges, // <-- Import new mono dark theme
  dfdNodes, dfdEdges,
  eventDrivenNodes, eventDrivenEdges,
  networkTopologyNodes, networkTopologyEdges,
  umlComponentNodes, umlComponentEdges,
  iacNodes, iacEdges,
  designOptions,
  engineeringDesignOptions
} from './ArchitectureData';
import { detailedArchitectureNodes, detailedArchitectureEdges } from './DetailedArchitectureData';
import { motion } from 'framer-motion';
import { Network, GitMerge, ArrowRight, ArrowDown, Palette, Star } from 'lucide-react';

const ArchitectureTab = ({ onNodeClick }) => {
  const [isDetailedView, setIsDetailedView] = useState(false);
  const [isHorizontalLayout, setIsHorizontalLayout] = useState(false);
  const [selectedDesign, setSelectedDesign] = useState('monoDark'); // <-- Set as default
  const [c4Level, setC4Level] = useState('context'); // 'context', 'container', 'component', 'code'

  // Design data mapping
  const designDataMap = {
    traditional: { nodes: architectureNodes, edges: architectureEdges },
    horizontal: { nodes: horizontalArchitectureNodes, edges: horizontalArchitectureEdges },
    executive: { nodes: executiveArchitectureNodes, edges: executiveArchitectureEdges },
    modernFlat: { nodes: modernFlatNodes, edges: modernFlatEdges },
    swimlane: { nodes: swimlaneNodes, edges: swimlaneEdges },
    technicalArch: { nodes: technicalArchNodes, edges: technicalArchEdges },
    c4Model: { 
      nodes: selectedDesign === 'c4Model' ? c4ModelArchitecture[c4Level]?.nodes || c4ModelNodes : c4ModelNodes, 
      edges: selectedDesign === 'c4Model' ? c4ModelArchitecture[c4Level]?.edges || c4ModelEdges : c4ModelEdges 
    },
    agenticFlow: { 
      nodes: isDetailedView ? agenticFlowNodes : simpleAgenticFlowNodes, 
      edges: isDetailedView ? agenticFlowEdges : simpleAgenticFlowEdges 
    },
    professionalFlow: { nodes: professionalFlowNodes, edges: professionalFlowEdges }, // <-- Add to map
    corporateDesign: { nodes: corporateDesignNodes, edges: corporateDesignEdges }, // <-- Add to map
    monoDark: { nodes: monoDarkNodes, edges: monoDarkEdges }, // <-- Add to map
    dataFlowDiagram: { nodes: dfdNodes, edges: dfdEdges },
    eventDrivenArch: { nodes: eventDrivenNodes, edges: eventDrivenEdges },
    networkTopology: { nodes: networkTopologyNodes, edges: networkTopologyEdges },
    umlComponent: { nodes: umlComponentNodes, edges: umlComponentEdges },
    infrastructureAsCode: { nodes: iacNodes, edges: iacEdges },
    detailed: { nodes: detailedArchitectureNodes, edges: detailedArchitectureEdges }
  };

  // Merge design options
  const allDesignOptions = { ...designOptions, ...engineeringDesignOptions };

  // Select appropriate nodes and edges based on view and design
  const getNodesAndEdges = () => {
    if (isDetailedView) {
      return designDataMap.detailed;
    } else {
      return designDataMap[selectedDesign] || designDataMap.traditional;
    }
  };

  const { nodes, edges } = getNodesAndEdges();

  // Add the full description to the title for hover-over tooltips
  const nodesWithTitles = nodes.map(node => ({
    ...node,
    title: `<b>${node.label.replace(/\n/g, ' ')}</b><br><hr style="margin: 4px 0; border-color: #4b5563;">${node.description || 'No details available.'}`
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

  const DesignSelector = () => (
    <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10 bg-gray-900/70 backdrop-blur-md p-3 rounded-lg border border-gray-700/50 min-w-96">
      <div className="flex items-center gap-2 mb-2">
        <Palette size={16} className="text-blue-400" />
        <span className="text-sm font-medium text-white">Professional Engineering Diagrams</span>
      </div>
      <select 
        value={selectedDesign}
        onChange={(e) => setSelectedDesign(e.target.value)}
        className="w-full bg-gray-800 border border-gray-600 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        disabled={isDetailedView}
      >
        <optgroup label="🔧 Engineering Standards">
          {Object.entries(engineeringDesignOptions).map(([key, option]) => (
            <option key={key} value={key}>
              {option.name} - {option.standard} - Complexity: {option.complexity}/10 ⭐
            </option>
          ))}
        </optgroup>
        <optgroup label="📊 Business & Executive">
          {Object.entries(designOptions).map(([key, option]) => (
            <option key={key} value={key}>
              {option.name} - Complexity: {option.complexity}/10 ⭐
            </option>
          ))}
        </optgroup>
        <option value="professionalFlow">Professional Agentic Flow</option>
      </select>
      
      {/* C4 Model Level Selector */}
      {selectedDesign === 'c4Model' && !isDetailedView && (
        <div className="mt-3 p-2 bg-purple-900/30 rounded-md border border-purple-600/50">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
            <span className="text-sm font-medium text-purple-200">C4 Model Level</span>
          </div>
          <div className="grid grid-cols-4 gap-1">
            {[
              { key: 'context', label: 'Level 1\nContext', desc: 'System boundaries' },
              { key: 'container', label: 'Level 2\nContainer', desc: 'Applications & services' },
              { key: 'component', label: 'Level 3\nComponent', desc: 'Internal structure' },
              { key: 'code', label: 'Level 4\nCode', desc: 'Implementation' }
            ].map((level) => (
              <button
                key={level.key}
                onClick={() => setC4Level(level.key)}
                className={`px-2 py-1.5 text-xs rounded text-center transition-colors ${
                  c4Level === level.key 
                    ? 'bg-purple-600 text-white' 
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
                title={level.desc}
              >
                {level.label}
              </button>
            ))}
          </div>
        </div>
      )}
      
      {!isDetailedView && (
        <div className="mt-2 text-xs text-gray-400">
          <div className="font-medium text-white">{allDesignOptions[selectedDesign]?.name}</div>
          <div className="flex items-center gap-1 mt-1">
            <Star size={12} className="text-yellow-400" />
            <span>Complexity: {allDesignOptions[selectedDesign]?.complexity}/10</span>
            {allDesignOptions[selectedDesign]?.standard && (
              <>
                <span className="mx-1">•</span>
                <span className="text-blue-300">{allDesignOptions[selectedDesign]?.standard}</span>
              </>
            )}
          </div>
          <div className="mt-1">{allDesignOptions[selectedDesign]?.description}</div>
          {allDesignOptions[selectedDesign]?.pros && (
            <div className="mt-2">
              <div className="text-green-400 text-xs font-medium">Advantages:</div>
              <div className="text-xs">{allDesignOptions[selectedDesign]?.pros.join(', ')}</div>
            </div>
          )}
          {selectedDesign === 'c4Model' && (
            <div className="mt-2 text-xs text-purple-300">
              Currently viewing: <span className="font-medium capitalize">{c4Level}</span> Level - {
                c4Level === 'context' ? 'System boundaries and external entities' :
                c4Level === 'container' ? 'Applications, services, and data stores' :
                c4Level === 'component' ? 'Internal structure of key containers' :
                'Implementation details and class structures'
              }
            </div>
          )}
        </div>
      )}
    </div>
  );

  const LayoutToggle = () => (
    <div className="absolute top-4 right-4 z-10 bg-gray-900/70 backdrop-blur-md p-1 rounded-lg border border-gray-700/50 flex items-center gap-1">
      <button 
        onClick={() => setIsHorizontalLayout(false)}
        className={`px-3 py-1.5 text-xs font-medium rounded-md flex items-center gap-2 transition-colors ${!isHorizontalLayout ? 'bg-emerald-600 text-white' : 'text-gray-300 hover:bg-gray-800'}`}
      >
        <ArrowDown size={14} />
        Vertical
      </button>
      <button 
        onClick={() => setIsHorizontalLayout(true)}
        className={`px-3 py-1.5 text-xs font-medium rounded-md flex items-center gap-2 transition-colors ${isHorizontalLayout ? 'bg-emerald-600 text-white' : 'text-gray-300 hover:bg-gray-800'}`}
      >
        <ArrowRight size={14} />
        Horizontal
      </button>
    </div>
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -15 }}
      transition={{ duration: 0.25 }}
      className="h-full relative bg-gray-900" // Use a professional dark background
    >
      <ViewToggle />
      <DesignSelector />
      <LayoutToggle />
      <VisNetwork
        nodes={nodesWithTitles}
        edges={edges}
        onNodeClick={onNodeClick}
        isHierarchical={true}
        isHorizontalLayout={isHorizontalLayout}
      />
    </motion.div>
  );
};

export default ArchitectureTab; 