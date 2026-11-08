# Materia Incerta

Which plant does a Byzantine drug name refer to, and how far should we trust the answer?

Modern readings of plant names in old pharmacy texts lean on dictionaries and glossaries that disagree. Lardos et al. (2024) replaced that with a systematic test. They compared each botanical detail in Dioscorides' description with modern flora descriptions of every candidate species, scored the fit, and did it by hand for 50 names.

Materia Incerta automates that comparison with an LLM and adds two things the paper doesn't have:

1. **How stable is the answer?** The evidence is resampled 1,000 times to show how often each candidate keeps its rank and label.
2. **What depends on it?** Every candidate is joined to the LOTUS natural-products database. Each compound is then marked as found in all candidates, dependent on which plant is meant, or unknown.

**Example.** For *alyssos*, *Fibigia clypeata* fits Dioscorides' description strongly but has no modern medicinal uses in the sources checked. *Scutellaria galericulata* has the uses but fits weakly. Choosing by modern use would pick the worse botanical match.

Built for EthnoHack 2026, Track 1.

## Status

The pipeline, its tests and the site work end to end on synthetic data ([screenshots](docs/screenshots/)). The project hasn't been run on real data yet: the Lardos files still need to be downloaded and mapped, and no LLM provider has been chosen. Open decisions are in [docs/open-questions.md](docs/open-questions.md).

## Quick start

Requires Python 3.11+ and Node 20.9+.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e "pipeline[dev]"
npm --prefix client install

pytest pipeline/tests                  # run the tests
python -m materia_incerta demo         # run the whole pipeline on synthetic data
npm --prefix client run dev            # view the site at http://localhost:3000
```

The demo writes into the site's data folder. Run `python -m materia_incerta export` afterwards so it isn't committed.

With the real data in place:

```bash
python -m materia_incerta download     # fetch the files listed in pipeline/sources.toml
python -m materia_incerta run --all    # rebuild every result from cached model answers
```

## How it works

- **Check against the paper first.** Before any model runs, the pipeline recomputes the paper's labels from its own expert scores, and stops if they don't match.
- **Score the way the paper does.** Good is +2, partial +1, no match −2 and absent 0, averaged within each feature category. Matching categories minus conflicting ones gives Strong (5 or more), Moderate (3 to 4) or Weak.
- **Hide the names.** Before the model sees a text, every Greek, Latin and common name for the plant and its candidates becomes `[PLANT]`. This includes spelling variants such as *khamaimelon* and *Chamaemelum*. A prompt with a name left in is refused.
- **No quote, no match.** The model must quote both texts to claim a match, or the answer counts as absent.
- **Rebuild from cache.** Every model answer is cached, so one command reproduces every number offline, byte for byte.

Each stage is one module in [`pipeline/src/materia_incerta/`](pipeline/src/materia_incerta/). The site is a static Next.js export in [`client/`](client/) that only reads the JSON the pipeline writes.

## Evaluation

Prompts are tuned on 10 names and judged on the other 40, against the paper's 1,213 expert comparisons. We report:

- agreement on single details, labels and rankings, each against a naive baseline
- how often the model claims a match the experts marked absent
- a memorisation test, comparing agreement with names hidden and shown

No one knows for certain which plants these are, so all of this measures agreement with the experts, not correctness.

## Limitations

- Only the candidates suggested in the literature are compared. The true plant may not be among them.
- A compound missing from LOTUS may be unstudied rather than absent.
- Compound results are untested hypotheses, not evidence of any effect or of safety.
- The results support expert judgment; they don't replace it.

## Data

| Source | Used for | Licence |
| --- | --- | --- |
| Lardos et al. (2024) research data | Names, descriptions, candidates, expert scores | Paper CC BY 4.0; data licence unconfirmed |
| World Checklist of Vascular Plants (WCVP) | Accepted names, synonyms, native range | CC BY 3.0 for v10; confirm for the version used |
| LOTUS | Compounds reported per species | Confirm on the Zenodo record |

The Dioscorides translation and the regional floras arrive inside the Lardos files. Their text stays off the site until their licences are confirmed. Downloaded and intermediate data are never committed. Versions and checksums are pinned in [`pipeline/sources.toml`](pipeline/sources.toml).

## References

- Lardos A. et al. (2024). A systematic methodology to assess the identity of plants in historical texts: A case study based on the Byzantine pharmacy text John the Physician's Therapeutics. *Journal of Ethnopharmacology* 322: 117622. [doi:10.1016/j.jep.2023.117622](https://doi.org/10.1016/j.jep.2023.117622)
- Govaerts R. et al. (2021). The World Checklist of Vascular Plants, a continuously updated resource for exploring global plant diversity. *Scientific Data* 8: 215. [doi:10.1038/s41597-021-00997-6](https://doi.org/10.1038/s41597-021-00997-6)
- Rutz A. et al. (2022). The LOTUS initiative for open knowledge management in natural products research. *eLife* 11: e70780. [doi:10.7554/eLife.70780](https://doi.org/10.7554/eLife.70780)

## Contributing

Read [PRD.md](PRD.md) for the spec and [AGENTS.md](AGENTS.md) for the working rules.

## Team

To be added.
