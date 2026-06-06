from __future__ import annotations
from pathlib import Path
from typing import Optional
import typer
from tools_shared.logging import setup_logging, log_warning, log_success

app = typer.Typer(name="ci-triage", no_args_is_help=True, help="Triage CI failures for a GitHub PR.")


@app.callback()
def _main() -> None:
    pass


@app.command()
def analyze(
    pr_url: str = typer.Argument(..., help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write markdown report to this file"),
    refresh: bool = typer.Option(False, "--refresh", help="Re-download artifacts even if cached"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Download CI artifacts for a PR and show failure summary."""
    from ci_triage_tools.github import parse_pr_url, get_head_sha, get_failing_runs, fetch_run_log
    from ci_triage_tools.artifacts import (
        load_cached_failures, save_failures, clear_run_cache,
        download_run_artifacts, detect_artifact_type,
        load_cached_log, save_log,
    )
    from ci_triage_tools.parse_vitest import parse_blob as vitest_parse
    from ci_triage_tools.parse_playwright import parse_blob as pw_parse_blob, parse_html as pw_parse_html
    from ci_triage_tools.sanitize_log import sanitize
    from ci_triage_tools.schema import WorkflowResult, TriageReport
    from ci_triage_tools.render import render_terminal, render_markdown

    setup_logging(verbose)

    owner, repo, pr_number = parse_pr_url(pr_url)
    head_sha = get_head_sha(owner, repo, pr_number)
    failing_runs = get_failing_runs(owner, repo, head_sha)

    if not failing_runs:
        print("No failing workflow runs found for this PR.")
        raise typer.Exit(0)

    report = TriageReport(pr_url=pr_url, head_sha=head_sha)

    for run_info in failing_runs:
        if refresh:
            clear_run_cache(run_info.run_id)

        failures = load_cached_failures(run_info.run_id)
        if failures is None:
            dest = download_run_artifacts(owner, repo, run_info.run_id)
            failures = []
            for artifact_dir in sorted(dest.iterdir()):
                if not artifact_dir.is_dir():
                    continue
                kind = detect_artifact_type(artifact_dir.name)
                if kind == "vitest":
                    for json_file in sorted(artifact_dir.glob("*.json")):
                        failures.extend(vitest_parse(json_file))
                elif kind == "playwright":
                    for zip_file in sorted(artifact_dir.glob("*.zip")):
                        failures.extend(pw_parse_blob(zip_file))
                    for sub in artifact_dir.iterdir():
                        if sub.is_dir() and (sub / "index.html").exists():
                            failures.extend(pw_parse_html(sub))
                elif kind == "skip":
                    pass
                else:
                    log_warning(f"Skipping unknown artifact: {artifact_dir.name}")
            if failures:
                save_failures(run_info.run_id, failures)

        log_fallback: str | None = None
        if not failures:
            log_fallback = load_cached_log(run_info.run_id)
            if log_fallback is None:
                raw_log = fetch_run_log(run_info.run_id)
                if raw_log:
                    log_fallback = sanitize(raw_log)
                    save_log(run_info.run_id, log_fallback)

        report.workflows.append(WorkflowResult(
            workflow_name=run_info.workflow_name,
            run_id=run_info.run_id,
            run_url=run_info.run_url,
            failures=failures,
            log_fallback=log_fallback,
        ))

    render_terminal(report)
    if output:
        render_markdown(report, output)
        log_success(f"Report saved to {output}")


@app.command(name="from-file")
def from_file(
    log_path: Path = typer.Argument(..., help="Path to a downloaded GitHub Actions log file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write sanitized log to this file"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Sanitize a raw GitHub Actions log file to show only failures."""
    from ci_triage_tools.sanitize_log import sanitize_file
    from ci_triage_tools.render import render_sanitized_log

    setup_logging(verbose)

    if not log_path.exists():
        typer.echo(f"File not found: {log_path}", err=True)
        raise typer.Exit(1)

    cleaned = sanitize_file(log_path)
    render_sanitized_log(cleaned, output)
    if output:
        log_success(f"Sanitized log saved to {output}")
