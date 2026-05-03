import type { ReadingStatus } from "./data";

interface Props {
  activeStatus: "all" | ReadingStatus;
  onStatusChange: (s: "all" | ReadingStatus) => void;
  onImportClick: () => void;
  apiStatus: string;
  bookCount: number;
}

export default function GraphTopbar({
  activeStatus,
  onStatusChange,
  onImportClick,
  apiStatus,
  bookCount,
}: Props) {
  return (
    <header className="graph-topbar">
      <div className="brand">
        <strong>Niko · Reading Graph</strong>
        <span>/</span>
        <span>阅读图谱</span>
      </div>
      <nav aria-label="Reading status filter">
        {(["all", "read", "reading", "want"] as const).map((key) => (
          <button
            className={activeStatus === key ? "active" : ""}
            key={key}
            onClick={() => onStatusChange(key)}
          >
            {key === "all" ? "ALL" : key.toUpperCase()}
          </button>
        ))}
        <button onClick={onImportClick}>IMPORT</button>
      </nav>
      <label className="search">
        <span>搜索书名...</span>
        <input aria-label="Search books" placeholder=" " />
      </label>
      <div className="api-pill-inline">
        <span className={apiStatus === "ok" ? "api-dot on" : "api-dot"} />
        {apiStatus === "ok" ? "API ok" : "API offline"}
      </div>
      <div className="book-count">
        <strong>{bookCount}</strong>
        <span>books</span>
      </div>
    </header>
  );
}
