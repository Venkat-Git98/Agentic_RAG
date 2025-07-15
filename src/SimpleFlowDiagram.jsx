import React, { useCallback, useState, useEffect } from 'react';
import ReactFlow, {
    Controls,
    Background,
    MiniMap,
    useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { simpleFlowNodes, simpleFlowEdges } from './SimpleFlowData';

const nodeColor = (node) => {
    switch (node.type) {
        case 'input':
            return '#6366F1';
        case 'output':
            return '#FF6B6B';
        default:
            return '#4A5568';
    }
};

const CenteredFlow = ({ onNodeSelect, nodes, edges }) => {
    const { fitView } = useReactFlow();

    useEffect(() => {
        fitView({ padding: 0.2 });
    }, []);

    const handleNodeClick = useCallback((event, node) => {
        onNodeSelect(node);
    }, [onNodeSelect]);

    return (
        <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodeClick={handleNodeClick}
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable={false}
            colorMode="dark"
            className="bg-gray-800"
        >
            <Controls />
            <MiniMap />
            <Background variant="dots" gap={12} size={1} />
        </ReactFlow>
    );
};


const SimpleFlowDiagram = ({ onNodeSelect }) => {
    const [nodes, setNodes] = useState(simpleFlowNodes.map(node => ({
        ...node,
        style: { ...node.style, background: nodeColor(node), color: 'white', border: '1px solid #2D3748', width: 170 },
    })));
    
    const [edges, setEdges] = useState(simpleFlowEdges.map(edge => ({ 
        ...edge, 
        type: 'smoothstep',
        animated: edge.animated,
        style: { stroke: edge.animated ? '#6366F1' : '#A0AEC0', strokeWidth: 2 },
        markerEnd: {
            type: 'arrowclosed',
            color: edge.animated ? '#6366F1' : '#A0AEC0',
        },
    })));

    return (
        <div style={{ width: '100%', height: '100%' }}>
            <CenteredFlow onNodeSelect={onNodeSelect} nodes={nodes} edges={edges} />
        </div>
    );
};

export default SimpleFlowDiagram; 