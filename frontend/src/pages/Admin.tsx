import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Navigate } from "react-router-dom";
import { Layout } from "../components/Layout";
import { useAuth } from "../hooks/useAuth";
import * as api from "../services/api";

export function AdminPage() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const keys = useQuery({ queryKey: ["keys"], queryFn: api.keyStatus, enabled: user?.role === "ADMIN" });
  const audit = useQuery({ queryKey: ["audit"], queryFn: api.listAudit, enabled: user?.role === "ADMIN" });

  const rotateSearch = useMutation({
    mutationFn: api.rotateSearchKey,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["keys"] });
      void qc.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const rotateMaster = useMutation({
    mutationFn: api.rotateMasterKey,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["keys"] });
      void qc.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const reindex = useMutation({
    mutationFn: api.reindex,
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["audit"] }),
  });

  if (user && user.role !== "ADMIN") {
    return <Navigate to="/" replace />;
  }

  return (
    <Layout>
      <div className="animate-fade-up space-y-8">
        <div>
          <h1 className="font-display text-3xl font-semibold">Key management & audit</h1>
          <p className="mt-2 text-slate-400">
            Key material is never displayed. Rotation re-wraps DEKs or reindexes HMAC tokens under a new search-key
            version.
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            className="rounded border border-accent/50 px-4 py-2 text-accent"
            onClick={() => rotateSearch.mutate()}
            disabled={rotateSearch.isPending}
          >
            Rotate search key + reindex
          </button>
          <button
            type="button"
            className="rounded border border-warn/50 px-4 py-2 text-warn"
            onClick={() => rotateMaster.mutate()}
            disabled={rotateMaster.isPending}
          >
            Rotate master version + rewrap
          </button>
          <button
            type="button"
            className="rounded border border-white/20 px-4 py-2"
            onClick={() => reindex.mutate()}
            disabled={reindex.isPending}
          >
            Reindex only
          </button>
        </div>

        <section>
          <h2 className="text-lg font-medium">Key versions</h2>
          <div className="mt-3 overflow-x-auto rounded-xl border border-white/10">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-black/30 text-slate-400">
                <tr>
                  <th className="px-4 py-2">Type</th>
                  <th className="px-4 py-2">Version</th>
                  <th className="px-4 py-2">Status</th>
                  <th className="px-4 py-2">Activated</th>
                </tr>
              </thead>
              <tbody>
                {keys.data?.keys.map((k) => (
                  <tr key={`${k.key_type}-${k.version}`} className="border-t border-white/5">
                    <td className="px-4 py-2 font-mono text-xs">{k.key_type}</td>
                    <td className="px-4 py-2">{k.version}</td>
                    <td className="px-4 py-2">{k.status}</td>
                    <td className="px-4 py-2 font-mono text-xs">{k.activated_at ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section>
          <h2 className="text-lg font-medium">Recent audit events</h2>
          <ul className="mt-3 max-h-96 space-y-2 overflow-y-auto rounded-xl border border-white/10 p-3">
            {audit.data?.map((e) => (
              <li key={e.id} className="flex flex-wrap gap-3 border-b border-white/5 py-2 font-mono text-xs">
                <span className={e.success ? "text-accent" : "text-red-400"}>{e.action}</span>
                <span className="text-slate-500">{e.resource_type}/{e.resource_id}</span>
                <span className="text-slate-600">{e.created_at}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </Layout>
  );
}
