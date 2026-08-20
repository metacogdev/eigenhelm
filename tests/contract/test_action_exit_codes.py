"""Exit-code contract for the eigenhelm GitHub Action's `evaluate` step.

The action's `Run evaluation` step (``action.yml``, ``id: evaluate``) is a bash
script that invokes ``eh evaluate`` three times (Pass 1: JSON, Pass 2: the
user-requested format, Pass 3: SARIF for Code Scanning). Issue #66: Pass 2
treated any non-zero exit from its own invocation -- including the ordinary
warn(1)/reject(2) quality decisions -- as a hard crash, fatal-exiting 3 before
the fail-on policy block ran and before Pass 3 populated ``sarif-file``.

These tests extract the *real* ``run:`` script from ``action.yml`` (so they
stay in sync with it), substitute the GitHub-expression placeholders that
GitHub would render, stub ``eh`` to emit format-appropriate output with a
controlled exit code, and assert the script's behaviour across the
accept/warn/reject/crack matrix -- in particular that warn/reject no longer
short-circuit the fail-on policy or skip SARIF upload.
"""

from __future__ import annotations

import os
import re
import subprocess
import textwrap
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
ACTION_FILE = REPO_ROOT / "action.yml"

# bash with -eo pipefail -- the shell GitHub Actions uses for `shell: bash`.
BASH_OPTS = ["-eo", "pipefail"]


def _evaluate_script() -> str:
    """Extract the ``id: evaluate`` step's ``run:`` body from action.yml.

    GitHub substitutes ``${{ ... }}`` expressions before bash runs, so we do
    the same: replace every ``${{ ... }}`` with an empty string (the evaluate
    step's only such expression is ``steps.resolve-diff.outputs.range``, which
    being empty means "evaluate all files" -- exactly the no-diff path we want
    to exercise).
    """
    action = yaml.safe_load(ACTION_FILE.read_text())
    step = next(s for s in action["runs"]["steps"] if s.get("id") == "evaluate")
    script = step["run"]
    return re.sub(r"\$\{\{[^}]*\}\}", "", script)


def _write_eh_stub(bin_dir: Path) -> Path:
    """Write a stub `eh` that emits format-appropriate output and exits EH_STUB_EXIT."""
    stub = bin_dir / "eh"
    stub.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            # Stub eigenhelm CLI for action.yml exit-code contract tests.
            code="${EH_STUB_EXIT:-0}"
            case "$code" in
              0) d="accept" ;; 1) d="warn" ;; 2) d="reject" ;; *) d="reject" ;;
            esac
            # A real crash (3) produces no clean output -- mimic that.
            if [ "$code" -eq 3 ] || [ -n "${EH_STUB_EMPTY:-}" ]; then
              exit "$code"
            fi
            fmt=""
            prev=""
            for a in "$@"; do
              if [ "$prev" = "--format" ]; then fmt="$a"; fi
              prev="$a"
            done
            case "$fmt" in
              json)
                printf '{"summary":{"mean_score":0.5,"total_files":1,"overall_decision":"%s"}}\\n' "$d"
                ;;
              sarif)
                printf '{"version":"2.1.0","$schema":"https://example.com","runs":[]}\\n'
                ;;
              *)
                printf 'human report: decision %s score 0.5\\n' "$d"
                ;;
            esac
            exit "$code"
            """
        )
    )
    stub.chmod(0o755)
    return stub


def _parse_outputs(output_file: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if output_file.exists():
        for line in output_file.read_text().splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                out[k] = v
    return out


def _run_action(
    tmp_path: Path,
    *,
    eh_exit: int,
    fail_on: str,
    fmt: str,
    sarif_upload: bool,
    empty: bool = False,
) -> tuple[int, dict[str, str], str, str]:
    """Run the real evaluate script with a stubbed `eh`; return (rc, outputs, stdout, stderr)."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_eh_stub(bin_dir)

    script_file = tmp_path / "evaluate.sh"
    script_file.write_text(_evaluate_script())

    runner_temp = tmp_path / "runner"
    runner_temp.mkdir()
    github_output = tmp_path / "github_output.txt"

    env = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ.get('PATH', '')}",
        "INPUT_MODEL": "",
        "INPUT_PATHS": ".",
        "INPUT_CLASSIFY": "true",
        "INPUT_STRICT": "false",
        "INPUT_LENIENT": "false",
        "INPUT_FORMAT": fmt,
        "INPUT_FAIL_ON": fail_on,
        "INPUT_SARIF_UPLOAD": "true" if sarif_upload else "false",
        "RUNNER_TEMP": str(runner_temp),
        "GITHUB_OUTPUT": str(github_output),
        "EH_STUB_EXIT": str(eh_exit),
    }
    if empty:
        env["EH_STUB_EMPTY"] = "1"

    proc = subprocess.run(
        ["bash", *BASH_OPTS, str(script_file)],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return proc.returncode, _parse_outputs(github_output), proc.stdout, proc.stderr


# ---------------------------------------------------------------------------
# Pass 2 human branch (the quality-gate's default path): warn/reject must not
# fatal-exit 3 ("failed to generate human output") -- the fail-on policy decides.
# ---------------------------------------------------------------------------


def test_warn_with_fail_on_reject_does_not_fail_step(tmp_path):
    rc, out, _, _ = _run_action(
        tmp_path, eh_exit=1, fail_on="reject", fmt="human", sarif_upload=True
    )
    assert rc == 0, "fail-on: reject must not fail the step on a warn (exit 1)"
    assert out["exit-code"] == "1"
    # Pass 3 must populate sarif-file on a warn so the upload runs (#66).
    assert "sarif-file" in out


def test_reject_with_fail_on_reject_fails_with_real_exit_code(tmp_path):
    rc, out, stdout, _ = _run_action(
        tmp_path, eh_exit=2, fail_on="reject", fmt="human", sarif_upload=True
    )
    assert rc == 2, "reject under fail-on: reject must exit 2, not a fabricated 3"
    assert out["exit-code"] == "2"
    assert "sarif-file" in out, "SARIF upload must run on a reject (#66)"
    assert "code rejected" in stdout


def test_reject_with_fail_on_never_succeeds(tmp_path):
    rc, out, _, _ = _run_action(
        tmp_path, eh_exit=2, fail_on="never", fmt="human", sarif_upload=False
    )
    assert rc == 0, "fail-on: never must mean never-fail, even on reject"
    assert out["exit-code"] == "2"
    assert "sarif-file" not in out


def test_warn_with_fail_on_warn_fails_exit_one(tmp_path):
    rc, out, stdout, _ = _run_action(
        tmp_path, eh_exit=1, fail_on="warn", fmt="human", sarif_upload=False
    )
    assert rc == 1
    assert out["exit-code"] == "1"
    assert "quality issues detected" in stdout


def test_accept_succeeds(tmp_path):
    rc, out, _, _ = _run_action(
        tmp_path, eh_exit=0, fail_on="reject", fmt="human", sarif_upload=True
    )
    assert rc == 0
    assert out["exit-code"] == "0"
    assert "sarif-file" in out


def test_crash_propagates_as_exit_three(tmp_path):
    rc, out, _, _ = _run_action(
        tmp_path, eh_exit=3, fail_on="reject", fmt="human", sarif_upload=True
    )
    assert rc == 3, "a runtime crash (exit 3) must still propagate"
    assert out["exit-code"] == "3"


def test_empty_human_output_on_warn_is_a_generation_failure(tmp_path):
    # warn exit but no rendered output -> genuine generation failure, exit 3.
    rc, _, _, _ = _run_action(
        tmp_path,
        eh_exit=1,
        fail_on="reject",
        fmt="human",
        sarif_upload=False,
        empty=True,
    )
    assert rc == 3


# ---------------------------------------------------------------------------
# No evaluable files: a clean exit (0) with empty output means the diff had
# no files to gate -- paths/exclude filtered everything, or only unrecognized
# extensions changed (release-please PRs touch only CHANGELOG.md /
# pyproject.toml; dependabot lockfile-only bumps). The gate must accept, not
# crash. (Reproduces the v0.10.2 release-please PR QG failure.)
# ---------------------------------------------------------------------------


def test_no_evaluable_files_succeeds(tmp_path):
    rc, out, _, _ = _run_action(
        tmp_path,
        eh_exit=0,
        fail_on="reject",
        fmt="human",
        sarif_upload=True,
        empty=True,
    )
    assert rc == 0, "no evaluable files (exit 0, empty output) must not crash"
    assert out["exit-code"] == "0"
    # Pass 3 produced no SARIF either -> upload step skipped, sarif-file unset.
    assert "sarif-file" not in out


def test_no_evaluable_files_sarif_format_succeeds(tmp_path):
    rc, out, _, _ = _run_action(
        tmp_path,
        eh_exit=0,
        fail_on="reject",
        fmt="sarif",
        sarif_upload=False,
        empty=True,
    )
    assert rc == 0, "format: sarif with no evaluable files must not crash"
    assert out["exit-code"] == "0"
    assert "sarif-file" not in out


# ---------------------------------------------------------------------------
# Pass 2 sarif branch: warn/reject must not fatal-exit 3 ("failed to generate
# SARIF"), and sarif-file must be populated so the upload step can run.
# ---------------------------------------------------------------------------


def test_sarif_format_reject_does_not_crash_and_sets_sarif_file(tmp_path):
    rc, out, _, _ = _run_action(
        tmp_path, eh_exit=2, fail_on="reject", fmt="sarif", sarif_upload=False
    )
    assert rc == 2, "format: sarif + reject must exit 2, not a fabricated 3 (#66)"
    assert out["exit-code"] == "2"
    assert "sarif-file" in out


def test_sarif_format_warn_with_fail_on_reject_succeeds(tmp_path):
    rc, out, _, _ = _run_action(
        tmp_path, eh_exit=1, fail_on="reject", fmt="sarif", sarif_upload=False
    )
    assert rc == 0
    assert out["exit-code"] == "1"
    assert "sarif-file" in out


# ---------------------------------------------------------------------------
# SARIF upload step: must be best-effort. A consumer repo can have
# `sarif-upload: true` without GitHub Code Scanning enabled (private repos,
# Enterprise without Advanced Security); the upload-sarif action then errors
# with "Code scanning is not enabled". That must not fail the whole job -- the
# accept/warn/reject decision is what gates, not the telemetry upload. (#66)
# ---------------------------------------------------------------------------


def test_sarif_upload_step_is_non_fatal():
    """The upload-sarif step must set continue-on-error so a disabled Code
    Scanning feature cannot fail the action's job."""
    action = yaml.safe_load(ACTION_FILE.read_text())
    upload = next(
        s
        for s in action["runs"]["steps"]
        if s.get("name") == "Upload SARIF to GitHub Code Scanning"
    )
    assert upload.get("continue-on-error") is True, (
        "SARIF upload must be continue-on-error so a repo without Code "
        "Scanning enabled does not fail the job (#66)"
    )
    assert upload.get("if") == (
        "inputs.sarif-upload == 'true' && steps.evaluate.outputs.sarif-file != ''"
    ), "upload should only run when sarif-file was populated"
