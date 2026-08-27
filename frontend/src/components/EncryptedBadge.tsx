import { ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export function EncryptedBadge({ className, label = "Encrypted" }: { className?: string; label?: string }) {
  return (
    <Badge variant="success" className={cn("gap-1 font-medium", className)}>
      <ShieldCheck className="h-3 w-3" />
      {label}
    </Badge>
  );
}
