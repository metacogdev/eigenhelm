# eigenhelm

**A conscience for agents, not an agent** — language-agnostic code aesthetic evaluation sidecar.

Eigenhelm scores agent-generated code against mathematical aesthetic metrics derived from
information theory, complexity science, and a PCA eigenspace trained on curated elite
corpora. It runs alongside code-generating agents as a real-time quality signal.

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)

---

## Quick Start

### Install

```bash
uv tool install eigenhelm
```

For the HTTP server:

```bash
uv tool install "eigenhelm[serve]"
```

### Evaluate a file

```bash
eh evaluate path/to/file.py --model models/demo-python-v0.npz
```

### Run the scoring server

```bash
eh serve --model models/demo-python-v0.npz --host 0.0.0.0 --port 8080
```

### API example

```bash
curl -X POST http://localhost:8080/evaluate \
  -H "Content-Type: application/json" \
  -d '{"source": "def add(a, b):\n    return a + b\n", "language": "python"}'
```

---

## CLI Reference

All commands are available as `eigenhelm <command>` or `eh <command>`:

| Command | Description |
|---------|-------------|
| `eh evaluate` | Evaluate source files against an eigenspace model |
| `eh train` | Train a new eigenspace model from a corpus directory |
| `eh inspect` | Inspect a saved model's metadata |
| `eh serve` | Run the evaluation HTTP server |
| `eh harness` | Run a statistical comparison harness across two code sets |
| `eh corpus` | Manage training corpora (sync from manifest) |

Run `eh --help` or `eh <command> --help` for details.

---

## HTTP API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness probe |
| `/evaluate` | POST | Evaluate a code unit |
| `/evaluate/batch` | POST | Evaluate multiple code units |

---

## Supported Languages

| Language | Extension |
|----------|-----------|
| Python | `.py` |
| JavaScript | `.js` |
| TypeScript | `.ts` |
| Go | `.go` |
| Rust | `.rs` |
| Java | `.java` |
| C | `.c` |
| C++ | `.cpp` |
| Ruby | `.rb` |
| Swift | `.swift` |

---

## Models

The bundled `models/demo-python-v0.npz` is a small demo model so you can run the full
pipeline without a hosted account. Production-grade models trained on curated elite corpora
are available via the hosted service or as a paid download.

---

## Development Setup

```bash
git clone https://github.com/metacogdev/eigenhelm.git
cd eigenhelm

# Install with dev and serve dependencies
uv sync --extra dev --extra serve

# Run tests
uv run pytest

# Lint
uv run ruff check .
```

---

## Architecture

```
eigenhelm/
├── virtue_extractor.py   — Tree-sitter + Lizard → FeatureVector (69 dimensions)
├── critic/               — AestheticCritic: Birkhoff, entropy, compression metrics
├── eigenspace.py         — EigenspaceModel: PCA projection, drift scoring
├── training/             — train_eigenspace(), save_model(), inspect_model()
├── helm.py               — DynamicHelm: PID-controlled inference steering
└── serve.py              — FastAPI HTTP evaluation server
```

---

## Current Status

- **5-dim scoring**: manifold drift, alignment, entropy, compression, NCD exemplar distance
- **5 languages**: Python, JavaScript, TypeScript, Go, Rust — all discriminating (Cohen's d > 0.5)
- **Human correlation**: Spearman rho = 0.56 (p < 0.0001, n = 52)
- **Calibrated thresholds**: Models store empirical score distribution; accept/reject boundaries derived from training corpus percentiles (p25/p75)

---

## License

eigenhelm is licensed under the [GNU Affero General Public License v3.0](LICENSE).

### Commercial Licensing

Looking to use eigenhelm in a proprietary SaaS or enterprise product without AGPL-3.0
obligations? A commercial license is available.

Contact us at **licensing@eigenhelm.dev** to discuss terms.
