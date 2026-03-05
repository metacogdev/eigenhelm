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
eigenhelm-evaluate path/to/file.py --model models/demo-python-v0.npz
```

### Run the scoring server

```bash
eigenhelm-serve --model models/demo-python-v0.npz --host 0.0.0.0 --port 8080
```

### API example

```bash
curl -X POST http://localhost:8080/evaluate \
  -H "Content-Type: application/json" \
  -d '{"source": "def add(a, b):\n    return a + b\n", "language": "python"}'
```

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `eigenhelm-evaluate` | Evaluate a source file against an eigenspace model |
| `eigenhelm-train` | Train a new eigenspace model from a corpus directory |
| `eigenhelm-inspect` | Inspect a saved model's metadata |
| `eigenhelm-serve` | Run the evaluation HTTP server |
| `eigenhelm-harness` | Run a statistical comparison harness across two code sets |

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

## License

eigenhelm is licensed under the [GNU Affero General Public License v3.0](LICENSE).

### Commercial Licensing

Looking to use eigenhelm in a proprietary SaaS or enterprise product without AGPL-3.0
obligations? A commercial license is available.

Contact us at **licensing@eigenhelm.dev** to discuss terms.
