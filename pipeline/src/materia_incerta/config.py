"""Constants and paths shared by every pipeline stage.

Anything listed under "Ask before" in AGENTS.md lives here, so a change to it
shows up as a one-line diff that a reviewer can't miss.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Scoring (Lardos et al. 2024). Changing any of these needs team sign-off.
# ---------------------------------------------------------------------------

MATCH_SCORES: dict[str, int] = {
    "good": 2,
    "partial": 1,
    "no_match": -2,
    "absent": 0,
}

#: The paper groups botanical details into 13 feature categories. The category
#: identifiers come from the data (Data file 11), not from this module.
N_FEATURE_CATEGORIES = 13

#: Label thresholds on the degree of congruence (DoC).
#: Strong: DoC >= 5. Moderate: 3 <= DoC <= 4. Weak: DoC < 3.
#: Values strictly between 4 and 5 are unresolved (see docs/open-questions.md)
#: and raise instead of being guessed.
STRONG_MIN = 5
MODERATE_MIN = 3
MODERATE_MAX = 4

#: Ordered from weakest to strongest, used for "within one level" agreement.
LABEL_ORDER: tuple[str, ...] = ("Weak", "Moderate", "Strong")

# ---------------------------------------------------------------------------
# Stability
# ---------------------------------------------------------------------------

N_RESAMPLES = 1000
RANDOM_SEED = 20240301
#: A group's top candidate counts as stable at this first-rank share or above.
STABLE_TOP_SHARE = 0.8

# ---------------------------------------------------------------------------
# Chemistry
# ---------------------------------------------------------------------------

#: A candidate with fewer distinct LOTUS compounds than this is "no data".
#: The PRD calls 5 a starting value to tune.
LOTUS_MIN_RECORDS = 5

# ---------------------------------------------------------------------------
# Range check (Should). TDWG WGSRPD level-3 codes treated as the Eastern
# Mediterranean. Provisional: the domain lead should confirm this set.
# ---------------------------------------------------------------------------

EAST_MED_AREAS: frozenset[str] = frozenset(
    {
        "GRC",  # Greece
        "KRI",  # Kriti
        "EAI",  # East Aegean Is.
        "TUE",  # Turkey-in-Europe
        "TUR",  # Turkey
        "CYP",  # Cyprus
        "LBS",  # Lebanon-Syria
        "PAL",  # Palestine
        "SIN",  # Sinai
        "EGY",  # Egypt
    }
)

# ---------------------------------------------------------------------------
# Hazard labels (Should, but AGENTS.md requires them to stay visible).
# Keyed by accepted genus from WCVP. Wording is descriptive only: no dosing,
# preparation or treatment advice.
# ---------------------------------------------------------------------------

HAZARDOUS_GENERA: dict[str, str] = {
    "Aristolochia": "Toxic. Contains aristolochic acids, which are nephrotoxic and carcinogenic.",
    "Conium": "Highly toxic. Contains piperidine alkaloids such as coniine.",
    "Hyoscyamus": "Highly toxic. Contains tropane alkaloids.",
    "Nerium": "Highly toxic. Contains cardiac glycosides.",
}

# ---------------------------------------------------------------------------
# Publishing. Source text (Beck translation, regional floras) and any model
# reason quoting it stay out of the site export until licences are confirmed.
# ---------------------------------------------------------------------------

REPUBLISH_SOURCE_TEXT = False

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Paths:
    """Every location a run reads or writes. Tests point this at a temp dir."""

    root: Path = REPO_ROOT
    raw: Path = field(default=REPO_ROOT / "data" / "raw")
    interim: Path = field(default=REPO_ROOT / "data" / "interim")
    cache: Path = field(default=REPO_ROOT / "data" / "cache" / "llm")
    site_data: Path = field(default=REPO_ROOT / "client" / "public" / "data")
    sources: Path = field(default=REPO_ROOT / "pipeline" / "sources.toml")
    split: Path = field(default=REPO_ROOT / "pipeline" / "config" / "split.json")
    run_log: Path = field(default=REPO_ROOT / "pipeline" / "config" / "runs.jsonl")
    #: Which model and prompt version the cached responses belong to.
    scoring: Path = field(default=REPO_ROOT / "pipeline" / "config" / "scoring.json")
    #: candidate_key -> WCVP plant_name_id for names matched by hand.
    manual_wcvp: Path = field(default=REPO_ROOT / "pipeline" / "config" / "manual_wcvp.json")

    @classmethod
    def under(cls, root: Path) -> "Paths":
        """Lay out the standard tree under another root (used by tests)."""
        return cls(
            root=root,
            raw=root / "data" / "raw",
            interim=root / "data" / "interim",
            cache=root / "data" / "cache" / "llm",
            site_data=root / "client" / "public" / "data",
            sources=root / "pipeline" / "sources.toml",
            split=root / "pipeline" / "config" / "split.json",
            run_log=root / "pipeline" / "config" / "runs.jsonl",
            scoring=root / "pipeline" / "config" / "scoring.json",
            manual_wcvp=root / "pipeline" / "config" / "manual_wcvp.json",
        )
