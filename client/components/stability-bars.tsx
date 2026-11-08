import type { Label } from "@/lib/types";
import { cn, pct } from "@/lib/utils";

export function ShareBar({ value, label, className }: { value: number | null; label: string; className?: string }) {
  const width = value === null ? 0 : Math.max(0, Math.min(1, value)) * 100;
  return (
    <div className={cn("min-w-28", className)}>
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{label}</span>
        <span className="tabular-nums">{pct(value)}</span>
      </div>
      <div className="mt-0.5 h-1.5 rounded-full bg-muted" aria-hidden>
        <div className="h-1.5 rounded-full bg-accent" style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

const SEGMENT: Record<Label, string> = { Strong: "bg-strong", Moderate: "bg-moderate", Weak: "bg-weak" };

export function LabelDistributionBar({ dist }: { dist: Partial<Record<Label, number>> | null }) {
  if (!dist) return null;
  const order: Label[] = ["Strong", "Moderate", "Weak"];
  const title = order.map((l) => `${l} ${pct(dist[l] ?? 0)}`).join(", ");
  return (
    <div className="min-w-28" title={title}>
      <div className="text-xs text-muted-foreground">Label under resampling</div>
      <div className="mt-0.5 flex h-1.5 overflow-hidden rounded-full bg-muted">
        {order.map((l) => (
          <div key={l} className={SEGMENT[l]} style={{ width: `${(dist[l] ?? 0) * 100}%` }} />
        ))}
      </div>
      <div className="mt-0.5 text-[11px] text-muted-foreground tabular-nums">{title}</div>
    </div>
  );
}
