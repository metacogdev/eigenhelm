# AI Agent Skills

eigenhelm publishes agent skills for coding assistants. When an agent loads the skill, it gains a structured protocol for evaluating and improving code quality — with guardrails that prevent over-iteration.

## Install the skill

=== "npx skills"

    ```bash
    npx skills add metacogdev/skills
    ```

=== "eigenhelm CLI"

    ```bash
    eh skill --install           # writes to .claude/skills/eigenhelm.md
    eh skill path/to/skill.md    # write to a specific file
    eh skill                     # print to stdout
    ```

=== "Manual"

    Copy the skill file to your agent's skills directory:

    ```bash
    # Claude Code
    mkdir -p .claude/skills && eh skill .claude/skills/eigenhelm.md

    # OpenCode
    mkdir -p .opencode/skills && eh skill .opencode/skills/eigenhelm.md
    ```

## What the skill enforces

The skill encodes five rules based on controlled testing:

1. **One pass, not a loop.** Evaluate once after writing a file. If reject, apply obvious fixes, re-evaluate once. Two passes maximum.

2. **Never sacrifice correctness for score.** If a directive suggests refactoring that would change behavior, skip it. A working reject is better than a broken marginal.

3. **Directives are suggestions, not commands.** `extract_repeated_logic` means "this region has structural repetition" — it doesn't mean you must extract. Sometimes repetition is the right choice.

4. **Tests gate, eigenhelm advises.** Run tests before and after any eigenhelm-motivated change. If a change breaks tests, revert it immediately.

5. **Marginal is an acceptable end state.** Do not iterate to improve a marginal score.

## Why these rules matter

In controlled benchmarks, we tested two approaches:

**Loop-until-accept** (old approach): An agent rewrote code repeatedly to chase a better score. It introduced a fatal algorithm bug while optimizing for structure — the topological sort ran backwards because the agent refactored it to lower the WL hash penalty.

**Skill contract** (current approach): The same agent, same spec, but following the rules above. It produced code rated 46% higher on design, robustness, and spec compliance by an independent reviewer — with zero correctness regressions.

### Benchmark results (3 scenarios, 6 builds)

| Category (out of 15) | With skill | Without | Improvement |
|---|---|---|---|
| Bugs (fewer = better) | 10 | 7 | +43% |
| Design | 12 | 9 | +33% |
| Robustness | 12 | 7 | +71% |
| Clarity | 13 | 10 | +30% |
| Spec Compliance | 10 | 6 | +67% |
| **Total (out of 75)** | **57** | **39** | **+46%** |

The eigenhelm agent won all 3 scenarios: CLI tool, data pipeline library, and message protocol.

## Agent workflow

```
1. Write code
2. Run tests → all pass
3. Run: eh evaluate src/mymodule.py --classify
4. Read output:
   - accept/marginal → done, move on
   - reject → read directives, apply obvious fixes
5. If you changed anything: run tests again
6. Re-evaluate once. Accept the result regardless.
7. Done. Two passes maximum.
```

## Directive reference

| Category | Meaning | Action |
|----------|---------|--------|
| `extract_repeated_logic` | Structural repetition detected in AST | Look for shared abstractions, but only if the repetition is logic, not data |
| `reduce_complexity` | High cyclomatic/Halstead metrics | Break up complex functions |
| `review_structure` | Code structure diverges from corpus norms | Informational — review but don't necessarily change |
| `review_token_distribution` | Unusual token entropy | Usually noise — ignore unless extreme |
| `improve_compression` | Low information density | May indicate boilerplate — review for opportunities to simplify |

## Declaration-aware behavior

eigenhelm automatically handles files that are primarily type definitions or data tables:

- **Pure type-definition files** (dataclasses, interfaces, structs): Skipped entirely — the WL hash signal is syntax noise.
- **Data table files** (const arrays, probability tables): Scored with dampened drift/alignment and `review_structure` directives instead of `extract_repeated_logic`. Output includes a `[declaration-heavy]` tag.
- **Barrel files** (`__init__.py`, `index.ts`, `mod.rs`): Skipped when >=80% imports/exports.

Agents don't need to handle these cases — eigenhelm filters them automatically.

## Example agent prompt

If you can't use a skill file, add this to your system prompt or project instructions:

```
After writing or modifying code, evaluate it with:
  eh evaluate <file> --classify

Rules:
- Only evaluate after tests pass
- accept or marginal → move on, do not iterate
- reject → read directives, apply what's obviously correct, re-evaluate ONCE
- Never rewrite working code to improve a score
- Two evaluation passes maximum per file
```
