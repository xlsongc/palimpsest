import type { ThemeKey } from "./data";
import { themes } from "./data";

interface Props {
  onThemeClick?: (key: ThemeKey) => void;
}

export default function ThemeIndex({}: Props) {
  return (
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
  );
}
