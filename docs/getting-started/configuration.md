# Configuration

eigenhelm uses `.eigenhelm.toml` for project-level configuration. Run `eh init` to generate a starter file.

## Threshold hierarchy

Settings are resolved in priority order:

1. **CLI flags** (`--accept-threshold`, `--reject-threshold`, `--strict`, `--lenient`)
2. **Config file** (`.eigenhelm.toml`)
3. **Model calibration** (empirical p25/p75 from training corpus)
4. **Hardcoded defaults** (accept=0.4, reject=0.6)

## Full config reference

```toml
# .eigenhelm.toml

# Path to a pre-trained eigenspace model (.npz)
# model = "models/eigenspace.npz"

# Default language override for all files
# language = "python"

# Glob patterns for files/directories to skip during evaluation
# exclude = ["vendor/**", "*_pb2.py", "src/generated/**"]

# Global accept/reject thresholds
[thresholds]
accept = 0.3
reject = 0.7

# Treat all "warn" decisions as "reject" (useful for strict CI)
# strict = false

# Path-specific threshold overrides (last-match-wins)
[[paths]]
glob = "src/core/**"
[paths.thresholds]
accept = 0.3
reject = 0.5

[[paths]]
glob = "vendor/**"
[paths.thresholds]
accept = 0.6
reject = 0.9

# Map non-standard extensions to language keys
[language_overrides]
".jsx" = "javascript"
".tsx" = "typescript"
```

## Models

eigenhelm ships with bundled models for common use cases:

| Model | Languages | Use case |
|-------|-----------|----------|
| `general-polyglot-v1.npz` | Python, JS, TS, Go, Rust | General-purpose polyglot evaluation |
| `lang-python.npz` | Python | Python-specific evaluation |
| `lang-javascript.npz` | JavaScript | JavaScript-specific evaluation |
| `lang-typescript.npz` | TypeScript | TypeScript-specific evaluation |
| `lang-go.npz` | Go | Go-specific evaluation |
| `lang-rust.npz` | Rust | Rust-specific evaluation |

When no model is specified, eigenhelm uses the bundled polyglot model.

## Strict and lenient modes

```bash
# Strict: marginal → reject (exit code 1)
eh evaluate src/ --strict

# Lenient: marginal → accept (exit code 0)
eh evaluate src/ --lenient
```

In CI, `--strict` is recommended to prevent marginal code from merging. Note: `--strict` maps marginal to exit code 2 (same as reject), not exit code 1.

## Excluding files

### `.eigenhelm.toml`

Add glob patterns to the `exclude` array:

```toml
exclude = ["vendor/**", "*_pb2.py", "src/generated/**"]
```

Patterns use `fnmatch` syntax and match against paths relative to the evaluated directory.

### `.eigenhelmignore`

Place a `.eigenhelmignore` file in the project root with one pattern per line:

```gitignore
# Generated protobuf code
*_pb2.py

# Vendored dependencies
vendor/**
```

Lines starting with `#` are comments. Blank lines are ignored.

Both methods can be combined — patterns from all sources are merged with the built-in defaults (`.git`, `__pycache__`, `node_modules`, `.venv`, `dist`, `build`).
