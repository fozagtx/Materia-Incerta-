import { HazardLabel, LabelBadge, RangeFlag } from "@/components/labels";
import { LabelDistributionBar, ShareBar } from "@/components/stability-bars";
import { Table, Td, Th } from "@/components/ui/table";
import type { CandidateView, ScoreView } from "@/lib/types";

function ScoreCell({ score }: { score: ScoreView | null }) {
  if (!score) return <span className="text-xs text-muted-foreground">not scored</span>;
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <LabelBadge label={score.label} />
        <span className="text-xs tabular-nums text-muted-foreground" title="Degree of congruence: positive minus negative categories">
          DoC {score.degree_of_congruence} ({score.positive_categories}+ / {score.negative_categories}−)
        </span>
      </div>
    </div>
  );
}

function StabilityCell({ score }: { score: ScoreView | null }) {
  if (!score) return null;
  return (
    <div className="space-y-2">
      <ShareBar value={score.label_share} label="Keeps label" />
      <ShareBar value={score.first_rank_share} label="Ranks first" />
      <LabelDistributionBar dist={score.label_distribution} />
    </div>
  );
}

export function CandidateName({ c }: { c: CandidateView }) {
  return (
    <div>
      <div className="font-medium italic">{c.accepted_name ?? c.source_name}</div>
      {c.accepted_name && c.accepted_name !== c.source_name ? (
        <div className="text-xs text-muted-foreground">
          as given: <span className="italic">{c.source_name}</span>
        </div>
      ) : null}
      {c.wcvp_id ? (
        <div className="text-xs text-muted-foreground">WCVP {c.wcvp_id}</div>
      ) : (
        <div className="text-xs text-danger">Not matched in WCVP{c.reconcile_note ? `: ${c.reconcile_note}` : ""}</div>
      )}
    </div>
  );
}

export function CandidateTable({ candidates }: { candidates: CandidateView[] }) {
  return (
    <Table>
      <thead>
        <tr>
          <Th>Rank</Th>
          <Th>Candidate</Th>
          <Th>Expert scoring</Th>
          <Th>Stability (expert)</Th>
          <Th>Model scoring</Th>
          <Th>Stability (model)</Th>
          <Th>LOTUS</Th>
        </tr>
      </thead>
      <tbody>
        {candidates.map((c) => (
          <tr key={c.candidate_key}>
            <Td className="tabular-nums">{c.expert?.rank ?? "–"}</Td>
            <Td className="min-w-48">
              <CandidateName c={c} />
              <div className="mt-1 flex flex-wrap gap-1">
                {c.hazard ? <HazardLabel text={c.hazard} /> : null}
                <RangeFlag inEastMed={c.in_east_med} />
              </div>
              {c.paper_label ? (
                <div className="mt-1 text-xs text-muted-foreground">Paper label: {c.paper_label}</div>
              ) : null}
            </Td>
            <Td>
              <ScoreCell score={c.expert} />
            </Td>
            <Td>
              <StabilityCell score={c.expert} />
            </Td>
            <Td>
              <ScoreCell score={c.model} />
            </Td>
            <Td>
              <StabilityCell score={c.model} />
            </Td>
            <Td className="text-xs">
              {c.lotus_compounds === null ? (
                <span className="text-muted-foreground">not joined</span>
              ) : (
                <>
                  <div className="tabular-nums">{c.lotus_compounds} compounds</div>
                  {!c.has_lotus_data ? <div className="text-muted-foreground">below cutoff: no data</div> : null}
                </>
              )}
            </Td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}
