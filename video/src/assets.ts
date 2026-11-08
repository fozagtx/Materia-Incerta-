import { staticFile } from "remotion";

import live from "./data/alyssos-live.json";

// Everything shown as model output in this video comes from one real run:
// pipeline/examples/alyssos_live.py, Qwen3-235B on Nebius Token Factory,
// on Dioscorides' Greek text and Flora Europaea descriptions.

export const IMG = {
  folio: staticFile("img/vienna-dioscurides-anchusa.jpg"),
  fibigia: staticFile("img/fibigia-clypeata.jpg"),
  scutellaria: staticFile("img/scutellaria-galericulata.jpg"),
};

export const CREDITS = [
  "Vienna Dioscurides (c. 512 CE), public domain",
  "Fibigia clypeata photo: Jerzy Opioła, CC BY-SA 4.0",
  "Scutellaria galericulata: O. W. Thomé, Flora von Deutschland (1885), public domain",
  "Dioscorides 3.91, Greek text ed. M. Wellmann (1906)",
  "Flora Europaea descriptions via Plazi",
  "Example and expert labels: Lardos et al. (2024), J. Ethnopharmacol. 322: 117622",
];

export type MatchClass = "good" | "partial" | "no_match" | "absent";

export type LiveResult = {
  candidate: string;
  category: string;
  ancient_greek: string;
  ancient_gloss: string;
  match_class: MatchClass;
  reason: string;
  ancient_quote: string | null;
  modern_quote: string | null;
};

export const LIVE = live as {
  model: string;
  live_calls: number;
  seconds: number;
  run_at_utc: string;
  ancient_sentence: string;
  ancient_sentence_masked: string;
  results: LiveResult[];
};

export const FIBIGIA_FRUIT = LIVE.results.find((r) => r.candidate === "Fibigia clypeata" && r.category === "fruit")!;

export const FIBIGIA_MODERN_EXCERPT =
  "Perennial herbs; hairs stellate … Fruit a strongly compressed latiseptate silicula; valves flat, not veined … Seeds 2-8 in each loculus, winged.";

/** Exactly what the script printed, one line per comparison. */
export const TERMINAL_LINES = [
  ...LIVE.results.map(
    (r) => `${r.candidate.padEnd(26)} ${r.category.padEnd(8)} ${r.match_class.padEnd(9)} ${r.modern_quote ?? ""}`.trimEnd(),
  ),
  `${LIVE.live_calls} live calls in ${LIVE.seconds} s -> video/src/data/alyssos-live.json`,
];
