import { useCallback, useRef, useState } from "react";
import { UploadCloud } from "lucide-react";

interface Props {
  onFile: (file: File) => void;
}

export function DropZone({ onFile }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [hover, setHover] = useState(false);

  const pick = (file: File) => {
    const ok =
      file.type === "application/pdf" ||
      file.type === "text/plain" ||
      /\.(pdf|txt)$/i.test(file.name);
    if (!ok) return;
    onFile(file);
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setHover(false);
    const f = e.dataTransfer.files?.[0];
    if (f) pick(f);
  }, []);

  return (
    <div className="flex h-full w-full items-center justify-center px-8 py-10">
      <div className="w-full max-w-md text-center">
        <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/30">
          Begin
        </span>
        <h1 className="mt-2 text-2xl font-medium tracking-tight text-foreground">
          Ask your documents anything
        </h1>
        <p className="mx-auto mt-2 max-w-sm text-[13px] leading-relaxed text-white/45">
          Upload a PDF or text file. Every page is indexed, every answer cited.
        </p>

        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setHover(true);
          }}
          onDragLeave={() => setHover(false)}
          onDrop={onDrop}
          className={`mt-8 flex w-full flex-col items-center justify-center gap-3 rounded-2xl border bg-white/[0.02] px-8 py-12 transition-all ${
            hover
              ? "border-white/25 bg-white/[0.04]"
              : "border-white/[0.08] hover:border-white/15 hover:bg-white/[0.03]"
          }`}
        >
          <span className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/[0.08] bg-white/[0.03]">
            <UploadCloud className="h-4.5 w-4.5 text-white/60" strokeWidth={1.5} />
          </span>
          <span className="text-[13px] text-foreground/90">
            Drop a file, or{" "}
            <span className="underline decoration-white/25 underline-offset-4">
              browse
            </span>
          </span>
          <span className="text-[11px] text-white/35">
            PDF or TXT
          </span>
        </button>

        <input
          ref={inputRef}
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
    </div>
  );
}
