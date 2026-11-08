"""Fetch the files listed in pipeline/sources.toml into data/raw/.

Files without a URL are skipped and listed. Files with a sha256 are verified;
a mismatch deletes the download and fails, so a changed upstream file can't
silently change results.
"""

from __future__ import annotations

import hashlib
import shutil
import urllib.request
from pathlib import Path

from .sources import Sources


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(sources: Sources, raw: Path, *, only: set[str] | None = None, force: bool = False) -> dict:
    report: dict[str, list[str]] = {"downloaded": [], "present": [], "no_url": [], "unpinned": []}
    for source in sources.sources:
        if only and source.key not in only:
            continue
        for f in source.files:
            dest = raw / f.path
            if dest.exists() and not force:
                if f.sha256 and sha256_of(dest) != f.sha256:
                    raise ValueError(f"{dest}: sha256 differs from sources.toml; re-download with --force")
                report["present"].append(f.role)
                continue
            if not f.url:
                report["no_url"].append(f.role)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_suffix(dest.suffix + ".part")
            with urllib.request.urlopen(f.url, timeout=120) as resp, tmp.open("wb") as out:  # noqa: S310
                shutil.copyfileobj(resp, out)
            digest = sha256_of(tmp)
            if f.sha256 and digest != f.sha256:
                tmp.unlink()
                raise ValueError(f"{f.role}: sha256 {digest} does not match sources.toml")
            tmp.replace(dest)
            report["downloaded"].append(f.role)
            if not f.sha256:
                report["unpinned"].append(f"{f.role} sha256={digest}")
    return report
