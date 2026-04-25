"""Project dashboard: combined stats for specs and commits."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich import box

console = Console()


@click.command("stats")
@click.option("--path", "-p", default=".", help="Git repo path")
def stats(path):
    """Show a full project dashboard: specs + commit stats."""
    from forge.core import store, git_tracker

    # ── Specs ──────────────────────────────────────────────────────────────
    try:
        all_specs = store.all_specs()
    except FileNotFoundError:
        all_specs = []

    spec_counts = {
        "pending": sum(1 for s in all_specs if s["status"] == "pending"),
        "in_progress": sum(1 for s in all_specs if s["status"] == "in_progress"),
        "done": sum(1 for s in all_specs if s["status"] == "done"),
        "blocked": sum(1 for s in all_specs if s["status"] == "blocked"),
    }
    total_specs = len(all_specs)
    done_pct = round(spec_counts["done"] / total_specs * 100) if total_specs else 0

    spec_text = Text()
    spec_text.append(f"  Total:       {total_specs}\n", style="bold")

    bar_done = "█" * round(40 * done_pct / 100)
    bar_rest = "░" * (40 - len(bar_done))
    spec_text.append("  ")
    spec_text.append(bar_done, style="green")
    spec_text.append(bar_rest, style="dim")
    spec_text.append(f"  {done_pct}% done\n\n")

    spec_text.append(f"  ⬜ Pending:    {spec_counts['pending']}\n")
    spec_text.append("  ◑", style="yellow")
    spec_text.append(f" In progress: {spec_counts['in_progress']}\n")
    spec_text.append("  ●", style="green")
    spec_text.append(f" Done:        {spec_counts['done']}\n")
    spec_text.append("  ✗", style="red")
    spec_text.append(f" Blocked:     {spec_counts['blocked']}\n")

    # Tag breakdown
    tag_count: dict[str, int] = {}
    for s in all_specs:
        for t in s.get("tags", []):
            tag_count[t] = tag_count.get(t, 0) + 1
    if tag_count:
        top_tags = sorted(tag_count.items(), key=lambda x: -x[1])[:5]
        spec_text.append("\n  Top tags: ", style="dim")
        spec_text.append(", ".join(f"{t}({n})" for t, n in top_tags) + "\n", style="dim")

    spec_panel = Panel(spec_text, title="[bold]Specs[/bold]", border_style="green", width=44)

    # ── Commits ────────────────────────────────────────────────────────────
    commit_text = Text()
    if not git_tracker.is_git_repo(path):
        commit_text.append("  Not a git repository.\n", style="dim")
    else:
        all_commits = git_tracker.get_commits(limit=100, repo_path=path)
        if not all_commits:
            commit_text.append("  No commits found.\n", style="dim")
        else:
            ai_commits = [c for c in all_commits if c.is_ai]
            manual_commits = [c for c in all_commits if not c.is_ai]
            total_c = len(all_commits)
            ai_pct = round(len(ai_commits) / total_c * 100) if total_c else 0

            ai_bar = "█" * round(40 * ai_pct / 100)
            man_bar = "░" * (40 - len(ai_bar))

            commit_text.append(f"  Last {total_c} commits analysed\n\n", style="dim")
            commit_text.append("  ")
            commit_text.append(ai_bar, style="magenta")
            commit_text.append(man_bar, style="blue")
            commit_text.append("  ")
            commit_text.append(f"{ai_pct}% AI", style="magenta")
            commit_text.append("\n\n")
            commit_text.append(f"  🤖 AI:     {len(ai_commits)}\n", style="magenta")
            commit_text.append(f"  ✍ Manual:  {len(manual_commits)}\n", style="blue")

            ai_lines = sum(c.insertions + c.deletions for c in ai_commits)
            man_lines = sum(c.insertions + c.deletions for c in manual_commits)
            commit_text.append(f"\n  AI lines changed:    {ai_lines:,}\n", style="dim")
            commit_text.append(f"  Manual lines changed: {man_lines:,}\n", style="dim")

            info = git_tracker.get_repo_info(path)
            commit_text.append(f"\n  Branch: {info['branch']}\n", style="dim")

    commit_panel = Panel(commit_text, title="[bold]Commits[/bold]", border_style="magenta", width=44)

    console.print()
    console.print(Columns([spec_panel, commit_panel]))

    # Recent specs table
    if all_specs:
        recent = sorted(all_specs, key=lambda s: s.get("updated_at", ""), reverse=True)[:5]
        table = Table(
            title="Recent specs",
            box=box.SIMPLE,
            show_header=True,
            header_style="dim",
        )
        table.add_column("ID", style="cyan", width=10)
        table.add_column("Title")
        table.add_column("Status", width=12)
        table.add_column("Updated", width=11)
        for s in recent:
            icon = {"done": "[green]●[/green]", "pending": "○",
                    "in_progress": "[yellow]◑[/yellow]", "blocked": "[red]✗[/red]"}.get(
                s["status"], s["status"]
            )
            table.add_row(s["id"], s["title"][:40], f"{icon} {s['status']}", s["updated_at"][:10])
        console.print(table)
