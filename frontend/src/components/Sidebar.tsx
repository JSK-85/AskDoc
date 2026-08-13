import { useRef, useState } from "react";
import {
  FileText,
  Layers,
  MoreHorizontal,
  Pencil,
  Pin,
  PinOff,
  Trash2,
} from "lucide-react";
import type { Document } from "@/types";
import { StatusBadge } from "./StatusBadge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";

interface Props {
  documents: Document[];
  loading: boolean;
  activeDocId: number | null;
  onSelect: (id: number | null) => void;
  onUploadClick: () => void;
  onFile?: (file: File) => void;
  onRename?: (docId: number, newName: string) => void;
  onTogglePin?: (docId: number) => void;
  onDelete?: (docId: number) => void;
}

export function Sidebar({
  documents,
  loading,
  activeDocId,
  onSelect,
  onUploadClick,
  onFile,
  onRename,
  onTogglePin,
  onDelete,
}: Props) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [renamingDocId, setRenamingDocId] = useState<number | null>(null);
  const [renameValue, setRenameValue] = useState("");

  const handleUploadClick = () => {
    onUploadClick();
    fileInputRef.current?.click();
  };

  const pick = (file: File) => {
    const ok =
      file.type === "application/pdf" ||
      file.type === "text/plain" ||
      /\.(pdf|txt)$/i.test(file.name);
    if (!ok) return;
    onFile?.(file);
  };

  const startRename = (doc: Document) => {
    setRenamingDocId(doc.doc_id);
    setRenameValue(doc.filename);
  };

  const commitRename = () => {
    if (renamingDocId !== null && renameValue.trim()) {
      onRename?.(renamingDocId, renameValue.trim());
    }
    setRenamingDocId(null);
    setRenameValue("");
  };

  const cancelRename = () => {
    setRenamingDocId(null);
    setRenameValue("");
  };

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-white/[0.06] bg-white/[0.008]">
      <div className="flex flex-1 flex-col p-5">
        <span className="mb-5 px-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/30">
          Library
        </span>

        <button
          onClick={() => onSelect(null)}
          className={`flex w-full items-center justify-between rounded-lg px-3 py-2 text-left transition-colors ${
            activeDocId === null
              ? "border border-white/10 bg-white/[0.05] text-foreground"
              : "border border-transparent text-white/55 hover:bg-white/[0.03] hover:text-foreground"
          }`}
        >
          <span className="flex items-center gap-2.5">
            <Layers className="h-3.5 w-3.5 opacity-80" />
            <span className="text-[13px] font-medium">All documents</span>
          </span>
          <span className="font-mono text-[11px] text-white/40">
            {documents.length}
          </span>
        </button>

        <div className="my-4 h-px bg-white/[0.05]" />

        <div className="-mx-1 flex-1 overflow-y-auto px-1">
          {loading && documents.length === 0 ? (
            <p className="px-3 py-2 text-[12px] text-white/35">Loading…</p>
          ) : documents.length === 0 ? (
            <p className="px-3 py-2 text-[12px] leading-relaxed text-white/35">
              No documents yet. Upload a PDF to begin.
            </p>
          ) : (
            <ul className="space-y-0.5">
              {documents.map((doc) => {
                const active = doc.doc_id === activeDocId;
                const isRenaming = renamingDocId === doc.doc_id;

                return (
                  <li key={doc.doc_id} className="group/card relative">
                    <button
                      onClick={() => onSelect(doc.doc_id)}
                      className={`flex w-full items-start gap-2.5 rounded-lg border px-3 py-2 text-left transition-colors ${
                        active
                          ? "border-white/10 bg-white/[0.05]"
                          : "border-transparent hover:bg-white/[0.03]"
                      }`}
                    >
                      <FileText
                        className={`mt-0.5 h-3.5 w-3.5 shrink-0 ${
                          active ? "text-white/80" : "text-white/40"
                        }`}
                      />
                      <span className="min-w-0 flex-1">
                        {isRenaming ? (
                          <input
                            autoFocus
                            value={renameValue}
                            onChange={(e) => setRenameValue(e.target.value)}
                            onBlur={commitRename}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") commitRename();
                              if (e.key === "Escape") cancelRename();
                            }}
                            onClick={(e) => e.stopPropagation()}
                            className="block w-full truncate rounded bg-white/[0.08] px-1.5 py-0.5 text-[13px] text-foreground outline-none ring-1 ring-white/20 focus:ring-white/40"
                          />
                        ) : (
                          <span
                            className={`block truncate text-[13px] ${
                              active ? "text-foreground" : "text-white/70"
                            }`}
                          >
                            {doc.filename}
                          </span>
                        )}
                        <span className="mt-1 flex items-center gap-2">
                          <StatusBadge status={doc.status} />
                          {doc.pinned && (
                            <Pin className="h-2.5 w-2.5 text-white/30" />
                          )}
                        </span>
                      </span>
                    </button>

                    {/* Context menu trigger — visible on hover */}
                    <div className="absolute right-1.5 top-1.5 opacity-0 transition-opacity group-hover/card:opacity-100">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <button
                            onClick={(e) => e.stopPropagation()}
                            className="flex h-6 w-6 items-center justify-center rounded-md transition-colors hover:bg-white/[0.1]"
                          >
                            <MoreHorizontal className="h-3.5 w-3.5 text-white/50" />
                          </button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent
                          align="end"
                          side="bottom"
                          sideOffset={4}
                          className="doc-context-menu w-44 rounded-xl border-white/[0.08] bg-[#1c1c1e] p-1.5 shadow-2xl"
                        >
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              startRename(doc);
                            }}
                            className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-medium text-white/90 transition-colors hover:bg-white/[0.08] focus:bg-white/[0.08]"
                          >
                            <Pencil className="h-4 w-4 text-white/60" />
                            Rename
                          </DropdownMenuItem>

                          <DropdownMenuSeparator className="my-1 bg-white/[0.06]" />

                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              onTogglePin?.(doc.doc_id);
                            }}
                            className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-medium text-white/90 transition-colors hover:bg-white/[0.08] focus:bg-white/[0.08]"
                          >
                            {doc.pinned ? (
                              <>
                                <PinOff className="h-4 w-4 text-white/60" />
                                Unpin
                              </>
                            ) : (
                              <>
                                <Pin className="h-4 w-4 text-white/60" />
                                Pin
                              </>
                            )}
                          </DropdownMenuItem>

                          <DropdownMenuSeparator className="my-1 bg-white/[0.06]" />

                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              onDelete?.(doc.doc_id);
                            }}
                            className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-medium text-[#e05555] transition-colors hover:bg-[#e05555]/10 focus:bg-[#e05555]/10"
                          >
                            <Trash2 className="h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <button
          type="button"
          onClick={handleUploadClick}
          className="mt-4 w-full rounded-full bg-foreground py-2.5 text-[13px] font-semibold text-background transition-colors hover:bg-white/90 active:bg-white/80"
        >
          Upload document
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,application/pdf,text/plain"
          className="sr-only"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) pick(f);
            e.target.value = "";
          }}
        />
      </div>
    </aside>
  );
}
