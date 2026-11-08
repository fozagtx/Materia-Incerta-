"""Generate the voiceover with Kokoro TTS (kokoro-onnx) and fit scene timings to it.

Reads  src/data/narration.json
Writes public/audio/voiceover.wav   (not committed)
       src/data/voiceover.json      (scene lengths and where each line starts)

Usage:
    pip install kokoro-onnx soundfile
    python scripts/voiceover.py --models /path/to/kokoro-models
The models folder needs kokoro-v1.0.onnx and voices-v1.0.bin from
https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from kokoro_onnx.tokenizer import Tokenizer

HERE = Path(__file__).resolve().parent.parent


def to_phonemes(text: str, overrides: dict[str, str], tok: Tokenizer) -> str:
    """Phonemize text, using fixed pronunciations for names espeak gets wrong."""
    if not overrides:
        return tok.phonemize(text, "en-us")
    keys = sorted(overrides, key=len, reverse=True)
    pattern = re.compile("(" + "|".join(re.escape(k) for k in keys) + r")(?![\w'])")
    parts: list[str] = []
    pos = 0
    for m in pattern.finditer(text):
        before = text[pos : m.start()].strip()
        if before:
            parts.append(tok.phonemize(before, "en-us").strip())
        parts.append(overrides[m.group(1)])
        pos = m.end()
    rest = text[pos:].strip()
    if rest:
        parts.append(tok.phonemize(rest, "en-us").strip())
    return " ".join(p for p in parts if p)


def fade(x: np.ndarray, sr: int, ms: float = 15) -> np.ndarray:
    n = max(1, int(sr * ms / 1000))
    x = x.copy()
    x[:n] *= np.linspace(0, 1, n)
    x[-n:] *= np.linspace(1, 0, n)
    return x


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", required=True, type=Path)
    args = ap.parse_args()

    cfg = json.loads((HERE / "src/data/narration.json").read_text(encoding="utf-8"))
    fps, total = cfg["fps"], cfg["totalFrames"]
    k = Kokoro(str(args.models / "kokoro-v1.0.onnx"), str(args.models / "voices-v1.0.bin"))
    tok = Tokenizer()

    clips = []
    sr = 24000
    for scene in cfg["scenes"]:
        ph = to_phonemes(scene["text"], cfg["pronunciations"], tok)
        audio, sr = k.create(ph, voice=cfg["voice"], speed=cfg["speed"], is_phonemes=True)
        seconds = len(audio) / sr
        need = math.ceil((cfg["leadSeconds"] + seconds + cfg["tailSeconds"]) * fps)
        clips.append({"id": scene["id"], "audio": audio, "seconds": seconds, "frames": max(scene["minFrames"], need)})

    used = sum(c["frames"] for c in clips)
    if used > total:
        raise SystemExit(f"narration needs {used} frames, more than {total}; shorten a line")
    # Give spare frames to the scenes in proportion to their length, rest to the close.
    spare = total - used
    for c in clips:
        add = int(spare * c["frames"] / used)
        c["frames"] += add
    clips[-1]["frames"] += total - sum(c["frames"] for c in clips)

    track = np.zeros(int(total / fps * sr) + sr, dtype=np.float32)
    timing = []
    start = 0
    for c in clips:
        offset = start + round(cfg["leadSeconds"] * fps)
        i = int(offset / fps * sr)
        track[i : i + len(c["audio"])] += fade(c["audio"].astype(np.float32), sr)
        timing.append({"id": c["id"], "frames": c["frames"], "voiceStartFrame": offset - start, "voiceSeconds": round(c["seconds"], 2)})
        start += c["frames"]
    track = track[: int(total / fps * sr)]

    out = HERE / "public/audio/voiceover.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw.wav"
        sf.write(raw, track, sr)
        # Loudness to -16 LUFS (web video norm), 48 kHz.
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", str(out)],
            check=True,
        )
    (HERE / "src/data/voiceover.json").write_text(
        json.dumps({"voice": cfg["voice"], "fps": fps, "totalFrames": total, "scenes": timing}, indent=2) + "\n",
        encoding="utf-8",
    )
    for t in timing:
        print(f"{t['id']:<9} scene {t['frames'] / fps:5.2f}s  voice {t['voiceSeconds']:5.2f}s")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
