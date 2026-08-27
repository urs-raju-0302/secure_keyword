import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";
import { AdminPage } from "./pages/Admin";
import { DashboardPage } from "./pages/Dashboard";
import { DocumentDetailsPage } from "./pages/DocumentDetails";
import { DocumentsPage } from "./pages/Documents";
import { LoginPage } from "./pages/Login";
import { RegisterPage } from "./pages/Register";
import { SearchPage } from "./pages/Search";

function Private({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-slate-400">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/"
        element={
          <Private>
            <DashboardPage />
          </Private>
        }
      />
      <Route
        path="/documents"
        element={
          <Private>
            <DocumentsPage />
          </Private>
        }
      />
      <Route
        path="/documents/:id"
        element={
          <Private>
            <DocumentDetailsPage />
          </Private>
        }
      />
      <Route
        path="/search"
        element={
          <Private>
            <SearchPage />
          </Private>
        }
      />
      <Route
        path="/admin"
        element={
          <Private>
            <AdminPage />
          </Private>
        }
      />
    </Routes>
  );
}
