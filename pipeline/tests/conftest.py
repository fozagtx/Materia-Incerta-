from __future__ import annotations

from pathlib import Path

import pytest

from materia_incerta import tables
from materia_incerta.demo import build_demo, run_demo


@pytest.fixture(scope="session")
def demo_built(tmp_path_factory: pytest.TempPathFactory):
    """Synthetic demo, fully run. Read-only: copy before mutating."""
    root = tmp_path_factory.mktemp("demo")
    return run_demo(root)


@pytest.fixture
def fresh_demo(tmp_path: Path):
    """Synthetic demo with raw files, interim tables and cache, not yet run."""
    return build_demo(tmp_path)


@pytest.fixture(scope="session")
def demo_tables(demo_built):
    i = demo_built.interim
    return {name: tables.read_table(i, name) for name in tables.TABLES if tables.has_table(i, name)}
