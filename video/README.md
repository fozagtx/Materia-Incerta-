# Pitch video

A 90-second pitch and demo built with [Remotion](https://www.remotion.dev). Rendered files go to `video/out/` and are not committed.

The structure follows Oren Klaff's *Pitch Anything* (frame, story, intrigue, idea, proof, prize, close) and the demo-video guidance in The Hackathon Playbook: 60 to 90 seconds, problem first, then the product working.

## What is real

Every model answer in the video comes from one live run of [`pipeline/examples/alyssos_live.py`](../pipeline/examples/alyssos_live.py), saved in [`src/data/alyssos-live.json`](src/data/alyssos-live.json):

- **Model:** Qwen3-235B-A22B-Instruct-2507 on Nebius Token Factory, run 2026-11-08 11:45 UTC: 10 calls in 13.7 s.
- **Ancient text:** Dioscorides 3.91 in Greek, from Wellmann's edition (1906, public domain). Only OCR letter errors are corrected.
- **Modern text:** Flora Europaea descriptions via Plazi, which marks them "No known copyright restrictions apply".

The expert labels (Strong and Weak) come from Lardos et al. (2024). The five-detail run is a demonstration, not the benchmark.

## Voiceover

The narration is generated with [Kokoro TTS](https://github.com/thewh1teagle/kokoro-onnx) (Kokoro-82M, Apache-2.0, voice `af_heart`) from [`src/data/narration.json`](src/data/narration.json). That file also fixes the pronunciation of names the default phonemizer gets wrong (Dioscorides, *Fibigia*, *alyssos*, Qwen, Nebius, Materia Incerta).

```bash
pip install kokoro-onnx soundfile
python video/scripts/voiceover.py --models /path/to/kokoro-models
```

The models folder needs `kokoro-v1.0.onnx` and `voices-v1.0.bin` from the [kokoro-onnx model release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0). The script writes `public/audio/voiceover.wav` (not committed) and `src/data/voiceover.json`. Scene lengths follow the voice, and the total stays 90 seconds. Without the audio file, the video renders silent.

## Render

```bash
npm --prefix video install
npm --prefix video run render -- --audio-codec=aac   # writes video/out/materia-incerta-demo.mp4
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
