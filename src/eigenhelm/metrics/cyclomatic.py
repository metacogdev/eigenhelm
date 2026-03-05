"""Cyclomatic complexity via Lizard, normalized to density.

Reference: McCabe, T.J. (1976). A complexity measure.
           IEEE Transactions on Software Engineering, 2(4):308-320.

Density = v(G) / nloc  (complexity per non-comment line of code)

Lizard language detection is driven by the filename extension supplied to
analyze_source_code(). We derive the extension from our language_map.
"""

from __future__ import annotations

import lizard

from eigenhelm.models import CyclomaticMetrics
from eigenhelm.parsers.language_map import get_extension


def compute(source: str, language: str, name: str = "<snippet>") -> CyclomaticMetrics:
    """Compute Cyclomatic Complexity and density for a source code unit.

    Args:
        source: Raw source code string for the code unit.
        language: Language identifier (e.g., "python").
        name: Human-readable name for the unit (used in Lizard filename).

    Returns:
        CyclomaticMetrics with complexity, nloc, and density.
    """
    ext = get_extension(language)
    synthetic_filename = f"snippet{ext}"

    result = lizard.analyze_file.analyze_source_code(synthetic_filename, source)
    funcs = result.function_list

    if not funcs:
        # No functions found — treat entire snippet as one unit.
        nloc = result.nloc or max(1, source.count("\n") + 1)
        return CyclomaticMetrics(complexity=1, nloc=nloc, density=1.0 / nloc)

    # Aggregate across all functions in the snippet.
    total_cc = sum(f.cyclomatic_complexity for f in funcs)
    total_nloc = sum(f.nloc for f in funcs)

    if total_nloc == 0:
        total_nloc = 1

    density = total_cc / total_nloc

    return CyclomaticMetrics(
        complexity=total_cc,
        nloc=total_nloc,
        density=density,
    )
