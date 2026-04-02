# Why eigenhelm

CodeRabbit, Copilot code review, and similar tools use LLMs to read your code and offer
suggestions. They catch real bugs and give useful advice. eigenhelm does something different.

## The problem with LLM-only review

LLM reviewers operate on text. They read code the way a human does — scanning for patterns,
reasoning about intent, generating natural-language feedback. This works well for logic errors,
naming, documentation, and security smells. It does not work well for:

- **Structural quality.** Is this file doing too many things? Is the complexity distributed
  well or concentrated in one function? An LLM can guess, but it's reasoning from vibes,
  not measurement.

- **Consistency across a codebase.** LLM reviews typically operate per-PR without a stable
  project-wide structural baseline. Some tools ingest repo context, but none produce a
  comparable numeric score across runs. Each review is an independent opinion.

- **Determinism.** Run the same LLM review twice and you'll get different comments. Change the
  prompt and the severity shifts. There is no stable baseline to track over time.

- **Agent self-review.** When a coding agent generates code and an LLM reviews it, you have
  one language model checking another's work. The failure modes correlate. Both struggle with
  the same blind spots — verbose boilerplate that reads fine but is structurally degenerate,
  copy-paste patterns that pass a logic check but compress poorly.

## What eigenhelm measures instead

eigenhelm doesn't read your code. It parses the AST, extracts a 69-dimensional structural
fingerprint, and projects it into an eigenspace trained on curated high-quality corpora.
The score comes from five dimensions:

| Dimension | What it catches |
|-----------|----------------|
| **Manifold drift** | Code that is structurally unlike anything in the training corpus |
| **Manifold alignment** | Code that drifts along the wrong axes of variation |
| **Token entropy** | Repetitive, low-information-density code (or chaotic, over-compressed code) |
| **Compression structure** | Poor structural regularity — the opposite of elegant |
| **NCD exemplar distance** | Code that is dissimilar to the nearest high-quality example |

None of these require understanding what the code does. They measure **how it's built** —
the same properties that experienced engineers sense intuitively but can't articulate in
a linter rule.

## Complementary, not competing

The right setup is both, not either/or:

```
                    ┌─────────────┐
   Agent writes     │  eigenhelm  │   Structural gate
   code ──────────► │  (AST +     │──► accept / marginal / reject
                    │   math)     │   + directives → agent fixes
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
   PR opened        │  CodeRabbit │   Logic + intent review
   ──────────────► │  (LLM)      │──► comments → human reviews
                    └─────────────┘
```

eigenhelm runs first, in the inner loop. It gives the agent fast, deterministic feedback
before a human ever sees the code. CodeRabbit runs second, on the PR, where its strengths —
contextual reasoning, security analysis, documentation suggestions — add the most value.

## Concrete differences

| | eigenhelm | LLM reviewer |
|---|---|---|
| **Input** | AST structure (69-dim vector) | Source text |
| **Deterministic** | Yes — same code, same score, every time | No |
| **Trainable on your corpus** | Yes — `eh train` on your best code | No (prompt tuning only) |
| **Hard CI gate** | Yes — with calibrated thresholds | Suggestions only |
| **Tracks quality over time** | Yes — scores are comparable across runs | No stable metric |
| **Agent-proof** | Yes — can't be talked past | Susceptible to plausible-sounding code |
| **Catches logic bugs** | No | Yes |
| **Reviews naming/docs** | No | Yes |
| **Cost per evaluation** | Zero (local, no API calls) | Per-token LLM cost |

## Why structure matters — not just aesthetics

The most common objection to code quality tooling is: "it works, tests pass, ship it."
That's a reasonable position for human-authored code at human pace. It breaks down with
agent-generated code for three reasons.

**Structural complexity predicts defects.** This isn't opinion — it's one of the most
replicated findings in empirical software engineering. Modules with high cyclomatic density,
concentrated Halstead effort, and low structural regularity produce more post-merge defects.
The 75-line function that "works fine" is the one that breaks when requirements change,
because every change touches every branch.

**Agents generate debt at machine speed.** A human writing 200 lines per day accumulates
structural debt slowly enough that review catches it. An agent writing 2,000 lines per
hour doesn't give you that buffer. Without measurement, you won't notice the drift until
the cost of changing the code exceeds the cost of rewriting it.

**Review doesn't scale to agent output.** A team that carefully reviews a 50-line diff
cannot maintain the same rigor across ten 500-line agent PRs per day. The human eye
glazes over. Structural issues that would have been caught in a small diff pass
unnoticed in a large one. This is the gap where quality silently erodes.

**The fix is cheapest early.** An agent that receives a `[high] reduce_complexity` directive
and refactors before the PR exists costs seconds of compute. The same structural problem
discovered six months later during an incident costs days of debugging and a production
outage. eigenhelm moves the feedback to where the cost of acting on it is nearly zero.

eigenhelm doesn't ask you to write perfect code. It doesn't gate on style or naming or
comment density. It measures structural properties that predict maintenance cost, and it
gives you a number so you can make informed tradeoffs instead of uninformed ones.

## The "prayers" part

Without structural measurement, the quality assurance process for AI-generated code is:

1. Agent writes code
2. Tests pass (necessary but insufficient — tests check behavior, not structure)
3. Human squints at the diff
4. Merge and hope

Step 3 doesn't scale. eigenhelm replaces hope with measurement. A score of 0.38 today
and 0.52 next month is a signal. When used as a CI gate, a reject classification can block
the merge before a human has to spend time on code that should have been caught automatically.

## When you don't need eigenhelm

- **Solo projects where you read every line.** If you're the only author and reviewer,
  your taste is the quality gate.
- **Generated code that won't be maintained.** One-off scripts, prototypes, throwaway
  experiments — score them if you're curious, don't gate on them.
- **Codebases with no quality baseline.** If you don't know what "good" looks like for your
  project yet, start with a language model and `eh train` later when you have exemplars.
