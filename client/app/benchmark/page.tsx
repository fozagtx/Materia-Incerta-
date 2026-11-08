import type { Metadata } from "next";

import { AgreementWording, FirstRankFootnote } from "@/components/notices";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Table, Td, Th } from "@/components/ui/table";
import { getBenchmark, getManifest } from "@/lib/data";
import type { DetailAgreement, PartitionResult } from "@/lib/types";
import { MATCH_LABEL, num, pct } from "@/lib/utils";

export const metadata: Metadata = { title: "Benchmark and limits · Materia Incerta" };

const PARTITION_TITLE: Record<string, string> = {
  held_out: "Held-out names",
  tuning: "Tuning names",
  unsplit: "All names (split not assigned)",
  unassigned: "Names outside the split",
};

function Row({ name, value, baseline, bar }: { name: string; value: string; baseline?: string; bar?: string }) {
  return (
    <tr>
      <Td>{name}</Td>
      <Td className="tabular-nums">{value}</Td>
      <Td className="tabular-nums text-muted-foreground">{baseline ?? "–"}</Td>
      <Td className="text-muted-foreground">{bar ?? "–"}</Td>
    </tr>
  );
}

function Confusion({ d }: { d: DetailAgreement }) {
  const order = Object.keys(d.confusion);
  return (
    <Table className="max-w-lg">
      <thead>
        <tr>
          <Th>Expert ↓ / Model →</Th>
          {order.map((m) => (
            <Th key={m}>{MATCH_LABEL[m]}</Th>
          ))}
        </tr>
      </thead>
      <tbody>
        {order.map((e) => (
          <tr key={e}>
            <Td className="text-xs font-medium">{MATCH_LABEL[e]}</Td>
            {order.map((m) => (
              <Td key={m} className={e === m ? "font-semibold tabular-nums" : "tabular-nums"}>
                {d.confusion[e as keyof typeof d.confusion]?.[m as keyof typeof d.confusion]}
              </Td>
            ))}
          </tr>
        ))}
      </tbody>
    </Table>
  );
}

function PartitionCard({ name, p, bars }: { name: string; p: PartitionResult; bars: { detail_kappa_min: number; invented_evidence_max: number } }) {
  const hasModel = p.detail.n > 0;
  return (
    <Card className="space-y-4">
      <div>
        <CardTitle>{PARTITION_TITLE[name] ?? name}</CardTitle>
        {!hasModel ? <CardDescription>No model scores for these names yet.</CardDescription> : null}
      </div>
      {hasModel ? (
        <Table>
          <thead>
            <tr>
              <Th>Test</Th>
              <Th>Result</Th>
              <Th>Baseline</Th>
              <Th>Proposed bar</Th>
            </tr>
          </thead>
          <tbody>
            <Row
              name={`Detail matching, weighted kappa (n=${p.detail.n})`}
              value={num(p.detail.kappa_weighted)}
              baseline={`always "good": ${num(p.detail.baseline_always_good_kappa_weighted)}`}
              bar={`≥ ${bars.detail_kappa_min}`}
            />
            <Row
              name="Detail matching, exact agreement"
              value={pct(p.detail.exact_agreement)}
              baseline={`always "good": ${pct(p.detail.baseline_always_good_exact)}`}
            />
            <Row
              name={`Invented evidence on expert-absent items (n=${p.invented_evidence.n_expert_absent})`}
              value={pct(p.invented_evidence.match_claim_rate, 1)}
              bar={`< ${pct(bars.invented_evidence_max)}`}
            />
            <Row
              name={`Candidate labels, exact (n=${p.labels.n})`}
              value={pct(p.labels.exact)}
              baseline={`always Moderate: ${pct(p.labels.baseline_always_moderate_exact)}`}
              bar="clearly above baseline"
            />
            <Row name="Candidate labels, within one level" value={pct(p.labels.within_one)} />
            <Row
              name={`Top-candidate agreement (${p.ranking.n_groups} plants with several candidates)`}
              value={pct(p.ranking.top_agreement)}
              baseline={`random order: ${pct(p.ranking.baseline_random)}`}
              bar="clearly above baseline"
            />
            {p.memorisation ? (
              <Row
                name="Memorisation: unmasked minus masked kappa"
                value={num(p.memorisation.kappa_gap)}
                bar="report the gap"
              />
            ) : null}
          </tbody>
        </Table>
      ) : null}

      <div className="text-sm">
        <span className="font-medium">Stability (expert scores):</span>{" "}
        {pct(p.stability_expert.stable_share)} of {p.stability_expert.n_groups} plants with several candidates keep a
        unique top candidate in at least {pct(p.stability_expert.threshold)} of resamples.
        {p.stability_model ? (
          <>
            {" "}
            Model scores: {pct(p.stability_model.stable_share)} of {p.stability_model.n_groups}.
          </>
        ) : null}
      </div>

      {hasModel ? (
        <details className="text-sm">
          <summary className="cursor-pointer font-medium">Confusion matrix</summary>
          <div className="mt-2">
            <Confusion d={p.detail} />
          </div>
        </details>
      ) : null}

      {hasModel ? (
        <div className="space-y-2 text-sm">
          <h3 className="font-medium">Known failures</h3>
          {p.labels.disagreements.length === 0 &&
          p.invented_evidence.comparison_ids.length === 0 &&
          p.ranking.groups.every((g) => g.agree) ? (
            <p className="text-muted-foreground">None recorded in this partition.</p>
          ) : null}
          {p.labels.disagreements.length > 0 ? (
            <div>
              <div className="text-xs text-muted-foreground">Label disagreements</div>
              <ul className="list-disc pl-5 text-xs">
                {p.labels.disagreements.map((d) => (
                  <li key={d.candidate_key}>
                    <span className="font-mono">{d.candidate_key}</span>: expert {d.expert}, model {d.model}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {p.ranking.groups.some((g) => !g.agree) ? (
            <div>
              <div className="text-xs text-muted-foreground">Top candidate differs from expert scoring</div>
              <ul className="list-disc pl-5 text-xs">
                {p.ranking.groups
                  .filter((g) => !g.agree)
                  .map((g) => (
                    <li key={`${g.lemma_tag}-${g.dmm_id}`} className="font-mono">
                      {g.lemma_tag} / {g.dmm_id}
                    </li>
                  ))}
              </ul>
            </div>
          ) : null}
          {p.invented_evidence.comparison_ids.length > 0 ? (
            <div>
              <div className="text-xs text-muted-foreground">Model claimed a match where experts marked the detail absent</div>
              <ul className="list-disc pl-5 font-mono text-xs">
                {p.invented_evidence.comparison_ids.map((id) => (
                  <li key={id}>{id}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </Card>
  );
}

const LIMITS = [
  "No ground truth exists. Results are agreement with published expert scoring, never accuracy about the true plant.",
  "Candidates are inherited from the literature. The true plant may not be among them; 21 of the 130 taxa are missing from the two regional floras.",
  "Dioscorides often describes a plant by likening it to another. Those details give no direct feature and are flagged.",
  "The score uses botanical evidence only. Medicinal-use comparison is left out because the paper treats it as much less robust.",
  "First-rank share measures sensitivity to which features are counted. It is not the probability that an identification is correct.",
  "LOTUS lists what has been published. A compound missing from LOTUS is not absent from the plant; sparse taxa are labelled no data.",
  "Every compound result is a computational, unvalidated hypothesis. Nothing here is dosing, preparation or treatment advice.",
  "Hazardous genera in the benchmark, including Aristolochia, Conium, Hyoscyamus and Nerium, carry hazard labels.",
  "The model may recognise plants despite name masking. The memorisation test reports masked against unmasked agreement.",
  "The output supports philologists and botanists. It does not replace them.",
];

export default function BenchmarkPage() {
  const bench = getBenchmark();
  const manifest = getManifest();
  const b = bench.benchmark;
  const order = ["held_out", "tuning", "unsplit", "unassigned"];
  const partitions = b ? Object.keys(b.partitions).sort((x, y) => order.indexOf(x) - order.indexOf(y)) : [];

  return (
    <div className="space-y-6">
      <header className="max-w-3xl space-y-2">
        <h1 className="font-serif text-3xl font-semibold tracking-tight">Benchmark and limits</h1>
        <AgreementWording />
        <p className="text-sm text-muted-foreground">
          Benchmark: Lardos et al. (2024), 50 historical names, 61 Dioscorides plants, 141 candidate records and 1,213
          expert comparisons. Prompts are tuned on 10 names and reported on the other 40.
        </p>
      </header>

      <Card>
        <CardTitle>Reproduction check</CardTitle>
        <CardDescription>The pipeline recomputes the paper&apos;s labels from its own expert scores before any model runs.</CardDescription>
        <div className="mt-3 text-sm">
          {bench.reproduce ? (
            <div className="space-y-1">
              <div>
                {bench.reproduce.ok ? <Badge variant="strong">reproduced</Badge> : <Badge variant="danger">mismatches</Badge>}{" "}
                {bench.reproduce.checked} candidate labels checked, {bench.reproduce.mismatches.length} mismatches.
              </div>
              {bench.reproduce.gap_values.length > 0 ? (
                <div className="text-muted-foreground">
                  {bench.reproduce.gap_values.length} published values fall between 4 and 5, where the paper&apos;s rule is
                  unclear.
                </div>
              ) : null}
            </div>
          ) : (
            <span className="text-muted-foreground">Not run yet.</span>
          )}
        </div>
      </Card>

      {b ? (
        partitions.map((name) => {
          const p = b.partitions[name];
          return p ? <PartitionCard key={name} name={name} p={p} bars={b.bars} /> : null;
        })
      ) : (
        <Card>
          <CardTitle>Agreement</CardTitle>
          <CardDescription>The benchmark has not been run yet.</CardDescription>
        </Card>
      )}
      <FirstRankFootnote />

      <Card>
        <CardTitle>Method constants</CardTitle>
        <div className="mt-3 grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
          <div>
            Match scores: good {manifest.constants.match_scores.good}, partial {manifest.constants.match_scores.partial}, no
            match {manifest.constants.match_scores.no_match}, absent {manifest.constants.match_scores.absent}
          </div>
          <div>
            Labels: Strong ≥ {manifest.constants.strong_min}, Moderate {manifest.constants.moderate_min}–
            {manifest.constants.moderate_max}, Weak &lt; {manifest.constants.moderate_min}
          </div>
          <div>
            Resamples: {manifest.constants.n_resamples.toLocaleString("en")}, seed {manifest.constants.random_seed}
          </div>
          <div>LOTUS no-data cutoff: fewer than {manifest.constants.lotus_min_records} compounds</div>
          <div>Range check areas (WGSRPD L3): {manifest.constants.east_med_areas.join(", ")}</div>
          <div>
            Model:{" "}
            {manifest.scoring ? `${manifest.scoring.model}, prompt ${manifest.scoring.prompt_version}` : "not run yet"}
          </div>
        </div>
      </Card>

      <Card>
        <CardTitle>Limits</CardTitle>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm">
          {LIMITS.map((l) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
      </Card>

      <Card id="sources">
        <CardTitle>Data sources and licences</CardTitle>
        <CardDescription>
          The Osbaldeston version of Dioscorides is not used. Modern community knowledge from the ethnobotanical sources
          is not extracted or republished.
        </CardDescription>
        <div className="mt-3">
          {manifest.sources.length === 0 ? (
            <p className="text-sm text-muted-foreground">No sources recorded.</p>
          ) : (
            <Table>
              <thead>
                <tr>
                  <Th>Source</Th>
                  <Th>Version</Th>
                  <Th>Licence</Th>
                  <Th>Republished here</Th>
                </tr>
              </thead>
              <tbody>
                {manifest.sources.map((s) => (
                  <tr key={s.key}>
                    <Td className="max-w-md">
                      <div className="font-medium">{s.title}</div>
                      <div className="text-xs text-muted-foreground">{s.citation}</div>
                      {s.notes ? <div className="mt-1 text-xs text-muted-foreground">{s.notes}</div> : null}
                    </Td>
                    <Td className="text-xs">{s.version ?? "not pinned"}</Td>
                    <Td className="text-xs">
                      {s.licence}
                      {!s.licence_confirmed ? (
                        <div>
                          <Badge variant="moderate">unconfirmed</Badge>
                        </div>
                      ) : null}
                    </Td>
                    <Td className="text-xs">{s.republish ? "IDs and derived data" : "IDs and scores only"}</Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </div>
      </Card>
    </div>
  );
}
