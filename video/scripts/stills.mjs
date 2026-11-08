// Render one still per scene to check layout: node scripts/stills.mjs <outDir> [frames...]
import path from "node:path";
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";

const out = process.argv[2] ?? "out/stills";
const frames = process.argv.slice(3).map(Number);
const browserExecutable = process.env.REMOTION_BROWSER || null;
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts") });
const composition = await selectComposition({ serveUrl, id: "MateriaIncerta", browserExecutable });
for (const frame of frames.length ? frames : [150, 520, 860, 1150, 1560, 1960, 2120, 2460, 2660]) {
  await renderStill({ composition, serveUrl, frame, output: `${out}/f${frame}.png`, browserExecutable, scale: 0.5 });
  console.log("still", frame);
}
