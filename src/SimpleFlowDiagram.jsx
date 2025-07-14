import React, { useCallback, useState } from 'react';
import ReactFlow, {
    Controls,
    Background,
    MiniMap,
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

    const handleNodeClick = useCallback((event, node) => {
        onNodeSelect(node);
    }, [onNodeSelect]);

    return (
        <div style={{ width: '100%', height: '100%' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodeClick={handleNodeClick}
                nodesDraggable={false}
                nodesConnectable={false}
                elementsSelectable={false}
                colorMode="dark"
                className="bg-gray-800"
                fitView
            >
                <Controls />
                <MiniMap />
                <Background variant="dots" gap={12} size={1} />
            </ReactFlow>
        </div>
    );
};

export default SimpleFlowDiagram; 