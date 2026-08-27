import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Navigate } from "react-router-dom";
import { toast } from "sonner";
import { Layout } from "@/components/Layout";
import { PageHeader } from "@/components/PageHeader";
import { useAuth } from "@/hooks/useAuth";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import * as api from "@/services/api";

export function AdminPage() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const [confirmMaster, setConfirmMaster] = useState(false);

  const keys = useQuery({ queryKey: ["keys"], queryFn: api.keyStatus, enabled: user?.role === "ADMIN" });
  const audit = useQuery({ queryKey: ["audit"], queryFn: api.listAudit, enabled: user?.role === "ADMIN" });

  const rotateSearch = useMutation({
    mutationFn: api.rotateSearchKey,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["keys"] });
      void qc.invalidateQueries({ queryKey: ["audit"] });
      toast.success("Search key rotated and index rebuilt");
    },
    onError: () => toast.error("Search key rotation failed"),
  });

  const rotateMaster = useMutation({
    mutationFn: api.rotateMasterKey,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["keys"] });
      void qc.invalidateQueries({ queryKey: ["audit"] });
      setConfirmMaster(false);
      toast.success("Master key version rotated; DEKs rewrapped");
    },
    onError: () => toast.error("Master rotation failed"),
  });

  const reindex = useMutation({
    mutationFn: api.reindex,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["audit"] });
      toast.success("Reindex complete");
    },
    onError: () => toast.error("Reindex failed"),
  });

  if (user && user.role !== "ADMIN") {
    return <Navigate to="/" replace />;
  }

  return (
    <Layout>
      <div className="page-enter">
        <PageHeader
          title="Administration"
          description="Manage key versions and review audit events. Key material is never displayed."
        />

        <Tabs defaultValue="keys">
          <TabsList>
            <TabsTrigger value="keys">Key versions</TabsTrigger>
            <TabsTrigger value="audit">Audit</TabsTrigger>
          </TabsList>

          <TabsContent value="keys" className="space-y-6">
            <div className="rounded-lg border border-border bg-card p-4">
              <p className="text-sm text-muted-foreground">
                Rotation creates a new key version. Search rotation rebuilds the HMAC index; master rotation rewraps
                document DEKs.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  disabled={rotateSearch.isPending}
                  onClick={() => rotateSearch.mutate()}
                >
                  {rotateSearch.isPending ? "Rotating…" : "Rotate search key"}
                </Button>
                <Button variant="outline" disabled={reindex.isPending} onClick={() => reindex.mutate()}>
                  {reindex.isPending ? "Reindexing…" : "Reindex only"}
                </Button>
                <Button variant="destructive" onClick={() => setConfirmMaster(true)}>
                  Rotate master version
                </Button>
              </div>
            </div>

            <div className="overflow-hidden rounded-lg border border-border bg-card">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Version</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Activated</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {keys.data?.keys.map((k) => (
                    <TableRow key={`${k.key_type}-${k.version}`}>
                      <TableCell className="font-mono text-xs">{k.key_type}</TableCell>
                      <TableCell>{k.version}</TableCell>
                      <TableCell>
                        <Badge variant={k.status === "ACTIVE" ? "success" : "secondary"}>{k.status}</Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        {k.activated_at ?? "—"}
                      </TableCell>
                    </TableRow>
                  ))}
                  {!keys.data?.keys.length ? (
                    <TableRow>
                      <TableCell colSpan={4} className="text-muted-foreground">
                        No key versions loaded.
                      </TableCell>
                    </TableRow>
                  ) : null}
                </TableBody>
              </Table>
            </div>
          </TabsContent>

          <TabsContent value="audit">
            <div className="max-h-[32rem] overflow-y-auto rounded-lg border border-border bg-card">
              <ul>
                {audit.data?.map((e) => (
                  <li
                    key={e.id}
                    className="flex flex-wrap items-center gap-3 border-b border-border px-4 py-3 font-mono text-xs last:border-0"
                  >
                    <Badge variant={e.success ? "success" : "destructive"}>{e.action}</Badge>
                    <span className="text-muted-foreground">
                      {e.resource_type}/{e.resource_id}
                    </span>
                    <span className="ml-auto text-muted-foreground">{e.created_at}</span>
                  </li>
                ))}
                {!audit.data?.length ? (
                  <li className="px-4 py-10 text-center text-sm text-muted-foreground">No audit events yet.</li>
                ) : null}
              </ul>
            </div>
          </TabsContent>
        </Tabs>
      </div>

      <Dialog open={confirmMaster} onOpenChange={setConfirmMaster}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rotate master key version?</DialogTitle>
            <DialogDescription>
              This retires the active master version and rewraps all document DEKs. Search keys are unaffected.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmMaster(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={rotateMaster.isPending}
              onClick={() => rotateMaster.mutate()}
            >
              {rotateMaster.isPending ? "Rotating…" : "Confirm rotation"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
