"""Real-world use case benchmark harness.

Evaluates source files from real projects, categorizes them by type,
computes per-category score distributions, and produces structured
benchmark reports with quality target tracking.
"""

from __future__ import annotations

import subprocess
import tomllib
from datetime import date
from pathlib import Path

import numpy as np

from eigenhelm.helm import DynamicHelm
from eigenhelm.helm.models import EvaluationRequest
from eigenhelm.parsers.language_map import LANGUAGE_MAP
from eigenhelm.validation.categorize import categorize_file
from eigenhelm.validation.usecase_models import (
    BenchmarkReport,
    CategoryDistribution,
    CommitReplayResult,
    DimensionDiscrimination,
    FileCategory,
    FileEvaluation,
    QualityTarget,
    RegressionAlert,
)

# Extension → language mapping
_EXT_TO_LANG: dict[str, str] = {ext: lang for lang, (_, ext) in LANGUAGE_MAP.items()}

_DIMENSIONS: tuple[str, ...] = (
    "manifold_drift",
    "manifold_alignment",
    "token_entropy",
    "compression_structure",
    "ncd_exemplar_distance",
)

_DISCOVERY_SKIP_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "node_modules",
        ".pytest_cache",
        "dist",
        "build",
        ".tox",
        ".eggs",
    }
)


def sync_corpus(manifest_path: Path, target_dir: Path) -> list[dict]:
    """Clone or update projects listed in a corpus manifest.

    Args:
        manifest_path: Path to the TOML corpus manifest.
        target_dir: Directory to clone projects into.

    Returns:
        List of project dicts from the manifest.
    """
    with open(manifest_path, "rb") as f:
        manifest = tomllib.load(f)

    projects = manifest.get("projects", [])
    target_dir.mkdir(parents=True, exist_ok=True)

    for project in projects:
        name = project["name"]
        url = project["url"]
        commit = project.get("commit")
        project_dir = target_dir / name

        if project_dir.exists():
            continue  # already cloned

        subprocess.run(
            ["git", "clone", "--depth", "1", url, str(project_dir)],
            check=True,
            capture_output=True,
        )

        if commit:
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(project_dir),
                    "fetch",
                    "--depth",
                    "1",
                    "origin",
                    commit,
                ],
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(project_dir), "checkout", "FETCH_HEAD"],
                capture_output=True,
            )

    return projects


def _discover_source_files(
    project_dir: Path, src_dir: str | None = None
) -> list[tuple[Path, str]]:
    """Discover evaluable source files in a project."""
    root = project_dir / src_dir if src_dir else project_dir
    if not root.is_dir():
        root = project_dir

    results: list[tuple[Path, str]] = []

    import os

    for dirpath, dirs, files in os.walk(root, followlinks=False):
        _prune_discovery_dirs(dirs)
        for filename in files:
            child, lang = _source_file_in_dir(dirpath, filename)
            if lang is not None and child is not None:
                results.append((child, lang))

    return results


def _prune_discovery_dirs(dirs: list[str]) -> None:
    dirs[:] = [
        d for d in dirs if d not in _DISCOVERY_SKIP_DIRS and not d.endswith(".egg-info")
    ]


def _source_file_in_dir(dirpath: str, filename: str) -> tuple[Path | None, str | None]:
    child = Path(dirpath) / filename
    if child.is_symlink():
        return None, None
    return child, _EXT_TO_LANG.get(child.suffix)


def _compute_distribution(
    scores: list[float], category: FileCategory
) -> CategoryDistribution:
    """Compute 7-point score distribution for a file category."""
    arr = np.array(scores)
    return CategoryDistribution(
        category=category,
        n_files=len(scores),
        min=float(np.min(arr)),
        p10=float(np.percentile(arr, 10)),
        p25=float(np.percentile(arr, 25)),
        median=float(np.median(arr)),
        p75=float(np.percentile(arr, 75)),
        p90=float(np.percentile(arr, 90)),
        max=float(np.max(arr)),
    )


def _signal_quality_label(d: float | None) -> str:
    """Map Cohen's d to a signal quality label."""
    if d is None:
        return "noise"
    if abs(d) > 0.8:
        return "strong"
    if abs(d) > 0.5:
        return "medium"
    if abs(d) > 0.2:
        return "weak"
    return "noise"


def _compute_dimension_discrimination(
    evaluations: list[FileEvaluation],
) -> list[DimensionDiscrimination]:
    """Compute per-dimension discrimination metrics across file categories.

    For each dimension x category pair: compute CV within category.
    For implementation files: split by score median and compute Cohen's d.
    """
    results: list[DimensionDiscrimination] = []
    for cat in FileCategory:
        cat_evals = _category_evaluations(evaluations, cat)
        if len(cat_evals) < 2:
            continue
        results.extend(_dimension_metric(cat_evals, dim, cat) for dim in _DIMENSIONS)
    return results


def _category_evaluations(
    evaluations: list[FileEvaluation], category: FileCategory
) -> list[FileEvaluation]:
    return [e for e in evaluations if e.category == category]


def _dimension_metric(
    evaluations: list[FileEvaluation],
    dim: str,
    category: FileCategory,
) -> DimensionDiscrimination:
    scores = [e.dim_scores.get(dim, 0.0) for e in evaluations]
    arr = np.array(scores)
    mean = float(np.mean(arr))
    std = float(np.std(arr))
    cohens_d = _dimension_cohens_d(evaluations, scores, category)
    return DimensionDiscrimination(
        dimension=dim,
        category=category,
        cohens_d=cohens_d,
        cv=std / mean if mean > 0 else 0.0,
        mean=mean,
        std=std,
        signal_quality=_signal_quality_label(cohens_d),
    )


def _dimension_cohens_d(
    evaluations: list[FileEvaluation],
    scores: list[float],
    category: FileCategory,
) -> float | None:
    if category != FileCategory.IMPLEMENTATION or len(evaluations) < 10:
        return None

    median_score = float(np.median([e.score for e in evaluations]))
    low_group, high_group = _split_dimension_scores(evaluations, scores, median_score)
    if len(low_group) < 2 or len(high_group) < 2:
        return None

    return _cohens_d(low_group, high_group)


def _split_dimension_scores(
    evaluations: list[FileEvaluation], scores: list[float], median_score: float
) -> tuple[list[float], list[float]]:
    low_group = [s for e, s in zip(evaluations, scores) if e.score <= median_score]
    high_group = [s for e, s in zip(evaluations, scores) if e.score > median_score]
    return low_group, high_group


def _cohens_d(low_group: list[float], high_group: list[float]) -> float | None:
    mean_low = np.mean(low_group)
    mean_high = np.mean(high_group)
    pooled_std = np.sqrt(
        (
            np.var(low_group) * (len(low_group) - 1)
            + np.var(high_group) * (len(high_group) - 1)
        )
        / (len(low_group) + len(high_group) - 2)
    )
    if pooled_std <= 0:
        return None
    return float((mean_high - mean_low) / pooled_std)


def compute_fp_fn(
    good_evals: list[FileEvaluation],
    bad_evals: list[FileEvaluation],
    impl_only: bool = False,
) -> tuple[float | None, float | None]:
    """Compute false positive and false negative rates.

    FP = fraction of good files with decision="reject".
    FN = fraction of bad files with decision="accept".

    Args:
        good_evals: Evaluations from known-good corpus.
        bad_evals: Evaluations from known-problematic corpus.
        impl_only: If True, filter to implementation files only.

    Returns:
        (fp_rate, fn_rate) — None if insufficient data.
    """
    if impl_only:
        good_evals = _implementation_only(good_evals)
        bad_evals = _implementation_only(bad_evals)

    return _decision_rate(good_evals, "reject"), _decision_rate(bad_evals, "accept")


def _implementation_only(evaluations: list[FileEvaluation]) -> list[FileEvaluation]:
    return [e for e in evaluations if e.category == FileCategory.IMPLEMENTATION]


def _decision_rate(evaluations: list[FileEvaluation], decision: str) -> float | None:
    if not evaluations:
        return None
    matches = sum(1 for e in evaluations if e.decision == decision)
    return matches / len(evaluations)


class UseCaseBenchmark:
    """Real-world use case benchmark harness.

    Evaluates files from registered projects, categorizes them,
    and produces a BenchmarkReport with per-category distributions
    and quality target tracking.

    Args:
        helm: Configured DynamicHelm instance.
        model_name: Name of the model file (for report metadata).
        model_version: Model version string (for report metadata).
    """

    def __init__(
        self,
        helm: DynamicHelm,
        model_name: str = "",
        model_version: str = "",
        corpus_version: str = "",
    ) -> None:
        self._helm = helm
        self._model_name = model_name
        self._model_version = model_version
        self._corpus_version = corpus_version
        self._projects: list[tuple[Path, str | None, str]] = []  # (dir, src_dir, name)

    def add_project(
        self, project_dir: Path, src_dir: str | None = None, name: str | None = None
    ) -> None:
        """Register a project directory for evaluation."""
        project_name = name or project_dir.name
        self._projects.append((project_dir, src_dir, project_name))

    def run(self) -> BenchmarkReport:
        """Execute the benchmark: discover → categorize → evaluate → aggregate."""
        evaluations: list[FileEvaluation] = []
        for project_dir, src_dir, project_name in self._projects:
            evaluations.extend(self._run_project(project_dir, src_dir, project_name))

        categories = _category_distributions(evaluations)
        dim_disc = _compute_dimension_discrimination(evaluations)
        targets = self._compute_targets(evaluations, categories, dim_disc)

        return BenchmarkReport(
            date=date.today().isoformat(),
            model=self._model_name,
            model_version=self._model_version,
            git_sha=_current_git_sha(),
            corpus_version=self._corpus_version,
            n_files=len(evaluations),
            n_projects=len(self._projects),
            categories=tuple(categories),
            dimension_discrimination=tuple(dim_disc),
            targets=tuple(targets),
            file_evaluations=tuple(evaluations),
        )

    def _run_project(
        self, project_dir: Path, src_dir: str | None, project_name: str
    ) -> list[FileEvaluation]:
        evaluations: list[FileEvaluation] = []
        for file_path, lang in _discover_source_files(project_dir, src_dir):
            evaluation = self._evaluate_file(project_dir, project_name, file_path, lang)
            if evaluation is not None:
                evaluations.append(evaluation)
        return evaluations

    def _evaluate_file(
        self,
        project_dir: Path,
        project_name: str,
        file_path: Path,
        lang: str,
    ) -> FileEvaluation | None:
        source = _read_source(file_path)
        if source is None:
            return None

        rel_path = str(file_path.relative_to(project_dir))
        try:
            response = self._helm.evaluate(
                EvaluationRequest(
                    source=source, language=lang, file_path=str(file_path)
                )
            )
        except Exception:
            return None

        n_directives, directive_cats = _directive_summary(response.attribution)
        return FileEvaluation(
            file_path=rel_path,
            project=project_name,
            category=categorize_file(rel_path, content=source),
            score=response.score,
            decision=response.decision,
            percentile=response.percentile,
            dim_scores=_dimension_scores(response.attribution),
            n_directives=n_directives,
            directive_categories=directive_cats,
        )

    def _compute_targets(
        self,
        evaluations: list[FileEvaluation],
        categories: list[CategoryDistribution],
        dim_disc: list[DimensionDiscrimination] | None = None,
    ) -> list[QualityTarget]:
        """Compute quality targets SC-001 through SC-003."""
        return [
            _file_count_target(evaluations),
            _impl_vs_init_gap_target(categories),
            _dimension_discrimination_target(dim_disc),
        ]


def _read_source(file_path: Path) -> str | None:
    try:
        return file_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def _dimension_scores(attribution) -> dict[str, float]:
    if not attribution:
        return {}
    return {dim.dimension: dim.normalized_score for dim in attribution.dimensions}


def _directive_summary(attribution) -> tuple[int, tuple[str, ...]]:
    if not attribution:
        return 0, ()
    return len(attribution.directives), tuple(
        d.category for d in attribution.directives
    )


def _category_distributions(
    evaluations: list[FileEvaluation],
) -> list[CategoryDistribution]:
    categories: list[CategoryDistribution] = []
    for cat in FileCategory:
        cat_scores = [e.score for e in evaluations if e.category == cat]
        if cat_scores:
            categories.append(_compute_distribution(cat_scores, cat))
    return categories


def _current_git_sha() -> str | None:
    try:
        sha_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
        )
    except (OSError, FileNotFoundError):
        return None
    if sha_result.returncode != 0:
        return None
    return sha_result.stdout.strip()


def _file_count_target(evaluations: list[FileEvaluation]) -> QualityTarget:
    return QualityTarget(
        name="sc_001_file_count",
        description="At least 500 evaluated files across 4+ categories",
        baseline=float(len(evaluations)),
        target=500.0,
        direction="higher_is_better",
    )


def _impl_vs_init_gap_target(categories: list[CategoryDistribution]) -> QualityTarget:
    impl_dist = _distribution_for(categories, FileCategory.IMPLEMENTATION)
    init_dist = _distribution_for(categories, FileCategory.INIT)
    gap = init_dist.median - impl_dist.median if impl_dist and init_dist else None
    return QualityTarget(
        name="sc_002_impl_vs_init_gap",
        description="Implementation median score at least 0.15 lower than init median",
        baseline=gap,
        target=0.15,
        direction="higher_is_better",
    )


def _distribution_for(
    categories: list[CategoryDistribution], category: FileCategory
) -> CategoryDistribution | None:
    return next((c for c in categories if c.category == category), None)


def _dimension_discrimination_target(
    dim_disc: list[DimensionDiscrimination] | None,
) -> QualityTarget:
    impl_strong = _strong_impl_dimensions(dim_disc or [])
    return QualityTarget(
        name="sc_003_dimension_discrimination",
        description="At least 2 dimensions with Cohen's d > 0.5 for implementation files",
        baseline=float(impl_strong),
        target=2.0,
        direction="higher_is_better",
    )


def _strong_impl_dimensions(dim_disc: list[DimensionDiscrimination]) -> int:
    return sum(1 for dd in dim_disc if _is_strong_impl_dimension(dd))


def _is_strong_impl_dimension(dd: DimensionDiscrimination) -> bool:
    return (
        dd.category == FileCategory.IMPLEMENTATION
        and dd.cohens_d is not None
        and abs(dd.cohens_d) > 0.5
    )


def add_fp_fn_targets(
    report: BenchmarkReport,
    fp_rate: float | None,
    fn_rate: float | None,
) -> BenchmarkReport:
    """Attach FP/FN rates and SC-004/SC-005 targets to a report."""
    from dataclasses import replace

    new_targets = list(report.targets)
    new_targets.append(
        QualityTarget(
            name="sc_004_fp_rate",
            description="False positive rate on known-good impl files < 20%",
            baseline=fp_rate,
            target=0.20,
            direction="lower_is_better",
        )
    )
    new_targets.append(
        QualityTarget(
            name="sc_005_fn_rate",
            description="False negative rate on known-problematic files < 40%",
            baseline=fn_rate,
            target=0.40,
            direction="lower_is_better",
        )
    )
    return replace(report, fp_rate=fp_rate, fn_rate=fn_rate, targets=tuple(new_targets))


def add_replay_target(
    report: BenchmarkReport,
    noise_rate: float,
) -> BenchmarkReport:
    """Attach SC-007 replay noise rate target to a report."""
    from dataclasses import replace

    new_targets = list(report.targets)
    new_targets.append(
        QualityTarget(
            name="sc_007_noise_rate",
            description="CI replay noise rate < 6%",
            baseline=noise_rate,
            target=0.06,
            direction="lower_is_better",
        )
    )
    return replace(report, targets=tuple(new_targets))


def add_attribution_target(
    report: BenchmarkReport,
    precision: float | None,
) -> BenchmarkReport:
    """Attach SC-006 attribution precision target to a report."""
    from dataclasses import replace

    new_targets = list(report.targets)
    new_targets.append(
        QualityTarget(
            name="sc_006_attribution_precision",
            description="Directive precision >= 60%",
            baseline=precision,
            target=0.60,
            direction="higher_is_better",
        )
    )
    return replace(report, attribution_precision=precision, targets=tuple(new_targets))


def replay_commits(
    repo_path: Path,
    helm: DynamicHelm,
    n_commits: int = 50,
) -> list[CommitReplayResult]:
    """Replay eigenhelm evaluation against recent commits.

    For each of the last n_commits, discovers changed files via
    `git diff --name-only`, evaluates them, and records decisions.

    FP in replay context = flagged file with non-implementation category.

    Args:
        repo_path: Path to the git repository.
        helm: Configured DynamicHelm instance.
        n_commits: Number of recent commits to replay.

    Returns:
        List of CommitReplayResult, one per commit.
    """
    replay_results: list[CommitReplayResult] = []
    for sha in _resolve_commit_range(repo_path, n_commits):
        changed_files = _discover_range_files(repo_path, sha)
        evaluations = _evaluate_range(repo_path, helm, sha, changed_files)
        replay_results.append(_commit_replay_result(sha, evaluations))
    return replay_results


def _resolve_commit_range(repo_path: Path, n_commits: int) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repo_path), "log", f"--max-count={n_commits}", "--format=%H"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [s.strip() for s in result.stdout.strip().split("\n") if s.strip()]


def _discover_range_files(repo_path: Path, sha: str) -> list[str]:
    diff_result = subprocess.run(
        [
            "git",
            "-C",
            str(repo_path),
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            sha,
        ],
        capture_output=True,
        text=True,
    )
    return [f.strip() for f in diff_result.stdout.strip().split("\n") if f.strip()]


def _evaluate_range(
    repo_path: Path,
    helm: DynamicHelm,
    sha: str,
    changed_files: list[str],
) -> list[FileEvaluation]:
    evaluations: list[FileEvaluation] = []
    for rel_path in changed_files:
        evaluation = _evaluate_historical_file(repo_path, helm, sha, rel_path)
        if evaluation is not None:
            evaluations.append(evaluation)
    return evaluations


def _evaluate_historical_file(
    repo_path: Path,
    helm: DynamicHelm,
    sha: str,
    rel_path: str,
) -> FileEvaluation | None:
    lang = _EXT_TO_LANG.get(Path(rel_path).suffix)
    if lang is None:
        return None

    source = _show_file_at_commit(repo_path, sha, rel_path)
    if source is None:
        return None

    try:
        response = helm.evaluate(
            EvaluationRequest(source=source, language=lang, file_path=rel_path)
        )
    except Exception:
        return None

    return FileEvaluation(
        file_path=rel_path,
        project=repo_path.name,
        category=categorize_file(rel_path, content=source),
        score=response.score,
        decision=response.decision,
    )


def _show_file_at_commit(repo_path: Path, sha: str, rel_path: str) -> str | None:
    show_result = subprocess.run(
        ["git", "-C", str(repo_path), "show", f"{sha}:{rel_path}"],
        capture_output=True,
        text=True,
    )
    if show_result.returncode != 0:
        return None
    return show_result.stdout


def _commit_replay_result(
    sha: str, evaluations: list[FileEvaluation]
) -> CommitReplayResult:
    flagged = [e for e in evaluations if e.decision in ("warn", "reject")]
    fp_flagged = [e for e in flagged if e.category != FileCategory.IMPLEMENTATION]
    all_noise = len(flagged) > 0 and len(fp_flagged) == len(flagged)
    return CommitReplayResult(
        commit_sha=sha,
        n_files_changed=len(evaluations),
        n_flagged=len(flagged),
        n_false_positive=len(fp_flagged),
        all_noise=all_noise,
        file_results=tuple(evaluations),
    )


def compute_noise_rate(replays: list[CommitReplayResult]) -> float:
    """Compute fraction of commits where all flags were false positives."""
    if not replays:
        return 0.0
    noise_commits = sum(1 for r in replays if r.all_noise)
    return noise_commits / len(replays)


def compare_reports(
    current: BenchmarkReport,
    baseline: BenchmarkReport,
) -> list[RegressionAlert]:
    """Compare two benchmark reports and flag regressions.

    A regression is flagged when:
    - A target was previously met but now fails
    - A metric regressed by more than 10%
    """
    alerts: list[RegressionAlert] = []
    baseline_targets = {t.name: t for t in baseline.targets}
    for current_target in current.targets:
        prev = baseline_targets.get(current_target.name)
        if prev is None:
            continue
        target_alert = _target_regression_alert(current_target, prev)
        if target_alert is not None:
            alerts.append(target_alert)
            continue
        metric_alert = _metric_regression_alert(current_target, prev)
        if metric_alert is not None:
            alerts.append(metric_alert)

    return alerts


def _target_regression_alert(
    current_target: QualityTarget, previous_target: QualityTarget
) -> RegressionAlert | None:
    if not previous_target.met or current_target.met:
        return None
    return RegressionAlert(
        target_name=current_target.name,
        previous_value=previous_target.baseline,
        current_value=current_target.baseline,
        target_value=current_target.target,
        was_met=True,
        now_met=False,
        message=f"Target '{current_target.name}' regressed: was met, now failing",
    )


def _metric_regression_alert(
    current_target: QualityTarget, previous_target: QualityTarget
) -> RegressionAlert | None:
    change = _regression_change(current_target, previous_target)
    if change is None or change <= 0.10:
        return None
    return RegressionAlert(
        target_name=current_target.name,
        previous_value=previous_target.baseline,
        current_value=current_target.baseline,
        target_value=current_target.target,
        was_met=previous_target.met,
        now_met=current_target.met,
        message=f"Metric '{current_target.name}' regressed by {change:.0%}",
    )


def _regression_change(
    current_target: QualityTarget, previous_target: QualityTarget
) -> float | None:
    if previous_target.baseline is None or current_target.baseline is None:
        return None
    if previous_target.baseline == 0:
        return None
    if current_target.direction == "lower_is_better":
        return (current_target.baseline - previous_target.baseline) / abs(
            previous_target.baseline
        )
    return (previous_target.baseline - current_target.baseline) / abs(
        previous_target.baseline
    )
