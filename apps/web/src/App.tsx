import { useEffect, useState } from "react";
import "./styles.css";
import ImportPage from "./features/import/ImportPage";
import "./features/import/styles.css";
import GraphTopbar from "./features/graph/GraphTopbar";
import GraphCanvas from "./features/graph/GraphCanvas";
import ThemeIndex from "./features/graph/ThemeIndex";
import BookDrawer from "./features/graph/BookDrawer";
import { getGraph, rebuildGraph, type GraphNodeDTO, type GraphEdgeDTO } from "./api";
import { type ReadingStatus, type ThemeKey } from "./features/graph/data";

// Infer theme from tags
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

function App() {
  const [health, setHealth] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [activeStatus, setActiveStatus] = useState<"all" | ReadingStatus>("all");
  const [view, setView] = useState<"graph" | "import">("graph");
  const [allNodes, setAllNodes] = useState<GraphNodeDTO[]>([]);
  const [allEdges, setAllEdges] = useState<GraphEdgeDTO[]>([]);
  const [graphLoading, setGraphLoading] = useState(true);

  function refreshGraph(rebuild = false) {
    setGraphLoading(true);
    const load = rebuild ? rebuildGraph() : getGraph();
    return load
      .then((data) => {
        setAllNodes(data.nodes);
        setAllEdges(data.edges);
      })
      .catch(() => {})
      .finally(() => setGraphLoading(false));
  }

  useEffect(() => {
    fetch("/api/health")
      .then((res) => res.ok ? res.json() : Promise.reject())
      .then((d) => setHealth(d.status ?? "ok"))
      .catch(() => setHealth(null));

    refreshGraph();
  }, []);

  const selectedNode = selectedId ? allNodes.find(n => n.id === selectedId) : null;
  const selectedEdges = selectedId
    ? allEdges.filter(e => e.source_book_id === selectedId || e.target_book_id === selectedId)
    : [];

  // Build related books from edges
  const relatedBooks = selectedEdges.map(e => {
    const otherId = e.source_book_id === selectedId ? e.target_book_id : e.source_book_id;
    const other = allNodes.find(n => n.id === otherId);
    return other ? { title: other.title, reason: e.reason || e.edge_type, status: other.status } : null;
  }).filter(Boolean);

  // Import view
  if (view === "import") {
    return (
      <main className="reading-graph-shell import-shell">
        <header className="graph-topbar">
          <div className="brand">
            <strong>Niko · Reading Graph</strong>
            <span>/</span>
            <span>阅读图谱</span>
          </div>
          <nav aria-label="Primary view">
            <button onClick={() => setView("graph")}>GRAPH</button>
            <button className="active">IMPORT</button>
          </nav>
          <div className="topbar-note">Capture / Review / Commit</div>
          <div className="book-count">
            <strong>{allNodes.length}</strong>
            <span>books</span>
          </div>
        </header>
        <ImportPage onImportCommitted={() => refreshGraph(true)} />
      </main>
    );
  }

  // Graph view
  return (
    <main className="reading-graph-shell">
      <GraphTopbar
        activeStatus={activeStatus}
        onStatusChange={setActiveStatus}
        onImportClick={() => setView("import")}
        apiStatus={health ?? "offline"}
        bookCount={allNodes.length}
      />

      <GraphCanvas
        nodes={allNodes}
        edges={allEdges}
        loading={graphLoading}
        activeStatus={activeStatus}
        selectedId={selectedId}
        onSelectNode={(id) => setSelectedId(id === selectedId ? null : id)}
      />

      <ThemeIndex />

      {selectedNode && (
        <BookDrawer
          title={selectedNode.title}
          theme={inferTheme(selectedNode.tags)}
          status={(selectedNode.status || "want") as ReadingStatus}
          authors={selectedNode.authors}
          tags={selectedNode.tags}
          rating={selectedNode.rating}
          related={relatedBooks as { title: string; reason: string; status: string | null }[]}
          onClose={() => setSelectedId(null)}
        />
      )}
    </main>
  );
}

export default App;
