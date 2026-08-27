import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { Layout } from "../components/Layout";
import * as api from "../services/api";

export function DocumentDetailsPage() {
  const { id = "" } = useParams();
  const { data, isLoading, error } = useQuery({
    queryKey: ["document", id],
    queryFn: () => api.getDocument(id),
    enabled: !!id,
  });

  return (
    <Layout>
      <div className="animate-fade-up max-w-2xl">
        <h1 className="font-display text-3xl font-semibold">Document</h1>
        {isLoading && <p className="mt-4 text-slate-400">Loading…</p>}
        {error && <p className="mt-4 text-red-400">Not found or unauthorized</p>}
        {data && (
          <div className="mt-6 space-y-3 rounded-xl border border-white/10 bg-black/25 p-6">
            <p>
              <span className="text-slate-400">Filename:</span> {data.original_filename}
            </p>
            <p>
              <span className="text-slate-400">Content type:</span> {data.content_type}
            </p>
            <p>
              <span className="text-slate-400">Encryption:</span>{" "}
              <span className="font-mono text-accent">{data.encryption_algorithm}</span>
            </p>
            <p>
              <span className="text-slate-400">DEK key version:</span> {data.dek_key_version}
            </p>
            <p>
              <span className="text-slate-400">Size:</span> {data.size_bytes} bytes
            </p>
            <p className="text-sm text-slate-500">
              Ciphertext lives in object storage. Download unwraps the DEK and decrypts only after authorization.
            </p>
            <button
              type="button"
              className="mt-4 rounded bg-accent px-4 py-2 font-medium text-ink"
              onClick={() => void api.downloadDocument(data.id, data.original_filename)}
            >
              Decrypt & download
            </button>
          </div>
        )}
      </div>
    </Layout>
  );
}
