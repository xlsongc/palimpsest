import type { ThemeKey, ReadingStatus } from "./data";
import { themes, statusLabels } from "./data";

interface RelatedBook {
  title: string;
  reason: string;
  status: string | null;
}

interface Props {
  title: string;
  theme: ThemeKey;
  status: ReadingStatus;
  authors: string[];
  tags: string[];
  rating: number | null;
  related: RelatedBook[];
  onClose: () => void;
}

export default function BookDrawer({
  title,
  theme,
  status,
  authors,
  tags,
  rating,
  related,
  onClose,
}: Props) {
  const themeInfo = themes[theme];

  return (
    <aside
      className="book-drawer"
      style={{ "--drawer-theme": themeInfo.color } as React.CSSProperties}
    >
      <button
        aria-label="Close detail drawer"
        className="drawer-close"
        onClick={onClose}
      >
        ×
      </button>

      <p className="drawer-theme">{themeInfo.label}</p>
      <h1>{title}</h1>

      <div className="tag-row">
        <span className={`tag ${status}`}>{statusLabels[status]}</span>
        {authors.length > 0 && (
          <span className="tag">{authors.join(", ")}</span>
        )}
        {rating !== null && (
          <span className="tag" style={{ color: "#b8860b" }}>★ {rating}</span>
        )}
      </div>

      {tags.length > 0 && (
        <section>
          <h2>标签</h2>
          <div className="tag-row">
            {tags.map((tag) => (
              <span key={tag} className="tag" style={{ color: themeInfo.color }}>
                {tag}
              </span>
            ))}
          </div>
        </section>
      )}

      {related.length > 0 && (
        <section>
          <h2>关联书籍 →</h2>
          <ul className="related-list">
            {related.map((r) => (
              <li key={r.title}>
                <strong>→ {r.title}</strong>
                <span>{r.reason}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <footer className="drawer-stats">
        <p>
          <strong>{related.length}</strong>
          <span>关联数</span>
        </p>
        <p>
          <strong>{related.filter(r => r.status === "read").length}</strong>
          <span>已读关联</span>
        </p>
        <p>
          <strong>{related.filter(r => r.status === "want").length}</strong>
          <span>待读关联</span>
        </p>
      </footer>
    </aside>
  );
}
