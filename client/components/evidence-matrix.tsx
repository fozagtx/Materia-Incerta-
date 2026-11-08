import { MatchBadge } from "@/components/labels";
import { Table, Td, Th } from "@/components/ui/table";
import type { CandidateView, DetailView, EvidenceRow } from "@/lib/types";

function ComparativeFlag() {
  return (
    <span
      className="ml-1 rounded border border-moderate/50 px-1 text-[10px] font-medium text-moderate"
      title="Dioscorides describes this detail only by likening the plant to another, so it gives no direct feature"
    >
      by comparison
    </span>
  );
}

export function EvidenceMatrix({
  details,
  candidates,
  evidence,
}: {
  details: DetailView[];
  candidates: CandidateView[];
  evidence: EvidenceRow[];
}) {
  const categories = Array.from(new Set([...details.map((d) => d.category), ...evidence.map((e) => e.category)])).sort();
  const byCell = new Map<string, EvidenceRow[]>();
  for (const e of evidence) {
    const key = `${e.category}::${e.candidate_key}`;
    byCell.set(key, [...(byCell.get(key) ?? []), e]);
  }
  const detailsByCat = new Map<string, DetailView[]>();
  for (const d of details) detailsByCat.set(d.category, [...(detailsByCat.get(d.category) ?? []), d]);
  const withReasons = evidence.filter((e) => e.model_reason || e.ancient_text || e.modern_text);

  return (
    <div className="space-y-3">
      <Table>
        <thead>
          <tr>
            <Th>Feature category</Th>
            <Th>Ancient detail</Th>
            {candidates.map((c) => (
              <Th key={c.candidate_key} className="min-w-32 italic">
                {c.accepted_name ?? c.source_name}
              </Th>
            ))}
          </tr>
        </thead>
        <tbody>
          {categories.map((cat) => {
            const ds = detailsByCat.get(cat) ?? [];
            return (
              <tr key={cat}>
                <Td className="whitespace-nowrap text-xs font-medium">{cat}</Td>
                <Td className="max-w-72 text-xs">
                  {ds.length === 0 ? <span className="text-muted-foreground">-</span> : null}
                  {ds.map((d) => (
                    <div key={d.detail_id}>
                      {d.text ?? <span className="text-muted-foreground">{d.detail_id}</span>}
                      {d.comparative ? <ComparativeFlag /> : null}
                    </div>
                  ))}
                </Td>
                {candidates.map((c) => {
                  const rows = byCell.get(`${cat}::${c.candidate_key}`) ?? [];
                  return (
                    <Td key={c.candidate_key}>
                      {rows.length === 0 ? <span className="text-xs text-muted-foreground">-</span> : null}
                      <div className="space-y-1.5">
                        {rows.map((r) => (
                          <div
                            key={r.comparison_id}
                            className="grid grid-cols-[3.25rem_auto] items-center justify-start gap-x-1 gap-y-0.5 text-xs"
                            title={r.comparison_id}
                          >
                            <span className="text-muted-foreground">Expert</span>
                            <MatchBadge value={r.expert_class} />
                            <span className="text-muted-foreground">Model</span>
                            <MatchBadge value={r.model_class} />
                          </div>
                        ))}
                      </div>
                    </Td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </Table>
      {withReasons.length > 0 ? (
        <details className="rounded-md border p-3 text-sm">
          <summary className="cursor-pointer font-medium">Modern details and model reasons ({withReasons.length})</summary>
          <ul className="mt-2 space-y-2">
            {withReasons.map((e) => (
              <li key={e.comparison_id} className="border-t pt-2 text-xs">
                <div className="font-mono text-[11px] text-muted-foreground">{e.comparison_id}</div>
                {e.modern_text ? <div>Modern: {e.modern_text}</div> : null}
                {e.model_reason ? <div className="text-muted-foreground">Reason: {e.model_reason}</div> : null}
              </li>
            ))}
          </ul>
        </details>
      ) : null}
    </div>
  );
}
