import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Layout } from "../components/Layout";

export function LoginPage() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await signIn(email, password);
      navigate("/");
    } catch {
      setError("Invalid credentials");
    }
  };

  return (
    <Layout>
      <div className="mx-auto max-w-md animate-fade-up rounded-2xl border border-white/10 bg-black/25 p-8 shadow-xl">
        <h1 className="font-display text-2xl font-semibold text-white">Sign in</h1>
        <p className="mt-2 text-sm text-slate-400">JWT + Argon2id. Secrets never appear in the UI.</p>
        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <label className="block text-sm">
            Email
            <input
              className="mt-1 w-full rounded border border-white/15 bg-ink px-3 py-2"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              type="email"
              required
            />
          </label>
          <label className="block text-sm">
            Password
            <input
              className="mt-1 w-full rounded border border-white/15 bg-ink px-3 py-2"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              type="password"
              required
            />
          </label>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button type="submit" className="w-full rounded bg-accent px-4 py-2 font-medium text-ink hover:bg-teal-300">
            Login
          </button>
        </form>
        <p className="mt-4 text-sm text-slate-400">
          No account? <Link className="text-accent" to="/register">Register</Link>
        </p>
      </div>
    </Layout>
  );
}
