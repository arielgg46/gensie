import typer
import uvicorn
import httpx
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.progress import track
from collections import defaultdict
from gensie.task import Task
from gensie.eval import (
    Evaluator,
    flatten_json,
    summarize_timing,
    summarize_token_usage,
)
from gensie.ranking import compute_ranking, load_reports
from gensie.runtime import slugify
from gensie.usage import aggregate_rows, parse_usage_header, usage_disagrees, usage_rows

app = typer.Typer(help="GenSIE Developer Tools")
console = Console()


def _write_json(path: Path, payload: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def _write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _collect_trace_metrics(task_dir: Path) -> Optional[Dict[str, Any]]:
    steps_dir = task_dir / "steps"
    if not steps_dir.is_dir():
        return None

    step_summaries = []
    for summary_path in sorted(steps_dir.glob("*/summary.json")):
        with open(summary_path, "r", encoding="utf-8") as f:
            step_summaries.append(json.load(f))

    if not step_summaries:
        return None

    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    total_duration_ms = 0.0
    measured_durations = 0
    request_count = 0
    failed_requests = 0
    ttft_values = []

    for step in step_summaries:
        metrics = step.get("metrics") or {}
        tokens = metrics.get("tokens") or {}
        timings = metrics.get("timings") or {}

        request_count += 1
        if step.get("error"):
            failed_requests += 1

        prompt_tokens += int(tokens.get("prompt_tokens") or 0)
        completion_tokens += int(tokens.get("completion_tokens") or 0)
        total_tokens += int(tokens.get("total_tokens") or 0)

        duration_ms = timings.get("total_duration_ms")
        if duration_ms is not None:
            total_duration_ms += float(duration_ms)
            measured_durations += 1

        ttft_ms = timings.get("time_to_first_token_ms")
        if ttft_ms is not None:
            ttft_values.append(float(ttft_ms))

    return {
        "request_count": request_count,
        "failed_request_count": failed_requests,
        "tokens": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        },
        "timings": {
            "total_duration_ms": round(total_duration_ms, 3),
            "average_duration_ms": round(total_duration_ms / measured_durations, 3)
            if measured_durations
            else None,
            "time_to_first_token_ms": round(sum(ttft_values) / len(ttft_values), 3)
            if ttft_values
            else None,
            "time_to_first_token_available": bool(ttft_values),
            "time_to_first_token_note": None
            if ttft_values
            else "Not captured by the current non-streaming baseline.",
        },
        "steps": [
            {
                "step_index": step.get("step_index"),
                "step_name": step.get("step_name"),
                "error": step.get("error"),
                "tokens": (step.get("metrics") or {}).get("tokens"),
                "timings": (step.get("metrics") or {}).get("timings"),
            }
            for step in step_summaries
        ],
    }


def _write_task_details(
    details_dir: Path,
    task: Task,
    system_output: Optional[Dict[str, Any]],
    tps: float,
    gold_keys: int,
    system_keys: int,
    status: str,
    error: Optional[str] = None,
):
    task_dir = details_dir / task.id
    prompt = task.get_input_prompt()

    _write_text(task_dir / "prompt.txt", prompt)
    _write_json(task_dir / "task.json", task.model_dump(mode="json"))
    _write_json(task_dir / "gold.json", task.output)

    if system_output is not None:
        _write_json(task_dir / "prediction.json", system_output)

    summary = {
        "task_id": task.id,
        "tps": tps,
        "gold_keys": gold_keys,
        "system_keys": system_keys,
        "status": status,
    }
    trace_metrics = _collect_trace_metrics(task_dir)
    if trace_metrics is not None:
        summary["trace_metrics"] = trace_metrics
    if error:
        summary["error"] = error
        _write_text(task_dir / "error.txt", error)

    _write_json(task_dir / "summary.json", summary)
    return summary


@app.command()
def serve(host: str = "0.0.0.0", port: int = 8000):
    """Starts the FastAPI server for the agent."""
    console.print(
        f"[bold green]Starting GenSIE Agent Server on {host}:{port}...[/bold green]"
    )
    uvicorn.run("gensie.server:app", host=host, port=port, reload=True)


@app.command()
def eval(
    data: Path = typer.Option(..., help="Path to directory containing JSON tasks"),
    url: str = typer.Option("http://localhost:8000", help="Agent service URL"),
    pipeline: str = typer.Option("baseline", help="Name of the pipeline to evaluate"),
    model: str = typer.Option(..., help="The exact model name to use for inference"),
    limit: Optional[int] = typer.Option(
        None, help="Limit the number of tasks to evaluate"
    ),
    output: Optional[Path] = typer.Option(
        None, help="Path to save the JSON evaluation report"
    ),
    details_dir: Optional[Path] = typer.Option(
        None,
        help="Directory to save prompts, predictions, gold outputs, and per-task summaries",
    ),
):
    """Evaluates the agent against a local dataset and generates a report.

    Per-instance wall time and token usage are recorded but never hard-stopped at
    their soft budgets; the report includes a timing summary and (when a usage log
    or the ``X-GenSIE-Token-Usage`` header is available) a token-usage summary, so
    the soft, averaged budgets from the submission spec can be reviewed afterwards.
    """
    evaluator = Evaluator()

    if not data.is_dir():
        console.print(f"[bold red]Error: {data} is not a directory.[/bold red]")
        raise typer.Exit(1)

    json_files = list(data.rglob("*.json"))
    if limit:
        json_files = json_files[:limit]

    if details_dir:
        details_dir.mkdir(parents=True, exist_ok=True)

    tps_list = []
    gold_counts = []
    system_counts = []
    elapsed_list: List[float] = []
    usage_warnings: List[str] = []
    sources_seen: set = set()
    individual_results: List[Dict[str, Any]] = []

    results_table = Table(title=f"Evaluation Results (Pipeline: {pipeline})")
    results_table.add_column("Task ID", style="cyan")
    results_table.add_column("TPS", justify="right")
    results_table.add_column("Gold Keys", justify="right")
    results_table.add_column("System Keys", justify="right")
    results_table.add_column("Time (s)", justify="right")
    results_table.add_column("Tokens", justify="right")
    results_table.add_column("Status", justify="center")

    params = {"pipeline": pipeline}
    if model:
        params["model"] = model

    participant_info = {"team_name": "Unknown", "institution": "Unknown"}

    with httpx.Client(timeout=request_timeout_s) as client:
        # 1. Fetch Participant Info
        try:
            info_resp = client.get(f"{url}/info")
            info_resp.raise_for_status()
            participant_info = info_resp.json()
            console.print(
                f"Auditing Team: [bold magenta]{participant_info.get('team_name', 'Unknown')}[/bold magenta]"
            )
        except Exception as e:
            console.print(f"[yellow]Could not retrieve participant info: {e}[/yellow]")

        # 2. Process Tasks
        for file_path in track(json_files, description="Processing tasks..."):
            task = None
            system_output = None
            error_message = None
            try:
                task = Task.load(file_path)
                task_payload = task.model_dump(mode="json")
                if details_dir:
                    task_payload.setdefault("metadata", {})
                    task_payload["metadata"]["_trace_dir"] = str(
                        (details_dir / task.id).absolute()
                    )

                # Call agent
                resp = client.post(f"{url}/run", json=task_payload, params=params)
                resp.raise_for_status()
                system_output = resp.json()
                header_usage = parse_usage_header(
                    resp.headers.get("X-GenSIE-Token-Usage")
                )

                # Score
                tps = evaluator.score_instance(
                    task.output, system_output, task.target_schema
                )
                g_count = len(flatten_json(task.output, expand_lists=False))
                s_count = len(flatten_json(system_output, expand_lists=False))
                status = "PASS"

            except Exception as e:
                # Penalize failures with 0 score
                status = "FAIL"
                tps = 0.0
                s_count = 0
                error_message = str(e)
                g_count = (
                    len(flatten_json(task.output, expand_lists=False)) if task else 0
                )
                console.print(
                    f"[bold red]Error processing {file_path.name}:[/bold red] {e}"
                )
            finally:
                elapsed = time.perf_counter() - t0

            # Attribute token usage to this instance.
            log_usage = None
            if usage_log is not None and n0 is not None:
                log_usage = aggregate_rows(usage_rows(usage_log, log_key)[n0:])
            label = task.id if task else file_path.name
            if log_usage is not None:
                tokens = log_usage
                source = "usage_log"
                if header_usage is not None and usage_disagrees(
                    log_usage["total"], header_usage["total"]
                ):
                    usage_warnings.append(
                        f"{label}: usage log {log_usage['total']} vs agent header "
                        f"{header_usage['total']} tokens — flagged for review"
                    )
            elif header_usage is not None:
                tokens = header_usage
                source = "header"
            else:
                tokens = None
                source = "unavailable"
            sources_seen.add(source)

            tps_list.append(tps)
            gold_counts.append(g_count)
            system_counts.append(s_count)
            elapsed_list.append(elapsed)

            if task:
                over = elapsed > time_budget_s
                results_table.add_row(
                    task.id,
                    f"{tps:.2f}",
                    str(g_count),
                    str(s_count),
                    f"[yellow]{elapsed:.1f}[/yellow]" if over else f"{elapsed:.1f}",
                    f"{tokens['total']}" if tokens else "—",
                    f"[green]{status}[/green]"
                    if status == "PASS"
                    else f"[red]{status}[/red]",
                )

                task_result = {
                    "task_id": task.id,
                    "tps": tps,
                    "gold_keys": g_count,
                    "system_keys": s_count,
                    "status": status,
                    "error": error_message,
                }

                if details_dir:
                    summary = _write_task_details(
                        details_dir,
                        task,
                        system_output,
                        tps,
                        g_count,
                        s_count,
                        status,
                        error=error_message,
                    )
                    if "trace_metrics" in summary:
                        task_result["trace_metrics"] = summary["trace_metrics"]

                individual_results.append(task_result)

    # 3. Calculate final metrics
    metrics = evaluator.calculate_metrics(tps_list, gold_counts, system_counts)
    timing = summarize_timing(elapsed_list, budget_s=time_budget_s)
    token_usage = summarize_token_usage([r.get("tokens") for r in individual_results])
    token_usage["source"] = (
        sources_seen.pop()
        if len(sources_seen) == 1
        else ("mixed" if sources_seen else "unavailable")
    )

    console.print(results_table)

    summary_table = Table(title="Aggregate Metrics", show_header=False)
    summary_table.add_row("Precision", f"{metrics['precision']:.4f}")
    summary_table.add_row("Recall", f"{metrics['recall']:.4f}")
    summary_table.add_row("Micro-F1", f"[bold green]{metrics['f1']:.4f}[/bold green]")
    console.print(summary_table)

    timing_table = Table(
        title=f"Timing (soft budget: {time_budget_s:.0f}s/instance, averaged)",
        show_header=False,
    )
    timing_table.add_row("Avg time / instance", f"{timing['avg_elapsed_s']:.2f}s")
    timing_table.add_row("Max time / instance", f"{timing['max_elapsed_s']:.2f}s")
    timing_table.add_row(
        "Instances over budget", f"{timing['over_budget_count']} / {timing['n']}"
    )
    timing_table.add_row(
        "Average within budget?",
        "[green]yes[/green]" if timing["avg_within_budget"] else "[red]no[/red]",
    )
    console.print(timing_table)
    if not timing["avg_within_budget"]:
        console.print(
            "[yellow]Note:[/yellow] the average exceeds the soft budget — this would be "
            "reviewed case by case, not auto-penalized."
        )

    tok_table = Table(
        title=f"Token usage (soft target: {token_usage['target']}/instance, averaged)",
        show_header=False,
    )
    tok_table.add_row(
        "Avg tokens / instance", f"{token_usage['avg_total_per_instance']:.0f}"
    )
    tok_table.add_row("Max tokens / instance", f"{token_usage['max_total']}")
    tok_table.add_row(
        "Over target (>32K)", f"{token_usage['over_target_count']} / {token_usage['n']}"
    )
    tok_table.add_row(
        "Over soft cap (>64K)", f"{token_usage['over_soft_count']} / {token_usage['n']}"
    )
    tok_table.add_row(
        "Total tokens / calls",
        f"{token_usage['total_tokens']} / {token_usage['calls_total']}",
    )
    tok_table.add_row("Source", token_usage["source"])
    tok_table.add_row(
        "Average within target?",
        "[green]yes[/green]" if token_usage["avg_within_target"] else "[red]no[/red]",
    )
    console.print(tok_table)
    if not token_usage["avg_within_target"]:
        console.print(
            "[yellow]Note:[/yellow] average token usage exceeds the soft target — "
            "reviewed case by case, not auto-penalized."
        )
    for w in usage_warnings:
        console.print(f"[yellow]warning:[/yellow] {w}")

    # 4. Export JSON Report
    if output:
        report = {
            "participant": participant_info,
            "config": {
                "model": model,
                "pipeline": pipeline,
                "data_source": str(data.absolute()),
                "details_dir": str(details_dir) if details_dir else None,
            },
            "metrics": metrics,
            "timing": timing,
            "token_usage": token_usage,
            "tasks": individual_results,
        }
        _write_json(output, report)
        console.print(f"\n[bold blue]Report saved to {output}[/bold blue]")

    if details_dir:
        detailed_report = {
            "participant": participant_info,
            "config": {
                "model": model,
                "pipeline": pipeline,
                "data_source": str(data.absolute()),
                "details_dir": str(details_dir.absolute()),
            },
            "metrics": metrics,
            "tasks": individual_results,
        }
        _write_json(details_dir / "detailed_report.json", detailed_report)
        console.print(
            f"[bold blue]Detailed artifacts saved to {details_dir}[/bold blue]"
        )


@app.command()
def leaderboard(
    results_dir: Path = typer.Argument(
        Path("results"), help="Directory containing evaluation JSON reports"
    ),
    plain: bool = typer.Option(
        False, "--plain", help="Output in plain Markdown format"
    ),
):
    """
    Aggregates evaluation reports and displays a leaderboard.
    Groups results by (Model, Dataset) and ranks by Micro-F1.
    """
    if not results_dir.is_dir():
        console.print(f"[bold red]Error: {results_dir} is not a directory.[/bold red]")
        raise typer.Exit(1)

    reports = []
    for file_path in results_dir.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Robustness: Validate required fields
            if not all(k in data for k in ["participant", "config", "metrics"]):
                continue

            reports.append(
                {
                    "team": data["participant"].get("team_name", "Unknown"),
                    "model": data["config"].get("model", "Unknown"),
                    "pipeline": data["config"].get("pipeline", "Unknown"),
                    "dataset": Path(data["config"].get("data_source", "Unknown")).name,
                    "f1": data["metrics"].get("f1", 0.0),
                }
            )
        except Exception:
            # Skip malformed or incompatible JSONs
            continue

    if not reports:
        console.print("[yellow]No valid evaluation reports found.[/yellow]")
        return

    # Grouping by (Model, Dataset)
    groups = defaultdict(list)
    for r in reports:
        groups[(r["model"], r["dataset"])].append(r)

    for (model, dataset), entries in groups.items():
        # Sort all entries by F1 descending
        entries.sort(key=lambda x: x["f1"], reverse=True)

        # Calculate Best-per-team
        best_per_team = {}
        for e in entries:
            if e["team"] not in best_per_team:
                best_per_team[e["team"]] = e
        best_entries = sorted(
            best_per_team.values(), key=lambda x: x["f1"], reverse=True
        )

        if plain:
            # Manual Markdown output
            print(f"## Leaderboard: {dataset} (Model: {model})")
            for title, data_list in [
                ("Best per Team", best_entries),
                ("All Pipelines", entries),
            ]:
                print(f"\n### {title}")
                print("| Rank | Team | Pipeline | Micro-F1 |")
                print("|---:|:---|:---|---:|")
                for i, e in enumerate(data_list, 1):
                    print(f"| {i} | {e['team']} | {e['pipeline']} | {e['f1']:.4f} |")
            print("\n")
        else:
            # Rich Terminal output
            console.rule(
                f"[bold green]Leaderboard: {dataset} (Model: {model})[/bold green]"
            )
            for title, data_list in [
                ("Best per Team", best_entries),
                ("All Pipelines", entries),
            ]:
                table = Table(title=title, box=None)
                table.add_column("Rank", justify="right", style="cyan")
                table.add_column("Team", style="magenta")
                table.add_column("Pipeline")
                table.add_column("Micro-F1", justify="right", style="bold green")
                for i, e in enumerate(data_list, 1):
                    table.add_row(str(i), e["team"], e["pipeline"], f"{e['f1']:.4f}")
                console.print(table)
            console.print("\n")


@app.command()
def rank(
    results_dir: Path = typer.Argument(
        Path("results"), help="Directory containing evaluation JSON reports"
    ),
    baseline_pipeline: str = typer.Option(
        "baseline", help="Pipeline name that identifies the official baseline report"
    ),
    plain: bool = typer.Option(
        False, "--plain", help="Output in plain Markdown format"
    ),
):
    """Official primary leaderboard: fraction of the baseline→perfect F1 gap closed, averaged over models.

    Reads `gensie eval --output ...` reports, computes per-model gap_closed for each
    team's best pipeline, and ranks by the average across models. Also prints the
    per-model breakdown and a secondary raw-F1 leaderboard.
    """
    reports = load_reports(results_dir)
    if not reports:
        console.print(
            f"[yellow]No valid evaluation reports found in {results_dir}.[/yellow]"
        )
        raise typer.Exit(1)

    result = compute_ranking(reports, baseline_pipeline=baseline_pipeline)

    if not result["models"]:
        console.print(
            "[bold red]No model has both a baseline report and at least one submission — "
            "cannot rank.[/bold red]"
        )
        for w in result["warnings"]:
            console.print(f"[yellow]warning:[/yellow] {w}")
        raise typer.Exit(1)

    models = result["models"]

    if plain:
        print("## Primary leaderboard — gap closed over baseline (avg over models)\n")
        print(
            "Baselines: "
            + ", ".join(f"`{m}` = {b:.4f}" for m, b in result["baselines"].items())
            + "\n"
        )
        header = "| Rank | Team | Avg gap closed | " + " | ".join(models) + " |"
        print(header)
        print("|---:|:---|---:|" + "|".join(["---:"] * len(models)) + "|")
        for i, row in enumerate(result["leaderboard"], 1):
            cells = []
            for m in models:
                pm = row["per_model"].get(m)
                cells.append(
                    f"{pm['gap_closed']:.4f} ({pm['pipeline']})" if pm else "—"
                )
            print(
                f"| {i} | {row['team']} | {row['avg_gap_closed']:.4f} | "
                + " | ".join(cells)
                + " |"
            )
        print()
        for m in models:
            print(
                f"### Per-model: `{m}` (baseline F1 = {result['baselines'][m]:.4f})\n"
            )
            print("| Rank | Team | Pipeline | F1 | Gap closed |")
            print("|---:|:---|:---|---:|---:|")
            for i, e in enumerate(result["per_model"][m], 1):
                print(
                    f"| {i} | {e['team']} | {e['pipeline']} | {e['f1']:.4f} | {e['gap_closed']:.4f} |"
                )
            print()
        print("### Secondary — raw average Micro-F1 (reference only)\n")
        print("| Rank | Team | Avg F1 | " + " | ".join(models) + " |")
        print("|---:|:---|---:|" + "|".join(["---:"] * len(models)) + "|")
        for i, row in enumerate(result["raw_f1_leaderboard"], 1):
            cells = [
                f"{row['per_model'][m]['f1']:.4f}" if m in row["per_model"] else "—"
                for m in models
            ]
            print(
                f"| {i} | {row['team']} | {row['avg_f1']:.4f} | "
                + " | ".join(cells)
                + " |"
            )
        print()
        for w in result["warnings"]:
            print(f"> ⚠️ {w}")
        return

    console.rule(
        "[bold green]Primary leaderboard — gap closed over baseline (avg over models)[/bold green]"
    )
    console.print(
        "Baselines: "
        + ", ".join(
            f"[cyan]{m}[/cyan] = {b:.4f}" for m, b in result["baselines"].items()
        )
    )
    primary = Table(box=None)
    primary.add_column("Rank", justify="right", style="cyan")
    primary.add_column("Team", style="magenta")
    primary.add_column("Avg gap closed", justify="right", style="bold green")
    for m in models:
        primary.add_column(m, justify="right")
    for i, row in enumerate(result["leaderboard"], 1):
        cells = []
        for m in models:
            pm = row["per_model"].get(m)
            cells.append(f"{pm['gap_closed']:.4f} ({pm['pipeline']})" if pm else "—")
        primary.add_row(str(i), row["team"], f"{row['avg_gap_closed']:.4f}", *cells)
    console.print(primary)

    for m in models:
        console.rule(
            f"[bold]Per-model: {m}[/bold]  (baseline F1 = {result['baselines'][m]:.4f})"
        )
        t = Table(box=None)
        t.add_column("Rank", justify="right", style="cyan")
        t.add_column("Team", style="magenta")
        t.add_column("Pipeline")
        t.add_column("F1", justify="right")
        t.add_column("Gap closed", justify="right", style="bold green")
        for i, e in enumerate(result["per_model"][m], 1):
            t.add_row(
                str(i),
                e["team"],
                e["pipeline"],
                f"{e['f1']:.4f}",
                f"{e['gap_closed']:.4f}",
            )
        console.print(t)

    console.rule("[bold]Secondary — raw average Micro-F1 (reference only)[/bold]")
    sec = Table(box=None)
    sec.add_column("Rank", justify="right", style="cyan")
    sec.add_column("Team", style="magenta")
    sec.add_column("Avg F1", justify="right", style="bold")
    for m in models:
        sec.add_column(m, justify="right")
    for i, row in enumerate(result["raw_f1_leaderboard"], 1):
        cells = [
            f"{row['per_model'][m]['f1']:.4f}" if m in row["per_model"] else "—"
            for m in models
        ]
        sec.add_row(str(i), row["team"], f"{row['avg_f1']:.4f}", *cells)
    console.print(sec)

    for w in result["warnings"]:
        console.print(f"[yellow]warning:[/yellow] {w}")


if __name__ == "__main__":
    app()
