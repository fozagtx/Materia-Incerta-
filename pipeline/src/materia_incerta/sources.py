"""Read pipeline/sources.toml: what each dataset is, where it comes from,
which version is pinned, and what its licence allows."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceFile:
    role: str
    path: str
    url: str = ""
    sha256: str = ""


@dataclass(frozen=True)
class Source:
    key: str
    title: str
    citation: str
    version: str
    licence: str
    licence_confirmed: bool
    republish: bool
    notes: str
    files: tuple[SourceFile, ...]


@dataclass(frozen=True)
class Sources:
    sources: tuple[Source, ...]

    @classmethod
    def load(cls, path: Path) -> "Sources":
        if not path.exists():
            return cls(sources=())
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        out = []
        for key, entry in data.get("sources", {}).items():
            files = tuple(
                SourceFile(
                    role=f["role"],
                    path=f["path"],
                    url=f.get("url", ""),
                    sha256=f.get("sha256", ""),
                )
                for f in entry.get("files", [])
            )
            out.append(
                Source(
                    key=key,
                    title=entry.get("title", key),
                    citation=entry.get("citation", ""),
                    version=entry.get("version", ""),
                    licence=entry.get("licence", "unconfirmed"),
                    licence_confirmed=bool(entry.get("licence_confirmed", False)),
                    republish=bool(entry.get("republish", False)),
                    notes=entry.get("notes", ""),
                    files=files,
                )
            )
        return cls(sources=tuple(out))

    def file_for(self, role: str) -> SourceFile | None:
        for s in self.sources:
            for f in s.files:
                if f.role == role:
                    return f
        return None

    def path_for(self, role: str, raw: Path) -> Path | None:
        f = self.file_for(role)
        return None if f is None else raw / f.path

    def get(self, key: str) -> Source | None:
        return next((s for s in self.sources if s.key == key), None)

    def manifest(self) -> list[dict]:
        """What the site shows on the limits page."""
        return [
            {
                "key": s.key,
                "title": s.title,
                "citation": s.citation,
                "version": s.version or None,
                "licence": s.licence,
                "licence_confirmed": s.licence_confirmed,
                "republish": s.republish,
                "notes": s.notes or None,
            }
            for s in self.sources
        ]
