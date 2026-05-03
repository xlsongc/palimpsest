import type { GraphNodeDTO, GraphEdgeDTO } from "../../api";
import { themes } from "./data";
import type { ReadingStatus, ThemeKey } from "./data";

interface Props {
  nodes: GraphNodeDTO[];
  edges: GraphEdgeDTO[];
  loading: boolean;
  activeStatus: "all" | ReadingStatus;
  selectedId: number | null;
  onSelectNode: (id: number) => void;
}

// Assign theme based on tags
function inferTheme(tags: string[]): ThemeKey {
  const tagStr = tags.join(" ");
  if (/投资|金融|经济/.test(tagStr)) return "finance";
  if (/编程|计算机|算法|技术/.test(tagStr)) return "cs";
  if (/历史|人文/.test(tagStr)) return "history";
  if (/AI|科技|传记/.test(tagStr)) return "ai";
  if (/文学|小说/.test(tagStr)) return "literature";
  if (/心理|社科/.test(tagStr)) return "psychology";
  if (/数学|信息/.test(tagStr)) return "math";
  if (/哲学|思想/.test(tagStr)) return "biography";
  return "cs"; // default
}

function stableNoise(seed: string, salt: string): number {
  let hash = 0;
  const input = `${seed}:${salt}`;
  for (let i = 0; i < input.length; i += 1) {
    hash = (hash * 31 + input.charCodeAt(i)) >>> 0;
  }
  return (hash % 1000) / 1000 - 0.5;
}

// Assign position based on theme cluster with deterministic jitter.
function assignPosition(node: GraphNodeDTO, index: number, total: number): { x: number; y: number } {
  const theme = inferTheme(node.tags);
  const clusters: Record<ThemeKey, { cx: number; cy: number }> = {
    cs: { cx: 15, cy: 35 },
    ai: { cx: 30, cy: 40 },
    history: { cx: 48, cy: 25 },
    finance: { cx: 68, cy: 45 },
    literature: { cx: 80, cy: 15 },
    psychology: { cx: 78, cy: 35 },
    math: { cx: 25, cy: 60 },
    biography: { cx: 55, cy: 50 },
  };

  const cluster = clusters[theme];
  const safeTotal = Math.max(total, 1);
  const angle = (index / safeTotal) * Math.PI * 2;
  const radius = 8 + (index % 5) * 3;
  const seed = `${node.id}:${node.title}`;
  const x = cluster.cx + Math.cos(angle) * radius + stableNoise(seed, "x") * 4;
  const y = cluster.cy + Math.sin(angle) * radius + stableNoise(seed, "y") * 4;

  return { x: Math.max(5, Math.min(95, x)), y: Math.max(5, Math.min(95, y)) };
}

export default function GraphCanvas({ nodes, edges, loading, activeStatus, selectedId, onSelectNode }: Props) {
  const positions = new Map<number, { x: number; y: number }>();
  nodes.forEach((node, index) => {
    positions.set(node.id, assignPosition(node, index, nodes.length));
  });

  if (loading) {
    return (
      <section className="graph-workbench" aria-label="Reading graph preview">
        <div className="loading-indicator">Loading graph...</div>
      </section>
    );
  }

  if (nodes.length === 0) {
    return (
      <section className="graph-workbench" aria-label="Reading graph preview">
        <div className="empty-graph">
          <p>No books in library yet.</p>
          <p>Import some books first.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="graph-workbench" aria-label="Reading graph preview">
      {/* Theme fields */}
      <div className="theme-field finance-field" />
      <div className="theme-field cs-field" />
      <div className="theme-field history-field" />
      <div className="theme-field literature-field" />
      <div className="theme-field psychology-field" />

      {/* Edges */}
      <svg className="edge-layer" viewBox="0 0 1000 720" role="presentation">
        {edges.map((edge) => {
          const srcPos = positions.get(edge.source_book_id);
          const tgtPos = positions.get(edge.target_book_id);
          if (!srcPos || !tgtPos) return null;

          const x1 = srcPos.x * 10;
          const y1 = srcPos.y * 7.2;
          const x2 = tgtPos.x * 10;
          const y2 = tgtPos.y * 7.2;
          const mx = (x1 + x2) / 2;
          const my = (y1 + y2) / 2 - 20;

          return (
            <path
              d={`M${x1} ${y1} Q${mx} ${my} ${x2} ${y2}`}
              key={edge.id}
              style={{ stroke: themes[inferTheme(nodes.find(n => n.id === edge.source_book_id)?.tags || [])]?.color || "#999" }}
            />
          );
        })}
      </svg>

      {/* Nodes */}
      {nodes.map((node) => {
        const pos = positions.get(node.id);
        if (!pos) return null;

        const status = (node.status || "want") as ReadingStatus;
        const theme = inferTheme(node.tags);
        const muted = activeStatus !== "all" && activeStatus !== status;
        const isSelected = selectedId === node.id;
        const isImportant = node.rating !== null && node.rating >= 8.5;

        return (
          <button
            className={[
              "book-node",
              status,
              isImportant ? "lg" : "md",
              muted ? "muted" : "",
              isSelected ? "selected" : "",
            ].join(" ")}
            key={node.id}
            onClick={() => onSelectNode(node.id)}
            style={{
              "--x": `${pos.x}%`,
              "--y": `${pos.y}%`,
              "--theme": themes[theme].color,
            } as React.CSSProperties}
          >
            <span>{node.title}</span>
          </button>
        );
      })}
    </section>
  );
}
