import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Layout } from "../components/Layout";

export function RegisterPage() {
  const { signUp } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await signUp(email, password);
      navigate("/");
    } catch {
      setError("Registration failed (password min 10 chars, unique email)");
    }
  };

  return (
    <Layout>
      <div className="mx-auto max-w-md animate-fade-up rounded-2xl border border-white/10 bg-black/25 p-8">
        <h1 className="font-display text-2xl font-semibold">Create account</h1>
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
            Password (min 10)
            <input
              className="mt-1 w-full rounded border border-white/15 bg-ink px-3 py-2"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              type="password"
              minLength={10}
              required
            />
          </label>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button type="submit" className="w-full rounded bg-accent px-4 py-2 font-medium text-ink">
            Register
          </button>
        </form>
        <p className="mt-4 text-sm text-slate-400">
          Already registered? <Link className="text-accent" to="/login">Login</Link>
        </p>
      </div>
    </Layout>
  );
}
