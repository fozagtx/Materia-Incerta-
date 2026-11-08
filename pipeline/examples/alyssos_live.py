"""Live check on real texts: Dioscorides' alyssos against two candidate species.

Runs the real pipeline pieces (name masking, prompt, Nebius model, evidence
rule, response cache) on public-domain and copyright-free sources:

- Ancient: Dioscorides, De materia medica 3.91, Greek text of Wellmann's
  edition (Berlin, 1906, vol. 2), public domain. Taken from the Internet
  Archive OCR (pedaniidioscuri01pedagoog); only OCR letter errors are
  corrected (e.g. χ read for κ), no words changed.
- Modern: Flora Europaea (Tutin et al.) genus and species treatments for
  Fibigia clypeata (vol. 1, 1964, pp. 304-305) and Scutellaria galericulata
  (vol. 3, 1972, pp. 135-136), via Plazi TreatmentBank ("No known copyright
  restrictions apply"). Names, authorities and chromosome counts are removed
  so the model sees only the description; OCR slips are fixed.

This is a demonstration on five details, not the paper's 13-category
scoring, and there are no expert scores for it. It does not replace the
benchmark on the Lardos data.

Run (needs LLM_API_KEY and LLM_MODEL):
    python pipeline/examples/alyssos_live.py out.json
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from materia_incerta.mask import NameLexicon, assert_masked, mask
from materia_incerta.schemas import ComparisonRequest
from materia_incerta.score import (
    PROMPT_VERSION,
    ResponseCache,
    build_prompt,
    cache_key,
    client_from_env,
    parse_response,
    response_schema,
)
from materia_incerta.schemas import CacheEntry

DIOSCORIDES_3_91 = (
    "ἄλυσσον φρυγάνιόν ἐστιν ὑπότραχυ, μονόκαυλον, φύλλα ἔχον στρογγύλα, "
    "παρ᾽ οἷς ὁ καρπὸς ὡς ἀσπιδίσκια διπλᾶ, ἐν οἷς τὸ σπέρμα ὑπόπλατυ· "
    "φύεται ἐν ὀρεινοῖς καὶ τραχέσι χωρίοις."
)

#: (category, Greek clause, plain English gloss for display only)
ANCIENT_DETAILS = [
    ("habit", "φρυγάνιόν ἐστιν ὑπότραχυ, μονόκαυλον", "a small, somewhat rough shrub with a single stem"),
    ("leaves", "φύλλα ἔχον στρογγύλα", "round leaves"),
    ("fruit", "παρ᾽ οἷς ὁ καρπὸς ὡς ἀσπιδίσκια διπλᾶ", "fruit like little double shields"),
    ("seed", "ἐν οἷς τὸ σπέρμα ὑπόπλατυ", "a flattish seed inside"),
    ("habitat", "φύεται ἐν ὀρεινοῖς καὶ τραχέσι χωρίοις", "grows in mountainous, rough places"),
]

CANDIDATES = {
    "Fibigia clypeata": (
        "Perennial herbs; hairs stellate, rarely mixed with some unbranched hairs. Sepals erect, the inner "
        "saccate or not saccate at base; petals yellow, shortly clawed. Fruit a strongly compressed "
        "latiseptate silicula; valves flat, not veined; style long; stigma more or less capitate. Seeds 2-8 "
        "in each loculus, winged. Stems 30-75 cm. Lower leaves oblong or oblanceolate, usually green or "
        "grey-green, with lanate indumentum. Fruiting racemes 10-20 cm; pedicels 2-5 mm. Sepals 4.5-7.0 mm; "
        "petals 8-13 mm. Silicula 14-28 x 9-13 mm, elliptical. Italy; Balkan peninsula southwards to "
        "N.E. Greece; Krym."
    ),
    "Scutellaria galericulata": (
        "Rhizomatous perennials. Flowers in pairs, remote or in a dense oblong raceme. Calyx 2-lipped, the "
        "tube campanulate, with an erect dorsal scale; lips entire, closed in fruit. Corolla 2-lipped; tube "
        "long and more or less curved upwards from the base, glabrous inside. Stamens parallel. Stems 7-70 cm, "
        "more or less erect, simple or branched. Leaves 1-5(-7) x 0.3-2 cm, ovate-elliptical to "
        "oblong-lanceolate, weakly crenate-serrate, more or less cordate at base, acute, glabrous to "
        "pubescent. Flowers in remote axillary pairs. Bracts like the leaves, usually exceeding the flowers, "
        "though smaller above. Calyx glabrous or eglandular-pubescent. Corolla 10-18 mm, violet-blue, rarely "
        "pink, whitish towards base of tube; tube curved through c. 45°. Damp places. Almost throughout "
        "Europe, except for some islands."
    ),
}

LEXICON = NameLexicon.from_terms(
    [
        "ἄλυσσον", "alyssos", "alysson", "Alyssum",
        "Fibigia clypeata", "Farsetia clypeata", "Alyssum clypeatum", "buckler mustard",
        "Scutellaria galericulata", "skullcap", "helmet flower",
    ]
)


def main(out_path: str) -> None:
    client = client_from_env()
    cache = ResponseCache(Path("data/cache/llm"))
    masked_sentence = mask(DIOSCORIDES_3_91, LEXICON)
    assert_masked(masked_sentence, LEXICON)
    results = []
    started = time.time()
    calls = 0
    for cand, modern in CANDIDATES.items():
        modern_masked = mask(modern, LEXICON)
        for category, greek, gloss in ANCIENT_DETAILS:
            req = ComparisonRequest(
                comparison_id=f"alyssos|{cand}|{category}",
                category=category,
                ancient_text=mask(greek, LEXICON),
                modern_text=modern_masked,
            )
            prompt = build_prompt(req, LEXICON)  # refuses if any name is left
            key = cache_key(client.model, prompt)
            entry = cache.get(key)
            if entry is None:
                raw = client.complete_json(prompt, response_schema())
                calls += 1
                entry = CacheEntry(cache_key=key, model=client.model, prompt_version=PROMPT_VERSION, prompt=prompt, raw_response=raw)
                cache.put(entry)
            resp = parse_response(entry.raw_response, req)
            results.append(
                {
                    "candidate": cand,
                    "category": category,
                    "ancient_greek": greek,
                    "ancient_gloss": gloss,
                    "match_class": resp.match_class,
                    "reason": resp.reason,
                    "ancient_quote": resp.ancient_quote,
                    "modern_quote": resp.modern_quote,
                    "cache_key": key,
                }
            )
            print(f"{cand:<26} {category:<8} {resp.match_class:<9} {resp.modern_quote or ''}")
    out = {
        "model": client.model,
        "prompt_version": PROMPT_VERSION,
        "live_calls": calls,
        "seconds": round(time.time() - started, 1),
        "run_at_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "ancient_sentence": DIOSCORIDES_3_91,
        "ancient_sentence_masked": masked_sentence,
        "results": results,
    }
    Path(out_path).write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{calls} live calls in {out['seconds']} s -> {out_path}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "alyssos-live.json")
