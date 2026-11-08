// Fixed wording required by AGENTS.md "Domain constraints". Edit with care.

export function HypothesisBanner() {
  return (
    <div role="note" className="rounded-md border border-moderate/50 bg-moderate/10 px-3 py-2 text-sm">
      <strong className="font-semibold">Computational hypothesis, not validated.</strong> Compounds listed here
      come from a database join on suggested identifications. They are not evidence of activity, safety or use,
      and nothing on this site is dosing, preparation or treatment advice.
    </div>
  );
}

export function SyntheticBanner() {
  return (
    <div role="alert" className="bg-danger px-4 py-2 text-center text-sm font-semibold text-white">
      Synthetic test data. None of the names, plants, scores or compounds shown are real.
    </div>
  );
}

export function CandidatePoolNotice() {
  return (
    <p className="text-sm text-muted-foreground">
      Candidates are the species suggested in the literature. The true plant may be outside this list.
    </p>
  );
}

export function ExpertAuthorityNote() {
  return (
    <p className="text-sm text-muted-foreground">
      These results support the judgment of philologists and botanists. They do not replace it.
    </p>
  );
}

export function TextWithheldNote() {
  return (
    <p className="rounded-md border border-dashed px-3 py-2 text-sm text-muted-foreground">
      Source text is withheld until the licences of the Beck translation and the regional floras are confirmed.
      Detail IDs, categories and scores are shown instead.
    </p>
  );
}

export function FirstRankFootnote() {
  return (
    <p className="text-xs text-muted-foreground">
      First-rank share is how often a candidate ranks first when the feature categories are resampled. It
      measures how much the ranking depends on which features are counted. It is not the probability that the
      identification is correct.
    </p>
  );
}

export function AgreementWording() {
  return (
    <p className="text-sm text-muted-foreground">
      No ground truth exists for these identifications. Every figure is agreement with published expert scoring,
      not accuracy.
    </p>
  );
}
