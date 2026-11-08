"""Load the Lardos et al. (2024) research files into clean tables.

Inputs: the Lardos data files under data/raw/, located through the roles in
pipeline/sources.toml. The PRD names Data files 2, 3, 5, 6, 9 and 11.
Outputs (data/interim/): historical_names, dmm_plants, candidates and
feature_comparisons, all keyed on the paper's lemma tags and DMM IDs.

The column mapping can't be written until the files have been opened (build
step 1). Until then `ingest()` stops with instructions, and every later stage
runs from interim tables, which the tests and the demo build directly.

When writing the mapping:
- Key everything on lemma tags and DMM IDs, never on plant names.
- Put the paper's published DoC and label on Candidate.paper_doc / paper_label
  so reproduce.py can check them.
- Mark details Dioscorides gives only by comparison with another plant as
  BotanicalDetail.comparative / FeatureComparison.comparative.
- Leave text fields None if the licence doesn't allow holding the text.
"""

from __future__ import annotations

from .config import Paths
from .sources import Sources

#: Data files the PRD says to load. Their individual roles are confirmed when
#: the files are opened; record them in sources.toml as lardos_file_NN.
REQUIRED_FILES = (2, 3, 5, 6, 9, 11)


class IngestNotReady(RuntimeError):
    pass


def ingest(paths: Paths, sources: Sources) -> dict[str, int]:
    missing = []
    for n in REQUIRED_FILES:
        role = f"lardos_file_{n:02d}"
        path = sources.path_for(role, paths.raw)
        if path is None or not path.exists():
            missing.append(role)
    if missing:
        raise IngestNotReady(
            f"Lardos files not found: {', '.join(missing)}. Fill in their URLs in "
            f"{paths.sources} and run `python -m materia_incerta download`, or place them "
            "under data/raw/ by hand."
        )
    raise IngestNotReady(
        "The Lardos files are present but the column mapping in ingest.py hasn't been "
        "written yet (build step 1). Open the files, write the mapping, and reproduce the "
        "labels for five names before going further."
    )
