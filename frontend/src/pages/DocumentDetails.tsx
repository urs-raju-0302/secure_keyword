import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { toast } from "sonner";
import { ArrowLeft, Download } from "lucide-react";
import { Layout } from "@/components/Layout";
import { EncryptedBadge } from "@/components/EncryptedBadge";
import { PageHeader } from "@/components/PageHeader";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import * as api from "@/services/api";

export function DocumentDetailsPage() {
  const { id = "" } = useParams();
  const { data, isLoading, error } = useQuery({
    queryKey: ["document", id],
    queryFn: () => api.getDocument(id),
    enabled: !!id,
  });

  const onDownload = async () => {
    if (!data) return;
    try {
      await api.downloadDocument(data.id, data.original_filename);
      toast.success("Decrypted download started");
    } catch {
      toast.error("Download failed");
    }
  };

  return (
    <Layout>
      <div className="page-enter max-w-2xl">
        <Button asChild variant="ghost" size="sm" className="mb-4 -ml-2 text-muted-foreground">
          <Link to="/documents">
            <ArrowLeft className="h-4 w-4" />
            Back to documents
          </Link>
        </Button>

        <PageHeader title="Document" actions={<EncryptedBadge />} />

        {isLoading ? <p className="text-muted-foreground">Loading…</p> : null}
        {error ? (
          <Alert variant="destructive">
            <AlertDescription>Not found or unauthorized.</AlertDescription>
          </Alert>
        ) : null}

        {data ? (
          <div className="rounded-lg border border-border bg-card p-6">
            <dl className="space-y-4">
              <div>
                <dt className="text-xs uppercase tracking-wide text-muted-foreground">Filename</dt>
                <dd className="mt-1 text-base font-medium">{data.original_filename}</dd>
              </div>
              <Separator />
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <dt className="text-xs uppercase tracking-wide text-muted-foreground">Content type</dt>
                  <dd className="mt-1 text-sm">{data.content_type}</dd>
                </div>
                <div>
                  <dt className="text-xs uppercase tracking-wide text-muted-foreground">Size</dt>
                  <dd className="mt-1 text-sm">{data.size_bytes} bytes</dd>
                </div>
                <div>
                  <dt className="text-xs uppercase tracking-wide text-muted-foreground">Encryption</dt>
                  <dd className="mt-1">
                    <Badge variant="outline" className="font-mono text-[11px]">
                      {data.encryption_algorithm}
                    </Badge>
                  </dd>
                </div>
                <div>
                  <dt className="text-xs uppercase tracking-wide text-muted-foreground">DEK key version</dt>
                  <dd className="mt-1 font-mono text-sm">{data.dek_key_version}</dd>
                </div>
              </div>
            </dl>
            <p className="mt-6 text-sm text-muted-foreground">
              Ciphertext remains in object storage. Download unwraps the DEK and decrypts only after authorization.
            </p>
            <Button className="mt-6" onClick={() => void onDownload()}>
              <Download className="h-4 w-4" />
              Decrypt & download
            </Button>
          </div>
        ) : null}
      </div>
    </Layout>
  );
}
