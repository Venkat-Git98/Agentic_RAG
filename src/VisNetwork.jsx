import React, { useEffect, useRef } from 'react';
import { DataSet, Network } from 'vis-network/standalone/esm/vis-network.min.js';
import 'vis-network/styles/vis-network.css';

const VisNetwork = ({ nodes, edges, onNodeClick }) => {
  const containerRef = useRef(null);
  const networkRef = useRef(null);

  useEffect(() => {
    if (containerRef.current) {
      const visNodes = new DataSet(nodes);
      const visEdges = new DataSet(edges);

      const data = {
        nodes: visNodes,
        edges: visEdges,
      };

      const options = {
        nodes: {
          shape: 'dot',
          size: 25,
          font: {
            color: '#ffffff',
          },
          borderWidth: 2,
          color: {
            border: '#2B7CE9',
            background: '#97C2FC',
            highlight: {
              border: '#2B7CE9',
              background: '#D2E5FF'
            },
            hover: {
              border: '#2B7CE9',
              background: '#D2E5FF'
            }
          }
        },
        edges: {
          width: 1,
          color: {
            color: '#FFFFFF',
            highlight: '#FFFFFF',
            hover: '#FFFFFF',
            inherit: false,
          },
          arrows: {
            to: {
              enabled: true,
              scaleFactor: 1,
              type: 'arrow',
            },
          },
          font: {
            color: '#ffffff',
            size: 14,
            face: 'arial',
            background: 'none',
            strokeWidth: 0,
          },
        },
        physics: {
          barnesHut: {
            gravitationalConstant: -5000,
            centralGravity: 0.1,
            springLength: 200,
          },
          minVelocity: 0.75,
          solver: 'barnesHut',
        },
      };

      networkRef.current = new Network(containerRef.current, data, options);

      if (onNodeClick) {
        networkRef.current.on('click', (params) => {
          if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const node = visNodes.get(nodeId);
            onNodeClick(params, node);
          }
        });
      }
    }

    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [nodes, edges, onNodeClick]);

  return <div ref={containerRef} style={{ width: '100%', height: '100%' }} />;
};

export default VisNetwork; 