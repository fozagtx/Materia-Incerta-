import { LedgerBadge } from "@/components/labels";
import { HypothesisBanner } from "@/components/notices";
import { Table, Td, Th } from "@/components/ui/table";
import type { CandidateView, ChemStatus, PlantCase } from "@/lib/types";
import { STATUS_LABEL, cn } from "@/lib/utils";

const STATUS_CLASS: Record<ChemStatus, string> = {
  reported: "text-strong",
  not_reported: "text-foreground",
  no_data: "text-muted-foreground",
};

export function CompoundLedger({ ledger, candidates }: { ledger: PlantCase["ledger"]; candidates: CandidateView[] }) {
  const names = new Map<string, string>();
  for (const c of candidates) if (c.wcvp_id) names.set(c.wcvp_id, c.accepted_name ?? c.source_name);
  const taxa = Array.from(new Set(ledger.entries.flatMap((e) => Object.keys(e.status_by_candidate)))).sort();
  const unjoined = ledger.entries[0]?.unjoined_candidates ?? [];

  return (
    <div className="space-y-3">
      <HypothesisBanner />
      <div className="flex flex-wrap gap-3 text-sm">
        <span>
          <LedgerBadge label="robust" /> {ledger.counts.robust}
        </span>
        <span>
          <LedgerBadge label="id_dependent" /> {ledger.counts.id_dependent}
        </span>
        <span>
          <LedgerBadge label="no_data" /> {ledger.counts.no_data}
        </span>
      </div>
      <ul className="list-disc space-y-1 pl-5 text-xs text-muted-foreground">
        <li>Robust: reported in LOTUS for every candidate that has enough records.</li>
        <li>ID-dependent: reported for some candidates but not others, so it depends on which plant is meant.</li>
        <li>
          No data: fewer than {ledger.min_records} LOTUS compounds for a candidate. Missing records do not mean a
          compound is absent.
        </li>
        {unjoined.length > 0 ? <li>{unjoined.length} candidate(s) could not be joined to LOTUS (no WCVP match).</li> : null}
      </ul>
      {ledger.entries.length === 0 ? (
        <p className="text-sm text-muted-foreground">No LOTUS records for any candidate of this name.</p>
      ) : (
        <div className="max-h-[32rem] overflow-y-auto rounded-md border">
          <Table>
            <thead className="sticky top-0 bg-card">
              <tr>
                <Th>Compound</Th>
                <Th>Class</Th>
                <Th>Ledger</Th>
                {taxa.map((t) => (
                  <Th key={t} className="italic">
                    {names.get(t) ?? t}
                  </Th>
                ))}
                <Th>References</Th>
              </tr>
            </thead>
            <tbody>
              {ledger.entries.map((e) => (
                <tr key={e.inchikey}>
                  <Td>
                    <div>{e.compound_name ?? <span className="text-muted-foreground">unnamed</span>}</div>
                    <div className="font-mono text-[10px] text-muted-foreground">{e.inchikey}</div>
                  </Td>
                  <Td className="text-xs">
                    {e.pathway}
                    {e.compound_class ? <div className="text-muted-foreground">{e.compound_class}</div> : null}
                  </Td>
                  <Td>
                    <LedgerBadge label={e.label} />
                  </Td>
                  {taxa.map((t) => {
                    const s = e.status_by_candidate[t];
                    return (
                      <Td key={t} className={cn("text-xs", s ? STATUS_CLASS[s] : "")}>
                        {s ? STATUS_LABEL[s] : "-"}
                      </Td>
                    );
                  })}
                  <Td className="text-xs">
                    {e.dois.slice(0, 3).map((d) => (
                      <div key={d}>
                        <a className="text-accent underline-offset-2 hover:underline" href={`https://doi.org/${d}`} rel="noreferrer">
                          {d}
                        </a>
                      </div>
                    ))}
                    {e.dois.length > 3 ? <div className="text-muted-foreground">+{e.dois.length - 3} more</div> : null}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      )}
    </div>
  );
}
