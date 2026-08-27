import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Layout } from "../components/Layout";
import * as api from "../services/api";

export function DocumentsPage() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["documents"], queryFn: api.listDocuments });
  const upload = useMutation({
    mutationFn: (file: File) => api.uploadDocument(file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });
  const remove = useMutation({
    mutationFn: (id: string) => api.deleteDocument(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });

  return (
    <Layout>
      <div className="animate-fade-up">
        <h1 className="font-display text-3xl font-semibold">Encrypted documents</h1>
        <p className="mt-2 text-slate-400">Uploaded files are encrypted client-side-of-storage (AES-256-GCM) before MinIO/S3.</p>

        <label className="mt-6 inline-flex cursor-pointer items-center gap-3 rounded border border-dashed border-accent/40 px-4 py-3 text-sm text-accent">
          <input
            type="file"
            className="hidden"
            accept=".txt,.md,.json,.pdf,text/plain,text/markdown,application/json,application/pdf"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) upload.mutate(f);
            }}
          />
          {upload.isPending ? "Encrypting & uploading…" : "Upload file"}
        </label>
        {upload.isError && <p className="mt-2 text-sm text-red-400">Upload failed</p>}

        <div className="mt-8 overflow-x-auto rounded-xl border border-white/10">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-black/30 text-slate-400">
              <tr>
                <th className="px-4 py-3">Filename</th>
                <th className="px-4 py-3">Algorithm</th>
                <th className="px-4 py-3">KEK ver</th>
                <th className="px-4 py-3">Size</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr>
                  <td className="px-4 py-4" colSpan={5}>
                    Loading…
                  </td>
                </tr>
              )}
              {data?.map((d) => (
                <tr key={d.id} className="border-t border-white/5">
                  <td className="px-4 py-3">
                    <Link className="text-accent hover:underline" to={`/documents/${d.id}`}>
                      {d.original_filename}
                    </Link>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">{d.encryption_algorithm}</td>
                  <td className="px-4 py-3 font-mono text-xs">{d.dek_key_version}</td>
                  <td className="px-4 py-3">{d.size_bytes} B</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      className="text-red-300 hover:text-red-200"
                      onClick={() => remove.mutate(d.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {!isLoading && data?.length === 0 && (
                <tr>
                  <td className="px-4 py-6 text-slate-500" colSpan={5}>
                    No documents yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
}
