# Eigenspace Models

This directory contains pre-trained eigenspace (PCA) models in `.npz` format.
Each file embeds full provenance metadata and can be loaded with
`eigenhelm.eigenspace.load_model(path)`. The default bundled model for all CLI
commands is `general-polyglot-v1.npz`.

---

## Bundled Models

| File | Language | Corpus class | Training files | PCs | EVR | Accept threshold | Reject threshold |
|------|----------|--------------|---------------|-----|-----|-----------------|-----------------|
| `general-polyglot-v1.npz` | multi (5 langs) | B | 1,483 | 36 | 0.90 | 0.56 | 0.68 |
| `lang-python.npz` | python | A | 250 | 30 | 0.91 | 0.56 | 0.70 |
| `lang-typescript.npz` | typescript | A | 464 | 30 | 0.90 | 0.51 | 0.66 |
| `lang-rust.npz` | rust | A | 566 | 28 | 0.90 | 0.55 | 0.67 |
| `lang-go.npz` | go | A | 153 | 29 | 0.91 | 0.53 | 0.67 |
| `lang-javascript.npz` | javascript | A | 50 | 27 | 0.91 | 0.57 | 0.72 |
| `pattern-cli.npz` | multi | B | 111 | 31 | 0.90 | 0.57 | 0.68 |
| `baseline.npz` | python | A | 250 | 30 | 0.91 | 0.56 | 0.70 |

**Corpus classes:** A = single-language high-quality corpus; B = multi-language or pattern-focused corpus.

**`baseline.npz`** is identical to `lang-python.npz` (same training corpus, same `corpus_hash`).
It is retained as a stable reference for tests and CI fixtures. Use `lang-python.npz` for
production Python-only evaluation; `general-polyglot-v1.npz` is the default for everything else.

All models ship with version `0.2.0`, include 015-calibration thresholds, and have score
distribution statistics embedded for percentile-relative feedback.

---

## Model Schema

All `.npz` files contain the following keys (27 total):

### Core projection (6 keys)

| Key | Shape | dtype | Description |
|-----|-------|-------|-------------|
| `projection_matrix` | `(69, k)` | float64 | PCA loadings |
| `mean` | `(69,)` | float64 | Feature mean used for centering |
| `std` | `(69,)` | float64 | Feature std used for scaling |
| `n_components` | scalar | int | Number of retained principal components |
| `version` | scalar | str | Semantic version string (e.g. `"0.2.0"`) |
| `corpus_hash` | scalar | str | SHA-256 of the training corpus manifest |

### Training metadata (7 keys)

| Key | Shape | dtype | Description |
|-----|-------|-------|-------------|
| `explained_variance_ratio` | `(k,)` | float64 | Per-component EVR; sum = total variance explained |
| `sigma_drift` | scalar | float64 | Drift axis scale (used for L_drift normalization) |
| `sigma_virtue` | scalar | float64 | Virtue axis scale (used for L_virtue normalization) |
| `n_training_files` | scalar | int | Number of files used in training |
| `language` | scalar | str | Primary language (`"multi"` for polyglot models) |
| `corpus_class` | scalar | str | Corpus class (`"A"` or `"B"`) |
| `n_exemplars` | scalar | int | Number of exemplar vectors stored |

### Calibration thresholds (2 keys)

| Key | Shape | dtype | Description |
|-----|-------|-------|-------------|
| `calibrated_accept` | scalar | float64 | Empirical p25 score threshold — below this → accept |
| `calibrated_reject` | scalar | float64 | Empirical p75 score threshold — above this → reject |

### Score distribution statistics (8 keys)

| Key | Shape | dtype | Description |
|-----|-------|-------|-------------|
| `score_dist_min` | scalar | float64 | Minimum score observed in training corpus |
| `score_dist_p10` | scalar | float64 | 10th percentile |
| `score_dist_p25` | scalar | float64 | 25th percentile (= `calibrated_accept`) |
| `score_dist_median` | scalar | float64 | Median score |
| `score_dist_p75` | scalar | float64 | 75th percentile (= `calibrated_reject`) |
| `score_dist_p90` | scalar | float64 | 90th percentile |
| `score_dist_max` | scalar | float64 | Maximum score observed |
| `score_dist_n_scores` | scalar | int | Number of scores used to fit the distribution |

### Exemplar storage (4 keys)

| Key | Shape | dtype | Description |
|-----|-------|-------|-------------|
| `exemplar_vectors` | `(n_exemplars, k)` | float64 | Projected exemplar feature vectors |
| `exemplar_labels` | `(n_exemplars,)` | str | Source file paths / identifiers |
| `exemplar_blob` | `(1,)` | bytes | Serialized exemplar metadata blob |
| `exemplar_offsets` | `(n_exemplars+1,)` | int64 | Byte offsets into `exemplar_blob` |

---

## Using Models in Tests

Use the `synthetic_model` session-scoped fixture from `tests/conftest.py`:

```python
from tests.conftest import make_synthetic_model

model = make_synthetic_model(n_components=3, seed=42)
```

This produces a deterministic 3-component `EigenspaceModel` suitable for unit and
contract tests without loading a real `.npz` file.

---

## Model Registry

Additional and community-contributed models are distributed via the
[`metacogdev/eigenhelm-models`](https://github.com/metacogdev/eigenhelm-models) registry.
The registry manifest is fetched automatically by `eh model`.

```bash
eh model list --remote           # list available models in the registry
eh model pull general-polyglot-v1   # download and cache a model locally
eh model list                    # show bundled + locally cached models
```

Downloaded models are cached at `~/.eigenhelm/models/` and can be passed to any command:

```bash
eh evaluate src/ --model general-polyglot-v1
```

The `general-polyglot-v1` model in the registry is the same polyglot model bundled with
the package, versioned and SHA-256-verified for integrity. Future registry entries will
include community models, domain-specific variants, and enterprise-tier models.

---

## Adding a New Model

1. Train the model using `eh train` (see `src/eigenhelm/cli/train.py`).
2. Record the corpus manifest in `corpora/` and compute its SHA-256 for `corpus_hash`.
3. Drop the `.npz` file here **and** in `src/eigenhelm/trained_models/` (the bundled copy).
4. Update this README with a provenance row.
5. If total `models/` size exceeds 50 MB or you have more than 10 model variants,
   see Decision 8 in `docs/alpha-decisions.md` for migration triggers to a hosted registry.
