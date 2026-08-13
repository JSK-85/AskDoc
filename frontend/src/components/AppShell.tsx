import { useEffect, useState } from "react";
import { Sidebar } from "./Sidebar";
import { ChatView } from "./ChatView";
import { DropZone } from "./DropZone";
import { UploadProgress } from "./UploadProgress";
import { DocumentPanel } from "./DocumentPanel";
import { AuthGate } from "./AuthGate";

import { useDocuments } from "@/hooks/useDocuments";
import { useUpload } from "@/hooks/useUpload";
import { useHealth } from "@/hooks/useHealth";
import {
  renameDocument,
  togglePinDocument,
  deleteDocument,
  getApiKey,
  clearApiKey,
} from "@/lib/api";

export function AppShell() {
  const [authenticated, setAuthenticated] = useState(!!getApiKey());

  // If not authenticated, show the AuthGate
  if (!authenticated) {
    return <AuthGate onAuthenticated={() => setAuthenticated(true)} />;
  }

  return <AuthenticatedApp onLogout={() => {
    clearApiKey();
    setAuthenticated(false);
  }} />;
}


function AuthenticatedApp({ onLogout }: { onLogout: () => void }) {
  const online = useHealth();
  const { documents, loading, refetch } = useDocuments();
  const [activeDocId, setActiveDocId] = useState<number | null>(null);
  const [showUpload, setShowUpload] = useState(false);

  const upload = useUpload((id) => {
    refetch();
    setActiveDocId(id);
    setShowUpload(false);
  });

  useEffect(() => {
    if (upload.status === "ingesting" || upload.status === "done") refetch();
  }, [upload.status, upload.chunkCount, refetch]);

  const activeDoc = documents.find((d) => d.doc_id === activeDocId) ?? null;

  const handleSelect = (id: number | null) => {
    setActiveDocId(id);
    setShowUpload(false);
    if (upload.status === "done" || upload.status === "failed") upload.reset();
  };

  const openUpload = () => {
    upload.reset();
    setShowUpload(true);
    setActiveDocId(null);
  };

  const handleRename = async (docId: number, newName: string) => {
    try {
      await renameDocument(docId, newName);
      refetch();
    } catch (e) {
      console.error("Rename failed:", e);
    }
  };

  const handleTogglePin = async (docId: number) => {
    try {
      await togglePinDocument(docId);
      refetch();
    } catch (e) {
      console.error("Pin toggle failed:", e);
    }
  };

  const handleDelete = async (docId: number) => {
    try {
      await deleteDocument(docId);
      if (activeDocId === docId) setActiveDocId(null);
      refetch();
    } catch (e) {
      console.error("Delete failed:", e);
    }
  };

  const showUploadView = showUpload || upload.status !== "idle";

  const statusLabel =
    online === null ? "Connecting" : online ? "System ready" : "Offline";
  const statusColor =
    online === null
      ? "bg-[color:var(--status-pending)]"
      : online
        ? "bg-[color:var(--status-done)]"
        : "bg-[color:var(--status-failed)]";

  return (
    <div className="flex h-screen w-screen bg-[color:var(--shell)]">
      <div className="flex h-full w-full flex-col overflow-hidden bg-[color:var(--shell)]">
        {/* Header */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-white/[0.06] bg-white/[0.015] px-6">
          <div className="flex items-center gap-3">
            <div className="relative h-5 w-5">
              <div className="absolute inset-0 rounded-[5px] bg-foreground" />
              <div className="absolute inset-[5px] rounded-[2px] bg-[color:var(--shell)]" />
            </div>
            <div className="flex items-baseline gap-2.5">
              <span className="text-[13px] font-semibold tracking-tight text-foreground">
                AskDoc
              </span>
              <span className="hidden text-[10px] font-medium uppercase tracking-[0.2em] text-white/35 sm:inline">
                Intelligence
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span
                className={`h-1.5 w-1.5 rounded-full ${statusColor}`}
                aria-hidden
              />
              <span className="text-[10px] font-medium uppercase tracking-[0.16em] text-white/40">
                {statusLabel}
              </span>
            </div>
            <button
              onClick={onLogout}
              className="rounded-md px-2 py-1 text-[10px] font-medium uppercase tracking-wider text-white/30 transition-colors hover:text-white/60 hover:bg-white/[0.05]"
            >
              Logout
            </button>
          </div>
        </header>

        {/* Body */}
        <div className="flex min-h-0 flex-1">
          <Sidebar
            documents={documents}
            loading={loading}
            activeDocId={activeDocId}
            onSelect={handleSelect}
            onUploadClick={openUpload}
            onFile={upload.upload}
            onRename={handleRename}
            onTogglePin={handleTogglePin}
            onDelete={handleDelete}
          />

          <main className="flex min-w-0 flex-1 flex-col bg-[color:var(--canvas)]">
            {showUploadView ? (
              upload.status === "idle" ? (
                <DropZone onFile={upload.upload} />
              ) : (
                <UploadProgress
                  status={upload.status}
                  filename={upload.filename}
                  chunkCount={upload.chunkCount}
                  error={upload.error}
                  onReset={() => {
                    upload.reset();
                    setShowUpload(false);
                  }}
                  onChat={() => {
                    if (upload.docId) {
                      setActiveDocId(upload.docId);
                    }
                    upload.reset();
                    setShowUpload(false);
                  }}
                />
              )
            ) : documents.length === 0 && !loading ? (
              <DropZone onFile={upload.upload} />
            ) : (
              <ChatView activeDoc={activeDoc} totalDocs={documents.length} />
            )}
          </main>

          {!showUploadView && <DocumentPanel activeDoc={activeDoc} />}
        </div>
      </div>
    </div>
  );
}
