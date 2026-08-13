export type DocStatus = "pending" | "ingesting" | "done" | "failed";

export interface Document {
  doc_id: number;
  filename: string;
  status: DocStatus;
  total_chunks: number;
  pinned: boolean;
}

export interface Source {
  page: number;
  excerpt: string;
  doc_id: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  latency_ms?: number;
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
  latency_ms: number;
}

export interface IngestResponse {
  doc_id: number;
  status: string;
  message: string;
}
