#!/usr/bin/env python3
"""scopematrix — parse a bug-bounty program scope and answer in-scope questions.

Workflows:
  scopematrix parse SCOPE            summarize the scope file
  scopematrix check SCOPE ASSET...   verdict for each asset
  scopematrix batch SCOPE FILE       verdicts for a list of assets (one per line)

Everything runs locally on files you provide. No targets are contacted.
"""
from __future__ import annotations

import json
import pathlib
import sys

import click
from rich.console import Console
from rich.table import Table

from scopematrix.scope import Scope, ScopeError, check, summary

console = Console()


def _load(path: pathlib.Path) -> Scope:
    try:
        return Scope.parse(path.read_text(encoding="utf-8"))
    except (OSError, ScopeError) as exc:
        console.print(f"[red]error:[/red] {path}: {exc}")
        sys.exit(2)


@click.group()
def main() -> None:
    """Turn program scope definitions into structured in/out verdicts."""


@main.command("parse")
@click.argument("scope_file", type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path))
@click.option("--json-out", is_flag=True)
def parse_cmd(scope_file: pathlib.Path, json_out: bool) -> None:
    """Summarize SCOPE_FILE: counts by action and asset kind."""
    scope = _load(scope_file)
    info = summary(scope)
    if json_out:
        click.echo(json.dumps(info, indent=2))
        return
    table = Table(title=str(scope_file))
    table.add_column("action")
    table.add_column("kind")
    table.add_column("pattern")
    for e in scope.entries:
        action = "[green]+ include[/green]" if e.action == "include" else "[red]- exclude[/red]"
        table.add_row(action, e.kind, e.raw)
    console.print(table)
    console.print(f"{info['total']} entries: {info['includes']} include, "
                  f"{info['excludes']} exclude; kinds: {info['by_kind']}")


@main.command("check")
@click.argument("scope_file", type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path))
@click.argument("assets", nargs=-1, required=True)
@click.option("--json-out", is_flag=True)
def check_cmd(scope_file: pathlib.Path, assets: tuple[str, ...], json_out: bool) -> None:
    """Print an in-scope/out-of-scope verdict for each ASSET."""
    scope = _load(scope_file)
    verdicts = []
    for asset in assets:
        try:
            verdicts.append(check(scope, asset))
        except ScopeError as exc:
            console.print(f"[red]error:[/red] {exc}")
            sys.exit(2)
    if json_out:
        click.echo(json.dumps(verdicts, indent=2))
    else:
        for v in verdicts:
            color = "green" if v["verdict"] == "in-scope" else "red"
            console.print(f"[{color}]{v['verdict']:<13}[/] {v['asset']}  ({v['reason']})")
    if any(v["verdict"] != "in-scope" for v in verdicts):
        sys.exit(1)


@main.command("batch")
@click.argument("scope_file", type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path))
@click.argument("asset_list", type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path))
@click.option("--json-out", is_flag=True)
def batch_cmd(scope_file: pathlib.Path, asset_list: pathlib.Path, json_out: bool) -> None:
    """Check every line of ASSET_LIST against SCOPE_FILE; exit 1 if any is out."""
    scope = _load(scope_file)
    assets = [line.strip() for line in asset_list.read_text(encoding="utf-8").splitlines()
              if line.strip() and not line.strip().startswith("#")]
    if not assets:
        console.print("[red]error:[/red] asset list is empty")
        sys.exit(2)
    verdicts = [check(scope, a) for a in assets]
    out_of = [v for v in verdicts if v["verdict"] != "in-scope"]
    if json_out:
        click.echo(json.dumps({"checked": len(verdicts), "out_of_scope": len(out_of),
                               "verdicts": verdicts}, indent=2))
    else:
        for v in verdicts:
            color = "green" if v["verdict"] == "in-scope" else "red"
            console.print(f"[{color}]{v['verdict']:<13}[/] {v['asset']}")
        console.print(f"{len(verdicts)} checked, {len(out_of)} out of scope")
    if out_of:
        sys.exit(1)


if __name__ == "__main__":
    main()