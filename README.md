# eigenhelm

**Catch low-quality AI-generated code before it lands.**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)

---

## The problem

AI agents write working code fast. But "working" isn't "good." Tests pass, the diff looks plausible, and it gets merged — but complexity concentrates in the wrong places, patterns repeat where they should be abstracted, and structure decays toward GitHub average.

LLM reviewers help, but they share the agent's blind spots. They reason from text, not structure. Run the same review twice, get different comments.

The argument against caring: it works, tests pass, ship it. But structural quality isn't aesthetics — it predicts what happens next. High cyclomatic density and concentrated complexity produce more post-merge defects. Agents generate code at machine speed; without measurement, you accumulate structural debt just as fast. And review doesn't scale to agent output volume — the human eye glazes over at 500 lines.

eigenhelm measures code structure using information theory — not an LLM. It parses the AST, extracts a structural fingerprint, and scores how closely the code resembles curated high-quality corpora. Deterministic, trainable on your code, zero API cost.

---

## Before and after

An agent writes a module. eigenhelm evaluates it:

```
src/pipeline.py
  decision: reject
  score:    0.72
  directives:
    [high] reduce_complexity → process_batch (lines 15-89)
    [high] extract_repeated_logic → validate_row (lines 42-67)
```

The agent reads the directives, refactors, tests still pass. Re-evaluate:

```
src/pipeline.py
  decision: accept
  score:    0.35
```

0.72 → 0.35. Structurally sound. No human reviewed it.

In controlled benchmarks, agents using eigenhelm produced code rated **46% higher** on design, robustness, and spec compliance — with zero correctness regressions.

---

## Install

```bash
pip install eigenhelm
```

Or with uv (no venv required):

```bash
uv tool install eigenhelm
```

A bundled model is included — no setup needed.

```bash
eh evaluate src/ --rank           # rank files best-to-worst
eh evaluate path/to/file.py --classify   # single-file classification
```

### What the scores mean

- **accept** (score < 0.4): Structurally sound. Move on.
- **marginal** (score 0.4-0.6): Acceptable; review directives if improvement is straightforward.
- **reject** (score > 0.6): Worth reviewing. Read the directives for guidance.

Scores are relative to high-quality open-source training corpora. Most production code scores marginal — that's normal, not a problem.

---

## How is this different from CodeRabbit?

| | eigenhelm | LLM reviewer |
|---|---|---|
| **Input** | AST structure (69-dim vector) | Source text |
| **Deterministic** | Yes — same code, same score | No |
| **Trainable on your corpus** | Yes — `eh train` | No |
| **Hard CI gate** | Yes — with calibrated thresholds | Suggestions only |
| **Tracks quality over time** | Yes — comparable scores | No stable metric |
| **Catches logic bugs** | No | Yes |
| **Cost** | Zero (local) | Per-token LLM cost |

They're complementary. eigenhelm runs first — in the agent's inner loop. LLM review runs second, on the PR. [Full comparison.](https://eigenhelm.sh/concepts/why-eigenhelm/)

---

## Agent integration

```bash
eh skill --install
```

The skill teaches AI agents the correct workflow: evaluate after tests pass, two passes maximum, never sacrifice correctness for score.

**Important:** Do not loop until accept. Do not optimize for the score. Do not hard-gate merges with default thresholds. eigenhelm is a signal for focusing attention, not a judge.

In a controlled benchmark (3 scenarios, scored by a separate reviewer not involved in generation), agents using the skill produced code rated 46% higher on quality metrics. [Full guide.](https://eigenhelm.sh/integrations/agent-skills/)

---

## CLI Reference

All commands are available as `eigenhelm <command>` or `eh <command>`:

| Command | Description |
|---------|-------------|
| `eh evaluate` | Evaluate source files against the trained quality model |
| `eh train` | Train a new eigenspace model from a corpus directory |
| `eh inspect` | Inspect a saved model's metadata |
| `eh serve` | Run the evaluation HTTP server |
| `eh harness` | Run a statistical comparison harness across two code sets |
| `eh benchmark` | Run real-world use case benchmarks |
| `eh skill` | Install the agent skill file |
| `eh model` | Manage eigenhelm models (list, pull, info) |
| `eh init` | Generate a starter `.eigenhelm.toml` configuration |
| `eh corpus` | Manage training corpora (sync from manifest) |
| `eh mcp` | Start the MCP stdio server |

Run `eh --help` or `eh <command> --help` for details.

---

## HTTP API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness probe |
| `/ready` | GET | Readiness probe (model loaded) |
| `/v1/evaluate` | POST | Evaluate a code unit |
| `/v1/evaluate/batch` | POST | Evaluate multiple code units |

---

## Supported Languages

**Trained models**: Python, JavaScript, TypeScript, Go, Rust.

**Parser support** (feature extraction available, bring your own model): Java, C, C++, Ruby, Kotlin.

---

## Development Setup

```bash
git clone https://github.com/metacogdev/eigenhelm.git
cd eigenhelm
uv sync --extra dev --extra serve
uv run pytest
uv run ruff check .
```

---

## Architecture

```
eigenhelm/
├── virtue_extractor.py   — Tree-sitter + Lizard → FeatureVector (69 dimensions)
├── critic/               — StructuralCritic: 5-dim scoring (drift, alignment, entropy, compression, NCD)
├── declarations/         — Declaration-aware scoring (type defs, barrel files, data tables)
├── regions/              — Test/production code region detection
├── eigenspace/           — EigenspaceModel: PCA projection, drift scoring
├── attribution/          — Score attribution and directive generation
├── training/             — PCA training, calibration, exemplar selection
├── helm/                 — DynamicHelm: threshold-calibrated evaluation + PID steering
├── config/               — .eigenhelm.toml loader and models
├── output/               — SARIF 2.1.0 and JSON formatters
├── scoring/              — Per-repo scorecard (M1-M5, Q1-Q5)
├── harness/              — Statistical evaluation harness (Mann-Whitney U)
├── parsers/              — Language parsing (tree-sitter integration)
├── mcp/                  — Model Context Protocol stdio server
├── registry/             — Model registry and resolution
├── trained_models/       — Bundled .npz models
└── serve/                — HTTP evaluation server (requires `eigenhelm[serve]` extra)
```

---

## Current Status

- **5-dim scoring**: manifold drift, alignment, entropy, compression, NCD exemplar distance
- **5 languages**: Python, JavaScript, TypeScript, Go, Rust — all discriminating (Cohen's d > 0.5)
- **Human correlation**: Spearman rho = 0.54 overall (n = 92, 5 languages), 0.66 Python-only (n = 52)
- **Declaration-aware**: Automatically detects type-definition and data-table files, adjusts scoring and directives
- **Agent-tested**: Skill contract validated in controlled arena (3 scenarios, 46% quality improvement)

---

## License

eigenhelm is licensed under the [GNU Affero General Public License v3.0](LICENSE).

### Commercial Licensing

Looking to use eigenhelm in a proprietary SaaS or enterprise product without AGPL-3.0
obligations? A commercial license is available.

Contact us at **licensing@eigenhelm.sh** to discuss terms.
