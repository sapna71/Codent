const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

export interface IngestResult {
  owner: string;
  name: string;
  default_branch: string;
  raw_file_count: number;
  filtered_file_count: number;
  chunk_count: number;
  repo_key: string;
}

export interface Source {
  ref: number;
  file: string;
  name: string;
  kind: string;
  start_line: number;
  end_line: number;
  github_url: string;
}

export interface AskResult {
  question: string;
  answer: string;
  sources: Source[];
}

export interface CodeResult extends Source {
  code: string;
}

export interface QueryResult {
  question: string;
  results: CodeResult[];
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail || "Something went wrong.");
  }
  return res.json();
}

export async function ingestRepo(url: string): Promise<IngestResult> {
  const res = await fetch(`${API_BASE}/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  return handle<IngestResult>(res);
}

export async function askQuestion(repoKey: string, question: string, topK = 5): Promise<AskResult> {
  const res = await fetch(`${API_BASE}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_key: repoKey, question, top_k: topK }),
  });
  return handle<AskResult>(res);
}

export async function queryCode(repoKey: string, question: string, topK = 5): Promise<QueryResult> {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_key: repoKey, question, top_k: topK }),
  });
  return handle<QueryResult>(res);
}

export interface ImpactEntry {
  file: string;
  depth: number;
  evidence: string[];
}

export interface ImpactResult {
  file: string;
  affected_file_count: number;
  affected_files: ImpactEntry[];
}

export async function getImpact(repoKey: string, filePath: string, maxDepth = 2): Promise<ImpactResult> {
  const res = await fetch(`${API_BASE}/impact`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_key: repoKey, file_path: filePath, max_depth: maxDepth }),
  });
  return handle<ImpactResult>(res);
}
