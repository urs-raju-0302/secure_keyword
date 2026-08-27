import { useRef, useState } from "react";
import { Upload } from "lucide-react";
import { cn } from "@/lib/utils";

export function Dropzone({
  onFile,
  pending,
  accept,
}: {
  onFile: (file: File) => void;
  pending?: boolean;
  accept?: string;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handleFiles = (files: FileList | null) => {
    const file = files?.[0];
    if (file) onFile(file);
  };

  return (
    <button
      type="button"
      disabled={pending}
      onClick={() => inputRef.current?.click()}
      onDragEnter={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragOver={(e) => e.preventDefault()}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        handleFiles(e.dataTransfer.files);
      }}
      className={cn(
        "flex w-full flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-border bg-card px-6 py-10 text-center transition-colors",
        dragging && "border-primary bg-primary/5",
        pending && "opacity-60",
      )}
    >
      <Upload className="h-5 w-5 text-primary" />
      <div>
        <p className="text-sm font-medium text-foreground">
          {pending ? "Encrypting and uploading…" : "Drop a file or click to upload"}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">TXT, MD, JSON, PDF — encrypted before object storage</p>
      </div>
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept={accept}
        onChange={(e) => {
          handleFiles(e.target.files);
          e.target.value = "";
        }}
      />
    </button>
  );
}
