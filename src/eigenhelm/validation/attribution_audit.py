"""Attribution accuracy measurement for directive validation.

Collects directives from evaluations, loads human annotations,
and computes precision metrics.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DirectiveRecord:
    """A single directive produced during evaluation."""

    file_path: str
    directive_index: int
    category: str
    dimension: str
    severity: str


@dataclass(frozen=True)
class AttributionPrecision:
    """Precision metrics for directive accuracy."""

    total: int
    accurate: int
    partial: int
    inaccurate: int
    unannotated: int

    @property
    def precision(self) -> float:
        """Fraction of annotated directives that are accurate or partially accurate."""
        annotated = self.accurate + self.partial + self.inaccurate
        if annotated == 0:
            return 0.0
        return (self.accurate + self.partial) / annotated

    @property
    def strict_precision(self) -> float:
        """Fraction of annotated directives that are fully accurate."""
        annotated = self.accurate + self.partial + self.inaccurate
        if annotated == 0:
            return 0.0
        return self.accurate / annotated


class AttributionAudit:
    """Measure directive accuracy against human annotations.

    Workflow:
    1. Collect directives from evaluation results
    2. Generate an annotation template (JSON with null ratings)
    3. Human fills in ratings (accurate/partial/inaccurate)
    4. Load annotations and compute precision
    """

    def collect_directives(
        self,
        evaluations: list,
    ) -> list[DirectiveRecord]:
        """Extract directive records from FileEvaluation results."""
        records: list[DirectiveRecord] = []
        for ev in evaluations:
            for idx, cat in enumerate(ev.directive_categories):
                records.append(
                    DirectiveRecord(
                        file_path=ev.file_path,
                        directive_index=idx,
                        category=cat,
                        dimension="",  # populated from full attribution if available
                        severity="",
                    )
                )
        return records

    def generate_annotation_template(
        self,
        directives: list[DirectiveRecord],
        output_path: Path,
    ) -> None:
        """Write an annotation template JSON for human review.

        The template has all directives pre-filled with rating=null.
        Reviewers fill in: "accurate", "partial", or "inaccurate".
        """
        entries = []
        for dr in directives:
            entries.append(
                {
                    "file_path": dr.file_path,
                    "directive_index": dr.directive_index,
                    "category": dr.category,
                    "rating": None,  # to be filled by reviewer
                    "rater": None,
                }
            )
        output_path.write_text(json.dumps(entries, indent=2))

    def load_annotations(self, path: Path) -> dict[tuple[str, int], list[str]]:
        """Load human annotations from JSON.

        Supports multiple raters per directive. Returns mapping of
        (file_path, directive_index) -> [rating1, rating2, ...].
        """
        data = json.loads(path.read_text())
        annotations: dict[tuple[str, int], list[str]] = {}
        for entry in data:
            if entry.get("rating") is not None:
                key = (entry["file_path"], entry["directive_index"])
                annotations.setdefault(key, []).append(entry["rating"])
        return annotations

    def compute_precision(
        self,
        directives: list[DirectiveRecord],
        annotations: dict[tuple[str, int], list[str]],
    ) -> AttributionPrecision:
        """Compute precision from directives and human annotations.

        When multiple raters exist for a directive, uses majority vote.
        """
        accurate = partial = inaccurate = unannotated = 0

        for dr in directives:
            key = (dr.file_path, dr.directive_index)
            ratings = annotations.get(key)
            if not ratings:
                unannotated += 1
                continue
            # Majority vote across raters
            rating = max(set(ratings), key=ratings.count)
            if rating == "accurate":
                accurate += 1
            elif rating == "partial":
                partial += 1
            elif rating == "inaccurate":
                inaccurate += 1
            else:
                unannotated += 1

        return AttributionPrecision(
            total=len(directives),
            accurate=accurate,
            partial=partial,
            inaccurate=inaccurate,
            unannotated=unannotated,
        )

    def compute_inter_rater_kappa(
        self,
        annotations: dict[tuple[str, int], list[str]],
    ) -> float | None:
        """Compute Cohen's kappa for inter-rater agreement.

        Only considers directives with exactly 2 ratings.
        Collapses to binary: accurate+partial vs inaccurate.
        Returns None if insufficient paired data.
        """
        paired = [ratings for ratings in annotations.values() if len(ratings) == 2]
        if len(paired) < 5:
            return None

        # Binary: 1 = accurate/partial, 0 = inaccurate
        def _binary(r: str) -> int:
            return 1 if r in ("accurate", "partial") else 0

        r1 = [_binary(p[0]) for p in paired]
        r2 = [_binary(p[1]) for p in paired]

        # Cohen's kappa
        n = len(paired)
        agreement = sum(1 for a, b in zip(r1, r2) if a == b)
        p_o = agreement / n  # observed agreement

        p1_pos = sum(r1) / n
        p2_pos = sum(r2) / n
        p_e = p1_pos * p2_pos + (1 - p1_pos) * (1 - p2_pos)  # expected agreement

        if p_e == 1.0:
            return 1.0
        return (p_o - p_e) / (1 - p_e)
