# Materia Incerta

How confident can we be about which plant a Byzantine drug name refers to, and which compounds depend on that answer?

Materia Incerta takes plant names from John the Physician's *Therapeutics* and the candidate species suggested for them in the literature. For each name it produces:

- **Candidate ranking:** each ancient botanical detail from Dioscorides is compared with each candidate's modern flora description, and the paper's formula turns the matches into Strong, Moderate or Weak.
- **Stability:** feature categories are resampled 1,000 times to show how often each label and ranking holds.
- **Compound ledger:** LOTUS compounds are labelled robust (reported for every candidate with data), ID-dependent, or no data.

An LLM does the feature comparison with plant names masked. Its scores are benchmarked against the 1,213 published expert comparisons of Lardos et al. (2024).

EthnoHack 2026, Track 1. See [`PRD.md`](PRD.md) for the product spec and [`AGENTS.md`](AGENTS.md) for the rules every contributor follows.

> **Status:** scaffold. The pipeline, tests and site run end to end on synthetic data. The Lardos files have not been downloaded or mapped yet (build step 1), so the deployed site has no results. Open decisions are in [`docs/open-questions.md`](docs/open-questions.md).

## What this is not

This is not a plant identification app, a drug discovery engine or a clinical tool.

Every compound result is a computational, unvalidated hypothesis. Nothing here is dosing, preparation or treatment advice.

No ground truth exists for these identifications, so results are reported as agreement with published expert scoring, never as accuracy.

## Repo layout

```text
pipeline/      Python pipeline (src/materia_incerta), tests, sources.toml
client/        Next.js static site; reads only client/public/data/
data/          raw/ and interim/ are never committed; cache/llm/ holds model responses
docs/          open questions
```

Pipeline stages, in order, one module each: `ingest`, `reconcile`, `reproduce`, `score`, `aggregate`, `stability`, `chemistry`, `evaluate`, `export`.

## Setup

Requires Python 3.11+ and Node 20.9+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e "pipeline[dev]"
npm --prefix client install
```

## Commands

```bash
python -m materia_incerta download        # fetch files listed in pipeline/sources.toml
python -m materia_incerta run --all       # offline rebuild from the response cache
pytest pipeline/tests                     # pipeline tests
npm --prefix client run dev               # local site
npm --prefix client run build             # static export to client/out/
```

Other commands:

| Command | What it does |
| --- | --- |
| `python -m materia_incerta run --stage <name>` | Run selected stages |
| `python -m materia_incerta split` | Assign the 10 tuning and 40 held-out names once. Refuses to overwrite. Commit the file. |
| `python -m materia_incerta score --names a,b` | Live LLM scoring into the cache, tuning names only. Needs `LLM_API_KEY` and `LLM_MODEL`, and a provider adapter. |
| `python -m materia_incerta score --held-out-run --reason "..." --confirm-full-run` | The held-out run, logged to `pipeline/config/runs.jsonl` |
| `python -m materia_incerta demo` | Export synthetic data to the site, with a red banner, for frontend work |
| `python -m materia_incerta export` | Rewrite site JSON from interim tables. Run this after `demo` to restore the real export before committing. |

`run --all` never calls a model. Model scores come only from `data/cache/llm/`, keyed on the model, the prompt version and the exact masked prompt. A missing response leaves that comparison unscored, or fails under `--strict-cache`.

## Method

The scoring follows Lardos et al. (2024), and `reproduce.py` checks it against the paper's own labels before any model work.

| Match class | Score |
| --- | --- |
| Good | 2 |
| Partial | 1 |
| No match | -2 |
| Absent | 0 |

1. Scores are averaged within each of the 13 feature categories.
2. Degree of congruence = categories with a positive mean minus categories with a negative mean.
3. Strong at 5 or above, Moderate at 3 to 4, Weak below 3. Values between 4 and 5 are unresolved and raise an error ([Q1](docs/open-questions.md)).
4. Botanical evidence only. Medicinal-use data is not in the score.

Model comparisons see texts with every Greek, Latin, genus, species, synonym and common name for the plant and all its candidates replaced by `[PLANT]`. Matching ignores case and diacritics and covers transliteration variants such as *khamaimelon* and *Chamaemelum*. A prompt that still holds a name is refused.

A model match must quote both texts verbatim, or it is recorded as absent.

## Evaluation

Prompts are tuned on 10 names, and results are reported on the other 40, split by historical name. The site's benchmark page shows, per partition:

- Detail matching: weighted Cohen's kappa against always predicting "good"
- Invented evidence: matches claimed on items experts marked absent
- Candidate labels: exact and within-one-level agreement against always predicting "Moderate"
- Top-candidate agreement against random order
- Memorisation: masked against unmasked agreement
- Stability: share of plants whose top candidate holds in at least 80% of resamples
- Known failures

## Data sources and licences

| Source | Used for | Licence | Republished here |
| --- | --- | --- | --- |
| Lardos A. et al. (2024). A systematic methodology to assess the identity of plants in historical texts: A case study based on the Byzantine pharmacy text John the Physician's Therapeutics. *Journal of Ethnopharmacology* 322: 117622. [doi:10.1016/j.jep.2023.117622](https://doi.org/10.1016/j.jep.2023.117622) | Names, Dioscorides descriptions, candidates, expert scores | Paper CC BY 4.0. Data licence **unconfirmed**. | IDs and scores only, until confirmed |
| Govaerts R. et al. (2021). The World Checklist of Vascular Plants. *Scientific Data* 8: 215. [doi:10.1038/s41597-021-00997-6](https://doi.org/10.1038/s41597-021-00997-6) | Accepted names, synonyms, native range | CC BY 3.0 on the v10 deposit; confirm for the version used | IDs and derived flags |
| Rutz A. et al. (2022). The LOTUS initiative for open knowledge management in natural products research. *eLife* 11: e70780. [doi:10.7554/eLife.70780](https://doi.org/10.7554/eLife.70780) | Compounds per species (InChIKey, DOI, class) | Confirm on the Zenodo record | Pending confirmation |
| Beck's translation of Dioscorides, *De materia medica*, and two regional floras | Reach this project only through the Lardos files | Assumed copyrighted | No. Text is withheld from the site (`REPUBLISH_SOURCE_TEXT = False`). |
| Kew Medicinal Plant Names Services | Manual name checks only | No bulk access | No |

- The Osbaldeston version of Dioscorides is not used.
- Modern community knowledge from ethnobotanical sources is not extracted or republished.
- Versions, URLs and checksums are pinned in [`pipeline/sources.toml`](pipeline/sources.toml) and recorded in `client/public/data/manifest.json`.
- Nothing under `data/raw/` or `data/interim/` is committed.
- Cached model responses may quote copyrighted text, so they are committed only once the licences allow.

## Limits

- The true plant may be outside the suggested candidate list. 21 of the 130 taxa are missing from the two regional floras.
- Details that Dioscorides gives only by comparison with another plant are flagged; they give no direct feature.
- First-rank share measures sensitivity to which features are counted. It is not the probability that an identification is correct.
- A compound missing from LOTUS is not absent from the plant.
- The output supports philologists and botanists. It does not replace them.

## Team

To be listed (2 to 5 members).
