# Pre-commit Hook

eigenhelm provides a [pre-commit](https://pre-commit.com/) hook that evaluates staged files before each commit.

## Setup

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/metacogdev/eigenhelm
    rev: v0.4.0
    hooks:
      - id: eigenhelm-check
```

Then install:

```bash
pre-commit install
```

## What it does

On each commit, `eigenhelm-check` evaluates all staged files against the configured model and thresholds. If any file scores above the reject threshold, the commit is blocked.

## Configuration

The hook reads from `.eigenhelm.toml` in your project root. The most relevant settings:

```toml
[thresholds]
accept = 0.3
reject = 0.7
```

To make the hook stricter or more lenient, adjust these thresholds.

## Skipping the hook

For exceptional cases:

```bash
git commit --no-verify -m "emergency fix"
```

## Caching

The hook caches results by file content hash. Re-committing an unchanged file skips re-evaluation, making subsequent commits fast.
