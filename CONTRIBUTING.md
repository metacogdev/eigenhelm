# Contributing to eigenhelm

Thank you for your interest in contributing. This document explains how to contribute effectively
and what to expect from the process.

---

## Contributor License Agreement (CLA)

**Before your first pull request can be merged, you must sign the Contributor License Agreement.**

eigenhelm is dual-licensed: the community edition is AGPL-3.0, and a separate commercial license
is available for proprietary and enterprise use. To keep both licensing paths open, all
contributors must grant the project maintainers the right to use, distribute, and relicense
contributions under both the AGPL-3.0 and commercial terms.

- **Individual contributors:** Sign the CLA via [CLA Assistant](https://cla-assistant.io) when
  you open your first pull request. The bot will prompt you automatically.
- **Corporate contributors:** If you are contributing as part of your employment, your employer
  must sign the Corporate CLA before any of your PRs can be merged. Contact the maintainers to
  obtain the Corporate CLA template.

PRs from contributors who have not signed the CLA will not be merged.

---

## What We Welcome

| Contribution type | Notes |
|-------------------|-------|
| Bug fixes | Always welcome; include a regression test |
| New language support | Add an entry to `parsers/language_map.py`; include a fixture in `tests/fixtures/` |
| New grammar node types for Halstead | Extend `OPERATOR_NODE_TYPES` in `language_map.py` |
| Test coverage improvements | Unit, contract, and integration tests |
| Documentation corrections | Typos, clarifications, broken links |
| Performance improvements | Must not change public API or metric values |

## What Requires a Discussion First

Open an issue before submitting a PR for any of the following. These involve trade-offs that
need alignment before implementation work begins:

- Changes to the feature vector schema (dimensions, ordering, or semantics of `FeatureVector`)
- New external dependencies anywhere in `src/eigenhelm/critic/` (Stage 2 is stdlib-only by
  design)
- Alternative backends for PCA or Halstead computation
- Changes to the `Critique`, `AestheticScore`, or `Violation` data models
- New CLI entry points or changes to existing CLI flag names

## What We Will Decline

- Code generation features (eigenhelm is an evaluation sidecar, not an agent)
- Changes that weaken the AGPL-3.0 license terms
- Contributions that introduce dependencies with GPL-incompatible licenses

---

## Development Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repo
git clone https://github.com/metacogdev/eigenhelm.git
cd eigenhelm

# Install with dev + serve extras
uv sync --extra dev --extra serve

# Run the test suite
uv run pytest

# Lint
uv run ruff check .
```

Tests are organized into three categories:

| Marker | Command | Purpose |
|--------|---------|---------|
| (none) | `uv run pytest tests/unit/` | Unit tests — fast, per-module |
| `contract` | `uv run pytest -m contract` | Interface invariant tests |
| `integration` | `uv run pytest -m integration` | End-to-end pipeline tests |

All three must pass before a PR can be merged.

---

## Pull Request Guidelines

1. **One concern per PR.** If you are fixing a bug and adding a feature, split them into
   separate PRs.
2. **Tests required.** Every bug fix must include a regression test. New functionality must
   include unit tests and, where appropriate, contract or integration tests.
3. **No breaking changes to public APIs** without prior issue discussion and maintainer approval.
4. **Commit messages** should follow the imperative mood: `fix: handle empty source in critic`
   not `Fixed empty source handling`.
5. **Ruff must pass.** Run `uv run ruff check .` locally before pushing.

---

## Reporting Bugs

Open a GitHub issue with:
- Python version and OS
- Minimal reproducible example (a failing test is ideal)
- Expected vs. actual behavior
- Any relevant tracebacks

---

## Security Issues

Do **not** open a public issue for security vulnerabilities. Email the maintainers directly
(see the repository security policy). We will respond within 48 hours.

---

## Commercial Licensing

If you want to use eigenhelm in a proprietary product or SaaS offering without complying with
AGPL-3.0 requirements, a commercial license is available.

Contact us at **licensing@eigenhelm.dev** to discuss terms.
