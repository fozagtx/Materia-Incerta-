"""Pydantic models for every table the pipeline writes and every model response.

Join keys are the paper's lemma tags, Dioscorides (DMM) IDs, WCVP IDs and
InChIKeys. Plant names appear only as display fields and masking input.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MatchClass = Literal["good", "partial", "no_match", "absent"]
Label = Literal["Strong", "Moderate", "Weak"]
LedgerLabel = Literal["robust", "id_dependent", "no_data"]
CandidateChemStatus = Literal["reported", "not_reported", "no_data"]
ScoreSource = Literal["expert", "model"]
Partition = Literal["tuning", "held_out"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# ---------------------------------------------------------------------------
# Core tables
# ---------------------------------------------------------------------------


class HistoricalName(Strict):
    """A plant name from John the Physician's Therapeutics."""

    lemma_tag: str
    greek_name: str
    transliteration: str
    dmm_ids: tuple[str, ...]
    #: Other spellings and common names, used only for masking.
    name_variants: tuple[str, ...] = ()


class BotanicalDetail(Strict):
    detail_id: str
    category: str
    #: None when the source text cannot be held or republished.
    text: str | None = None
    #: Dioscorides describes this detail only by likening it to another plant.
    comparative: bool = False


class DmmPlant(Strict):
    """A plant chapter in Dioscorides' De materia medica."""

    dmm_id: str
    chapter: str
    plant_type: str | None = None
    detail_level: str | None = None
    #: Greek and Latin names in the chapter, used only for masking.
    names: tuple[str, ...] = ()
    details: tuple[BotanicalDetail, ...] = ()


class Candidate(Strict):
    """A species suggested in the literature for one DMM plant of one name."""

    candidate_key: str
    lemma_tag: str
    dmm_id: str
    #: The name exactly as the source gives it. Used only by reconcile.py.
    source_name: str
    wcvp_id: str | None = None
    accepted_name: str | None = None
    accepted_genus: str | None = None
    synonyms: tuple[str, ...] = ()
    common_names: tuple[str, ...] = ()
    #: True if WCVP lists native occurrence in config.EAST_MED_AREAS.
    in_east_med: bool | None = None
    hazard: str | None = None
    #: Published values from the paper, used by reproduce.py.
    paper_doc: float | None = None
    paper_label: Label | None = None
    #: Why reconciliation failed or needs a human, if it did.
    reconcile_note: str | None = None


class FeatureComparison(Strict):
    """One ancient detail compared against one modern flora detail."""

    comparison_id: str
    candidate_key: str
    category: str
    ancient_detail_id: str
    ancient_text: str | None = None
    modern_text: str | None = None
    comparative: bool = False
    expert_class: MatchClass | None = None
    model_class: MatchClass | None = None
    model_reason: str | None = None
    model_ancient_quote: str | None = None
    model_modern_quote: str | None = None
    cache_key: str | None = None


class CandidateScore(Strict):
    candidate_key: str
    lemma_tag: str
    dmm_id: str
    source: ScoreSource
    category_means: dict[str, float]
    positive_categories: int
    negative_categories: int
    degree_of_congruence: int
    label: Label
    rank: int
    #: Filled by stability.py.
    label_share: float | None = None
    label_distribution: dict[str, float] | None = None
    first_rank_share: float | None = None
    rank_distribution: dict[str, float] | None = None


class CompoundRecord(Strict):
    """One compound reported for one accepted WCVP taxon in LOTUS."""

    inchikey: str
    wcvp_id: str
    compound_name: str | None = None
    pathway: str | None = None
    superclass: str | None = None
    compound_class: str | None = None
    dois: tuple[str, ...] = ()


class LedgerEntry(Strict):
    lemma_tag: str
    inchikey: str
    compound_name: str | None = None
    pathway: str | None = None
    compound_class: str | None = None
    label: LedgerLabel
    #: Status of the compound for each candidate wcvp_id.
    status_by_candidate: dict[str, CandidateChemStatus]
    #: Candidates (distinct taxa) with at least config.LOTUS_MIN_RECORDS compounds.
    candidates_with_data: int
    candidates_total: int
    #: Candidates with no WCVP ID, which cannot be joined to LOTUS.
    unjoined_candidates: tuple[str, ...] = ()
    dois: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Model I/O
# ---------------------------------------------------------------------------


class ComparisonRequest(Strict):
    """What the model sees. Both texts must already be masked."""

    comparison_id: str
    category: str
    ancient_text: str
    modern_text: str


class ComparisonResponse(Strict):
    """Structured output the model must return for one comparison."""

    match_class: MatchClass
    reason: str = Field(min_length=1, max_length=2000)
    #: Verbatim span from the ancient detail that supports the class.
    ancient_quote: str | None = None
    #: Verbatim span from the modern detail that supports the class.
    modern_quote: str | None = None

    @field_validator("ancient_quote", "modern_quote")
    @classmethod
    def _blank_is_none(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            return None
        return v


class CacheEntry(Strict):
    cache_key: str
    model: str
    prompt_version: str
    prompt: str
    raw_response: str


# ---------------------------------------------------------------------------
# Evaluation split
# ---------------------------------------------------------------------------


class Split(Strict):
    seed: int
    tuning: tuple[str, ...]
    held_out: tuple[str, ...]

    @model_validator(mode="after")
    def _disjoint(self) -> "Split":
        overlap = set(self.tuning) & set(self.held_out)
        if overlap:
            raise ValueError(f"lemma tags in both partitions: {sorted(overlap)}")
        return self

    def partition_of(self, lemma_tag: str) -> Partition | None:
        if lemma_tag in self.tuning:
            return "tuning"
        if lemma_tag in self.held_out:
            return "held_out"
        return None
