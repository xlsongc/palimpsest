const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// --- Types ---

export interface ImportSessionDTO {
  id: number;
  source: string;
  raw_hash: string;
  created_at: string;
  status: string;
  expected_count: number;
  extracted_count: number;
  reviewed_count: number;
  inserted_count: number;
  duplicate_count: number;
  warning_count: number;
}

export interface ReviewRowDTO {
  row_id: number;
  row_index: number;
  raw_fragment: string;
  parsed_json: ParsedBook | null;
  status: string;
  confidence: number;
  warnings: string[];
}

export interface ParsedBook {
  title: string;
  status: string | null;
  authors: string[];
  rating: number | null;
  comment: string | null;
  tags: string[];
  read_date: string | null;
  marked_date: string | null;
}

export interface ReviewRowAction {
  row_id: number;
  action: "accept" | "reject" | "needs_edit";
  title?: string;
  authors?: string[];
  status?: string | null;
  rating?: number | null;
  read_date?: string | null;
  marked_date?: string | null;
  comment?: string | null;
  tags?: string[];
}

export interface ValidationReportDTO {
  session_id: number;
  raw_input_hash: string;
  parsed_count: number;
  accepted_count: number;
  rejected_count: number;
  needs_edit_count: number;
  committed_count: number;
  duplicate_count: number;
  failed_count: number;
  warning_count: number;
  rows: {
    row_id: number;
    row_index: number;
    title: string;
    status: string;
    book_id: number | null;
    entry_id: number | null;
    warnings: string[];
  }[];
}

// --- Endpoints ---

export function createImport(rawInput: string, source = "douban") {
  return request<ImportSessionDTO>("/imports", {
    method: "POST",
    body: JSON.stringify({ source, raw_input: rawInput }),
  });
}

export function getImport(sessionId: number) {
  return request<ImportSessionDTO>(`/imports/${sessionId}`);
}

export function parseImport(sessionId: number) {
  return request<{
    session: ImportSessionDTO;
    rows: { row_index: number; raw_fragment: string; parsed_json: string | null; status: string; confidence: number; warnings: string[] }[];
    parser_warnings: string[];
  }>(`/imports/${sessionId}/parse`, { method: "POST" });
}

export function getReview(sessionId: number) {
  return request<{ session: ImportSessionDTO; rows: ReviewRowDTO[] }>(
    `/imports/${sessionId}/review`
  );
}

export function submitReview(sessionId: number, rows: ReviewRowAction[]) {
  return request<{
    session: ImportSessionDTO;
    updated_rows: { row_id: number; status: string }[];
  }>(`/imports/${sessionId}/review`, {
    method: "POST",
    body: JSON.stringify({ rows }),
  });
}

export function commitImport(sessionId: number) {
  return request<{
    session: ImportSessionDTO;
    committed: { row_id: number; book_id: number; entry_id: number }[];
    duplicates: { row_id: number; existing_book_id: number }[];
    skipped: { row_id: number; reason: string }[];
  }>(`/imports/${sessionId}/commit`, { method: "POST" });
}

export function getValidation(sessionId: number) {
  return request<ValidationReportDTO>(`/imports/${sessionId}/validate`);
}

// --- Graph ---

export interface GraphNodeDTO {
  id: number;
  title: string;
  authors: string[];
  status: string | null;
  rating: number | null;
  tags: string[];
}

export interface GraphEdgeDTO {
  id: number;
  source_book_id: number;
  target_book_id: number;
  edge_type: string;
  weight: number;
  reason: string | null;
}

export interface GraphResponseDTO {
  nodes: GraphNodeDTO[];
  edges: GraphEdgeDTO[];
}

export function getGraph() {
  return request<GraphResponseDTO>("/graph");
}

export function rebuildGraph() {
  return request<GraphResponseDTO>("/graph/rebuild", { method: "POST" });
}
