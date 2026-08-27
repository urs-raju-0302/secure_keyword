import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, signOut } = useAuth();

  return (
    <div className="min-h-screen">
      <header className="border-b border-white/10 bg-black/20 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4">
          <Link to="/" className="font-display text-lg font-semibold tracking-tight text-accent">
            Secure Keyword
          </Link>
          {user && (
            <nav className="flex flex-wrap items-center gap-4 text-sm text-slate-300">
              <NavLink to="/documents" className={({ isActive }) => (isActive ? "text-accent" : "hover:text-white")}>
                Documents
              </NavLink>
              <NavLink to="/search" className={({ isActive }) => (isActive ? "text-accent" : "hover:text-white")}>
                Search
              </NavLink>
              {user.role === "ADMIN" && (
                <NavLink to="/admin" className={({ isActive }) => (isActive ? "text-accent" : "hover:text-white")}>
                  Admin
                </NavLink>
              )}
              <span className="font-mono text-xs text-slate-400">{user.email}</span>
              <button
                type="button"
                onClick={() => void signOut()}
                className="rounded border border-white/20 px-3 py-1 hover:border-accent hover:text-accent"
              >
                Logout
              </button>
            </nav>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
    </div>
  );
}
