from __future__ import annotations
import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from .dashboard import generate_dashboard, generate_regression_dashboard
from .providers.claude import ClaudeProvider
from .runner import SuiteRunner
from .suite_loader import load_suite
from .tracker import ResultTracker

console = Console()


@click.group()
def main() -> None:
    """redteam-eval: LLM red-teaming and eval for high-stakes government/regulatory use cases."""


@main.command()
@click.argument("suite_path")
@click.option("--model", default=None, help="Override suite model (e.g. claude-haiku-4-5-20251001)")
@click.option("--verbose", "-v", is_flag=True, help="Print each case as it runs")
@click.option("--no-save", is_flag=True, help="Skip saving result to regression tracker")
@click.option("--api-key", envvar="ANTHROPIC_API_KEY", default=None, hidden=True)
def run(suite_path: str, model: str, verbose: bool, no_save: bool, api_key: str) -> None:
    """Run an eval suite against a model."""
    suite = load_suite(suite_path)
    if model:
        suite.model = model

    provider = ClaudeProvider(model=suite.model, api_key=api_key)
    runner = SuiteRunner(provider=provider)

    console.print(f"\n[bold]Suite:[/bold]  {suite.name}")
    console.print(f"[bold]Model:[/bold]  {suite.model}")
    console.print(f"[bold]Cases:[/bold]  {len(suite.cases)}\n")

    result = runner.run(suite, verbose=verbose)

    table = Table(title=f"Results — {result.pass_rate:.0%} pass rate ({result.pass_count}/{len(result.case_results)})")
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Score", width=6)
    table.add_column("Reason")
    table.add_column("ms", justify="right", style="dim")

    for cr in result.case_results:
        color = {"PASS": "green", "FAIL": "red", "WARN": "yellow", "ERROR": "dim"}.get(
            cr.score.value, "white"
        )
        table.add_row(
            cr.test_id,
            f"[{color}]{cr.score.value}[/{color}]",
            cr.reason[:90],
            str(cr.latency_ms),
        )

    console.print(table)

    if not no_save:
        tracker = ResultTracker()
        tracker.save(result)
        console.print(f"\n[dim]Saved · run ID: {result.run_id[:8]}[/dim]")


@main.command("list")
@click.option("--limit", default=20, show_default=True, help="Max runs to display")
def list_runs(limit: int) -> None:
    """List past eval runs."""
    tracker = ResultTracker()
    runs = tracker.list_runs(limit=limit)

    if not runs:
        console.print("No runs saved yet. Run [bold]redteam run <suite.yaml>[/bold] first.")
        return

    table = Table(title="Past Eval Runs")
    table.add_column("Run ID", style="dim")
    table.add_column("Suite")
    table.add_column("Model", style="dim")
    table.add_column("Date")
    table.add_column("Pass/Total", justify="right")
    table.add_column("Pass %", justify="right")

    for r in runs:
        pct = r["pass_rate"]
        color = "green" if pct >= 0.8 else "yellow" if pct >= 0.5 else "red"
        table.add_row(
            r["run_id"],
            r["suite_name"],
            r["model"],
            r["timestamp"][:10],
            f"{r['pass_count']}/{r['total_count']}",
            f"[{color}]{pct:.0%}[/{color}]",
        )
    console.print(table)


@main.command()
@click.argument("run_id")
def show(run_id: str) -> None:
    """Show detailed results for a run (prefix is enough)."""
    tracker = ResultTracker()
    data = tracker.get_run(run_id)
    if not data:
        console.print(f"[red]Run '{run_id}' not found.[/red]")
        sys.exit(1)

    console.print(f"\n[bold]Run:[/bold]    {data['run_id']}")
    console.print(f"[bold]Suite:[/bold]  {data['suite_name']}")
    console.print(f"[bold]Model:[/bold]  {data['model']}")
    console.print(f"[bold]Date:[/bold]   {data['timestamp'][:10]}")
    console.print(f"[bold]Pass rate:[/bold] {data['pass_rate']:.0%}\n")

    for c in data["cases"]:
        color = {"PASS": "green", "FAIL": "red", "WARN": "yellow", "ERROR": "dim"}.get(
            c["score"], "white"
        )
        console.print(f"[{color}]{c['score']:5}[/{color}]  [{c['test_id']}]  {c['reason'][:100]}")
        if c.get("error"):
            console.print(f"        [dim]Error: {c['error']}[/dim]")


@main.command()
@click.argument("run_a")
@click.argument("run_b")
@click.option("--output", default="regression.png", show_default=True)
def compare(run_a: str, run_b: str, output: str) -> None:
    """Compare two runs and generate a regression dashboard image."""
    tracker = ResultTracker()
    data_a = tracker.get_run(run_a)
    data_b = tracker.get_run(run_b)

    if not data_a:
        console.print(f"[red]Run '{run_a}' not found.[/red]")
        sys.exit(1)
    if not data_b:
        console.print(f"[red]Run '{run_b}' not found.[/red]")
        sys.exit(1)

    path = generate_regression_dashboard(data_a, data_b, output)
    console.print(f"Regression dashboard saved to [bold]{path}[/bold]")


@main.command()
@click.argument("run_id")
@click.option("--output", default="dashboard.png", show_default=True)
def dashboard(run_id: str, output: str) -> None:
    """Generate a visual dashboard PNG for a run."""
    tracker = ResultTracker()
    data = tracker.get_run(run_id)
    if not data:
        console.print(f"[red]Run '{run_id}' not found.[/red]")
        sys.exit(1)

    path = generate_dashboard(data, output)
    console.print(f"Dashboard saved to [bold]{path}[/bold]")
