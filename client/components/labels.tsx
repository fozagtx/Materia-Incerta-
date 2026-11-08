import { Badge, type BadgeVariant } from "@/components/ui/badge";
import type { Label, LedgerLabel, MatchClass, StabilityBadge } from "@/lib/types";
import { LEDGER_LABEL, MATCH_LABEL, pct } from "@/lib/utils";

const LABEL_VARIANT: Record<Label, BadgeVariant> = { Strong: "strong", Moderate: "moderate", Weak: "weak" };

export function LabelBadge({ label }: { label: Label | null | undefined }) {
  if (!label) return <span className="text-muted-foreground">n/a</span>;
  return <Badge variant={LABEL_VARIANT[label]}>{label}</Badge>;
}

const MATCH_VARIANT: Record<MatchClass, BadgeVariant> = {
  good: "strong",
  partial: "moderate",
  no_match: "danger",
  absent: "outline",
};

export function MatchBadge({ value }: { value: MatchClass | null }) {
  if (!value) return <span className="text-xs text-muted-foreground">-</span>;
  return <Badge variant={MATCH_VARIANT[value]}>{MATCH_LABEL[value]}</Badge>;
}

const LEDGER_VARIANT: Record<LedgerLabel, BadgeVariant> = {
  robust: "strong",
  id_dependent: "moderate",
  no_data: "outline",
};

export function LedgerBadge({ label }: { label: LedgerLabel }) {
  return <Badge variant={LEDGER_VARIANT[label]}>{LEDGER_LABEL[label]}</Badge>;
}

export function HazardLabel({ text }: { text: string }) {
  return (
    <Badge variant="danger" title={text} className="whitespace-normal">
      <span aria-hidden>⚠</span> Hazardous plant: {text}
    </Badge>
  );
}

export function RangeFlag({ inEastMed }: { inEastMed: boolean | null }) {
  if (inEastMed === false) {
    return (
      <Badge variant="moderate" title="WCVP lists no native occurrence in the Eastern Mediterranean areas used">
        Not native to E. Mediterranean (WCVP)
      </Badge>
    );
  }
  if (inEastMed === null) return <Badge variant="outline">Range unknown</Badge>;
  return null;
}

export function StabilityBadgeView({ badge }: { badge: StabilityBadge | null }) {
  if (!badge) return <span className="text-xs text-muted-foreground">n/a</span>;
  if (badge.kind === "tied") {
    return (
      <Badge variant="weak" title="Two or more candidates share the top expert score for a Dioscorides plant">
        tied at top
      </Badge>
    );
  }
  const variant: BadgeVariant = badge.level === "high" ? "strong" : badge.level === "medium" ? "moderate" : "weak";
  const what = badge.kind === "first_rank" ? "top candidate holds" : "label holds";
  return (
    <Badge variant={variant} title={`${what} in ${pct(badge.share)} of resamples (expert scores)`}>
      {what} {pct(badge.share)}
    </Badge>
  );
}
