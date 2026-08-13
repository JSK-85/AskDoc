import { useEffect, useState } from "react";
import { FileText } from "lucide-react";
import type { Document } from "@/types";
import { StatusBadge } from "./StatusBadge";
import { getDocumentFileUrl } from "@/lib/api";

interface Props {
  activeDoc: Document | null;
}

export function DocumentPanel({ activeDoc }: Props) {
  const [textContent, setTextContent] = useState<string | null>(null);
  const [loadingText, setLoadingText] = useState(false);

  const isPdf = activeDoc?.filename?.toLowerCase().endsWith(".pdf");
  const isTxt = activeDoc?.filename?.toLowerCase().endsWith(".txt");

  // For TXT files, fetch content to display inline
  useEffect(() => {
    if (!activeDoc || !isTxt) {
      setTextContent(null);
      return;
    }
    let cancelled = false;
    setLoadingText(true);
    fetch(getDocumentFileUrl(activeDoc.doc_id))
      .then((r) => (r.ok ? r.text() : Promise.reject("Failed to load")))
      .then((text) => {
        if (!cancelled) setTextContent(text);
      })
      .catch(() => {
        if (!cancelled) setTextContent(null);
      })
      .finally(() => {
        if (!cancelled) setLoadingText(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeDoc?.doc_id, isTxt]);

  return (
    <aside className="hidden h-full w-[380px] shrink-0 flex-col border-l border-white/[0.06] bg-white/[0.008] lg:flex">
      <div className="flex h-14 shrink-0 items-center border-b border-white/[0.06] px-6">
        <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/30">
          Document
        </span>
      </div>

      {activeDoc ? (
        <div className="flex min-h-0 flex-1 flex-col">
          <div className="border-b border-white/[0.06] px-6 py-5">
            <div className="flex items-start gap-3">
              <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-white/[0.08] bg-white/[0.02]">
                <FileText className="h-4 w-4 text-white/60" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-[13px] font-medium text-foreground">
                  {activeDoc.filename}
                </p>
                <div className="mt-1.5 flex items-center gap-2">
                  <StatusBadge status={activeDoc.status} />
                </div>
              </div>
            </div>
          </div>

          {/* Scrollable PDF / TXT viewer */}
          <div className="flex min-h-0 flex-1 flex-col">
            <div className="px-6 pt-5 pb-3">
              <span className="block text-[10px] font-semibold uppercase tracking-[0.18em] text-white/30">
                Preview
              </span>
            </div>

            <div className="flex-1 overflow-hidden px-4 pb-4">
              {isPdf ? (
                <div className="pdf-viewer-container h-full w-full overflow-hidden rounded-lg border border-white/[0.06]">
                  <iframe
                    key={activeDoc.doc_id}
                    src={getDocumentFileUrl(activeDoc.doc_id)}
                    title={`Preview of ${activeDoc.filename}`}
                    className="h-full w-full border-0"
                    style={{ colorScheme: "normal" }}
                  />
                </div>
              ) : isTxt ? (
                <div className="h-full overflow-y-auto rounded-lg border border-white/[0.06] bg-black/30 p-4">
                  {loadingText ? (
                    <div className="flex h-full items-center justify-center">
                      <span className="text-[11px] text-white/30">
                        Loading…
                      </span>
                    </div>
                  ) : textContent ? (
                    <pre className="whitespace-pre-wrap break-words font-mono text-[11px] leading-relaxed text-white/60">
                      {textContent}
                    </pre>
                  ) : (
                    <div className="flex h-full items-center justify-center">
                      <span className="text-[11px] text-white/35">
                        Could not load file content.
                      </span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex h-full items-center justify-center rounded-lg border border-white/[0.06] bg-white/[0.01]">
                  <div className="text-center">
                    <FileText className="mx-auto mb-2 h-6 w-6 text-white/20" />
                    <p className="text-[11px] text-white/35">
                      Preview not available for this file type.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="flex flex-1 flex-col items-center justify-center px-8 text-center">
          <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl border border-white/[0.08] bg-white/[0.02]">
            <FileText className="h-4 w-4 text-white/25" />
          </div>
          <p className="text-[13px] font-medium text-white/70">
            No document selected
          </p>
          <p className="mt-1 text-[11px] leading-relaxed text-white/35">
            Choose a document from the library to view its index and ask
            grounded questions.
          </p>
        </div>
      )}
    </aside>
  );
}
