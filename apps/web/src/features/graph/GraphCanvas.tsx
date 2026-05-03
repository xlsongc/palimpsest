import { useRef, useState } from "react";
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

interface LayoutNode {
  node: GraphNodeDTO;
  theme: ThemeKey;
  x: number;
  y: number;
}

const VIEWBOX = { width: 1000, height: 720 };

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
  return "cs";
}

function stableHash(input: string): number {
  let hash = 2166136261;
  for (let i = 0; i < input.length; i += 1) {
    hash ^= input.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function stableUnit(seed: string, salt: string): number {
  return (stableHash(`${seed}:${salt}`) % 1000) / 1000;
}

function buildLayout(nodes: GraphNodeDTO[]): LayoutNode[] {
  const anchors: Record<ThemeKey, { x: number; y: number }> = {
    cs: { x: 170, y: 285 },
    ai: { x: 325, y: 395 },
    history: { x: 535, y: 205 },
    finance: { x: 665, y: 405 },
    literature: { x: 805, y: 155 },
    psychology: { x: 805, y: 340 },
    math: { x: 325, y: 545 },
    biography: { x: 565, y: 470 },
  };

  const groups = new Map<ThemeKey, GraphNodeDTO[]>();
  for (const node of nodes) {
    const theme = inferTheme(node.tags);
    groups.set(theme, [...(groups.get(theme) ?? []), node]);
  }

  const laidOut: LayoutNode[] = [];
  for (const [theme, group] of groups) {
    const anchor = anchors[theme];
    const sorted = [...group].sort((a, b) => a.id - b.id);
    const count = Math.max(sorted.length, 1);

    sorted.forEach((node, index) => {
      const seed = `${node.id}:${node.title}`;
      const ring = Math.floor(index / 7);
      const angle = (index / count) * Math.PI * 2 + stableUnit(seed, "angle") * 0.72;
      const radius = 34 + ring * 34 + (index % 7) * 9 + stableUnit(seed, "radius") * 20;
      laidOut.push({
        node,
        theme,
        x: anchor.x + Math.cos(angle) * radius,
        y: anchor.y + Math.sin(angle) * radius * 0.78,
      });
    });
  }

  if (laidOut.length === 0) return laidOut;

  const minX = Math.min(...laidOut.map((n) => n.x));
  const maxX = Math.max(...laidOut.map((n) => n.x));
  const minY = Math.min(...laidOut.map((n) => n.y));
  const maxY = Math.max(...laidOut.map((n) => n.y));
  const padding = 72;
  const width = Math.max(maxX - minX, 1);
  const height = Math.max(maxY - minY, 1);
  const scale = Math.min(
    (VIEWBOX.width - padding * 2) / width,
    (VIEWBOX.height - padding * 2) / height,
    1.18,
  );
  const centerX = (minX + maxX) / 2;
  const centerY = (minY + maxY) / 2;

  return laidOut.map((item) => ({
    ...item,
    x: VIEWBOX.width / 2 + (item.x - centerX) * scale,
    y: VIEWBOX.height / 2 + (item.y - centerY) * scale,
  }));
}

function limitEdges(
  edges: GraphEdgeDTO[],
  positions: Map<number, LayoutNode>,
  selectedId: number | null,
): GraphEdgeDTO[] {
  const visible = edges
    .filter((edge) => positions.has(edge.source_book_id) && positions.has(edge.target_book_id))
    .sort((a, b) => b.weight - a.weight);

  if (selectedId) {
    return visible.filter(
      (edge) => edge.source_book_id === selectedId || edge.target_book_id === selectedId,
    );
  }

  const perNode = new Map<number, number>();
  const result: GraphEdgeDTO[] = [];
  for (const edge of visible) {
    const sourceCount = perNode.get(edge.source_book_id) ?? 0;
    const targetCount = perNode.get(edge.target_book_id) ?? 0;
    if (sourceCount >= 3 || targetCount >= 3) continue;
    result.push(edge);
    perNode.set(edge.source_book_id, sourceCount + 1);
    perNode.set(edge.target_book_id, targetCount + 1);
    if (result.length >= 42) break;
  }
  return result;
}

function edgePath(source: LayoutNode, target: LayoutNode): string {
  const dx = target.x - source.x;
  const dy = target.y - source.y;
  const distance = Math.max(Math.hypot(dx, dy), 1);
  const bend = Math.min(54, distance * 0.12);
  const normalX = (-dy / distance) * bend;
  const normalY = (dx / distance) * bend;
  const c1x = source.x + dx * 0.35 + normalX;
  const c1y = source.y + dy * 0.35 + normalY;
  const c2x = source.x + dx * 0.65 + normalX;
  const c2y = source.y + dy * 0.65 + normalY;
  return `M${source.x.toFixed(1)} ${source.y.toFixed(1)} C${c1x.toFixed(1)} ${c1y.toFixed(1)} ${c2x.toFixed(1)} ${c2y.toFixed(1)} ${target.x.toFixed(1)} ${target.y.toFixed(1)}`;
}

function displayTitle(title: string): string {
  return title.length > 26 ? `${title.slice(0, 24)}...` : title;
}

export default function GraphCanvas({
  nodes,
  edges,
  loading,
  activeStatus,
  selectedId,
  onSelectNode,
}: Props) {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const dragRef = useRef<{ x: number; y: number; panX: number; panY: number } | null>(null);

  const layout = buildLayout(nodes);
  const positions = new Map(layout.map((item) => [item.node.id, item]));
  const visibleEdges = limitEdges(edges, positions, selectedId);

  function resetView() {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }

  function handleWheel(event: React.WheelEvent<SVGSVGElement>) {
    event.preventDefault();
    const next = Math.max(0.72, Math.min(2.25, zoom * (event.deltaY > 0 ? 0.92 : 1.08)));
    setZoom(next);
  }

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
      <div className="theme-field finance-field" />
      <div className="theme-field cs-field" />
      <div className="theme-field history-field" />
      <div className="theme-field humanities-field" />

      <div className="graph-controls" aria-label="Graph view controls">
        <button onClick={() => setZoom((value) => Math.min(2.25, value * 1.14))}>+</button>
        <button onClick={() => setZoom((value) => Math.max(0.72, value / 1.14))}>−</button>
        <button onClick={resetView}>FIT</button>
      </div>

      <svg
        className="graph-layer"
        viewBox={`0 0 ${VIEWBOX.width} ${VIEWBOX.height}`}
        role="presentation"
        onWheel={handleWheel}
        onPointerDown={(event) => {
          dragRef.current = { x: event.clientX, y: event.clientY, panX: pan.x, panY: pan.y };
          event.currentTarget.setPointerCapture(event.pointerId);
        }}
        onPointerMove={(event) => {
          if (!dragRef.current) return;
          setPan({
            x: dragRef.current.panX + (event.clientX - dragRef.current.x),
            y: dragRef.current.panY + (event.clientY - dragRef.current.y),
          });
        }}
        onPointerUp={() => {
          dragRef.current = null;
        }}
      >
        <g transform={`translate(${pan.x} ${pan.y}) scale(${zoom})`}>
          <g className="edge-layer">
            {visibleEdges.map((edge) => {
              const source = positions.get(edge.source_book_id);
              const target = positions.get(edge.target_book_id);
              if (!source || !target) return null;
              const isSelected =
                selectedId === edge.source_book_id || selectedId === edge.target_book_id;
              return (
                <path
                  className={isSelected || edge.weight >= 5 ? "strong" : ""}
                  d={edgePath(source, target)}
                  key={edge.id}
                  style={{ stroke: themes[source.theme].color }}
                />
              );
            })}
          </g>

          <g className="node-layer">
            {layout.map(({ node, theme, x, y }) => {
              const status = (node.status || "want") as ReadingStatus;
              const muted = activeStatus !== "all" && activeStatus !== status;
              const isSelected = selectedId === node.id;
              const isImportant = node.rating !== null && node.rating >= 8.5;
              return (
                <g
                  className={[
                    "graph-node",
                    status,
                    muted ? "muted" : "",
                    isSelected ? "selected" : "",
                  ].join(" ")}
                  key={node.id}
                  onClick={(event) => {
                    event.stopPropagation();
                    onSelectNode(node.id);
                  }}
                  style={{ "--theme": themes[theme].color } as React.CSSProperties}
                  transform={`translate(${x.toFixed(1)} ${y.toFixed(1)})`}
                >
                  <circle r={isImportant ? 19 : 12} />
                  <text y={isImportant ? -25 : -19}>{displayTitle(node.title)}</text>
                </g>
              );
            })}
          </g>
        </g>
      </svg>
    </section>
  );
}
