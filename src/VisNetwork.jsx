import React, { useEffect, useRef } from 'react';
import { Network } from 'vis-network';
import 'vis-network/styles/vis-network.css';

const VisNetwork = ({ nodes, edges, onNodeClick, isHierarchical = false, isHorizontalLayout = false }) => {
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
                    type: isHorizontalLayout ? 'cubicBezier' : 'cubicBezier',
                    forceDirection: isHierarchical ? (isHorizontalLayout ? 'horizontal' : 'vertical') : 'none',
                    roundness: isHorizontalLayout ? 0.3 : 0.7
                },
            },
            groups: {
                // Enhanced Simple View
                input: { 
                    color: { background: '#0d9488', border: '#2dd4bf' }, 
                    font: { bold: '600', size: 16 },
                    shape: 'box', 
                    shapeProperties: { borderRadius: 8 }
                },
                agent: { 
                    color: { background: '#2563eb', border: '#60a5fa' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 6 },
                    font: { bold: '500', size: 14 }
                },
                decision: { 
                    shape: 'diamond', 
                    color: { background: '#7c3aed', border: '#a78bfa' },
                    font: { bold: '500', size: 13 }
                },
                orchestrator: { 
                    color: { background: '#ca8a04', border: '#facc15' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 8 },
                    font: { bold: '600', size: 15 },
                    borderWidth: 3
                },
                process: { 
                    color: { background: '#475569', border: '#94a3b8' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 6 },
                    font: { size: 13 }
                },
                augment: { 
                    color: { background: '#c2410c', border: '#fb923c' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 6 },
                    font: { bold: '500', size: 14 }
                },
                end: { 
                    shape: 'ellipse',
                    color: { background: '#166534', border: '#22c55e' },
                    font: { bold: '600', size: 14 },
                    borderWidth: 2
                },
                error: { 
                    shape: 'box', 
                    color: { background: '#7f1d1d', border: '#ef4444' },
                    font: { bold: '500', size: 13 },
                    shapeProperties: { borderRadius: 4 }
                },
                
                // Enhanced Detailed View
                'sub-process': { 
                    color: { background: '#083344', border: '#06b6d4' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 4 },
                    font: { size: 12 }
                },
                'sub-process-llm': { 
                    color: { background: '#1e1b4b', border: '#818cf8' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 4 },
                    font: { size: 12, bold: '500' }
                },
                'sub-process-io': { 
                    color: { background: '#5f1603', border: '#fdba74' }, 
                    shape: 'database',
                    font: { size: 12, bold: '500' }
                },
                'decision-small': { 
                    shape: 'diamond', 
                    size: 15, 
                    color: { background: '#4c1d95', border: '#a78bfa' },
                    font: { size: 11 }
                },
                'fallback': { 
                    shape: 'box', 
                    color: { background: '#525220', border: '#eab308' }, 
                    shapeProperties: { borderRadius: 3 },
                    font: { size: 12 }
                },
                'fallback-web': { 
                    shape: 'box', 
                    color: { background: '#6c2303', border: '#fb923c' }, 
                    shapeProperties: { borderRadius: 3 },
                    font: { size: 12, bold: '500' }
                },
                'error-sub': { 
                    shape: 'box', 
                    color: { background: '#7f1d1d', border: '#f87171' }, 
                    font: { size: 11 },
                    shapeProperties: { borderRadius: 3 }
                },

                // Knowledge Graph (from original)
                chapternode: { color: { background: '#4338ca', border: '#a5b4fc' } },
                sectionnode: { color: { background: '#374151', border: '#9ca3af' } },
                subsectionnode: { color: { background: '#52525b', border: '#a1a1aa' } },

                // Executive Professional Design Groups
                'input-executive': { 
                    color: { background: '#1e40af', border: '#3b82f6' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 12 },
                    font: { bold: '600', size: 16, color: '#ffffff' },
                    borderWidth: 2,
                    shadow: { enabled: true, color: 'rgba(30,64,175,0.3)', size: 8, y: 4 }
                },
                'agent-executive': { 
                    color: { background: '#059669', border: '#10b981' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 12 },
                    font: { bold: '600', size: 16, color: '#ffffff' },
                    borderWidth: 2,
                    shadow: { enabled: true, color: 'rgba(5,150,105,0.3)', size: 8, y: 4 }
                },
                'planning-executive': { 
                    color: { background: '#7c3aed', border: '#a78bfa' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 12 },
                    font: { bold: '600', size: 16, color: '#ffffff' },
                    borderWidth: 2,
                    shadow: { enabled: true, color: 'rgba(124,58,237,0.3)', size: 8, y: 4 }
                },
                'crown-jewel': { 
                    color: { background: '#dc2626', border: '#f87171' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 16 },
                    font: { bold: '700', size: 18, color: '#ffffff' },
                    borderWidth: 4,
                    shadow: { enabled: true, color: 'rgba(220,38,38,0.4)', size: 12, y: 6 },
                    size: 40
                },
                'validation-executive': { 
                    color: { background: '#ea580c', border: '#fb923c' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 12 },
                    font: { bold: '600', size: 16, color: '#ffffff' },
                    borderWidth: 2,
                    shadow: { enabled: true, color: 'rgba(234,88,12,0.3)', size: 8, y: 4 }
                },
                'synthesis-executive': { 
                    color: { background: '#0891b2', border: '#06b6d4' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 12 },
                    font: { bold: '600', size: 16, color: '#ffffff' },
                    borderWidth: 2,
                    shadow: { enabled: true, color: 'rgba(8,145,178,0.3)', size: 8, y: 4 }
                },
                'infrastructure': { 
                    color: { background: '#374151', border: '#6b7280' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 8 },
                    font: { bold: '500', size: 14, color: '#ffffff' },
                    borderWidth: 1,
                    shadow: { enabled: true, color: 'rgba(55,65,81,0.2)', size: 4, y: 2 }
                },
                'metrics': { 
                    color: { background: '#16a34a', border: '#22c55e' }, 
                    shape: 'ellipse',
                    font: { bold: '700', size: 16, color: '#ffffff' },
                    borderWidth: 3,
                    shadow: { enabled: true, color: 'rgba(22,163,74,0.4)', size: 10, y: 5 }
                },

                // Modern Flat Design Groups
                'flat-input': { 
                    color: { background: '#3b82f6', border: '#60a5fa' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 20 },
                    font: { bold: '600', size: 18, color: '#ffffff' },
                    borderWidth: 0,
                    shadow: { enabled: false }
                },
                'flat-process': { 
                    color: { background: '#10b981', border: '#34d399' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 20 },
                    font: { bold: '600', size: 18, color: '#ffffff' },
                    borderWidth: 0,
                    shadow: { enabled: false }
                },
                'flat-research': { 
                    color: { background: '#f59e0b', border: '#fbbf24' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 20 },
                    font: { bold: '600', size: 18, color: '#ffffff' },
                    borderWidth: 0,
                    shadow: { enabled: false }
                },
                'flat-output': { 
                    color: { background: '#8b5cf6', border: '#a78bfa' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 20 },
                    font: { bold: '600', size: 18, color: '#ffffff' },
                    borderWidth: 0,
                    shadow: { enabled: false }
                },

                // Swimlane Design Groups
                'lane-user': { 
                    color: { background: '#1e40af', border: '#3b82f6' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 8 },
                    font: { bold: '600', size: 14, color: '#ffffff' },
                    borderWidth: 2
                },
                'lane-agents': { 
                    color: { background: '#059669', border: '#10b981' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 8 },
                    font: { bold: '600', size: 14, color: '#ffffff' },
                    borderWidth: 2
                },
                'lane-data': { 
                    color: { background: '#7c3aed', border: '#a78bfa' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 8 },
                    font: { bold: '600', size: 14, color: '#ffffff' },
                    borderWidth: 2
                },

                // Technical Architecture Groups
                'tech-gateway': { 
                    color: { background: '#dc2626', border: '#ef4444' }, 
                    shape: 'hexagon',
                    font: { bold: '700', size: 14, color: '#ffffff' },
                    borderWidth: 3
                },
                'tech-service': { 
                    color: { background: '#2563eb', border: '#3b82f6' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 6 },
                    font: { bold: '600', size: 13, color: '#ffffff' },
                    borderWidth: 2
                },
                'tech-orchestrator': { 
                    color: { background: '#ea580c', border: '#f97316' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 10 },
                    font: { bold: '700', size: 15, color: '#ffffff' },
                    borderWidth: 3,
                    size: 35
                },
                'tech-database': { 
                    color: { background: '#059669', border: '#10b981' }, 
                    shape: 'database',
                    font: { bold: '600', size: 13, color: '#ffffff' },
                    borderWidth: 2
                },
                'tech-cache': { 
                    color: { background: '#7c3aed', border: '#8b5cf6' }, 
                    shape: 'diamond',
                    font: { bold: '600', size: 12, color: '#ffffff' },
                    borderWidth: 2
                },
                'tech-external': { 
                    color: { background: '#6b7280', border: '#9ca3af' }, 
                    shape: 'ellipse',
                    font: { bold: '500', size: 12, color: '#ffffff' },
                    borderWidth: 1
                },

                // C4 Model Engineering Standard Groups
                'c4-person': { 
                    color: { background: '#1e40af', border: '#3b82f6' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 15 },
                    font: { bold: '600', size: 14, color: '#ffffff' },
                    borderWidth: 3,
                    shadow: { enabled: true, color: 'rgba(30,64,175,0.3)', size: 6, y: 3 }
                },
                'c4-system': { 
                    color: { background: '#dc2626', border: '#ef4444' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 8 },
                    font: { bold: '700', size: 16, color: '#ffffff' },
                    borderWidth: 4,
                    shadow: { enabled: true, color: 'rgba(220,38,38,0.4)', size: 8, y: 4 },
                    size: 50
                },
                'c4-external': { 
                    color: { background: '#6b7280', border: '#9ca3af' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 8 },
                    font: { bold: '600', size: 14, color: '#ffffff' },
                    borderWidth: 3,
                    shadow: { enabled: true, color: 'rgba(107,114,128,0.3)', size: 6, y: 3 }
                },
                'c4-container': { 
                    color: { background: '#059669', border: '#10b981' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 6 },
                    font: { bold: '600', size: 13, color: '#ffffff' },
                    borderWidth: 2,
                    shadow: { enabled: true, color: 'rgba(5,150,105,0.3)', size: 5, y: 2 }
                },
                'c4-orchestrator': { 
                    color: { background: '#ea580c', border: '#f97316' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 8 },
                    font: { bold: '700', size: 15, color: '#ffffff' },
                    borderWidth: 4,
                    shadow: { enabled: true, color: 'rgba(234,88,12,0.4)', size: 8, y: 4 },
                    size: 45
                },
                'c4-database': { 
                    color: { background: '#7c3aed', border: '#8b5cf6' }, 
                    shape: 'database',
                    font: { bold: '600', size: 13, color: '#ffffff' },
                    borderWidth: 3,
                    shadow: { enabled: true, color: 'rgba(124,58,237,0.3)', size: 6, y: 3 }
                },
                'c4-component': { 
                    color: { background: '#0891b2', border: '#06b6d4' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 4 },
                    font: { bold: '500', size: 12, color: '#ffffff' },
                    borderWidth: 2,
                    shadow: { enabled: true, color: 'rgba(8,145,178,0.2)', size: 4, y: 2 }
                },

                // Data Flow Diagram (DFD) Standard Groups
                'dfd-entity': { 
                    color: { background: '#374151', border: '#6b7280' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 0 },
                    font: { bold: '600', size: 14, color: '#ffffff' },
                    borderWidth: 3,
                    shadow: { enabled: true, color: 'rgba(55,65,81,0.4)', size: 6, y: 3 }
                },
                'dfd-process': { 
                    color: { background: '#1e40af', border: '#3b82f6' }, 
                    shape: 'ellipse',
                    font: { bold: '600', size: 13, color: '#ffffff' },
                    borderWidth: 3,
                    shadow: { enabled: true, color: 'rgba(30,64,175,0.4)', size: 6, y: 3 },
                    size: 40
                },
                'dfd-datastore': { 
                    color: { background: '#059669', border: '#10b981' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 0 },
                    font: { bold: '500', size: 12, color: '#ffffff' },
                    borderWidth: 2,
                    borderDashes: [5, 5],
                    shadow: { enabled: true, color: 'rgba(5,150,105,0.3)', size: 5, y: 2 }
                },

                // Event-Driven Architecture Groups
                'eda-producer': { 
                    color: { background: '#dc2626', border: '#ef4444' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 8 },
                    font: { bold: '600', size: 13, color: '#ffffff' },
                    borderWidth: 3,
                    shadow: { enabled: true, color: 'rgba(220,38,38,0.4)', size: 6, y: 3 }
                },
                'eda-bus': { 
                    color: { background: '#7c3aed', border: '#8b5cf6' }, 
                    shape: 'diamond',
                    font: { bold: '700', size: 14, color: '#ffffff' },
                    borderWidth: 4,
                    shadow: { enabled: true, color: 'rgba(124,58,237,0.4)', size: 8, y: 4 },
                    size: 50
                },
                'eda-consumer': { 
                    color: { background: '#059669', border: '#10b981' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 6 },
                    font: { bold: '600', size: 12, color: '#ffffff' },
                    borderWidth: 2,
                    shadow: { enabled: true, color: 'rgba(5,150,105,0.3)', size: 5, y: 2 }
                },
                'eda-store': { 
                    color: { background: '#ea580c', border: '#f97316' }, 
                    shape: 'database',
                    font: { bold: '600', size: 13, color: '#ffffff' },
                    borderWidth: 3,
                    shadow: { enabled: true, color: 'rgba(234,88,12,0.4)', size: 6, y: 3 }
                },

                // Network Topology Engineering Groups
                'network-edge': { 
                    color: { background: '#dc2626', border: '#ef4444' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 10 },
                    font: { bold: '700', size: 14, color: '#ffffff' },
                    borderWidth: 4,
                    shadow: { enabled: true, color: 'rgba(220,38,38,0.4)', size: 8, y: 4 }
                },
                'network-security': { 
                    color: { background: '#7f1d1d', border: '#dc2626' }, 
                    shape: 'diamond',
                    font: { bold: '700', size: 13, color: '#ffffff' },
                    borderWidth: 4,
                    shadow: { enabled: true, color: 'rgba(127,29,29,0.5)', size: 8, y: 4 }
                },
                'network-compute': { 
                    color: { background: '#1e40af', border: '#3b82f6' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 8 },
                    font: { bold: '600', size: 13, color: '#ffffff' },
                    borderWidth: 3,
                    shadow: { enabled: true, color: 'rgba(30,64,175,0.4)', size: 6, y: 3 }
                },
                'network-mesh': { 
                    color: { background: '#7c3aed', border: '#8b5cf6' }, 
                    shape: 'hexagon',
                    font: { bold: '600', size: 13, color: '#ffffff' },
                    borderWidth: 3,
                    shadow: { enabled: true, color: 'rgba(124,58,237,0.4)', size: 6, y: 3 }
                },
                'network-database': { 
                    color: { background: '#059669', border: '#10b981' }, 
                    shape: 'database',
                    font: { bold: '600', size: 13, color: '#ffffff' },
                    borderWidth: 3,
                    shadow: { enabled: true, color: 'rgba(5,150,105,0.4)', size: 6, y: 3 }
                },
                'network-cache': { 
                    color: { background: '#ea580c', border: '#f97316' }, 
                    shape: 'diamond',
                    font: { bold: '600', size: 12, color: '#ffffff' },
                    borderWidth: 2,
                    shadow: { enabled: true, color: 'rgba(234,88,12,0.3)', size: 5, y: 2 }
                },
                'network-monitoring': { 
                    color: { background: '#374151', border: '#6b7280' }, 
                    shape: 'ellipse',
                    font: { bold: '500', size: 12, color: '#ffffff' },
                    borderWidth: 2,
                    shadow: { enabled: true, color: 'rgba(55,65,81,0.3)', size: 4, y: 2 }
                },

                // UML Component Diagram Groups
                'uml-component': { 
                    color: { background: '#2563eb', border: '#3b82f6' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 4 },
                    font: { bold: '600', size: 12, color: '#ffffff' },
                    borderWidth: 2,
                    shadow: { enabled: true, color: 'rgba(37,99,235,0.3)', size: 5, y: 2 }
                },
                'uml-orchestrator': { 
                    color: { background: '#dc2626', border: '#ef4444' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 6 },
                    font: { bold: '700', size: 14, color: '#ffffff' },
                    borderWidth: 3,
                    shadow: { enabled: true, color: 'rgba(220,38,38,0.4)', size: 7, y: 3 },
                    size: 40
                },
                'uml-repository': { 
                    color: { background: '#059669', border: '#10b981' }, 
                    shape: 'database',
                    font: { bold: '600', size: 12, color: '#ffffff' },
                    borderWidth: 2,
                    shadow: { enabled: true, color: 'rgba(5,150,105,0.3)', size: 5, y: 2 }
                },
                'uml-interface': { 
                    color: { background: '#7c3aed', border: '#8b5cf6' }, 
                    shape: 'ellipse',
                    font: { bold: '600', size: 11, color: '#ffffff' },
                    borderWidth: 2,
                    borderDashes: [3, 3],
                    shadow: { enabled: true, color: 'rgba(124,58,237,0.3)', size: 5, y: 2 }
                },

                // Infrastructure as Code (IaC) Groups
                'iac-terraform': { 
                    color: { background: '#7c3aed', border: '#8b5cf6' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 8 },
                    font: { bold: '700', size: 13, color: '#ffffff' },
                    borderWidth: 3,
                    shadow: { enabled: true, color: 'rgba(124,58,237,0.4)', size: 6, y: 3 }
                },
                'iac-k8s': { 
                    color: { background: '#1e40af', border: '#3b82f6' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 6 },
                    font: { bold: '600', size: 12, color: '#ffffff' },
                    borderWidth: 2,
                    shadow: { enabled: true, color: 'rgba(30,64,175,0.3)', size: 5, y: 2 }
                },
                'iac-helm': { 
                    color: { background: '#059669', border: '#10b981' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 6 },
                    font: { bold: '600', size: 12, color: '#ffffff' },
                    borderWidth: 2,
                    shadow: { enabled: true, color: 'rgba(5,150,105,0.3)', size: 5, y: 2 }
                },
                'iac-cicd': { 
                    color: { background: '#ea580c', border: '#f97316' }, 
                    shape: 'ellipse',
                    font: { bold: '600', size: 12, color: '#ffffff' },
                    borderWidth: 2,
                    shadow: { enabled: true, color: 'rgba(234,88,12,0.3)', size: 5, y: 2 }
                },
                'iac-docker': { 
                    color: { background: '#0891b2', border: '#06b6d4' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 4 },
                    font: { bold: '600', size: 12, color: '#ffffff' },
                    borderWidth: 2,
                    shadow: { enabled: true, color: 'rgba(8,145,178,0.3)', size: 5, y: 2 }
                },
                'iac-cloud': { 
                    color: { background: '#dc2626', border: '#ef4444' }, 
                    shape: 'box', 
                    shapeProperties: { borderRadius: 10 },
                    font: { bold: '700', size: 14, color: '#ffffff' },
                    borderWidth: 3,
                    shadow: { enabled: true, color: 'rgba(220,38,38,0.4)', size: 7, y: 3 },
                    size: 35
                },
            },
            physics: {
                enabled: !isHierarchical,
                stabilization: {
                    enabled: isHierarchical && !isHorizontalLayout, // Disable stabilization for fixed horizontal layout
                    iterations: isHorizontalLayout ? 50 : 100,
                    updateInterval: 25
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 200,
                navigationButtons: true,
                zoomView: true,
                dragView: true
            },
            layout: {
                hierarchical: {
                    enabled: isHierarchical && !nodes.some(node => node.fixed), // Disable hierarchical for fixed positioned nodes
                    levelSeparation: isHorizontalLayout ? 200 : 150,
                    nodeSpacing: isHorizontalLayout ? 150 : 100,
                    treeSpacing: isHorizontalLayout ? 200 : 200,
                    blockShifting: true,
                    edgeMinimization: true,
                    parentCentralization: true,
                    direction: isHorizontalLayout ? 'LR' : 'UD',        // LR = Left to Right, UD = Up to Down
                    sortMethod: 'directed',
                    shakeTowards: 'roots'
                },
                randomSeed: isHorizontalLayout ? 42 : undefined, // Use consistent seed for horizontal layout
            },
        };

        network.setOptions(options);

        // Enhanced coordinate logger for layout positioning
        if (isHierarchical) {
            network.on('dragEnd', (params) => {
                if (params.nodes.length > 0) {
                    const nodeId = params.nodes[0];
                    const positions = network.getPositions([nodeId]);
                    const position = positions[nodeId];
                    console.log(`{ id: '${nodeId}', x: ${Math.round(position.x)}, y: ${Math.round(position.y)} },`);
                }
            });

            // Auto-fit the network when layout changes
            setTimeout(() => {
                network.fit({
                    animation: {
                        duration: 1000,
                        easingFunction: 'easeInOutQuad'
                    }
                });
            }, 100);
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
    }, [nodes, edges, onNodeClick, isHierarchical, isHorizontalLayout]);

    return <div ref={visJsRef} style={{ height: '100%', width: '100%' }} />;
};

export default VisNetwork; 