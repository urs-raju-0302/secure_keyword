import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { EncryptedBadge } from "@/components/EncryptedBadge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function LoginPage() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setPending(true);
    try {
      await signIn(email, password);
      navigate("/");
    } catch {
      setError("Invalid credentials");
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <aside className="relative hidden overflow-hidden bg-primary text-primary-foreground lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div
          className="pointer-events-none absolute inset-0 opacity-30"
          style={{
            backgroundImage:
              "linear-gradient(135deg, transparent 40%, rgba(255,255,255,0.08) 40%, rgba(255,255,255,0.08) 60%, transparent 60%)",
            backgroundSize: "24px 24px",
          }}
        />
        <div className="relative">
          <p className="font-display text-2xl font-bold tracking-tight">Secure Keyword</p>
        </div>
        <div className="relative max-w-md page-enter">
          <h1 className="font-display text-4xl font-semibold leading-tight tracking-tight xl:text-5xl">
            Search encrypted files without exposing your keywords.
          </h1>
          <p className="mt-4 text-base text-primary-foreground/80">
            Documents stay encrypted in object storage. Keywords become protected tokens before index lookup.
          </p>
          <div className="mt-8">
            <EncryptedBadge className="border-0 bg-white/15 text-primary-foreground" label="AES-256-GCM at rest" />
          </div>
        </div>
        <p className="relative text-xs text-primary-foreground/60">Educational searchable encryption console</p>
      </aside>

      <div className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-md page-enter">
          <div className="mb-8 lg:hidden">
            <p className="font-display text-2xl font-bold">Secure Keyword</p>
            <p className="mt-2 text-sm text-muted-foreground">Sign in to manage encrypted documents.</p>
          </div>
          <h2 className="font-display text-3xl font-semibold tracking-tight">Sign in</h2>
          <p className="mt-2 text-sm text-muted-foreground">Use your account credentials to continue.</p>

          <form className="mt-8 space-y-5" onSubmit={onSubmit}>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error ? (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            ) : null}
            <Button type="submit" className="w-full" disabled={pending}>
              {pending ? "Signing in…" : "Sign in"}
            </Button>
          </form>

          <p className="mt-6 text-sm text-muted-foreground">
            No account?{" "}
            <Link className="font-medium text-primary hover:underline" to="/register">
              Create one
            </Link>
          </p>
          <p className="mt-8 text-xs text-muted-foreground">Passwords hashed with Argon2id. Session via JWT.</p>
        </div>
      </div>
    </div>
  );
}
