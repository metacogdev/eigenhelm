"""eigenhelm model CLI — discover, download, and manage models."""

from __future__ import annotations

import sys

import click


@click.group("model")
def model() -> None:
    """Manage eigenhelm models."""


@model.command("list")
@click.option("--remote", is_flag=True, help="Show models from the remote registry.")
def list_models(remote: bool) -> None:
    """List available models."""
    if remote:
        _list_remote()
    else:
        _list_local()


@model.command("pull")
@click.argument("name")
@click.option("--force", is_flag=True, help="Re-download even if cached.")
def pull(name: str, force: bool) -> None:
    """Download a model from the registry."""
    from eigenhelm.registry import RegistryError, pull_model

    try:
        path = pull_model(name, force=force)
        click.echo(f"Downloaded {name} -> {path}")
    except RegistryError as exc:
        click.echo(f"ERROR: {exc}", err=True)
        sys.exit(1)


@model.command("info")
@click.argument("name")
def info(name: str) -> None:
    """Show metadata for a model (local or remote)."""
    from eigenhelm.eigenspace import load_model
    from eigenhelm.registry import resolve_model

    path = resolve_model(name)
    if path is None:
        click.echo(
            f"Model '{name}' not found locally. Try: eh model pull {name}", err=True
        )
        sys.exit(1)

    try:
        m = load_model(path)
    except Exception as exc:
        click.echo(f"ERROR: Failed to load {path}: {exc}", err=True)
        sys.exit(1)

    click.echo(f"Name:           {name}")
    click.echo(f"Path:           {path}")
    click.echo(f"Version:        {m.version}")
    click.echo(f"Components:     {m.n_components}")
    click.echo(f"Corpus hash:    {m.corpus_hash}")
    if m.language:
        click.echo(f"Language:       {m.language}")
    if m.corpus_class:
        click.echo(f"Corpus class:   {m.corpus_class}")
    if m.n_training_files:
        click.echo(f"Training files: {m.n_training_files}")
    if m.calibrated_accept is not None:
        click.echo(f"Accept thresh:  {m.calibrated_accept:.3f}")
    if m.calibrated_reject is not None:
        click.echo(f"Reject thresh:  {m.calibrated_reject:.3f}")
    if m.score_distribution:
        d = m.score_distribution
        click.echo(
            f"Score dist:     min={d.min:.2f} p25={d.p25:.2f} "
            f"median={d.median:.2f} p75={d.p75:.2f} max={d.max:.2f}"
        )


def _list_local() -> None:
    from eigenhelm.registry import list_local

    models = list_local()
    if not models:
        click.echo("No models found. Try: eh model pull <name>")
        return

    click.echo(f"{'Name':<30s} {'Source':<10s} Path")
    click.echo("-" * 70)
    for m in models:
        source = "bundled" if m.bundled else "cached"
        click.echo(f"{m.name:<30s} {source:<10s} {m.path}")


def _list_remote() -> None:
    from eigenhelm.registry import RegistryError, list_remote

    try:
        models = list_remote()
    except RegistryError as exc:
        click.echo(f"ERROR: {exc}", err=True)
        sys.exit(1)

    if not models:
        click.echo("No models in registry.")
        return

    click.echo(f"{'Name':<30s} {'Lang':<12s} {'Class':<6s} {'PCs':<5s} {'Size':<8s}")
    click.echo("-" * 65)
    for m in models:
        size = _fmt_size(m.size_bytes)
        click.echo(
            f"{m.name:<30s} {m.language:<12s} {m.corpus_class:<6s} {m.n_components:<5d} {size:<8s}"
        )


def _fmt_size(n: int) -> str:
    if n < 1024:
        return f"{n}B"
    if n < 1024 * 1024:
        return f"{n // 1024}K"
    return f"{n // (1024 * 1024)}M"
