import { useState } from "react";
import {
  createImport,
  parseImport,
  getReview,
  submitReview,
  commitImport,
  getValidation,
  type ImportSessionDTO,
  type ReviewRowDTO,
  type ReviewRowAction,
  type ValidationReportDTO,
} from "../../api";

type Step = "paste" | "parsing" | "review" | "committing" | "done";

interface EditableRow {
  row_id: number;
  action: "accept" | "reject" | "needs_edit";
  title: string;
  authors: string;
  status: string;
  rating: string;
  read_date: string;
  marked_date: string;
  comment: string;
  tags: string;
}

export default function ImportPage() {
  const [step, setStep] = useState<Step>("paste");
  const [rawInput, setRawInput] = useState("");
  const [session, setSession] = useState<ImportSessionDTO | null>(null);
  const [rows, setRows] = useState<ReviewRowDTO[]>([]);
  const [editableRows, setEditableRows] = useState<Map<number, EditableRow>>(new Map());
  const [validation, setValidation] = useState<ValidationReportDTO | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function showError(e: unknown) {
    setError(e instanceof Error ? e.message : String(e));
    setLoading(false);
  }

  async function handleCreateAndParse() {
    if (!rawInput.trim()) {
      setError("请粘贴豆瓣读书内容");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const s = await createImport(rawInput);
      setSession(s);
      setStep("parsing");
      await parseImport(s.id);
      const review = await getReview(s.id);
      setRows(review.rows);
      const init = new Map<number, EditableRow>();
      for (const r of review.rows) {
        const requiresReview =
          r.confidence < 0.7 || r.warnings.length > 0 || !r.parsed_json?.title;
        init.set(r.row_id, {
          row_id: r.row_id,
          action: requiresReview ? "needs_edit" : "accept",
          title: r.parsed_json?.title ?? "",
          authors: (r.parsed_json?.authors ?? []).join(", "),
          status: r.parsed_json?.status ?? "",
          rating: r.parsed_json?.rating != null ? String(r.parsed_json.rating) : "",
          read_date: r.parsed_json?.read_date ?? "",
          marked_date: r.parsed_json?.marked_date ?? "",
          comment: r.parsed_json?.comment ?? "",
          tags: (r.parsed_json?.tags ?? []).join(", "),
        });
      }
      setEditableRows(init);
      setStep("review");
    } catch (e) {
      showError(e);
      setStep("paste");
    } finally {
      setLoading(false);
    }
  }

  function updateEditable(rowId: number, patch: Partial<EditableRow>) {
    setEditableRows((prev) => {
      const next = new Map(prev);
      const cur = next.get(rowId);
      if (cur) next.set(rowId, { ...cur, ...patch });
      return next;
    });
  }

  async function handleSubmitReview() {
    if (!session) return;
    setError(null);
    setLoading(true);
    try {
      const actions: ReviewRowAction[] = [];
      for (const [, er] of editableRows) {
        const a: ReviewRowAction = { row_id: er.row_id, action: er.action };
        if (er.action === "accept" || er.action === "needs_edit") {
          a.title = er.title;
          a.authors = er.authors ? er.authors.split(",").map((s) => s.trim()).filter(Boolean) : [];
          a.status = er.status || null;
          a.rating = er.rating ? parseFloat(er.rating) : null;
          a.read_date = er.read_date || null;
          a.marked_date = er.marked_date || null;
          a.comment = er.comment || null;
          a.tags = er.tags ? er.tags.split(",").map((s) => s.trim()).filter(Boolean) : [];
        }
        actions.push(a);
      }
      await submitReview(session.id, actions);
      setStep("committing");
      await commitImport(session.id);
      const v = await getValidation(session.id);
      setValidation(v);
      setStep("done");
    } catch (e) {
      showError(e);
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setStep("paste");
    setRawInput("");
    setSession(null);
    setRows([]);
    setEditableRows(new Map());
    setValidation(null);
    setError(null);
  }

  return (
    <div className="import-page">
      <header className="import-header">
        <div>
          <p className="import-kicker">Capture / 豆瓣导入</p>
          <h1>Review before it becomes memory</h1>
        </div>
        {session && (
          <span className="session-badge">
            Session #{session.id} · {session.status}
          </span>
        )}
        {step !== "paste" && (
          <button className="reset-btn" onClick={handleReset}>
            New Import / 重新导入
          </button>
        )}
      </header>

      {error && <div className="error-banner">{error}</div>}

      {step === "paste" && (
        <section className="paste-section">
          <label>
            <span>Paste your Douban reading list / 粘贴豆瓣读书记录</span>
            <textarea
              value={rawInput}
              onChange={(e) => setRawInput(e.target.value)}
              rows={12}
              placeholder={"已读\n\n思考，快与慢\n作者: [美] 丹尼尔·卡尼曼\n..."}
            />
          </label>
          <button onClick={handleCreateAndParse} disabled={loading}>
            {loading ? "Processing..." : "Create / Parse"}
          </button>
        </section>
      )}

      {step === "parsing" && (
        <div className="loading-indicator">Parsing import session...</div>
      )}

      {step === "review" && (
        <section className="review-section">
          <div className="section-heading">
            <p>Import Review</p>
            <h2>Review {rows.length} rows before commit</h2>
            <span>Low-confidence rows default to Needs Edit. Change to Accept only after checking.</span>
          </div>
          <div className="review-actions">
            <button onClick={handleSubmitReview} disabled={loading}>
              {loading ? "Submitting..." : "Review / Commit"}
            </button>
          </div>
          <div className="review-table-wrap">
            <table className="review-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Action</th>
                  <th>Title</th>
                  <th>Authors</th>
                  <th>Status</th>
                  <th>Rating</th>
                  <th>Date</th>
                  <th>Comment</th>
                  <th>Tags</th>
                  <th>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => {
                  const er = editableRows.get(row.row_id);
                  if (!er) return null;
                  return (
                    <tr key={row.row_id} className={`action-${er.action}`}>
                      <td>{row.row_index + 1}</td>
                      <td>
                        <select
                          value={er.action}
                          onChange={(e) =>
                            updateEditable(row.row_id, {
                              action: e.target.value as EditableRow["action"],
                            })
                          }
                        >
                          <option value="accept">Accept</option>
                          <option value="reject">Reject</option>
                          <option value="needs_edit">Needs Edit</option>
                        </select>
                      </td>
                      <td>
                        {er.action !== "reject" ? (
                          <input
                            value={er.title}
                            onChange={(e) =>
                              updateEditable(row.row_id, { title: e.target.value })
                            }
                            className="field-title"
                          />
                        ) : (
                          <span className="muted">{row.parsed_json?.title}</span>
                        )}
                      </td>
                      <td>
                        {er.action !== "reject" ? (
                          <input
                            value={er.authors}
                            onChange={(e) =>
                              updateEditable(row.row_id, { authors: e.target.value })
                            }
                            placeholder="comma separated"
                            className="field-authors"
                          />
                        ) : (
                          <span className="muted">
                            {row.parsed_json?.authors?.join(", ")}
                          </span>
                        )}
                      </td>
                      <td>
                        {er.action !== "reject" ? (
                          <select
                            value={er.status}
                            onChange={(e) =>
                              updateEditable(row.row_id, { status: e.target.value })
                            }
                          >
                            <option value="">—</option>
                            <option value="read">Read</option>
                            <option value="reading">Reading</option>
                            <option value="want">Want</option>
                          </select>
                        ) : (
                          <span className="muted">{row.parsed_json?.status}</span>
                        )}
                      </td>
                      <td>
                        {er.action !== "reject" ? (
                          <input
                            type="number"
                            min="0"
                            max="10"
                            step="0.1"
                            value={er.rating}
                            onChange={(e) =>
                              updateEditable(row.row_id, { rating: e.target.value })
                            }
                            className="field-rating"
                          />
                        ) : (
                          <span className="muted">{row.parsed_json?.rating}</span>
                        )}
                      </td>
                      <td>
                        {er.action !== "reject" ? (
                          <input
                            type="date"
                            value={er.read_date || er.marked_date}
                            onChange={(e) => {
                              const isWant = er.status === "want";
                              updateEditable(row.row_id, isWant
                                ? { marked_date: e.target.value, read_date: "" }
                                : { read_date: e.target.value, marked_date: "" });
                            }}
                            className="field-date"
                          />
                        ) : (
                          <span className="muted">
                            {row.parsed_json?.read_date || row.parsed_json?.marked_date}
                          </span>
                        )}
                      </td>
                      <td>
                        {er.action !== "reject" ? (
                          <input
                            value={er.comment}
                            onChange={(e) =>
                              updateEditable(row.row_id, { comment: e.target.value })
                            }
                            className="field-comment"
                          />
                        ) : (
                          <span className="muted">{row.parsed_json?.comment}</span>
                        )}
                      </td>
                      <td>
                        {er.action !== "reject" ? (
                          <input
                            value={er.tags}
                            onChange={(e) =>
                              updateEditable(row.row_id, { tags: e.target.value })
                            }
                            placeholder="comma separated"
                            className="field-tags"
                          />
                        ) : (
                          <span className="muted">
                            {row.parsed_json?.tags?.join(", ")}
                          </span>
                        )}
                      </td>
                      <td>
                        <span className={`confidence-${row.confidence >= 0.9 ? "high" : row.confidence >= 0.5 ? "mid" : "low"}`}>
                          {Math.round(row.confidence * 100)}%
                        </span>
                        {row.warnings.length > 0 && (
                          <span className="warning-badge" title={row.warnings.join(", ")}>
                            ⚠
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {step === "committing" && (
        <div className="loading-indicator">Committing...</div>
      )}

      {step === "done" && validation && (
        <section className="validation-section">
          <div className="section-heading">
            <p>Validation Report</p>
            <h2>Import Complete</h2>
          </div>
          <div className="validation-counts">
            <div className="count-card">
              <strong>{validation.parsed_count}</strong>
              <span>Parsed</span>
            </div>
            <div className="count-card accepted">
              <strong>{validation.accepted_count}</strong>
              <span>Accepted</span>
            </div>
            <div className="count-card rejected">
              <strong>{validation.rejected_count}</strong>
              <span>Rejected</span>
            </div>
            <div className="count-card">
              <strong>{validation.committed_count}</strong>
              <span>Committed</span>
            </div>
            <div className="count-card">
              <strong>{validation.duplicate_count}</strong>
              <span>Duplicates</span>
            </div>
            <div className="count-card warning">
              <strong>{validation.warning_count}</strong>
              <span>Warnings</span>
            </div>
            <div className="count-card">
              <strong>{validation.failed_count}</strong>
              <span>Failed</span>
            </div>
          </div>
          <div className="validation-rows">
            <table className="review-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Title</th>
                  <th>Status</th>
                  <th>Book ID</th>
                  <th>Warnings</th>
                </tr>
              </thead>
              <tbody>
                {validation.rows.map((r) => (
                  <tr key={r.row_id} className={`status-${r.status}`}>
                    <td>{r.row_index + 1}</td>
                    <td>{r.title}</td>
                    <td>{r.status}</td>
                    <td>{r.book_id ?? "—"}</td>
                    <td>
                      {r.warnings.length > 0 ? (
                        <span className="warning-badge" title={r.warnings.join(", ")}>
                          {r.warnings.join(", ")}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button onClick={handleReset} className="reset-btn">
            New Import / 重新导入
          </button>
        </section>
      )}
    </div>
  );
}
