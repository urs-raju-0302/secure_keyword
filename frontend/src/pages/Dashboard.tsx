import { Link } from "react-router-dom";
import { ArrowRight, Search } from "lucide-react";
import { Layout } from "@/components/Layout";
import { EncryptedBadge } from "@/components/EncryptedBadge";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";

export function DashboardPage() {
  const { user } = useAuth();

  return (
    <Layout>
      <section className="page-enter flex min-h-[70vh] flex-col justify-center">
        <EncryptedBadge className="w-fit" />
        <p className="mt-6 font-display text-5xl font-bold tracking-tight text-foreground sm:text-6xl md:text-7xl">
          Secure Keyword
        </p>
        <h1 className="mt-4 max-w-2xl font-display text-2xl font-semibold tracking-tight text-foreground/90 sm:text-3xl">
          Encrypted storage with protected keyword search
        </h1>
        <p className="mt-4 max-w-xl text-base text-muted-foreground sm:text-lg">
          Files are encrypted before object storage. Search uses opaque tokens — plaintext keywords are never stored in
          the index.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Button asChild size="lg">
            <Link to="/documents">
              Manage documents
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link to="/search">
              <Search className="h-4 w-4" />
              Protected search
            </Link>
          </Button>
        </div>
        <p className="mt-8 text-sm text-muted-foreground">
          Signed in as <span className="font-medium text-foreground">{user?.email}</span>
          <span className="mx-2 text-border">·</span>
          {user?.role}
        </p>
      </section>
    </Layout>
  );
}
