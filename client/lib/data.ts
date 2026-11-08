// Build-time loaders. The site reads only public/data/, which the pipeline writes.
import fs from "node:fs";
import path from "node:path";

import type { BenchmarkFile, IndexRow, Manifest, PlantCase } from "./types";

const DATA_DIR = path.join(process.cwd(), "public", "data");

function readJson<T>(relative: string): T {
  const file = path.join(DATA_DIR, relative);
  return JSON.parse(fs.readFileSync(file, "utf-8")) as T;
}

export function getManifest(): Manifest {
  return readJson<Manifest>("manifest.json");
}

export function getIndex(): IndexRow[] {
  return readJson<{ names: IndexRow[] }>("index.json").names;
}

export function getCase(lemmaTag: string): PlantCase | null {
  const file = path.join("names", `${lemmaTag}.json`);
  if (!fs.existsSync(path.join(DATA_DIR, file))) return null;
  return readJson<PlantCase>(file);
}

export function getBenchmark(): BenchmarkFile {
  return readJson<BenchmarkFile>("benchmark.json");
}
