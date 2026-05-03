import { useEffect, useState } from "react";

interface HealthStatus {
  status: string;
}

function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(setHealth)
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div style={{ padding: "2rem", fontFamily: "system-ui, sans-serif" }}>
      <h1>Palimpsest / 忘筌</h1>
      <p>愿你得鱼而忘筌；得意而忘言。</p>
      <div>
        <h2>Backend Status</h2>
        {error && <p style={{ color: "red" }}>Error: {error}</p>}
        {health ? (
          <p style={{ color: "green" }}>API: {health.status}</p>
        ) : (
          !error && <p>Checking...</p>
        )}
      </div>
    </div>
  );
}

export default App;
