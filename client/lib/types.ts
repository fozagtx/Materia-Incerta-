// Shapes of the JSON in public/data/, written by pipeline/src/materia_incerta/export.py.
// Keep these in step with export.py.

export type Label = "Strong" | "Moderate" | "Weak";
export type MatchClass = "good" | "partial" | "no_match" | "absent";
export type LedgerLabel = "robust" | "id_dependent" | "no_data";
export type ChemStatus = "reported" | "not_reported" | "no_data";
export type Partition = "tuning" | "held_out";

export interface ScoreView {
  degree_of_congruence: number;
  positive_categories: number;
  negative_categories: number;
  category_means: Record<string, number>;
  label: Label;
  rank: number;
  label_share: number | null;
  label_distribution: Partial<Record<Label, number>> | null;
  first_rank_share: number | null;
  rank_distribution: Record<string, number> | null;
}

export interface CandidateView {
  candidate_key: string;
  source_name: string;
  wcvp_id: string | null;
  accepted_name: string | null;
  in_east_med: boolean | null;
  hazard: string | null;
  reconcile_note: string | null;
  paper_label: Label | null;
  expert: ScoreView | null;
  model: ScoreView | null;
  lotus_compounds: number | null;
  has_lotus_data: boolean;
}

export interface DetailView {
  detail_id: string;
  category: string;
  text: string | null;
  comparative: boolean;
}

export interface EvidenceRow {
  comparison_id: string;
  candidate_key: string;
  category: string;
  ancient_detail_id: string;
  ancient_text: string | null;
  modern_text: string | null;
  comparative: boolean;
  expert_class: MatchClass | null;
  model_class: MatchClass | null;
  model_reason: string | null;
}

export interface PlantView {
  dmm_id: string;
  chapter: string | null;
  plant_type: string | null;
  detail_level: string | null;
  details: DetailView[];
  candidates: CandidateView[];
  evidence: EvidenceRow[];
}

export interface LedgerEntry {
  lemma_tag: string;
  inchikey: string;
  compound_name: string | null;
  pathway: string | null;
  compound_class: string | null;
  label: LedgerLabel;
  status_by_candidate: Record<string, ChemStatus>;
  candidates_with_data: number;
  candidates_total: number;
  unjoined_candidates: string[];
  dois: string[];
}

export interface PlantCase {
  lemma_tag: string;
  greek_name: string;
  transliteration: string;
  partition: Partition | null;
  text_withheld: boolean;
  dmm_plants: PlantView[];
  ledger: {
    min_records: number;
    counts: Record<LedgerLabel, number>;
    entries: LedgerEntry[];
  };
}

export interface StabilityBadge {
  kind: "first_rank" | "label" | "tied";
  share: number;
  level: "high" | "medium" | "low";
}

export interface IndexRow {
  lemma_tag: string;
  greek_name: string;
  transliteration: string;
  dmm_ids: string[];
  candidate_count: number;
  hazard: boolean;
  has_model_scores: boolean;
  stability: StabilityBadge | null;
}

export interface SourceInfo {
  key: string;
  title: string;
  citation: string;
  version: string | null;
  licence: string;
  licence_confirmed: boolean;
  republish: boolean;
  notes: string | null;
}

export interface Manifest {
  pipeline_version: string;
  synthetic: boolean;
  text_withheld: boolean;
  counts: { names: number; dmm_plants: number; candidates: number; comparisons: number };
  constants: {
    match_scores: Record<MatchClass, number>;
    strong_min: number;
    moderate_min: number;
    moderate_max: number;
    n_resamples: number;
    random_seed: number;
    stable_top_share: number;
    lotus_min_records: number;
    east_med_areas: string[];
  };
  scoring: { model: string; prompt_version: string; memorisation?: boolean } | null;
  sources: SourceInfo[];
}

export interface DetailAgreement {
  n: number;
  kappa_weighted: number | null;
  kappa_unweighted: number | null;
  exact_agreement: number | null;
  baseline_always_good_exact: number | null;
  baseline_always_good_kappa_weighted: number | null;
  confusion: Record<MatchClass, Record<MatchClass, number>>;
}

export interface PartitionResult {
  detail: DetailAgreement;
  invented_evidence: {
    n_expert_absent: number;
    match_claim_rate: number | null;
    any_claim_rate: number | null;
    comparison_ids: string[];
  };
  labels: {
    n: number;
    exact: number | null;
    within_one: number | null;
    baseline_always_moderate_exact: number | null;
    disagreements: { candidate_key: string; expert: Label; model: Label }[];
  };
  ranking: {
    n_groups: number;
    top_agreement: number | null;
    baseline_random: number | null;
    groups: { lemma_tag: string; dmm_id: string; n_candidates: number; agree: boolean; random_baseline: number }[];
  };
  stability_expert: StabilitySummary;
  stability_model: StabilitySummary | null;
  memorisation?: { masked: DetailAgreement; unmasked: DetailAgreement; kappa_gap: number | null };
}

export interface StabilitySummary {
  threshold: number;
  n_groups: number;
  stable_share: number | null;
  groups: {
    lemma_tag: string;
    dmm_id: string;
    top_candidate: string | null;
    first_rank_share: number | null;
    stable: boolean;
  }[];
}

export interface BenchmarkFile {
  status: "ready" | "not_run";
  benchmark: {
    wording: string;
    bars: { detail_kappa_min: number; invented_evidence_max: number };
    class_order: MatchClass[];
    split: { seed: number; tuning: string[]; held_out: string[] } | null;
    partitions: Record<string, PartitionResult>;
  } | null;
  reproduce: {
    checked: number;
    ok: boolean;
    mismatches: {
      candidate_key: string;
      paper_label: Label | null;
      computed_label: Label | null;
      paper_doc: number | null;
      computed_doc: number | null;
      note: string | null;
    }[];
    gap_values: [string, number][];
  } | null;
}
