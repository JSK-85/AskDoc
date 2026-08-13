import { useCallback, useEffect, useRef, useState } from "react";
import { getDocStatus, uploadDocument } from "../lib/api";
import type { DocStatus } from "../types";

type UploadState = "idle" | "uploading" | DocStatus;

export function useUpload(onSuccess: (docId: number) => void) {
  const [status, setStatus] = useState<UploadState>("idle");
  const [filename, setFilename] = useState<string | null>(null);
  const [chunkCount, setChunkCount] = useState(0);
  const [docId, setDocId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const startPolling = useCallback(
    (id: number) => {
      intervalRef.current = setInterval(async () => {
        try {
          const doc = await getDocStatus(id);
          setChunkCount(doc.total_chunks);
          setStatus(doc.status);
          if (doc.status === "done") {
            clearPolling();
            onSuccess(id);
          } else if (doc.status === "failed") {
            clearPolling();
            setError("Ingestion failed on the server.");
          }
        } catch (e) {
          clearPolling();
          setError(e instanceof Error ? e.message : "Status check failed");
        }
      }, 2000);
    },
    [onSuccess],
  );

  const upload = useCallback(
    async (file: File) => {
      setError(null);
      setFilename(file.name);
      setChunkCount(0);
      setStatus("uploading");
      try {
        const res = await uploadDocument(file);
        setDocId(res.doc_id);
        setStatus("pending");
        startPolling(res.doc_id);
      } catch (e) {
        setStatus("failed");
        setError(e instanceof Error ? e.message : "Upload failed");
      }
    },
    [startPolling],
  );

  const reset = useCallback(() => {
    clearPolling();
    setStatus("idle");
    setFilename(null);
    setChunkCount(0);
    setDocId(null);
    setError(null);
  }, []);

  useEffect(() => clearPolling, []);

  return { status, filename, chunkCount, docId, error, upload, reset };
}
