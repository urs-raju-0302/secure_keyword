import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { Trash2 } from "lucide-react";
import { Layout } from "@/components/Layout";
import { Dropzone } from "@/components/Dropzone";
import { PageHeader } from "@/components/PageHeader";
import { EncryptedBadge } from "@/components/EncryptedBadge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import * as api from "@/services/api";

export function DocumentsPage() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["documents"], queryFn: api.listDocuments });
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const upload = useMutation({
    mutationFn: (file: File) => api.uploadDocument(file),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["documents"] });
      toast.success("Document encrypted and uploaded");
    },
    onError: () => toast.error("Upload failed"),
  });

  const remove = useMutation({
    mutationFn: (id: string) => api.deleteDocument(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["documents"] });
      setDeleteId(null);
      toast.success("Document deleted");
    },
    onError: () => toast.error("Delete failed"),
  });

  return (
    <Layout>
      <div className="page-enter">
        <PageHeader
          title="Documents"
          description="Files are encrypted with a unique DEK before they reach object storage."
          actions={<EncryptedBadge />}
        />

        <Dropzone
          pending={upload.isPending}
          accept=".txt,.md,.json,.pdf,text/plain,text/markdown,application/json,application/pdf"
          onFile={(file) => upload.mutate(file)}
        />

        <div className="mt-8 overflow-hidden rounded-lg border border-border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Filename</TableHead>
                <TableHead>Algorithm</TableHead>
                <TableHead>KEK ver</TableHead>
                <TableHead>Size</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-muted-foreground">
                    Loading…
                  </TableCell>
                </TableRow>
              ) : null}
              {data?.map((d) => (
                <TableRow key={d.id}>
                  <TableCell>
                    <Link className="font-medium text-primary hover:underline" to={`/documents/${d.id}`}>
                      {d.original_filename}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="font-mono text-[11px]">
                      {d.encryption_algorithm}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">{d.dek_key_version}</TableCell>
                  <TableCell className="text-muted-foreground">{d.size_bytes} B</TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" className="text-destructive" onClick={() => setDeleteId(d.id)}>
                      <Trash2 className="h-4 w-4" />
                      Delete
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {!isLoading && data?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="py-10 text-center text-muted-foreground">
                    No documents yet. Upload a file to get started.
                  </TableCell>
                </TableRow>
              ) : null}
            </TableBody>
          </Table>
        </div>
      </div>

      <Dialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete document?</DialogTitle>
            <DialogDescription>
              This removes ciphertext, metadata, and search-index entries. This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={!deleteId || remove.isPending}
              onClick={() => deleteId && remove.mutate(deleteId)}
            >
              {remove.isPending ? "Deleting…" : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
