import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import VisNetwork from './VisNetwork';
import { architectureNodes as simpleNodes, architectureEdges as simpleEdges } from './ArchitectureData';
import { userFlowNodes, userFlowEdges } from './UserFlowData';
import { Eye, Code, GitMerge, Figma, PanelLeft, Workflow, Users } from 'lucide-react';
import InteractiveDiagram from './InteractiveDiagram';
import SidebarContent from './SidebarContent';
import SimpleFlowDiagram from './SimpleFlowDiagram';

const ArchitectureTab = ({ onNodeClick }) => {
    const [view, setView] = useState('agents'); // agents, architecture
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [selectedNode, setSelectedNode] = useState(null);

    const renderContent = () => {
        switch (view) {
            case 'agents':
                return <SimpleFlowDiagram onNodeSelect={setSelectedNode} />;
            case 'architecture':
                return <InteractiveDiagram />;
            default:
                return null;
        }
    };

    const handleToggleSidebar = () => {
        setIsSidebarOpen(!isSidebarOpen);
        if (isSidebarOpen) {
            setSelectedNode(null); // Clear selection when closing
        }
    };

    const TabButton = ({ id, label, icon: Icon }) => (
        <button
            onClick={() => {
                setView(id);
                setSelectedNode(null); // Reset selection on view change
            }}
            className={`flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                view === id ? 'bg-cyan-600/90 text-white' : 'text-gray-300 hover:bg-gray-800/60'
            }`}
        >
            <Icon size={14} />
            {label}
        </button>
    );

    return (
        <div className="h-full flex flex-col bg-gray-900/50 backdrop-blur-sm rounded-xl border border-gray-700/50 m-4 p-4 gap-4">
            <div className="flex-shrink-0 flex justify-between items-center">
                <div className="flex items-center gap-2 p-1 bg-gray-900/50 rounded-lg border border-gray-700/50">
                    <TabButton id="agents" label="Agents View" icon={Users} />
                    <TabButton id="architecture" label="Architectural Diagram" icon={Figma} />
                </div>
                 {(view === 'architecture' || view === 'agents') && (
                    <button onClick={handleToggleSidebar} className="p-2 text-gray-300 hover:bg-gray-800/60 rounded-md">
                        <PanelLeft size={16} />
                    </button>
                )}
            </div>

            <div className="flex-1 min-h-0 flex gap-4">
                <div className="flex-1 min-h-0 relative">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={view}
                            initial={{ opacity: 0, scale: 0.98 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.98 }}
                            transition={{ duration: 0.2 }}
                            className="absolute inset-0"
                        >
                            {renderContent()}
                        </motion.div>
                    </AnimatePresence>
                </div>
                <AnimatePresence>
                    {isSidebarOpen && (view === 'architecture' || view === 'agents') && (
                        <motion.div
                            initial={{ width: 0, opacity: 0 }}
                            animate={{ width: 400, opacity: 1 }}
                            exit={{ width: 0, opacity: 0 }}
                            transition={{ duration: 0.3 }}
                            className="bg-gray-800/60 p-4 rounded-lg border border-gray-700 overflow-y-auto"
                        >
                            {view === 'agents' ? <SidebarContent node={selectedNode} /> : <SidebarContent />}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default ArchitectureTab; 