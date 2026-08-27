import { Link } from "react-router-dom";
import { Layout } from "../components/Layout";
import { useAuth } from "../hooks/useAuth";

export function DashboardPage() {
  const { user } = useAuth();

  return (
    <Layout>
      <section className="animate-fade-up">
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-accent">Secure Keyword Search</p>
        <h1 className="mt-3 max-w-2xl font-display text-4xl font-semibold leading-tight text-white">
          Encrypted cloud storage with protected keyword search
        </h1>
        <p className="mt-4 max-w-xl text-slate-300">
          Documents are encrypted with per-file DEKs (AES-256-GCM) before object storage. Search uses HMAC-SHA-256
          tokens — plaintext keywords are not stored in the index.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link to="/documents" className="rounded bg-accent px-5 py-2.5 font-medium text-ink">
            Manage documents
          </Link>
          <Link to="/search" className="rounded border border-accent/40 px-5 py-2.5 text-accent">
            Protected search
          </Link>
        </div>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          <div className="rounded-xl border border-white/10 bg-black/20 p-4">
            <div className="h-1 w-12 animate-pulse-line rounded bg-accent" />
            <h2 className="mt-3 font-medium">Envelope encryption</h2>
            <p className="mt-1 text-sm text-slate-400">Unique DEK per document, wrapped by versioned KEK.</p>
          </div>
          <div className="rounded-xl border border-white/10 bg-black/20 p-4">
            <div className="h-1 w-12 animate-pulse-line rounded bg-accent" style={{ animationDelay: "0.4s" }} />
            <h2 className="mt-3 font-medium">Search tokens</h2>
            <p className="mt-1 text-sm text-slate-400">Deterministic HMAC tokens — equality leakage documented.</p>
          </div>
          <div className="rounded-xl border border-white/10 bg-black/20 p-4">
            <div className="h-1 w-12 animate-pulse-line rounded bg-accent" style={{ animationDelay: "0.8s" }} />
            <h2 className="mt-3 font-medium">Signed in as</h2>
            <p className="mt-1 font-mono text-sm text-slate-300">{user?.email} ({user?.role})</p>
          </div>
        </div>
      </section>
    </Layout>
  );
}
