"""Unified CLI for eigenhelm — invokable as `eigenhelm` or `eh`."""

from __future__ import annotations

import sys

import click


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(package_name="eigenhelm")
def cli() -> None:
    """eigenhelm — Software Poet Conscience."""


def _passthrough(module_path: str) -> click.Command:
    """Create a Click command that delegates to an argparse-based main()."""

    @click.command(
        context_settings={
            "ignore_unknown_options": True,
            "allow_extra_args": True,
        },
        add_help_option=False,
    )
    @click.pass_context
    def cmd(ctx: click.Context) -> None:
        import importlib

        mod = importlib.import_module(module_path)
        result = mod.main(ctx.args)
        if isinstance(result, int) and result != 0:
            sys.exit(result)

    return cmd


cli.add_command(_passthrough("eigenhelm.cli.evaluate"), "evaluate")
cli.add_command(_passthrough("eigenhelm.cli.train"), "train")
cli.add_command(_passthrough("eigenhelm.cli.inspect"), "inspect")
cli.add_command(_passthrough("eigenhelm.cli.serve"), "serve")
cli.add_command(_passthrough("eigenhelm.cli.harness"), "harness")
cli.add_command(_passthrough("eigenhelm.cli.corpus"), "corpus")
