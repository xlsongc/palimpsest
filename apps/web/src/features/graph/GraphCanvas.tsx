import { useEffect, useRef } from "react";
import * as d3 from "d3";
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

interface SimNode extends d3.SimulationNodeDatum {
  id: number;
  title: string;
  authors: string[];
  status: ReadingStatus;
  rating: number | null;
  tags: string[];
  theme: ThemeKey;
  degree: number;
}

interface SimLink extends d3.SimulationLinkDatum<SimNode> {
  id: number;
  source: number | SimNode;
  target: number | SimNode;
  source_book_id: number;
  target_book_id: number;
  edge_type: string;
  weight: number;
  reason: string | null;
}

const TOPBAR_HEIGHT = 52;

function inferTheme(tags: string[]): ThemeKey {
  const tagStr = tags.join(" ");
  if (/投资|金融|经济|财报|基金|股票/.test(tagStr)) return "finance";
  if (/编程|计算机|算法|技术|Python|软件|系统/.test(tagStr)) return "cs";
  if (/历史|人文|政治|战争|帝国/.test(tagStr)) return "history";
  if (/AI|人工智能|科技|芯片|机器学习|deep|learning/i.test(tagStr)) return "ai";
  if (/文学|小说|毛姆|奥威尔|村上/.test(tagStr)) return "literature";
  if (/心理|社科|行为|神经/.test(tagStr)) return "psychology";
  if (/数学|信息|统计|线性代数/.test(tagStr)) return "math";
  if (/哲学|思想|传记|自传|原则/.test(tagStr)) return "biography";
  return "cs";
}

function normalizeStatus(status: string | null): ReadingStatus {
  if (status === "read" || status === "读过") return "read";
  if (status === "reading" || status === "在读") return "reading";
  return "want";
}

function stableHash(input: string): number {
  let hash = 2166136261;
  for (let index = 0; index < input.length; index += 1) {
    hash ^= input.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function stableUnit(seed: string, salt: string): number {
  return (stableHash(`${seed}:${salt}`) % 1000) / 1000;
}

function displayTitle(title: string): string {
  return title.length > 22 ? `${title.slice(0, 20)}...` : title;
}

function nodeRadius(node: SimNode): number {
  const base = node.status === "read" ? 10 : node.status === "reading" ? 8 : 5.5;
  const ratingBoost = node.rating !== null && node.rating >= 8.5 ? 3 : 0;
  return base + node.degree * 1.2 + ratingBoost;
}

function statusFillOpacity(status: ReadingStatus): number {
  if (status === "read") return 0.92;
  if (status === "reading") return 0.6;
  return 0.18;
}

function statusStroke(status: ReadingStatus): string {
  if (status === "read") return "#2B6B3A";
  if (status === "reading") return "#8B6914";
  return "#9A9088";
}

function curvePath(link: SimLink): string {
  const source = link.source as SimNode;
  const target = link.target as SimNode;
  const sx = source.x ?? 0;
  const sy = source.y ?? 0;
  const tx = target.x ?? 0;
  const ty = target.y ?? 0;
  const dx = tx - sx;
  const dy = ty - sy;
  const len = Math.max(Math.hypot(dx, dy), 1);
  const off = Math.min(len * 0.18, 40);
  const nx = (-dy / len) * off;
  const ny = (dx / len) * off;
  return `M${sx},${sy} Q${(sx + tx) / 2 + nx},${(sy + ty) / 2 + ny} ${tx},${ty}`;
}

function makeThemeAnchors(width: number, height: number): Record<ThemeKey, { x: number; y: number }> {
  return {
    cs: { x: width * 0.18, y: height * 0.34 },
    ai: { x: width * 0.36, y: height * 0.44 },
    history: { x: width * 0.55, y: height * 0.32 },
    finance: { x: width * 0.68, y: height * 0.5 },
    literature: { x: width * 0.82, y: height * 0.2 },
    psychology: { x: width * 0.82, y: height * 0.42 },
    math: { x: width * 0.36, y: height * 0.72 },
    biography: { x: width * 0.58, y: height * 0.62 },
  };
}

export default function GraphCanvas({
  nodes,
  edges,
  loading,
  activeStatus,
  selectedId,
  onSelectNode,
}: Props) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const tooltipRef = useRef<HTMLDivElement | null>(null);
  const activeStatusRef = useRef(activeStatus);
  const selectedIdRef = useRef(selectedId);
  const onSelectNodeRef = useRef(onSelectNode);
  const updateVisualStateRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    activeStatusRef.current = activeStatus;
    selectedIdRef.current = selectedId;
    onSelectNodeRef.current = onSelectNode;
    updateVisualStateRef.current?.();
  }, [activeStatus, selectedId, onSelectNode]);

  useEffect(() => {
    const svgElement = svgRef.current;
    if (!svgElement || loading || nodes.length === 0) return undefined;

    const svg = d3.select(svgElement);
    svg.selectAll("*").remove();

    const rect = svgElement.getBoundingClientRect();
    const width = Math.max(rect.width, 900);
    const height = Math.max(rect.height, 640);
    const anchors = makeThemeAnchors(width, height);

    const degree = new Map<number, number>();
    nodes.forEach((node) => degree.set(node.id, 0));
    edges.forEach((edge) => {
      degree.set(edge.source_book_id, (degree.get(edge.source_book_id) ?? 0) + 1);
      degree.set(edge.target_book_id, (degree.get(edge.target_book_id) ?? 0) + 1);
    });

    const simNodes: SimNode[] = nodes.map((node) => {
      const theme = inferTheme(node.tags);
      const anchor = anchors[theme];
      const seed = `${node.id}:${node.title}`;
      return {
        ...node,
        status: normalizeStatus(node.status),
        theme,
        degree: degree.get(node.id) ?? 0,
        x: anchor.x + (stableUnit(seed, "x") - 0.5) * 220,
        y: anchor.y + (stableUnit(seed, "y") - 0.5) * 180,
      };
    });
    const nodeById = new Map(simNodes.map((node) => [node.id, node]));
    const simLinks: SimLink[] = edges
      .filter((edge) => nodeById.has(edge.source_book_id) && nodeById.has(edge.target_book_id))
      .map((edge) => ({
        ...edge,
        source: edge.source_book_id,
        target: edge.target_book_id,
      }));

    const defs = svg.append("defs");
    const shadow = defs
      .append("filter")
      .attr("id", "graph-node-shadow")
      .attr("x", "-30%")
      .attr("y", "-30%")
      .attr("width", "160%")
      .attr("height", "160%");
    shadow
      .append("feDropShadow")
      .attr("dx", "0")
      .attr("dy", "1")
      .attr("stdDeviation", "3")
      .attr("flood-color", "rgba(0,0,0,0.18)");

    const root = svg.append("g").attr("class", "d3-graph-root");
    const zoneGroup = root.append("g").attr("class", "zones");
    const linkGroup = root.append("g").attr("class", "edge-layer");
    const ringGroup = root.append("g").attr("class", "focus-ring-layer");
    const nodeGroup = root.append("g").attr("class", "node-layer");
    const labelGroup = root.append("g").attr("class", "label-layer");

    const zoomBehavior = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.18, 4])
      .on("zoom", (event) => {
        root.attr("transform", event.transform.toString());
      });
    svg.call(zoomBehavior);

    const linkSel = linkGroup
      .selectAll<SVGPathElement, SimLink>("path")
      .data(simLinks)
      .join("path")
      .attr("fill", "none")
      .attr("stroke-linecap", "round")
      .attr("stroke", (link) => {
        const source = nodeById.get(link.source_book_id);
        return source ? themes[source.theme].color : "#C4BCB4";
      })
      .attr("stroke-width", (link) => Math.max(0.5, link.weight * 0.55))
      .attr("stroke-opacity", (link) => 0.14 + link.weight * 0.04);

    const nodeSel = nodeGroup
      .selectAll<SVGCircleElement, SimNode>("circle")
      .data(simNodes)
      .join("circle")
      .attr("r", nodeRadius)
      .attr("fill", (node) => themes[node.theme].color)
      .attr("fill-opacity", (node) => statusFillOpacity(node.status))
      .attr("stroke", (node) => statusStroke(node.status))
      .attr("stroke-width", (node) => (node.status === "read" ? 2 : node.status === "reading" ? 1.6 : 1))
      .attr("stroke-dasharray", (node) => (node.status === "reading" ? "4,2" : "none"))
      .attr("filter", (node) => (node.status === "read" ? "url(#graph-node-shadow)" : "none"))
      .style("cursor", "pointer")
      .call(
        d3
          .drag<SVGCircleElement, SimNode>()
          .on("start", (event, node) => {
            if (!event.active) simulation.alphaTarget(0.24).restart();
            node.fx = node.x;
            node.fy = node.y;
          })
          .on("drag", (event, node) => {
            node.fx = event.x;
            node.fy = event.y;
          })
          .on("end", (event, node) => {
            if (!event.active) simulation.alphaTarget(0);
            node.fx = null;
            node.fy = null;
          }),
      );

    const labelSel = labelGroup
      .selectAll<SVGTextElement, SimNode>("text")
      .data(simNodes)
      .join("text")
      .attr("class", "node-label")
      .attr("text-anchor", "middle")
      .attr("dy", (node) => -nodeRadius(node) - 5)
      .text((node) => {
        if (node.status !== "want" || node.degree >= 2) return displayTitle(node.title);
        return "";
      })
      .attr("font-size", "14px")
      .attr("fill", (node) => (node.status === "read" ? "#1A1714" : node.status === "reading" ? "#3D3830" : "#9A9088"))
      .attr("font-weight", (node) => (node.status === "read" ? "700" : "400"));

    function connectedIds(node: SimNode): Set<number> {
      const ids = new Set<number>([node.id]);
      simLinks.forEach((link) => {
        const source = link.source as SimNode;
        const target = link.target as SimNode;
        if (source.id === node.id) ids.add(target.id);
        if (target.id === node.id) ids.add(source.id);
      });
      return ids;
    }

    function isVisible(node: SimNode): boolean {
      const filter = activeStatusRef.current;
      return filter === "all" || filter === node.status;
    }

    function linkEndpoints(link: SimLink): [SimNode, SimNode] {
      return [link.source as SimNode, link.target as SimNode];
    }

    function drawZones() {
      zoneGroup.selectAll("*").remove();
      const grouped = d3.group(simNodes.filter((node) => node.x !== undefined && node.y !== undefined), (node) => node.theme);
      grouped.forEach((themeNodes, theme) => {
        if (themeNodes.length < 2) return;
        const xs = themeNodes.map((node) => node.x ?? 0);
        const ys = themeNodes.map((node) => node.y ?? 0);
        const minX = Math.min(...xs);
        const maxX = Math.max(...xs);
        const minY = Math.min(...ys);
        const maxY = Math.max(...ys);
        zoneGroup
          .append("ellipse")
          .attr("cx", (minX + maxX) / 2)
          .attr("cy", (minY + maxY) / 2)
          .attr("rx", Math.max((maxX - minX) / 2 + 55, 70))
          .attr("ry", Math.max((maxY - minY) / 2 + 55, 70))
          .attr("fill", themes[theme].color)
          .attr("fill-opacity", 0.04)
          .attr("stroke", themes[theme].color)
          .attr("stroke-width", 0.5)
          .attr("stroke-opacity", 0.08)
          .style("pointer-events", "none");
      });
    }

    function drawRing(ids: Set<number>, theme: ThemeKey) {
      ringGroup.selectAll("*").remove();
      const ringNodes = simNodes.filter((node) => ids.has(node.id) && node.x !== undefined && node.y !== undefined);
      if (ringNodes.length < 2) return;
      const xs = ringNodes.map((node) => node.x ?? 0);
      const ys = ringNodes.map((node) => node.y ?? 0);
      const minX = Math.min(...xs);
      const maxX = Math.max(...xs);
      const minY = Math.min(...ys);
      const maxY = Math.max(...ys);
      ringGroup
        .append("ellipse")
        .attr("cx", (minX + maxX) / 2)
        .attr("cy", (minY + maxY) / 2)
        .attr("rx", Math.max((maxX - minX) / 2 + 38, 50))
        .attr("ry", Math.max((maxY - minY) / 2 + 38, 50))
        .attr("fill", "none")
        .attr("stroke", themes[theme].color)
        .attr("stroke-width", 1.2)
        .attr("stroke-opacity", 0.3)
        .attr("stroke-dasharray", "4,5")
        .style("pointer-events", "none");
    }

    function applyVisualState(focusIds?: Set<number>) {
      const selected = selectedIdRef.current;
      let selectedIds: Set<number> | undefined = focusIds;
      const selectedNode = selected ? nodeById.get(selected) : null;
      if (!selectedIds && selectedNode) selectedIds = connectedIds(selectedNode);

      nodeSel
        .attr("display", (node) => (isVisible(node) ? null : "none"))
        .attr("fill-opacity", (node) => {
          if (!isVisible(node)) return 0;
          if (!selectedIds) return statusFillOpacity(node.status);
          return selectedIds.has(node.id) ? Math.max(statusFillOpacity(node.status), 0.55) : 0.04;
        })
        .attr("stroke-opacity", (node) => {
          if (!isVisible(node)) return 0;
          if (!selectedIds) return node.status === "want" ? 0.45 : 0.85;
          return selectedIds.has(node.id) ? 1 : 0.06;
        })
        .attr("r", (node) => (selected === node.id ? nodeRadius(node) * 1.18 : nodeRadius(node)));

      linkSel
        .attr("display", (link) => {
          const [source, target] = linkEndpoints(link);
          return isVisible(source) && isVisible(target) ? null : "none";
        })
        .attr("stroke-opacity", (link) => {
          const [source, target] = linkEndpoints(link);
          if (!isVisible(source) || !isVisible(target)) return 0;
          if (!selectedIds) return 0.14 + link.weight * 0.04;
          return selectedIds.has(source.id) && selectedIds.has(target.id) ? 0.66 : 0.03;
        })
        .attr("stroke-width", (link) => {
          const [source, target] = linkEndpoints(link);
          const active = selectedIds?.has(source.id) && selectedIds.has(target.id);
          return active ? Math.max(1.2, link.weight * 1.1) : Math.max(0.5, link.weight * 0.55);
        });

      labelSel
        .attr("display", (node) => (isVisible(node) ? null : "none"))
        .attr("fill", (node) => {
          if (!selectedIds) return node.status === "read" ? "#1A1714" : node.status === "reading" ? "#3D3830" : "#9A9088";
          return selectedIds.has(node.id) ? "#1A1714" : "#C4BCB4";
        })
        .attr("font-size", (node) => (selected === node.id ? "15px" : "14px"));

      if (selectedNode) drawRing(selectedIds ?? new Set([selectedNode.id]), selectedNode.theme);
      else if (!focusIds) ringGroup.selectAll("*").remove();
    }

    function autoFit() {
      const xs = simNodes.map((node) => node.x).filter((value): value is number => typeof value === "number");
      const ys = simNodes.map((node) => node.y).filter((value): value is number => typeof value === "number");
      if (xs.length === 0 || ys.length === 0) return;
      const x0 = Math.min(...xs) - 48;
      const x1 = Math.max(...xs) + 48;
      const y0 = Math.min(...ys) - 48;
      const y1 = Math.max(...ys) + 48;
      const boxWidth = Math.max(x1 - x0, 1);
      const boxHeight = Math.max(y1 - y0, 1);
      const scale = Math.min(0.95, width / boxWidth, (height - TOPBAR_HEIGHT) / boxHeight);
      const tx = (width - boxWidth * scale) / 2 - x0 * scale;
      const ty = TOPBAR_HEIGHT + (height - TOPBAR_HEIGHT - boxHeight * scale) / 2 - y0 * scale;
      svg
        .transition()
        .duration(900)
        .ease(d3.easeCubicOut)
        .call(zoomBehavior.transform, d3.zoomIdentity.translate(tx, ty).scale(scale));
    }

    nodeSel
      .on("mouseover", (event, node) => {
        const ids = connectedIds(node);
        applyVisualState(ids);
        drawRing(ids, node.theme);
        const tooltip = tooltipRef.current;
        if (!tooltip) return;
        tooltip.innerHTML = `<strong>${node.title}</strong><span>${themes[node.theme].label} · ${node.status}</span><em>点击打开卡片</em>`;
        tooltip.style.opacity = "1";
        tooltip.style.left = `${Math.min(event.clientX + 16, window.innerWidth - 260)}px`;
        tooltip.style.top = `${Math.max(event.clientY - 8, 64)}px`;
      })
      .on("mousemove", (event) => {
        const tooltip = tooltipRef.current;
        if (!tooltip) return;
        tooltip.style.left = `${Math.min(event.clientX + 16, window.innerWidth - 260)}px`;
        tooltip.style.top = `${Math.max(event.clientY - 8, 64)}px`;
      })
      .on("mouseout", () => {
        const tooltip = tooltipRef.current;
        if (tooltip) tooltip.style.opacity = "0";
        applyVisualState();
      })
      .on("click", (event, node) => {
        event.stopPropagation();
        onSelectNodeRef.current(node.id);
      });

    svg.on("click", () => {
      const selected = selectedIdRef.current;
      if (selected) onSelectNodeRef.current(selected);
    });

    const simulation = d3
      .forceSimulation<SimNode>(simNodes)
      .force(
        "link",
        d3
          .forceLink<SimNode, SimLink>(simLinks)
          .id((node) => String(node.id))
          .distance((link) => 55 + (5 - Math.min(link.weight || 1, 5)) * 29)
          .strength(0.7),
      )
      .force("charge", d3.forceManyBody<SimNode>().strength(-280))
      .force("center", d3.forceCenter(width / 2, height / 2 + TOPBAR_HEIGHT / 2).strength(0.02))
      .force("collide", d3.forceCollide<SimNode>().radius((node) => nodeRadius(node) + 14))
      .force("x", d3.forceX<SimNode>((node) => anchors[node.theme].x).strength(0.018))
      .force("y", d3.forceY<SimNode>((node) => anchors[node.theme].y).strength(0.018));

    let fitDone = false;
    const zoneTimer = window.setInterval(() => {
      drawZones();
      if (!fitDone && simulation.alpha() < 0.12) {
        fitDone = true;
        autoFit();
      }
    }, 900);

    simulation.on("tick", () => {
      linkSel.attr("d", curvePath);
      nodeSel.attr("cx", (node) => node.x ?? 0).attr("cy", (node) => node.y ?? 0);
      labelSel.attr("x", (node) => node.x ?? 0).attr("y", (node) => node.y ?? 0);
    });

    simulation.on("end", () => {
      drawZones();
      if (!fitDone) autoFit();
      fitDone = true;
    });

    updateVisualStateRef.current = applyVisualState;
    applyVisualState();

    return () => {
      window.clearInterval(zoneTimer);
      simulation.stop();
      svg.on(".zoom", null);
      svg.on("click", null);
      updateVisualStateRef.current = null;
    };
  }, [nodes, edges, loading]);

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
      <svg ref={svgRef} className="graph-layer" role="presentation" />
      <div ref={tooltipRef} className="graph-tooltip" />
    </section>
  );
}
