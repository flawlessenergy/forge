"""Commit tracking: AI vs manual detection and stats."""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from forge.core import git_tracker, store

console = Console()


@click.group()
def commits():
    """Track and analyse git commits (AI vs manual)."""
    pass


@commits.command("log")
@click.option("--limit", "-n", default=20, show_default=True, help="Number of commits")
@click.option("--ai-only", is_flag=True, help="Show only AI commits")
@click.option("--manual-only", is_flag=True, help="Show only manual commits")
@click.option("--path", "-p", default=".", help="Git repo path")
def log(limit, ai_only, manual_only, path):
    """Show recent commits with AI/manual labels."""
    if not git_tracker.is_git_repo(path):
        console.print("[red]Not inside a git repository.[/red]")
        return

    all_commits = git_tracker.get_commits(limit=limit, repo_path=path)
    if not all_commits:
        console.print("[dim]No commits found.[/dim]")
        return

    if ai_only:
        all_commits = [c for c in all_commits if c.is_ai]
    if manual_only:
        all_commits = [c for c in all_commits if not c.is_ai]

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("SHA", style="cyan", width=9)
    table.add_column("Date", width=11)
    table.add_column("Type", width=10)
    table.add_column("Author", width=16)
    table.add_column("Message", min_width=40)
    table.add_column("+/-", width=12, justify="right")

    for c in all_commits:
        if c.is_ai:
            type_cell = "[magenta]🤖 AI[/magenta]"
        else:
            type_cell = "[blue]✍ Manual[/blue]"

        diff_str = (
            f"[green]+{c.insertions}[/green] [red]-{c.deletions}[/red]"
            if c.insertions or c.deletions
            else "[dim]—[/dim]"
        )
        subj = c.subject[:55] + "…" if len(c.subject) > 55 else c.subject
        table.add_row(
            c.short_sha,
            c.date,
            type_cell,
            c.author_name[:15],
            subj,
            diff_str,
        )

    console.print(table)
    ai_count = sum(1 for c in all_commits if c.is_ai)
    manual_count = len(all_commits) - ai_count
    console.print(
        f"[dim]Showing {len(all_commits)} commits — "
        f"[magenta]{ai_count} AI[/magenta] / [blue]{manual_count} manual[/blue][/dim]"
    )


@commits.command("stats")
@click.option("--limit", "-n", default=100, show_default=True)
@click.option("--path", "-p", default=".", help="Git repo path")
def stats(limit, path):
    """Show commit statistics: AI vs manual breakdown."""
    if not git_tracker.is_git_repo(path):
        console.print("[red]Not inside a git repository.[/red]")
        return

    all_commits = git_tracker.get_commits(limit=limit, repo_path=path)
    if not all_commits:
        console.print("[dim]No commits found.[/dim]")
        return

    ai = [c for c in all_commits if c.is_ai]
    manual = [c for c in all_commits if not c.is_ai]

    ai_ins = sum(c.insertions for c in ai)
    ai_del = sum(c.deletions for c in ai)
    manual_ins = sum(c.insertions for c in manual)
    manual_del = sum(c.deletions for c in manual)
    total = len(all_commits)

    ai_pct = round(len(ai) / total * 100) if total else 0
    manual_pct = 100 - ai_pct

    bar_len = 40
    ai_bar = "█" * round(bar_len * ai_pct / 100)
    manual_bar = "░" * (bar_len - len(ai_bar))

    text = Text()
    text.append("\nCommit breakdown\n", style="bold")
    text.append("  ")
    text.append(ai_bar, style="magenta")
    text.append(manual_bar, style="dim")
    text.append("  ")
    text.append(f"{ai_pct}% AI", style="magenta")
    text.append("  ")
    text.append(f"{manual_pct}% manual", style="blue")
    text.append("\n\n")

    text.append("  🤖 AI commits:     ", style="bold")
    text.append(f"{len(ai):>4}  ")
    text.append(f"+{ai_ins} / -{ai_del} lines\n", style="dim")

    text.append("  ✍  Manual commits: ", style="bold")
    text.append(f"{len(manual):>4}  ")
    text.append(f"+{manual_ins} / -{manual_del} lines\n", style="dim")

    text.append(f"\n  Total analysed:    {total}\n", style="dim")

    # Authors breakdown
    authors: dict[str, dict] = {}
    for c in all_commits:
        if c.author_name not in authors:
            authors[c.author_name] = {"total": 0, "ai": 0}
        authors[c.author_name]["total"] += 1
        if c.is_ai:
            authors[c.author_name]["ai"] += 1

    text.append("\nBy author:\n", style="bold")
    for name, data in sorted(authors.items(), key=lambda x: -x[1]["total"]):
        ai_n = data["ai"]
        man_n = data["total"] - ai_n
        text.append(f"  {name[:20]:<20} total={data['total']}  ")
        text.append(f"ai={ai_n} ", style="magenta")
        text.append(f"manual={man_n}\n", style="blue")

    info = git_tracker.get_repo_info(path)
    text.append(f"\nBranch: {info['branch']}  Total repo commits: {info['total_commits']}\n", style="dim")

    console.print(Panel(text, title="Commit Stats", border_style="cyan"))


@commits.command("show")
@click.argument("sha")
@click.option("--path", "-p", default=".", help="Git repo path")
def show(sha, path):
    """Show details of a single commit."""
    import subprocess
    result = subprocess.run(
        ["git", "show", "--stat", sha],
        capture_output=True, text=True, cwd=path,
    )
    if result.returncode != 0:
        console.print(f"[red]Commit {sha} not found.[/red]")
        return

    # Detect AI
    log_result = subprocess.run(
        ["git", "log", "-1", "--format=%s%n%b", sha],
        capture_output=True, text=True, cwd=path,
    )
    lines = log_result.stdout.splitlines()
    subject = lines[0] if lines else ""
    body = "\n".join(lines[1:]) if len(lines) > 1 else ""
    is_ai, reason = git_tracker.detect_ai(subject, body)

    label = "[magenta]🤖 AI commit[/magenta]" if is_ai else "[blue]✍ Manual commit[/blue]"
    console.print(f"\n{label}" + (f" (matched: {reason})" if reason else "") + "\n")
    console.print(result.stdout)


@commits.command("label")
@click.argument("sha")
@click.argument("label", type=click.Choice(["ai", "manual"]))
def label_cmd(sha, label):
    """Manually label a commit as 'ai' or 'manual'."""
    try:
        git_tracker.label_commit(sha, label)
        console.print(f"[green]✓[/green] {sha[:8]} labeled as {label}.")
    except FileNotFoundError:
        console.print("[red]Run `forge init` first.[/red]")


@commits.command("diff")
@click.argument("sha")
@click.option("--path", "-p", default=".", help="Git repo path")
def diff(sha, path):
    """Show the full diff for a commit."""
    import subprocess
    result = subprocess.run(
        ["git", "diff", f"{sha}^", sha],
        capture_output=True, text=True, cwd=path,
    )
    if result.returncode != 0:
        console.print(f"[red]Could not diff {sha}.[/red]")
        return
    # Use rich syntax highlighting via Pager
    click.echo_via_pager(result.stdout)
