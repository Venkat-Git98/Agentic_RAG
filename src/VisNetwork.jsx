import React, { useEffect, useRef } from 'react';
import { Network } from 'vis-network';
import 'vis-network/styles/vis-network.css';
import { clusterData } from './UserFlowData';


const VisNetwork = ({ nodes, edges, onNodeClick, isHierarchical = false, isHorizontalLayout = false, isUserFlow = false }) => {
    const visJsRef = useRef(null);

    useEffect(() => {
        if (!visJsRef.current) return;

        const mappedNodes = nodes.map(node => ({
            ...node,
            shape: node.shape || 'dot',
            widthConstraint: node.width ? { minimum: node.width, maximum: node.width } : undefined,
            heightConstraint: node.height ? { minimum: node.height, maximum: node.height } : undefined,
            font: {
                color: '#ffffff',
                size: 14,
                face: 'Inter',
                multi: true,
                align: 'center',
                // Ensure text appears inside the shape
                vadjust: (node.shape === 'diamond') ? 0 : undefined
            },
            fixed: isUserFlow ? { x: true, y: true } : node.fixed
        }));

        const network = new Network(visJsRef.current, { nodes: mappedNodes, edges }, {});
        
        const architectureNodeOptions = {
            shape: 'dot',
            font: {
                size: 16,
                face: 'Inter',
                color: '#e5e7eb'
            },
            borderWidth: 1,
            color: {
                border: '#4b5563',
                background: '#2563eb',
                highlight: {
                    border: '#38bdf8',
                    background: '#0c4a6e'
                }
            },
            margin: {
                top: 10,
                right: 15,
                bottom: 10,
                left: 15
            },
            widthConstraint: { minimum: 150 },
            heightConstraint: { minimum: 50 },
        };
        
        const userFlowGroups = {
            input: { color: { background: '#2563eb', border: '#60a5fa' }, shape: 'ellipse' },
            agent: { color: { background: '#166534', border: '#4ade80' }, shape: 'box' },
            decision: { color: { background: '#be123c', border: '#fb7185' }, shape: 'diamond' },
            database: { color: { background: '#b45309', border: '#f97316' }, shape: 'database' },
            output: { color: { background: '#6d28d9', border: '#a78bfa' }, shape: 'box' }
        };

        const options = {
            autoResize: true,
            height: '100%',
            width: '100%',
            physics: {
                enabled: !isUserFlow,
                hierarchicalRepulsion: {
                  nodeDistance: isHorizontalLayout ? 250 : 200,
                },
                solver: 'hierarchicalRepulsion'
            },
            interaction: {
                dragNodes: !isUserFlow,
                zoomView: true,
                dragView: true,
                navigationButtons: false,
                tooltipDelay: 200,
            },
            layout: {
                hierarchical: isHierarchical ? {
                    enabled: true,
                    direction: isHorizontalLayout ? 'LR' : 'UD',
                    sortMethod: 'directed',
                    levelSeparation: isHorizontalLayout ? 300 : 200,
                    nodeSpacing: 150,
                } : false,
            },
            nodes: architectureNodeOptions,
            edges: {
                arrows: 'to',
                smooth: isUserFlow ? { enabled: false } : {
                    type: 'cubicBezier',
                    forceDirection: isHorizontalLayout ? 'horizontal' : 'vertical',
                    roundness: 0.4
                },
                color: {
                    color: '#6b7280',
                    highlight: '#38bdf8',
                },
                font: {
                    color: '#e5e7eb',
                    size: 12,
                    align: 'middle',
                    strokeWidth: 0,
                }
            },
            groups: isUserFlow ? userFlowGroups : {},
        };

        network.setOptions(options);

        network.on('stabilized', () => {
            network.setOptions({ physics: false });
        });

        if (isUserFlow && clusterData) {
            Object.keys(clusterData).forEach(clusterId => {
                const cluster = clusterData[clusterId];
                network.clusterByConnection(cluster.nodes[0], {
                    joinCondition: (nodeOptions) => {
                        return cluster.nodes.includes(nodeOptions.id);
                    },
                    clusterNodeProperties: {
                        id: clusterId,
                        label: cluster.label,
                        shape: 'box',
                        color: {
                            background: 'rgba(107, 114, 128, 0.1)',
                            border: 'rgba(156, 163, 175, 0.3)'
                        },
                        font: {
                            color: '#d1d5db',
                            size: 16,
                            face: 'Inter',
                            align: 'left',
                        },
                        borderWidth: 1,
                        shapeProperties: {
                            borderRadius: 8
                        },
                        allowSingleNodeCluster: true,
                    }
                });
            });

                network.fit({
                    animation: {
                        duration: 1000,
                        easingFunction: 'easeInOutQuad'
                    }
                });
        }

        network.on('click', (event) => {
                if (event.nodes.length > 0) {
                    const nodeId = event.nodes[0];
                const nodeData = nodes.find(n => n.id === String(nodeId));
                if (onNodeClick && nodeData && !nodeData.isCluster) {
                    onNodeClick(event, nodeData);
                }
                }
            });

        return () => {
            if (network) {
            network.destroy();
            }
        };
    }, [nodes, edges, onNodeClick, isHierarchical, isHorizontalLayout, isUserFlow]);

    return <div ref={visJsRef} className="h-full w-full" />;
};

export default VisNetwork; 