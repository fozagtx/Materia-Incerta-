# Pitch video

A 90-second pitch and demo built with [Remotion](https://www.remotion.dev). The rendered file is [`docs/video/materia-incerta-demo.mp4`](../docs/video/materia-incerta-demo.mp4).

The structure follows Oren Klaff's *Pitch Anything* (frame, story, intrigue, idea, proof, prize, close) and the demo-video guidance in The Hackathon Playbook: 60 to 90 seconds, problem first, then the product working.

## What is real

Every model answer in the video comes from one live run of [`pipeline/examples/alyssos_live.py`](../pipeline/examples/alyssos_live.py), saved in [`src/data/alyssos-live.json`](src/data/alyssos-live.json):

- **Model:** Qwen3-235B-A22B-Instruct-2507 on Nebius Token Factory, run 2026-11-08 11:45 UTC: 10 calls in 13.7 s.
- **Ancient text:** Dioscorides 3.91 in Greek, from Wellmann's edition (1906, public domain). Only OCR letter errors are corrected.
- **Modern text:** Flora Europaea descriptions via Plazi, which marks them "No known copyright restrictions apply".

The expert labels (Strong and Weak) come from Lardos et al. (2024). The five-detail run is a demonstration, not the benchmark.

## Render

```bash
npm --prefix video install
npm --prefix video run render        # writes video/out/materia-incerta-demo.mp4
npm --prefix video run studio        # preview and scrub in the browser
```

On a machine without Remotion's own Chrome download, pass a local Chromium with `--browser-executable=/path/to/chrome-headless-shell`.

To refresh the model output, run the example script with `LLM_API_KEY` and `LLM_MODEL` set:

```bash
python pipeline/examples/alyssos_live.py video/src/data/alyssos-live.json
```

## Credits

- Vienna Dioscurides (c. 512 CE), Anchusa folio: public domain
- *Fibigia clypeata* photo: Jerzy Opioła, CC BY-SA 4.0 (Wikimedia Commons)
- *Scutellaria galericulata* plate: O. W. Thomé, *Flora von Deutschland* (1885), public domain
- Fonts: EB Garamond, Inter and JetBrains Mono, all under the SIL Open Font License (see `public/fonts/`)

Remotion is free for individuals and teams of up to three people. Larger companies need a company licence.
