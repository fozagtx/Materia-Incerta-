# Open questions

Decisions the code deliberately does not make on its own. Each one names where the answer goes once it is settled. Items marked **Ask before** in `AGENTS.md` need team sign-off.

## Q1. DoC values between 4 and 5 (needs Data file 11)

`AGENTS.md` sets Strong at 5 or above, Moderate at 3 to 4 and Weak below 3. The PRD says Weak at 2 or below. The two agree for integers.

Degree of congruence as described (positive categories minus negative categories) is always an integer, so the range between 4 and 5 can only be reached if the paper computes it some other way.

- `aggregate.label_for` raises `ThresholdGapError` for any value strictly between 4 and 5 rather than guessing.
- `reproduce.py` lists every published DoC in that range (`gap_values`), and the benchmark page reports the count.

**To settle:** open Data file 11, check whether any published DoC is non-integer, and record what the paper does with it. Then change `config.py` (Ask before) and update this note.

## Q2. Lardos file layout (build step 1)

`ingest.py` stops with `IngestNotReady` until the column mapping is written. The PRD names Data files 2, 3, 5, 6, 9 and 11, but which file holds which table is unconfirmed.

**To settle:** fill in the URLs in `pipeline/sources.toml`, download, open the files, and write the mapping. Then reproduce the labels for five names.

## Q3. The 13 feature categories

The category IDs come from the data, not the code. `run.feature_categories` fails if the comparisons table does not contain exactly 13. Categories with no comparison for a candidate count as neutral.

## Q4. Stability details

These choices are implemented and documented in `stability.py`. Confirm them before the held-out run.

- Each resample draws 13 categories with replacement, shared across every candidate of a Dioscorides plant and across expert and model scores, so the comparisons are paired.
- When candidates tie at the top, first-rank credit is split equally, so first-rank shares in a group sum to 1.
- The "top candidate holds" metric counts a group as stable only if there is a unique top candidate whose first-rank share is at least 0.8. Ties at the top count as not stable. The unit is a Dioscorides plant with several candidates. The PRD says "names", and a name can link to several Dioscorides plants.

## Q5. Compound ledger edge cases

`chemistry.py` follows the PRD definitions:

- **No data** is counted as distinct InChIKeys per accepted WCVP taxon, below `LOTUS_MIN_RECORDS` (5, a starting value to tune).
- **Robust** ignores candidates with no data. A compound can be robust when only one of three candidates has enough records. The ledger shows `candidates_with_data` and per-candidate status so this stays visible.

**To decide:** should robust require at least two candidates with data?

## Q6. Weighted kappa weights

`evaluate.py` uses linear weights on the rank of the ordered classes (no match, absent, partial, good), not on the score values. Unweighted kappa and exact agreement are reported alongside. Fix this before the held-out run (Ask before).

## Q7. Eastern Mediterranean areas

`config.EAST_MED_AREAS` is a provisional set of WGSRPD level-3 codes for the range check: GRC, KRI, EAI, TUE, TUR, CYP, LBS, PAL, SIN, EGY. The domain lead should confirm it.

## Q8. Hazard list

`config.HAZARDOUS_GENERA` covers the four genera named in `AGENTS.md`. The domain lead should review the 130 candidate taxa for others once the data is in.

## Q9. LLM provider

`score.client_from_env` raises `NotImplementedError` until a provider is chosen. Any adapter needs only `model` and `complete_json(prompt, schema) -> str`. The prompt in `score.PROMPT_TEMPLATE` is a draft (`PROMPT_VERSION = "draft-0"`) for tuning on the 10 tuning names.

## Q10. Network access in cloud sessions

The cloud session that scaffolded this repo could not reach the paper, Zenodo or Kew hosts. Downloads need to run locally, or in an environment whose network allows those hosts.
