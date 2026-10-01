import { useEffect, useRef } from "react";
import { Network } from "vis-network";
import "vis-network/styles/vis-network.css";

export type GraphNode = { id: string; label: string; group: string; title?: string };
export type GraphEdge = { id: string; from: string; to: string; label?: string; arrows?: string };

const cssVar = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

/** Node size and theme token per kind of graph node. */
const KINDS: Record<string, { size: number; token: string }> = {
  Chapter: { size: 22, token: "--foreground" },
  Section: { size: 18, token: "--primary" },
  Subsection: { size: 12, token: "--primary" },
  Passage: { size: 6, token: "--muted-foreground" },
  Table: { size: 11, token: "--ok" },
  Math: { size: 9, token: "--amber" },
  Diagram: { size: 9, token: "--amber" },
  Standard: { size: 9, token: "--redline" },
};

export function GraphCanvas({
  nodes,
  edges,
  onNodeClick,
}: {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick?: (node: GraphNode) => void;
}) {
  const container = useRef<HTMLDivElement>(null);

  // Keep the latest click handler in a ref so a parent re-render never rebuilds
  // (and re-lays-out) the whole network.
  const clickRef = useRef(onNodeClick);
  useEffect(() => {
    clickRef.current = onNodeClick;
  }, [onNodeClick]);

  useEffect(() => {
    if (!container.current) return;
    const foreground = cssVar("--foreground");
    const styled = nodes.map((node) => {
      const kind = KINDS[node.group] ?? { size: 8, token: "--muted-foreground" };
      const color = cssVar(kind.token);
      return {
        ...node,
        // Passages are too many to label; everything else shows its number.
        label: node.group === "Passage" ? undefined : node.label,
        shape: "dot",
        size: kind.size,
        color: { background: color, border: color, highlight: { background: cssVar("--redline"), border: foreground } },
      };
    });
    const network = new Network(
      container.current,
      { nodes: styled, edges },
      {
        autoResize: true,
        nodes: { font: { color: foreground, size: 12, face: "IBM Plex Mono, monospace" }, borderWidth: 1 },
        edges: {
          color: { color: cssVar("--border"), highlight: cssVar("--primary") },
          font: { size: 0 },
          smooth: false,
          arrows: { to: { enabled: true, scaleFactor: 0.4 } },
        },
        physics: { solver: "barnesHut", barnesHut: { gravitationalConstant: -3500, springLength: 70 }, stabilization: { iterations: 250 } },
        interaction: { hover: true, tooltipDelay: 150 },
      },
    );
    network.once("stabilized", () => network.setOptions({ physics: false }));
    network.on("click", (event: { nodes: string[] }) => {
      const node = nodes.find((n) => n.id === String(event.nodes[0]));
      if (node) clickRef.current?.(node);
    });
    return () => network.destroy();
  }, [nodes, edges]);

  return <div ref={container} className="size-full" />;
}
