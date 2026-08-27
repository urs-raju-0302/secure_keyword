import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { Layout } from "../components/Layout";
import * as api from "../services/api";
import type { SearchResponse } from "../types";

export function SearchPage() {
  const [keyword, setKeyword] = useState("");
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setPending(true);
    setError(null);
    try {
      const data = await api.search(keyword);
      setResult(data);
    } catch {
      setError("Search failed");
    } finally {
      setPending(false);
    }
  };

  return (
    <Layout>
      <div className="animate-fade-up">
        <h1 className="font-display text-3xl font-semibold">Protected keyword search</h1>
        <p className="mt-2 max-w-2xl text-slate-400">
          Your keyword is normalized and converted to an HMAC-SHA-256 token before index lookup. The cloud index never
          stores plaintext keywords. Repeated identical keywords produce linkable tokens (search-pattern leakage).
        </p>

        <form onSubmit={onSubmit} className="mt-6 flex flex-wrap gap-3">
          <input
            className="min-w-[240px] flex-1 rounded border border-white/15 bg-black/30 px-4 py-2"
            placeholder="e.g. security"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            required
          />
          <button type="submit" className="rounded bg-accent px-5 py-2 font-medium text-ink" disabled={pending}>
            {pending ? "Searching…" : "Search"}
          </button>
        </form>
        {error && <p className="mt-3 text-sm text-red-400">{error}</p>}

        {result && (
          <div className="mt-8 space-y-4">
            <p className="font-mono text-xs text-slate-400">
              Results: {result.result_count} · normalized length: {result.keyword_normalized_length}
            </p>
            <p className="text-sm text-warn">{result.note}</p>
            <ul className="divide-y divide-white/10 rounded-xl border border-white/10">
              {result.documents.map((d) => (
                <li key={d.id} className="flex items-center justify-between px-4 py-3">
                  <Link to={`/documents/${d.id}`} className="text-accent hover:underline">
                    {d.original_filename}
                  </Link>
                  <span className="font-mono text-xs text-slate-500">{d.encryption_algorithm}</span>
                </li>
              ))}
              {result.documents.length === 0 && <li className="px-4 py-6 text-slate-500">No authorized matches.</li>}
            </ul>
          </div>
        )}
      </div>
    </Layout>
  );
}
