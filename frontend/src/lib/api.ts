import type {
  Document,
  IngestResponse,
  QueryResponse,
} from "../types";

const BASE = import.meta.env.VITE_API_BASE_URL as string;

// ---------------------------------------------------------------------------
// API Key Management (runtime, NOT baked into bundle)
// ---------------------------------------------------------------------------
let _apiKey: string | null = null;

export function getApiKey(): string | null {
  if (!_apiKey) {
    _apiKey = sessionStorage.getItem("askdoc_api_key");
  }
  return _apiKey;
}

export function setApiKey(key: string): void {
  _apiKey = key;
  sessionStorage.setItem("askdoc_api_key", key);
}

export function clearApiKey(): void {
  _apiKey = null;
  sessionStorage.removeItem("askdoc_api_key");
}

function authHeaders(): HeadersInit {
  const key = getApiKey();
  if (!key) throw new Error("Not authenticated");
  return { "X-API-KEY": key };
}

// ---------------------------------------------------------------------------
// API Functions
// ---------------------------------------------------------------------------

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE}/health`);
    if (!res.ok) return false;
    const json = await res.json();
    return json.status === "ok";
  } catch {
    return false;
  }
}

/** Quick auth validation — tries a lightweight authenticated call. */
export async function validateApiKey(key: string): Promise<boolean> {
  try {
    const res = await fetch(`${BASE}/api/v1/documents?limit=1`, {
      headers: { "X-API-KEY": key },
    });
    return res.ok;
  } catch {
    return false;
  }
}

export async function uploadDocument(file: File): Promise<IngestResponse> {
  const form = new FormData();
  form.append("file", file);
  // Do NOT set Content-Type — browser will set multipart boundary.
  const res = await fetch(`${BASE}/api/v1/ingest`, {
    method: "POST",
    headers: authHeaders(),
    body: form,
  });
  if (!res.ok) {
    let detail = "Upload failed";
    try {
      const err = await res.json();
      detail = err.detail ?? detail;
    } catch {}
    const error = new Error(detail) as Error & { status?: number };
    error.status = res.status;
    throw error;
  }
  return res.json();
}

export async function getDocStatus(docId: number): Promise<Document> {
  const res = await fetch(`${BASE}/api/v1/status/${docId}`);
  if (!res.ok) throw new Error("Status check failed");
  return res.json();
}

export async function listDocuments(
  skip = 0,
  limit = 100,
): Promise<Document[]> {
  const res = await fetch(
    `${BASE}/api/v1/documents?skip=${skip}&limit=${limit}`,
  );
  if (!res.ok) throw new Error("Failed to load documents");
  return res.json();
}

export async function queryDocument(
  question: string,
  docId?: number,
): Promise<QueryResponse> {
  const res = await fetch(`${BASE}/api/v1/query`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ question, doc_id: docId ?? null }),
  });
  if (!res.ok) {
    let detail = "Query failed";
    try {
      const err = await res.json();
      detail = err.detail ?? detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

// --- Document file URL (for PDF viewer) ---

export function getDocumentFileUrl(docId: number): string {
  return `${BASE}/api/v1/documents/${docId}/file`;
}

// --- Rename ---

export async function renameDocument(
  docId: number,
  newName: string,
): Promise<{ doc_id: number; filename: string }> {
  const res = await fetch(`${BASE}/api/v1/documents/${docId}`, {
    method: "PATCH",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ filename: newName }),
  });
  if (!res.ok) {
    let detail = "Rename failed";
    try {
      const err = await res.json();
      detail = err.detail ?? detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

// --- Pin / Unpin ---

export async function togglePinDocument(
  docId: number,
): Promise<{ doc_id: number; pinned: boolean }> {
  const res = await fetch(`${BASE}/api/v1/documents/${docId}/pin`, {
    method: "PATCH",
    headers: authHeaders(),
  });
  if (!res.ok) {
    let detail = "Pin toggle failed";
    try {
      const err = await res.json();
      detail = err.detail ?? detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

// --- Delete ---

export async function deleteDocument(
  docId: number,
): Promise<{ doc_id: number; status: string; message: string }> {
  const res = await fetch(`${BASE}/api/v1/documents/${docId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!res.ok) {
    let detail = "Delete failed";
    try {
      const err = await res.json();
      detail = err.detail ?? detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}
