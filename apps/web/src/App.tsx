import { useEffect, useMemo, useState } from "react";
import "./styles.css";

type View = "import" | "library" | "graph";

interface HealthStatus {
  status: string;
}

const asciiMark = String.raw`
                 ·
          ·              ·

              ><(((º>

       water without water
       trace without capture`;

const sampleBooks = [
  {
    title: "Poor Charlie's Almanack",
    status: "读过",
    theme: "投资 / 金融",
    note: "芒格思维体系核心，护城河 + 多元思维模型。",
  },
  {
    title: "失去的三十年",
    status: "读过",
    theme: "历史 / 人文",
    note: "理解日本长期停滞、资产泡沫和制度惯性的入口。",
  },
  {
    title: "算法导论（原书第2版）",
    status: "想读",
    theme: "CS / 技术",
    note: "算法理论基础，与系统、机器学习路线相连。",
  },
  {
    title: "哥德尔、艾舍尔、巴赫",
    status: "想读",
    theme: "数学 / 信息论",
    note: "逻辑、意识、形式系统与自指的长线节点。",
  },
];

const graphLinks = [
  ["Poor Charlie's Almanack", "彼得·林奇的成功投资", "投资哲学"],
  ["Poor Charlie's Almanack", "影响力", "芒格推荐"],
  ["失去的三十年", "涛动周期论", "宏观周期"],
  ["算法导论（原书第2版）", "深入理解计算机系统", "CS 基础"],
];

function App() {
  const [activeView, setActiveView] = useState<View>("import");
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <main className="shell">
      <aside className="intro">
        <div>
          <pre className="ascii" aria-label="Palimpsest goldfish mark">
            {asciiMark}
          </pre>
          <p className="kicker">PALIMPSEST / 忘筌</p>
          <h1>得鱼而忘筌；得意而忘言。</h1>
          <p className="lead">
            A local-first reading intelligence system for turning reading
            traces into recall, connection, judgment, and action.
          </p>
        </div>
        <div className="system-card">
          <span className={health ? "status-dot on" : "status-dot"} />
          <span>{statusText}</span>
        </div>
      </aside>

      <section className="workspace">
        <nav className="topbar" aria-label="Primary views">
          <button
            className={activeView === "import" ? "active" : ""}
            onClick={() => setActiveView("import")}
          >
            Import
          </button>
          <button
            className={activeView === "library" ? "active" : ""}
            onClick={() => setActiveView("library")}
          >
            Library
          </button>
          <button
            className={activeView === "graph" ? "active" : ""}
            onClick={() => setActiveView("graph")}
          >
            Graph
          </button>
        </nav>

        {activeView === "import" && <ImportPreview />}
        {activeView === "library" && <LibraryPreview />}
        {activeView === "graph" && <GraphPreview />}
      </section>
    </main>
  );
}

function ImportPreview() {
  return (
    <section className="panel">
      <div className="section-head">
        <p className="eyebrow">Capture</p>
        <h2>Paste Douban reading records</h2>
      </div>
      <div className="import-grid">
        <textarea
          aria-label="Douban paste input"
          defaultValue={`我读过的书(26)\n\n指数基金投资指南 2026-05-01\nThe Almanack of Naval Ravikant 2026-04-19\n芯片战争 2026-04-03\n失去的三十年 2026-03-20`}
        />
        <div className="receipt">
          <p className="receipt-title">Import audit preview</p>
          <dl>
            <div>
              <dt>raw lines</dt>
              <dd>6</dd>
            </div>
            <div>
              <dt>candidate books</dt>
              <dd>4</dd>
            </div>
            <div>
              <dt>blocking warnings</dt>
              <dd>0</dd>
            </div>
          </dl>
          <p className="muted">
            The real parser will preserve raw fragments before any durable
            write.
          </p>
        </div>
      </div>
    </section>
  );
}

function LibraryPreview() {
  return (
    <section className="panel">
      <div className="section-head">
        <p className="eyebrow">Structure</p>
        <h2>Books become reusable knowledge objects</h2>
      </div>
      <div className="book-list">
        {sampleBooks.map((book) => (
          <article className="book-row" key={book.title}>
            <div>
              <p className="book-theme">{book.theme}</p>
              <h3>{book.title}</h3>
              <p>{book.note}</p>
            </div>
            <span>{book.status}</span>
          </article>
        ))}
      </div>
    </section>
  );
}

function GraphPreview() {
  return (
    <section className="panel graph-panel">
      <div className="section-head">
        <p className="eyebrow">Connect</p>
        <h2>Explainable reading graph</h2>
      </div>
      <div className="graph-stage" aria-label="Static graph preview">
        <div className="node node-a">Poor Charlie</div>
        <div className="node node-b">影响力</div>
        <div className="node node-c">失去的三十年</div>
        <div className="node node-d">涛动周期论</div>
        <div className="node node-e">算法导论</div>
        <div className="node node-f">芯片战争</div>
        <div className="node node-g">海洋帝国</div>
        <div className="node node-h">GEB</div>
        <svg viewBox="0 0 720 420" role="presentation">
          <path d="M112 120 C215 68 315 72 430 118" />
          <path d="M112 132 C210 205 300 250 435 300" />
          <path d="M238 335 C328 370 455 360 596 318" />
          <path d="M555 92 C584 138 610 190 638 250" />
          <path d="M145 250 C226 206 305 196 388 220" />
          <path d="M315 92 C374 128 432 168 505 230" />
        </svg>
      </div>
      <div className="edge-list">
        {graphLinks.map(([from, to, reason]) => (
          <p key={`${from}-${to}`}>
            <span>{from}</span> → <span>{to}</span> · {reason}
          </p>
        ))}
      </div>
    </section>
  );
}

export default App;
