# eigenhelm

**Catch low-quality AI-generated code before it lands.**

---

## The problem

AI coding agents produce working code fast. But "working" isn't the same as "good." Tests pass, the diff looks plausible, and it gets merged — but the structure is off. Functions do too much. Patterns repeat where they should be abstracted. Complexity concentrates in the wrong places.

Humans catch this in review — when they have time. As agents write more code faster, review gets shallower. Quality drifts toward whatever the model's training data looks like, which is GitHub average.

LLM-based reviewers (CodeRabbit, Copilot review) help, but they reason from text, not structure. They share the same blind spots as the agent that wrote the code. And their feedback is non-deterministic — run the same review twice, get different comments.

## Why "good enough" isn't

The case against caring about code quality is familiar: it works, tests pass, we have deadlines. But structural quality isn't about aesthetics — it's about what happens next.

**Defect density correlates with structural complexity.** Code with high cyclomatic density and concentrated Halstead effort produces more post-merge defects. This isn't theory — it's been measured across decades of empirical software engineering research. The modules that "work fine" but have 75-line functions and repeated validation blocks are the ones that break when requirements change.

**AI-generated code accelerates the problem.** An agent can produce 500 lines in seconds. If 10% of that is structurally unsound, you're accumulating technical debt at machine speed. Without measurement, you won't notice until the cost of changing that code exceeds the cost of rewriting it.

**Review doesn't scale to agent output volume.** A team that reviews 200 lines per PR carefully can't maintain the same rigor when an agent opens 10 PRs a day. The human eye glazes over. Structural issues that would have been caught in a 50-line diff pass unnoticed in a 500-line one.

**The fix is cheap when it's early.** An agent that receives a `[high] reduce_complexity` directive and refactors before the PR exists costs nothing — it's a few seconds of compute. The same structural problem discovered six months later during an incident costs days of debugging.

eigenhelm doesn't ask you to write perfect code. It asks you to measure, so you can make informed tradeoffs instead of uninformed ones.

## What eigenhelm does

eigenhelm scores code structure using information theory — not an LLM. It parses the AST, extracts a structural fingerprint, and measures how closely the code resembles high-quality open-source projects. The output is a deterministic score, a ranking, and actionable directives pointing to specific code locations.

```bash
uv tool install eigenhelm
eh evaluate src/ --rank              # rank files best-to-worst
eh evaluate src/mymodule.py --classify  # single-file classification
```

---

## Before and after

An agent writes a module. eigenhelm evaluates it:

```
src/pipeline.py
  decision: reject
  score:    0.72 (p12 — worse than 88% of training corpus)
  confidence: high
  contributions:
    manifold_drift           0.22  (weight: 0.30, normalized: 0.73)
    manifold_alignment       0.18  (weight: 0.30, normalized: 0.60)
    token_entropy            0.10  (weight: 0.15, normalized: 0.67)
    compression_structure    0.13  (weight: 0.15, normalized: 0.87)
    ncd_exemplar_distance    0.09  (weight: 0.10, normalized: 0.90)
  directives:
    [high] reduce_complexity → process_batch (lines 15-89)
      #1 cyclomatic_density: contribution=-1.2, deviation=+2.8σ
    [high] extract_repeated_logic → validate_row (lines 42-67)
      #1 wl_hash_bin_44: contribution=-0.9, deviation=+2.1σ
    [medium] review_token_distribution → Pipeline.__init__ (lines 3-14)
      #1 halstead_effort: contribution=-0.6, deviation=+1.4σ
```

The agent reads the directives: `process_batch` is too complex, `validate_row` has repeated structure, the constructor is doing too much. It refactors — splits the batch processor, extracts validation, simplifies init. Tests still pass. Re-evaluate:

```
src/pipeline.py
  decision: accept
  score:    0.35 (p70 — better than 70% of training corpus)
  confidence: high
  contributions:
    manifold_drift           0.09  (weight: 0.30, normalized: 0.30)
    manifold_alignment       0.08  (weight: 0.30, normalized: 0.27)
    token_entropy            0.06  (weight: 0.15, normalized: 0.40)
    compression_structure    0.07  (weight: 0.15, normalized: 0.47)
    ncd_exemplar_distance    0.05  (weight: 0.10, normalized: 0.50)
```

Score dropped from 0.72 to 0.35. The code is structurally sound. No human reviewed it.

**Important:** eigenhelm is a signal, not a judge. Don't loop until accept. Don't optimize for the score. Don't hard-gate merges with default thresholds. Use it to focus attention on the code that needs it most.

In a controlled benchmark (3 scenarios, 6 builds, scored by a separate reviewer not involved in generation), agents using eigenhelm's skill contract produced code rated **46% higher** on design, robustness, and spec compliance — with zero correctness regressions. [Full benchmark results →](integrations/agent-skills.md#benchmark-results-3-scenarios-6-builds)

**See it on real code:** We ran eigenhelm against the official FastAPI full-stack template and found a grab-bag `utils.py` mixing email, JWT tokens, and SMTP configuration. Splitting the original file produced a new `tokens.py` scoring 0.59 (marginal), versus 0.89 (reject) for the original mixed-concern file — with zero behavior change. [Read the full case study →](case-studies/fastapi-template.md)

---

## Why not just use an LLM reviewer?

| | eigenhelm | LLM reviewer |
|---|---|---|
| **Input** | AST structure (69-dim vector) | Source text |
| **Deterministic** | Yes — same code, same score, every time | No |
| **Trainable on your corpus** | Yes — `eh train` on your best code | No |
| **Hard CI gate** | Yes — with calibrated thresholds | Suggestions only |
| **Tracks quality over time** | Yes — scores are comparable across runs | No stable metric |
| **Catches structural decay** | Yes — entropy, compression, manifold distance | Guesses from text |
| **Catches logic bugs** | No | Yes |
| **Reviews naming/docs** | No | Yes |
| **Cost per evaluation** | Zero (local, no API calls) | Per-token LLM cost |

They're complementary. eigenhelm runs first — in the agent's inner loop, before a PR exists. LLM reviewers run second, on the PR, where contextual reasoning adds the most value. [Full comparison →](concepts/why-eigenhelm.md)

---

## How it works

eigenhelm extracts a 69-dimensional structural fingerprint from each file using tree-sitter and projects it into a PCA eigenspace trained on high-quality open-source code. The score combines five dimensions:

| Dimension | What it measures |
|-----------|-----------------|
| **Manifold drift** | Distance from the learned code quality manifold |
| **Manifold alignment** | Alignment with principal quality axes |
| **Token entropy** | Information density of the byte stream |
| **Compression structure** | Structural regularity (Birkhoff aesthetic measure) |
| **NCD exemplar distance** | Similarity to nearest high-quality exemplar |

[Learn more about the scoring model →](concepts/how-it-works.md)

---

## Integrate in 30 seconds

=== "GitHub Action"

    ```yaml
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    - uses: metacogdev/eigenhelm@v0
      with:
        diff: origin/main...HEAD
        format: sarif
    ```

=== "Pre-commit"

    ```yaml
    repos:
      - repo: https://github.com/metacogdev/eigenhelm
        rev: v0.5.0
        hooks:
          - id: eigenhelm-check
    ```

=== "HTTP API"

    ```bash
    eh serve --port 8080
    curl -X POST http://localhost:8080/v1/evaluate \
      -H "Content-Type: application/json" \
      -d '{"source": "def add(a, b): return a + b", "language": "python"}'
    ```

=== "Agent skill"

    ```bash
    npx skills add metacogdev/skills
    # or: eh skill --install
    ```

---

## Outputs

- **Human** — readable terminal output with color and classification
- **JSON** — machine-readable for scripting and dashboards
- **[SARIF 2.1.0](https://sarifweb.azurewebsites.net/)** — upload to GitHub Code Scanning, VS Code, or any SARIF viewer

---

## Get started

<div class="grid cards" markdown>

- :material-download: **[Installation](getting-started/install.md)**

    Install via pip, uv, or Docker

- :material-rocket-launch: **[Quick Start](getting-started/quickstart.md)**

    Evaluate your first file in 60 seconds

- :material-cog: **[Configuration](getting-started/configuration.md)**

    Customize thresholds, models, and paths

- :material-github: **[GitHub Action](integrations/github-action.md)**

    Add eigenhelm to your CI pipeline

</div>

---

## Supported languages

**Trained models**: Python, JavaScript, TypeScript, Go, Rust.

**Parser support** (feature extraction available, bring your own model): Java, C, C++, Ruby, Kotlin.

---

## License

eigenhelm is licensed under [AGPL-3.0](license.md). A [commercial license](mailto:licensing@eigenhelm.sh) is available for proprietary use.
