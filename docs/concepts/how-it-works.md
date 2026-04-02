# How It Works

eigenhelm evaluates code quality by measuring how closely a source file's structural properties resemble those found in curated, high-quality codebases.

## The pipeline

```
Source code
    │
    ▼
┌─────────────────────┐
│  Feature extraction  │  tree-sitter AST + Lizard metrics → 69-dim vector
│  (VirtueExtractor)   │  Halstead, cyclomatic, WL hash, structural features
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  PCA projection      │  Project into trained eigenspace
│  (EigenspaceModel)   │  Measure drift + alignment against quality manifold
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Structural scoring  │  5-dimension weighted score
│  (StructuralCritic)  │  Entropy, Birkhoff, NCD, drift, alignment
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Attribution         │  Map score to source locations
│  (Directives)        │  Generate actionable improvement suggestions
└─────────┬───────────┘
          │
          ▼
    Decision: accept / marginal / reject
```

## Feature extraction

eigenhelm parses source code using [tree-sitter](https://tree-sitter.github.io/) and extracts a **69-dimensional feature vector** per code unit:

- **Halstead metrics** (3 dims): volume, difficulty, effort
- **Cyclomatic metrics** (2 dims): complexity, density
- **Weisfeiler-Leman hash bins** (64 dims): AST structural fingerprint capturing the distribution of subtree shapes

The WL hash captures structural patterns — repetitive code, unusual nesting, idiomatic constructs — without depending on naming or formatting.

## Eigenspace projection

The feature vector is projected into a PCA eigenspace trained on high-quality open-source code. This projection yields two measurements:

- **Manifold drift**: How far the code sits from the quality manifold (reconstruction error)
- **Manifold alignment**: How well the code aligns with the principal quality directions

Low drift + high alignment = code that structurally resembles the best examples in the training corpus.

## Structural scoring

The final score combines five dimensions with preset weights (selected based on available data):

| Dimension | Weight | Source |
|-----------|--------|--------|
| Manifold drift | 0.30 | PCA reconstruction error |
| Manifold alignment | 0.30 | Projection onto quality axes |
| Token entropy | 0.15 | Shannon entropy of byte stream |
| Compression structure | 0.15 | Birkhoff aesthetic measure (zlib) |
| NCD exemplar distance | 0.10 | Compression distance to nearest exemplar |

The score is normalized to [0.0, 1.0] and compared against calibrated thresholds to produce a classification.

## Training

Models are trained on curated corpora of high-quality code:

1. Collect source files from high-quality repositories
2. Extract feature vectors for each file
3. Fit PCA to learn the quality manifold
4. Store exemplars for NCD comparison
5. Calibrate thresholds from the score distribution

See [`eh train`](../cli/train.md) for details on training custom models.
