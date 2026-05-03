import { useEffect, useMemo, useState } from "react";
import "./styles.css";
import ImportPage from "./features/import/ImportPage";
import "./features/import/styles.css";

type ReadingStatus = "read" | "reading" | "want";
type ThemeKey =
  | "finance"
  | "cs"
  | "history"
  | "ai"
  | "literature"
  | "psychology"
  | "math"
  | "biography";

interface HealthStatus {
  status: string;
}

interface BookNode {
  id: string;
  title: string;
  status: ReadingStatus;
  theme: ThemeKey;
  x: number;
  y: number;
  size?: "sm" | "md" | "lg";
  faded?: boolean;
}

interface Edge {
  from: string;
  to: string;
  path: string;
  theme: ThemeKey;
  strong?: boolean;
}

const themes: Record<ThemeKey, { label: string; color: string }> = {
  finance: { label: "投资 / 金融", color: "#294f86" },
  cs: { label: "CS / 技术", color: "#19785c" },
  history: { label: "历史 / 人文", color: "#8b3a2b" },
  ai: { label: "AI / 科技传记", color: "#51308b" },
  literature: { label: "文学 / 小说", color: "#28723e" },
  psychology: { label: "心理 / 社科", color: "#175d6b" },
  math: { label: "数学 / 信息论", color: "#7a6414" },
  biography: { label: "传记 / 思想", color: "#7d2857" },
};

const statusLabels: Record<ReadingStatus, string> = {
  read: "读过",
  reading: "在读",
  want: "想读",
};

const nodes: BookNode[] = [
  { id: "python", title: "流畅的Python", status: "reading", theme: "cs", x: 17, y: 24 },
  { id: "clrs", title: "算法导论(C L R S)", status: "want", theme: "cs", x: 22, y: 28 },
  { id: "csapp", title: "深入理解计算机系统(CSAPP)", status: "reading", theme: "cs", x: 18.5, y: 34 },
  { id: "coding", title: "编码", status: "read", theme: "cs", x: 16, y: 40 },
  { id: "prml", title: "PRML", status: "reading", theme: "ai", x: 30.5, y: 38 },
  { id: "d2l", title: "Dive into Deep Learning", status: "reading", theme: "ai", x: 30.5, y: 45 },
  { id: "understanding", title: "Understanding...", status: "reading", theme: "ai", x: 30, y: 51 },
  { id: "ming", title: "明朝那些事儿", status: "read", theme: "history", x: 43.5, y: 26 },
  { id: "wei", title: "魏晋南北朝", status: "read", theme: "history", x: 48.5, y: 22 },
  { id: "golden", title: "黄金时代", status: "read", theme: "literature", x: 76, y: 14 },
  { id: "almanack", title: "The Almanack...", status: "read", theme: "biography", x: 52, y: 44 },
  { id: "poor", title: "Poor Charlie...", status: "read", theme: "finance", x: 63, y: 39, size: "lg" },
  { id: "lynch", title: "彼得·林奇的成功投资", status: "read", theme: "finance", x: 65, y: 46, size: "lg" },
  { id: "index", title: "指数基金投资指南", status: "read", theme: "finance", x: 58, y: 43 },
  { id: "common", title: "Common Stock...", status: "want", theme: "finance", x: 60, y: 55 },
  { id: "growth", title: "怎样选择成长股", status: "reading", theme: "finance", x: 57, y: 61 },
  { id: "selfish", title: "The Selfish ...", status: "reading", theme: "psychology", x: 57, y: 37 },
  { id: "animal", title: "社会性动物", status: "want", theme: "psychology", x: 68, y: 34 },
  { id: "mistakes", title: "错误的行为", status: "want", theme: "psychology", x: 72, y: 36 },
  { id: "principles", title: "经济学原理", status: "reading", theme: "finance", x: 84, y: 42 },
  { id: "xue", title: "薛兆丰经济学讲义", status: "read", theme: "finance", x: 84, y: 49 },
  { id: "deng", title: "邓小平传", status: "read", theme: "history", x: 81, y: 62 },
  { id: "lost", title: "失去的三十年", status: "read", theme: "history", x: 76, y: 69 },
  { id: "ocean", title: "海洋帝国", status: "read", theme: "history", x: 47, y: 76 },
  { id: "dutch", title: "荷兰海洋帝国史", status: "want", theme: "history", x: 51, y: 80 },
  { id: "war", title: "芯片战争", status: "read", theme: "ai", x: 9, y: 43 },
];

const edges: Edge[] = [
  { from: "python", to: "csapp", path: "M170 156 C190 188 178 218 185 245", theme: "cs" },
  { from: "python", to: "clrs", path: "M170 156 C188 170 205 174 220 184", theme: "cs" },
  { from: "csapp", to: "coding", path: "M185 245 C170 250 160 260 160 276", theme: "cs" },
  { from: "prml", to: "d2l", path: "M305 260 C310 284 309 304 305 330", theme: "ai" },
  { from: "d2l", to: "understanding", path: "M305 330 C307 358 305 375 300 394", theme: "ai" },
  { from: "ming", to: "wei", path: "M435 186 C462 172 479 154 485 138", theme: "history", strong: true },
  { from: "almanack", to: "index", path: "M520 318 C545 315 562 312 580 308", theme: "biography" },
  { from: "index", to: "poor", path: "M580 308 C605 286 617 282 630 270", theme: "finance" },
  { from: "poor", to: "lynch", path: "M630 270 C640 292 646 315 650 340", theme: "finance", strong: true },
  { from: "poor", to: "animal", path: "M630 270 C646 242 662 226 680 220", theme: "psychology" },
  { from: "poor", to: "mistakes", path: "M630 270 C664 260 700 246 720 234", theme: "psychology" },
  { from: "growth", to: "common", path: "M570 438 C582 414 595 396 600 374", theme: "finance" },
  { from: "principles", to: "xue", path: "M840 304 C850 330 848 350 840 370", theme: "finance" },
  { from: "lost", to: "deng", path: "M760 500 C780 468 795 448 810 418", theme: "history" },
  { from: "ocean", to: "dutch", path: "M470 548 C488 568 500 582 510 592", theme: "history" },
];

const detailById = {
  poor: {
    title: "Poor Charlie's Almanack",
    theme: "finance" as ThemeKey,
    status: "read" as ReadingStatus,
    note: "芒格思维体系核心，护城河 + 多元思维模型",
    related: [
      ["彼得·林奇的成功投资", "读过 · 投资哲学"],
      ["影响力", "想读 · 芒格推荐"],
      ["错误的行为", "想读 · 思维模型"],
      ["The Selfish Gene", "在读 · 芒格推荐书单"],
    ],
    stats: ["4", "1", "2"],
  },
  wei: {
    title: "魏晋南北朝",
    theme: "history" as ThemeKey,
    status: "read" as ReadingStatus,
    note: "门阀政治 / 历史背景",
    related: [
      ["东晋门阀政治", "想读 · 魏晋延伸"],
      ["明朝那些事儿", "读过 · 中国史脉络"],
    ],
    stats: ["2", "1", "1"],
  },
};

function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<keyof typeof detailById>("poor");
  const [activeStatus, setActiveStatus] = useState<"all" | ReadingStatus>("all");
  const [view, setView] = useState<"graph" | "import">("graph");
  const selected = detailById[selectedId];

  useEffect(() => {
    fetch("/api/health")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(setHealth)
      .catch((err: Error) => setError(err.message));
  }, []);

  const statusText = useMemo(() => {
    if (health) return `API ${health.status}`;
    if (error) return "API offline";
    return "API checking";
  }, [error, health]);

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
            <strong>01</strong>
            <span>import</span>
          </div>
        </header>
        <ImportPage />
      </main>
    );
  }

  return (
    <main className="reading-graph-shell">
      <header className="graph-topbar">
        <div className="brand">
          <strong>Niko · Reading Graph</strong>
          <span>/</span>
          <span>阅读图谱</span>
        </div>
        <nav aria-label="Reading status filter">
          {[
            ["all", "ALL"],
            ["read", "READ"],
            ["reading", "READING"],
            ["want", "WANT"],
          ].map(([key, label]) => (
            <button
              className={activeStatus === key ? "active" : ""}
              key={key}
              onClick={() => setActiveStatus(key as "all" | ReadingStatus)}
            >
              {label}
            </button>
          ))}
          <button onClick={() => setView("import")}>IMPORT</button>
        </nav>
        <label className="search">
          <span>搜索书名...</span>
          <input aria-label="Search books" />
        </label>
        <div className="book-count">
          <strong>117</strong>
          <span>books</span>
        </div>
      </header>

      <section className="graph-workbench" aria-label="Reading graph preview">
        <div className="api-pill">
          <span className={health ? "api-dot on" : "api-dot"} />
          {statusText}
        </div>

        <div className="theme-field finance-field" />
        <div className="theme-field cs-field" />
        <div className="theme-field history-field" />
        <div className="theme-field humanities-field" />

        <svg className="edge-layer" viewBox="0 0 1000 720" role="presentation">
          {edges.map((edge) => (
            <path
              className={edge.strong ? "strong" : ""}
              d={edge.path}
              key={`${edge.from}-${edge.to}`}
              style={{ stroke: themes[edge.theme].color }}
            />
          ))}
        </svg>

        <div className="cluster-ring history-ring" />
        <div className="cluster-ring finance-ring" />

        {nodes.map((node) => {
          const muted =
            activeStatus !== "all" && activeStatus !== node.status;
          return (
            <button
              className={[
                "book-node",
                node.status,
                node.size ?? "md",
                node.faded || muted ? "muted" : "",
                selected.title.startsWith(node.title.replace("...", "")) ||
                node.id === selectedId
                  ? "selected"
                  : "",
              ].join(" ")}
              key={node.id}
              onClick={() => {
                if (node.id === "wei" || node.id === "poor") {
                  setSelectedId(node.id);
                }
              }}
              style={{
                "--x": `${node.x}%`,
                "--y": `${node.y}%`,
                "--theme": themes[node.theme].color,
              } as React.CSSProperties}
            >
              <span>{node.title}</span>
            </button>
          );
        })}

        <aside className="theme-index" aria-label="Theme index">
          <h2>THEME INDEX</h2>
          <ol>
            {Object.entries(themes).map(([key, theme]) => (
              <li key={key}>
                <span style={{ background: theme.color }} />
                {theme.label}
              </li>
            ))}
          </ol>
          <div className="status-legend">
            <p>
              <span className="status-sample read" />
              读过
            </p>
            <p>
              <span className="status-sample reading" />
              在读
            </p>
            <p>
              <span className="status-sample want" />
              想读
            </p>
          </div>
        </aside>

        <aside
          className="book-drawer"
          style={{ "--drawer-theme": themes[selected.theme].color } as React.CSSProperties}
        >
          <button
            aria-label="Close detail drawer"
            className="drawer-close"
            onClick={() => setSelectedId("poor")}
          >
            ×
          </button>
          <p className="drawer-theme">{themes[selected.theme].label}</p>
          <h1>{selected.title}</h1>
          <div className="tag-row">
            <span className="tag read">{statusLabels[selected.status]}</span>
            <span className="tag" style={{ color: themes[selected.theme].color }}>
              {themes[selected.theme].label}
            </span>
          </div>

          <section>
            <h2>笔记</h2>
            <p className="note">{selected.note}</p>
          </section>

          <section>
            <h2>延伸阅读 →</h2>
            <ul className="related-list">
              {selected.related.map(([title, meta]) => (
                <li key={title}>
                  <strong>→ {title}</strong>
                  <span>{meta}</span>
                </li>
              ))}
            </ul>
          </section>

          <footer className="drawer-stats">
            <p>
              <strong>{selected.stats[0]}</strong>
              <span>关联数</span>
            </p>
            <p>
              <strong>{selected.stats[1]}</strong>
              <span>已读关联</span>
            </p>
            <p>
              <strong>{selected.stats[2]}</strong>
              <span>待读关联</span>
            </p>
          </footer>
        </aside>
      </section>
    </main>
  );
}

export default App;
