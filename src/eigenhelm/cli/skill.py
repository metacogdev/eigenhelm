"""eigenhelm skill CLI — install or print the agent skill file."""

from __future__ import annotations

import sys
from importlib import resources
from pathlib import Path

import click


def _load_skill() -> str:
    """Load the bundled skill.md content."""
    ref = resources.files("eigenhelm").joinpath("skill.md")
    return ref.read_text(encoding="utf-8")


@click.command("skill")
@click.argument("target", required=False, default=None)
@click.option(
    "--install",
    is_flag=True,
    default=False,
    help="Write to .claude/skills/eigenhelm.md in the target directory.",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite existing skill file.",
)
def skill(target: str | None, install: bool, force: bool) -> None:
    """Print or install the eigenhelm agent skill file.

    \b
    Usage:
      eh skill                    # print to stdout
      eh skill path/to/skill.md   # write to a specific file
      eh skill --install          # write to .claude/skills/eigenhelm.md
      eh skill --install --force  # overwrite existing
    """
    content = _load_skill()

    if not install and target is None:
        # Print to stdout
        click.echo(content)
        return

    if install:
        dest = Path(target) if target else Path.cwd()
        if dest.is_file():
            click.echo(
                "ERROR: --install target must be a directory, not a file.", err=True
            )
            sys.exit(1)
        out_path = dest / ".claude" / "skills" / "eigenhelm.md"
    else:
        out_path = Path(target)

    if out_path.exists() and not force:
        click.echo(
            f"ERROR: {out_path} already exists. Use --force to overwrite.",
            err=True,
        )
        sys.exit(1)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    click.echo(f"Installed skill to {out_path}")
