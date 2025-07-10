import React, { useEffect, useRef } from 'react';
import { Network } from 'vis-network/standalone/esm/vis-network.min.js';
import 'vis-network/styles/vis-network.css';

const VisNetwork = ({ nodes, edges, onNodeClick, isHierarchical = false }) => {
    const visJsRef = useRef(null);

    useEffect(() => {
        if (!visJsRef.current) return;

        const network = new Network(visJsRef.current, { nodes, edges }, {});
        
        const architectureNodeOptions = {
            shape: 'box',
            borderWidth: 1.5,
            shadow: { enabled: true, color: 'rgba(0,0,0,0.4)', size: 5, y: 2 },
            shapeProperties: { borderRadius: 6 },
            font: {
                color: '#ffffff',
                size: 15,
                face: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji"',
                multi: 'html',
                bold: '400'
            },
        };

        const knowledgeGraphNodeOptions = {
            shape: 'dot',
            size: 20,
            borderWidth: 2,
            shadow: { enabled: true, color: 'rgba(0,0,0,0.4)', size: 5, y: 2 },
            font: { color: '#ffffff', size: 14 },
        };

        const options = {
            autoResize: true,
            height: '100%',
            width: '100%',
            nodes: isHierarchical ? architectureNodeOptions : knowledgeGraphNodeOptions,
            edges: {
                width: 1.5,
                arrows: 'to',
                color: {
                    color: '#475569',
                    highlight: '#60a5fa',
                    hover: '#2563eb',
                },
                font: {
                    align: 'middle',
                    size: 13,
                    color: '#94a3b8',
                    strokeWidth: 0,
                },
                smooth: {
                    enabled: true,
                    type: 'cubicBezier',
                    forceDirection: isHierarchical ? 'vertical' : 'none',
                    roundness: 0.7
                },
            },
            groups: {
                // Simple View
                input: { color: { background: '#0d9488', border: '#2dd4bf' }, font: { bold: '600' } },
                agent: { color: { background: '#2563eb', border: '#60a5fa' }, shape: 'box', shapeProperties: { borderRadius: 6 } },
                decision: { 
                    shape: 'diamond', 
                    color: { background: '#7c3aed', border: '#a78bfa' } 
                },
                orchestrator: { color: { background: '#ca8a04', border: '#facc15' }, shape: 'box', shapeProperties: { borderRadius: 6 } },
                process: { color: { background: '#475569', border: '#94a3b8' }, shape: 'box', shapeProperties: { borderRadius: 6 } },
                augment: { color: { background: '#c2410c', border: '#fb923c' }, shape: 'box', shapeProperties: { borderRadius: 6 } },
                end: { 
                    shape: 'box',
                    color: { background: '#166534', border: '#22c55e' } ,
                    shapeProperties: {
                        borderRadius: 100
                    }
                },
                
                // Detailed View
                'sub-process': { color: { background: '#083344', border: '#06b6d4' }, shape: 'box', shapeProperties: { borderRadius: 4 } },
                'sub-process-llm': { color: { background: '#1e1b4b', border: '#818cf8' }, shape: 'box', shapeProperties: { borderRadius: 4 } },
                'sub-process-io': { color: { background: '#5f1603', border: '#fdba74' }, shape: 'database' },
                'decision-small': { shape: 'diamond', size: 10, color: { background: '#4c1d95', border: '#a78bfa' } },
                'fallback': { shape: 'box', color: { background: '#525220', border: '#eab308' }, shapeProperties: { borderRadius: 2 } },
                'fallback-web': { shape: 'box', color: { background: '#6c2303', border: '#fb923c' }, shapeProperties: { borderRadius: 2 } },
                'error': { shape: 'box', color: { background: '#7f1d1d', border: '#ef4444' } },
                'error-sub': { shape: 'box', color: { background: '#7f1d1d', border: '#f87171' }, font: { size: 12 } },


                // From original graph
                chapternode: { color: { background: '#4338ca', border: '#a5b4fc' } },
                sectionnode: { color: { background: '#374151', border: '#9ca3af' } },
                subsectionnode: { color: { background: '#52525b', border: '#a1a1aa' } },
            },
            physics: {
                // For layout mode, we enable physics. For the final version, we will disable it.
                enabled: !isHierarchical, 
            },
            interaction: {
                hover: true,
                tooltipDelay: 200,
                navigationButtons: true,
            },
            layout: {
                hierarchical: {
                    // Temporarily disable hierarchical for layout mode
                    enabled: false,
                },
            },
        };

        network.setOptions(options);

        // Add the coordinate logger for "Layout Mode"
        if (isHierarchical) {
            network.on('dragEnd', (params) => {
                if (params.nodes.length > 0) {
                    const nodeId = params.nodes[0];
                    const positions = network.getPositions([nodeId]);
                    const position = positions[nodeId];
                    console.log(`{ id: '${nodeId}', x: ${Math.round(position.x)}, y: ${Math.round(position.y)} },`);
                }
            });
        }


        if (onNodeClick) {
            network.on("click", (event) => {
                if (event.nodes.length > 0) {
                    const nodeId = event.nodes[0];
                    const nodeData = nodes.find(n => n.id === nodeId);
                    onNodeClick(event, nodeData);
                }
            });
        }

        return () => {
            network.destroy();
        };
    }, [nodes, edges, onNodeClick, isHierarchical]);

    return <div ref={visJsRef} style={{ height: '100%', width: '100%' }} />;
};

export default VisNetwork; 