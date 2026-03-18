"""eigenhelm init CLI command — generate a starter .eigenhelm.toml."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from eigenhelm.config.defaults import DEFAULT_CONFIG_TEMPLATE


@click.command("init")
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite existing .eigenhelm.toml if present.",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory to write .eigenhelm.toml into (default: current directory).",
)
def init(force: bool, output: Path | None) -> None:
    """Generate a starter .eigenhelm.toml with sensible defaults."""
    target_dir = (output or Path.cwd()).resolve()
    config_path = target_dir / ".eigenhelm.toml"
    eigenhelm_dir = target_dir / ".eigenhelm"
    gitignore_path = target_dir / ".gitignore"

    if config_path.exists() and not force:
        click.echo(
            f"ERROR: {config_path} already exists. Use --force to overwrite.",
            err=True,
        )
        sys.exit(1)

    # Write config template
    config_path.write_text(DEFAULT_CONFIG_TEMPLATE, encoding="utf-8")
    click.echo(f"Created {config_path}")

    # Create .eigenhelm/ directory for cache and other artifacts
    eigenhelm_dir.mkdir(exist_ok=True)
    click.echo(f"Created {eigenhelm_dir}/")

    # Append .eigenhelm/ to .gitignore if not already present
    _update_gitignore(gitignore_path)


def _update_gitignore(gitignore_path: Path) -> None:
    """Append '.eigenhelm/' to .gitignore if not already listed."""
    entry = ".eigenhelm/"
    if gitignore_path.exists():
        contents = gitignore_path.read_text(encoding="utf-8")
        if entry in contents.splitlines() or entry.rstrip("/") in contents.splitlines():
            return  # Already listed
        # Append entry
        separator = "\n" if contents and not contents.endswith("\n") else ""
        gitignore_path.write_text(contents + separator + entry + "\n", encoding="utf-8")
        click.echo(f"Updated {gitignore_path} (added {entry})")
    else:
        gitignore_path.write_text(entry + "\n", encoding="utf-8")
        click.echo(f"Created {gitignore_path} (added {entry})")
