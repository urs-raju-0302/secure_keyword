import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { Info, Search } from "lucide-react";
import { Layout } from "@/components/Layout";
import { PageHeader } from "@/components/PageHeader";
import { EncryptedBadge } from "@/components/EncryptedBadge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import * as api from "@/services/api";
import type { SearchResponse } from "@/types";

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
      <div className="page-enter">
        <PageHeader
          title="Protected search"
          description="Keywords are converted to HMAC tokens before index lookup. Only authorized documents are returned."
          actions={<EncryptedBadge label="Tokenized query" />}
        />

        <form onSubmit={onSubmit} className="flex flex-col gap-3 sm:flex-row">
          <Input
            className="h-11 flex-1 bg-card text-base"
            placeholder="Enter a keyword"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            required
          />
          <Button type="submit" size="lg" disabled={pending} className="sm:min-w-[140px]">
            <Search className="h-4 w-4" />
            {pending ? "Searching…" : "Search"}
          </Button>
        </form>

        {error ? (
          <Alert variant="destructive" className="mt-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}

        {result ? (
          <div className="mt-8 space-y-4">
            <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
              <span>
                <span className="font-medium text-foreground">{result.result_count}</span> authorized result
                {result.result_count === 1 ? "" : "s"}
              </span>
              <Separator orientation="vertical" className="hidden h-4 sm:block" />
              <span className="font-mono text-xs">normalized length {result.keyword_normalized_length}</span>
            </div>

            <Alert variant="muted">
              <Info className="h-4 w-4" />
              <AlertDescription>{result.note}</AlertDescription>
            </Alert>

            <ul className="overflow-hidden rounded-lg border border-border bg-card">
              {result.documents.map((d, i) => (
                <li
                  key={d.id}
                  className="result-row flex items-center justify-between gap-4 border-b border-border px-4 py-3 last:border-0"
                  style={{ animationDelay: `${i * 40}ms` }}
                >
                  <Link to={`/documents/${d.id}`} className="font-medium text-primary hover:underline">
                    {d.original_filename}
                  </Link>
                  <Badge variant="outline" className="font-mono text-[11px]">
                    {d.encryption_algorithm}
                  </Badge>
                </li>
              ))}
              {result.documents.length === 0 ? (
                <li className="px-4 py-10 text-center text-muted-foreground">No authorized matches.</li>
              ) : null}
            </ul>
          </div>
        ) : null}
      </div>
    </Layout>
  );
}
