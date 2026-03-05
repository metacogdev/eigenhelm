"""Shared pytest fixtures for eigenhelm tests."""

from __future__ import annotations

import pathlib

import pytest

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


def make_test_corpus(target_dir: pathlib.Path) -> pathlib.Path:
    """Populate target_dir with Python/JS/Go source files from tests/fixtures/.

    Copies all fixture source files into target_dir, producing a mini training
    corpus of 5 files across 5 languages (Python, JavaScript, Go, Java, Rust).
    """
    for src in FIXTURES_DIR.iterdir():
        if src.is_file():
            (target_dir / src.name).write_bytes(src.read_bytes())
    return target_dir


@pytest.fixture(scope="session")
def corpus_dir(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Session-scoped fixture: a temp directory populated with test corpus files."""
    d = tmp_path_factory.mktemp("corpus")
    return make_test_corpus(d)


@pytest.fixture(scope="session")
def python_quicksort_source() -> str:
    return (FIXTURES_DIR / "python_quicksort.py").read_text()


@pytest.fixture(scope="session")
def js_quicksort_source() -> str:
    return (FIXTURES_DIR / "js_quicksort.js").read_text()


@pytest.fixture(scope="session")
def go_quicksort_source() -> str:
    return (FIXTURES_DIR / "go_quicksort.go").read_text()


@pytest.fixture(scope="session")
def rust_quicksort_source() -> str:
    return (FIXTURES_DIR / "rust_quicksort.rs").read_text()


@pytest.fixture(scope="session")
def java_quicksort_source() -> str:
    return (FIXTURES_DIR / "java_quicksort.java").read_text()


@pytest.fixture(scope="session")
def synthetic_model():
    """A deterministic synthetic EigenspaceModel for projection tests."""
    from eigenhelm.eigenspace import make_synthetic_model

    return make_synthetic_model(n_components=3, seed=42)


@pytest.fixture()
def client():
    """TestClient with no eigenspace model (low-confidence mode)."""
    from eigenhelm.serve import create_app
    from starlette.testclient import TestClient

    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def client_with_model(synthetic_model):
    """TestClient with synthetic eigenspace model (high-confidence mode)."""
    from eigenhelm.serve import create_app
    from starlette.testclient import TestClient

    app = create_app(eigenspace=synthetic_model)
    with TestClient(app) as c:
        yield c
