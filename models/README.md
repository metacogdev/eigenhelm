# Eigenspace Models

This directory contains pre-trained eigenspace (PCA) models in `.npz` format.
Each file embeds full provenance metadata in its `corpus_hash`, `version`, and `n_components`
fields and can be loaded with `eigenhelm.eigenspace.load_model(path)`.

---

## `baseline.npz`

| Field | Value |
|-------|-------|
| **Status** | ⚠️ Placeholder — not suitable for production use |
| **Trained on** | `tests/fixtures/` (5 synthetic source files: `quicksort` in Python, JavaScript, Go, Rust, Java) |
| **Purpose** | CI and unit-test baseline only; verifies the full extraction→projection pipeline |
| **Corpus size** | ~50 LoC across 5 files |
| **Attribution** | All fixtures are original works written for this project; no third-party code |

> **Note:** `baseline.npz` will be replaced by a properly curated demo model
> (`demo-python-v0.npz` or similar) trained on a small, clearly attributed set of
> open-source repositories before the public release. See
> `strategy/open-source-strategy.md` Section 5 for the open core boundary and
> corpus attribution requirements.

---

## Model Schema

All `.npz` files in this directory must contain the following keys:

| Key | Shape | dtype | Description |
|-----|-------|-------|-------------|
| `projection_matrix` | `(69, k)` | float64 | PCA loadings |
| `mean` | `(69,)` | float64 | Feature mean used for centering |
| `std` | `(69,)` | float64 | Feature std used for scaling |
| `n_components` | scalar | int | Number of retained principal components |
| `version` | scalar | str | Semantic version string (e.g. `"0.1.0"`) |
| `corpus_hash` | scalar | str | SHA-256 of the training corpus manifest |

Load and verify a model in tests using the `synthetic_model` session-scoped fixture
defined in `tests/conftest.py` (`make_synthetic_model(n_components=3, seed=42)`).

---

## Adding a New Model

1. Train the model using `eigenhelm-train` (see `src/eigenhelm/cli/train.py`).
2. Record the corpus manifest (list of repos, commit SHAs, file counts) and compute its
   SHA-256 to populate `corpus_hash`.
3. Drop the `.npz` file here and update this README with a provenance row.
4. If total `models/` size exceeds 50 MB or you have more than 10 model variants,
   see Decision 8 in `docs/alpha-decisions.md` for migration triggers to a hosted registry.
