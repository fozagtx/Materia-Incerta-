# Materia Incerta PRD

Nov 8, 2026 · kaizen V2

## What this is

Materia Incerta shows how confident we can be about which plant a Byzantine drug name refers to, then shows which compounds depend on that answer.

**Problem.** Modern readings of ancient plant names often rest on dictionaries and glossaries that disagree or contain errors. Lardos et al. (2024) built a more systematic method, but its feature-by-feature comparison was done by hand.

### What is new

- **Automated comparison.** An LLM scores each ancient botanical detail against each modern flora description, with plant names hidden.
- **Measured stability.** The paper sorts candidates into Strong, Moderate or Weak. We show how often that label holds when the evidence is resampled.
- **Uncertainty carried into chemistry.** Each compound is marked as holding across candidates, depending on one identification, or unknown.

**Demo moment.** For the name *alyssos*, *Fibigia clypeata* fits the ancient description strongly but has no modern medicinal uses in the sources checked. *Scutellaria galericulata* has the modern uses but fits the description weakly. Picking by modern use would favour the worse botanical match.

## Target user and fit

The user is an ethnopharmacology researcher deciding which historical plants deserve lab work. Target prizes are Track 1, Best Scientific Rigor and Best AI Solution, plus Best Student Team if every member is a student.

| Judging criterion | How the project answers it |
| --- | --- |
| Scientific relevance | Plant identity is a stated, unresolved problem in historical ethnopharmacology |
| Innovation | Identification doubt is carried through to compound-level conclusions |
| Technical implementation | One command reproduces every score from cached model outputs |
| Data science quality | Benchmarked against 1,213 published expert comparisons, with a memorisation test |
| Feasibility | The method runs on any text that has plant descriptions and candidate species |
| Impact | Lab effort goes to hypotheses that survive identification doubt |
| Presentation | One clear case, *alyssos*, carries the pitch and demo |

## Core flow

A user picks a historical plant name and gets a ranked, uncertainty-aware identity card.

**Input:** one of the 50 benchmark names from John the Physician's *Therapeutics*.

**Process**

1. Load the linked Dioscorides description and the candidate species suggested in the literature.
2. Hide all plant names, then score each botanical detail as good, partial, no match or absent.
3. Combine those scores with the paper's formula to get Strong, Moderate or Weak.
4. Resample the feature categories to measure how stable each label and ranking is.
5. Join candidates to LOTUS and label each compound by how much it depends on the identification.

**Output:** candidate ranking, stability, the evidence behind each score, and a compound ledger. Every compound is presented as a hypothesis.

## MVP features

The MVP covers all 50 names in the pipeline and polishes three cases for the demo: *alyssos*, *khamaimelon* and *aristolokhia*.

| Feature | What it does | Priority |
| --- | --- | --- |
| Evidence matrix | Shows each ancient detail, the modern detail, the match class and the model's reason | Must |
| Name-masked scoring | Removes Greek, Latin and common names before scoring | Must |
| Candidate ranking | Applies the paper's scoring and thresholds | Must |
| Stability view | Shows how often each candidate keeps its label and rank under resampling | Must |
| Compound ledger | Labels compounds as robust, ID-dependent or no data | Must |
| Benchmark page | Publishes agreement, baselines and failures | Must |
| Range check | Flags candidates absent from the Eastern Mediterranean in WCVP | Should |
| Toxicity label | Marks known hazardous plants on their cards | Should |

## Screens

Three pages are enough, with no login.

| Page | Purpose | Key elements |
| --- | --- | --- |
| Name index | Choose a plant name | Greek name, transliteration, candidate count, stability badge, search |
| Plant case | Show the full result for one name | Ancient description, ranked candidates, stability bars, evidence matrix, compound ledger, hypothesis banner |
| Benchmark and limits | Let judges check the claims | Agreement tables, baselines, memorisation test, known failures, data licences |

## Data sources

The Lardos research data is the foundation, because it already links names, descriptions, candidates and expert scores. Its licence is the first thing to confirm.

| Source | Used for | Access | Licence or status |
| --- | --- | --- | --- |
| Lardos research data | 11 files, including names, descriptions, candidates and expert scores | File directory confirmed; individual files not yet opened | Paper is CC BY; data licence unconfirmed |
| LOTUS frozen export | Compounds per species, with InChIKey, DOI and compound classes | Open CSV on Zenodo, April 2026 | Confirm on the record |
| WCVP | Accepted names, synonyms, native range | Free full download | CC BY 3.0 on the v10 deposit; confirm for the version used |
| Kew MPNS | Manual name checks only | Portal search | No bulk access confirmed |
| Beck translation and regional floras | Reach us only through the Lardos files | Inside the research data | Assume copyrighted; do not republish without permission |

**Excluded:** the Osbaldeston version of Dioscorides. Its notice requires publisher permission for excerpts, and it is a modern reworking of Goodyer's paraphrase rather than a new translation from the Greek.

If republishing is not allowed, the public repo ships IDs, scores, code and a download script, not the source text.

## How it is built

No backend: a Python pipeline computes everything ahead of time and a static site reads the results. The app has no accounts, stored user data or secrets, so nothing can fail live in front of a judge.

**Stack:** Python with pandas and Pydantic, an LLM with structured output, then Next.js, Tailwind and shadcn/ui as a static export on Vercel. Swap any of these for what the team builds fastest with.

1. **Ingest.** Load data files 2, 3, 5, 6, 9 and 11 into clean tables keyed on the paper's lemma tags.
2. **Reconcile.** Map the 130 accepted species to WCVP IDs and synonyms from one fixed snapshot.
3. **Reproduce.** Recompute the paper's labels from its own expert scores before any AI runs.
4. **Mask.** Strip Greek, Latin, genus, species and common names from both sides.
5. **Score.** For each ancient and modern detail, return good (2), partial (1), no match (-2) or absent (0), with a reason. Cache every response.
6. **Aggregate.** Average within the paper's 13 feature categories, compute positive minus negative, and apply Strong at 5 or above, Moderate at 3 to 4, Weak at 2 or below.
7. **Stability.** Resample the feature categories 1,000 times and record each candidate's label share and first-rank share.
8. **Chemistry.** Join to LOTUS through WCVP synonyms and build the compound ledger.
9. **Evaluate and export.** Write the benchmark tables and the JSON the site reads.

### Compound labels

- **Robust:** reported for every candidate that has enough LOTUS records.
- **ID-dependent:** reported for some candidates but not others.
- **No data:** a candidate has fewer than 5 LOTUS records. Missing records do not mean a compound is absent. The cutoff of 5 is a starting value to tune.

First-rank share is not the probability that an identification is correct. The interface must not describe it that way.

## Data model

Six tables, all exported as JSON. Stable IDs replace plant names as join keys, as the paper recommends.

| Table | Key fields |
| --- | --- |
| historical_name | lemma_tag, Greek name, transliteration, linked Dioscorides plants |
| dmm_plant | dmm_id, chapter, type, detail level, botanical details |
| candidate | lemma_tag, dmm_id, wcvp_id, accepted name, synonyms, range flag |
| feature_comparison | candidate_key, feature category, detail, expert class, model class, model reason, cache key |
| candidate_score | candidate_key, expert label, model label, label shares, first-rank share |
| compound_record | inchikey, wcvp_id, compound class, DOI, ledger label |

## Evaluation plan

No ground truth exists for these identifications, so every result is reported as agreement with published expert scoring, never as accuracy about the true plant. Tune prompts on 10 names, then report on the other 40, splitting by historical name.

| Test | Measure | Compare against | Proposed bar |
| --- | --- | --- | --- |
| Detail matching | Weighted Cohen's kappa across the 1,213 expert comparisons | Always predicting "good" (36% of items) | Kappa of 0.6 or above |
| Invented evidence | How often the model claims a match on the 405 items experts marked absent | Expert "absent" labels | Below 10% |
| Candidate labels | Exact and within-one-level agreement on 141 candidate records | Always predicting "Moderate" (36%) | Clearly above baseline |
| Ranking | Top-candidate agreement on the 35 Dioscorides plants with several candidates | Random order | Clearly above baseline |
| Memorisation | Masked versus unmasked agreement | Masked run | Report the gap |
| Stability | Share of names whose top candidate holds in at least 80% of resamples | None, this is descriptive | Report it |

Bars are proposals to fix before the held-out run. Also review 20 disagreements by hand and publish the error types.

## Domain and responsible-research constraints

The tool ranks hypotheses about historical identity and gives no medical guidance.

- **Hypotheses only.** Every compound result carries a banner saying it is computational and unvalidated.
- **No dosing or use advice.** The benchmark includes hazardous genera such as *Aristolochia*, *Conium*, *Hyoscyamus* and *Nerium*.
- **Botanical evidence only in the MVP.** The paper treats medicinal-use comparison as much less robust, so the score ignores it.
- **Comparative descriptions are flagged.** Dioscorides often describes a plant by likening it to another, which gives no direct feature. These details get a visible warning.
- **Limited candidate pool.** We inherit the suggested candidates, and the true plant may not be among them. 21 of the 130 taxa are missing from the two regional floras.
- **Credit and consent.** Cite every dataset and historical source. Do not extract or republish modern community knowledge from the ethnobotanical sources.
- **Expert authority.** The output supports philologists and botanists and does not replace them.

## Success criteria

The project is done when a judge can check every claim from the deployed site and the repo.

- [ ] The pipeline reproduces the paper's labels from its expert scores
- [ ] All 50 names have results, including stability and a compound ledger
- [ ] The benchmark page reports held-out results and failures
- [ ] The memorisation test is published
- [ ] Three polished cases work on the deployed site
- [ ] One command rebuilds all results from the cached model outputs
- [ ] Every dataset's source and licence is listed in the README

## What this is not

This is not a plant identification app, a drug discovery engine or a clinical tool.

## Save for later

- **Open candidate search.** Compare descriptions against every species in a genus or region. A good first test is whether it surfaces *Equisetum palustre*, *Agrimonia repens* and *Hyoscyamus reticulatus*, which the authors flagged as possible missed matches.
- Target prediction for compounds that hold across candidates.
- Other texts and languages, including Arabic and Latin.
- Manuscript illustrations as a second evidence source.

## Risks and fallback

The stability and chemistry layers can run on the published expert scores alone, so a weak LLM result does not end the project.

| Risk | Effect | Response |
| --- | --- | --- |
| Research files cannot be downloaded | No benchmark or description data | Email the corresponding author; if still blocked, switch to Same Name, Different Plant |
| Licence blocks republishing | Repo cannot include source text | Ship IDs, scores, code and a download script |
| LLM agrees poorly with experts | Automation claim fails | Publish the result and lead with stability and chemistry on the expert scores |
| Model recognises plants despite masking | Scores are inflated | Report the masked-versus-unmasked gap and use masked scores only |
| Model invents details | False matches | Require a supporting quote or return absent; publish the rate |
| LOTUS is sparse for little-studied plants | False impression of absence | Use the no-data label instead of inferring absence |
| Species names do not join | Candidates lose their chemistry | Match through WCVP synonyms and review misses by hand |
| Results read as medical claims | Breaks the hackathon rules | Keep the banner on every compound view and in the pitch |

## Build order and team roles

Build the version that works without AI first, so there is a complete demo before any LLM risk.

1. **Spike.** Download the 11 files, check licences, and reproduce the labels for five names. Stop and reassess if this fails.
2. **Data spine.** Build the tables and WCVP mapping.
3. **Walking skeleton.** Run stability and chemistry on the expert scores and show *alyssos* on the site.
4. **LLM scoring.** Tune masking and prompts on 10 names.
5. **Full run.** Score the other 40 names and generate the benchmark.
6. **Polish.** Finish the three demo cases and the limits page.
7. **Package.** Write the README, slides and pitch video.

| Role | Owns | Team of two |
| --- | --- | --- |
| Data lead | Ingest, WCVP, LOTUS, stability | Person A |
| AI and evaluation | Masking, scoring, benchmark | Person A |
| Frontend | Static site and demo cases | Person B |
| Domain and pitch | Reviewing errors, limits, slides, video | Person B |

## Submission checklist

Each item below is required by the EthnoHack rules.

- [ ] Devpost page: title, track, description, problem, approach, technologies, data sources, results, team, impact and future work
- [ ] Public GitHub repo: code, processing scripts, install steps, README, dataset references and licences, reproduction steps
- [ ] Pitch video, 10 minutes at most: problem, motivation, approach, technology, data, results, demo, impact, future work
- [ ] Slide deck, 10 slides at most: Problem, Data, Method, Prototype, Results, Impact
- [ ] Assumptions, limitations, uncertainty and data-quality issues stated clearly
- [ ] Team of 2 to 5 members listed

## Sources

The paper was read through its first 100,000 of 131,633 characters, covering its methods, results and most of its discussion. The research files themselves have not been opened yet.

- Lardos et al., plant identity in historical texts
- Lardos research data directory
- LOTUS frozen dataset on Zenodo
- The LOTUS initiative, eLife
- World Checklist of Vascular Plants paper
- WCVP v10 deposit
- Kew Medicinal Plant Names Services
- Osbaldeston bibliographic entry
- The Hackathon Playbook: Execution
- The Hackathon Playbook: Domain to Spec
