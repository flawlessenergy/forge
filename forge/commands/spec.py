"""Spec management commands."""

import click
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from forge.core import store

console = Console()

PRIORITY_COLORS = {"high": "red", "medium": "yellow", "low": "cyan"}
STATUS_ICONS = {
    "pending": "[dim]○[/dim]",
    "in_progress": "[yellow]◑[/yellow]",
    "done": "[green]●[/green]",
    "blocked": "[red]✗[/red]",
}


@click.group()
def spec():
    """Manage specs (requirements and tasks)."""
    pass


@spec.command("add")
@click.argument("title")
@click.option("--desc", "-d", default="", help="Spec description")
@click.option(
    "--priority", "-p",
    type=click.Choice(["high", "medium", "low"]),
    default="medium",
    show_default=True,
)
@click.option("--tags", "-t", default="", help="Comma-separated tags")
def add(title, desc, priority, tags):
    """Add a new spec."""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    s = store.add_spec(title, desc, tag_list, priority)
    color = PRIORITY_COLORS[priority]
    console.print(
        f"[green]✓[/green] Created [{color}]{s['id']}[/{color}]: {s['title']}"
    )


@spec.command("list")
@click.option(
    "--status", "-s",
    type=click.Choice(["pending", "in_progress", "done", "blocked", "all"]),
    default="all",
    show_default=True,
)
@click.option("--tag", "-t", default="", help="Filter by tag")
def list_specs(status, tag):
    """List all specs."""
    specs = store.all_specs()
    if status != "all":
        specs = [s for s in specs if s["status"] == status]
    if tag:
        specs = [s for s in specs if tag in s.get("tags", [])]

    if not specs:
        console.print("[dim]No specs found.[/dim]")
        return

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("ID", style="bold cyan", width=10)
    table.add_column("Title", min_width=30)
    table.add_column("Status", width=12)
    table.add_column("Priority", width=10)
    table.add_column("Tags", width=20)
    table.add_column("Commits", width=8, justify="right")

    for s in specs:
        icon = STATUS_ICONS.get(s["status"], s["status"])
        pcolor = PRIORITY_COLORS.get(s["priority"], "white")
        tags_str = ", ".join(s.get("tags", []))
        commits_count = len(s.get("commits", []))
        table.add_row(
            s["id"],
            s["title"],
            f"{icon} {s['status']}",
            f"[{pcolor}]{s['priority']}[/{pcolor}]",
            tags_str or "[dim]—[/dim]",
            str(commits_count) if commits_count else "[dim]0[/dim]",
        )

    console.print(table)
    console.print(
        f"[dim]{len(specs)} spec(s) | "
        f"{sum(1 for s in specs if s['status'] == 'done')} done | "
        f"{sum(1 for s in specs if s['status'] == 'pending')} pending[/dim]"
    )


@spec.command("show")
@click.argument("spec_id")
def show(spec_id):
    """Show spec details."""
    s = store.get_spec(spec_id)
    if not s:
        console.print(f"[red]Spec {spec_id.upper()} not found.[/red]")
        return

    pcolor = PRIORITY_COLORS.get(s["priority"], "white")
    icon = STATUS_ICONS.get(s["status"], s["status"])

    content = Text()
    content.append(f"Status:   ", style="bold")
    content.append(f"{s['status']}\n")
    content.append(f"Priority: ", style="bold")
    content.append(f"{s['priority']}\n", style=pcolor)
    content.append(f"Tags:     ", style="bold")
    content.append(f"{', '.join(s.get('tags', [])) or '—'}\n")
    content.append(f"Created:  ", style="bold")
    content.append(f"{s['created_at'][:10]}\n")
    content.append(f"Updated:  ", style="bold")
    content.append(f"{s['updated_at'][:10]}\n")

    if s.get("description"):
        content.append(f"\nDescription:\n", style="bold")
        content.append(f"{s['description']}\n")

    if s.get("notes"):
        content.append(f"\nNotes:\n", style="bold")
        content.append(f"{s['notes']}\n")

    if s.get("commits"):
        content.append(f"\nLinked commits:\n", style="bold")
        for c in s["commits"]:
            content.append(f"  {c[:8]}…\n", style="cyan")

    console.print(Panel(content, title=f"{icon} {s['id']}: {s['title']}", border_style="cyan"))


@spec.command("done")
@click.argument("spec_id")
def done(spec_id):
    """Mark a spec as done."""
    s = store.update_spec(spec_id, status="done")
    if not s:
        console.print(f"[red]Spec {spec_id.upper()} not found.[/red]")
        return
    console.print(f"[green]✓[/green] {s['id']} marked as done.")


@spec.command("start")
@click.argument("spec_id")
def start(spec_id):
    """Mark a spec as in_progress."""
    s = store.update_spec(spec_id, status="in_progress")
    if not s:
        console.print(f"[red]Spec {spec_id.upper()} not found.[/red]")
        return
    console.print(f"[yellow]◑[/yellow] {s['id']} marked as in_progress.")


@spec.command("block")
@click.argument("spec_id")
@click.option("--reason", "-r", default="", help="Reason for blocking")
def block(spec_id, reason):
    """Mark a spec as blocked."""
    updates = {"status": "blocked"}
    if reason:
        s = store.get_spec(spec_id)
        if s:
            notes = s.get("notes", "")
            updates["notes"] = f"{notes}\nBlocked: {reason}".strip()
    s = store.update_spec(spec_id, **updates)
    if not s:
        console.print(f"[red]Spec {spec_id.upper()} not found.[/red]")
        return
    console.print(f"[red]✗[/red] {s['id']} marked as blocked.")


@spec.command("note")
@click.argument("spec_id")
@click.argument("text")
def note(spec_id, text):
    """Append a note to a spec."""
    s = store.get_spec(spec_id)
    if not s:
        console.print(f"[red]Spec {spec_id.upper()} not found.[/red]")
        return
    existing = s.get("notes", "")
    new_notes = f"{existing}\n{text}".strip()
    store.update_spec(spec_id, notes=new_notes)
    console.print(f"[green]✓[/green] Note added to {spec_id.upper()}.")


@spec.command("delete")
@click.argument("spec_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def delete(spec_id, yes):
    """Delete a spec."""
    if not yes:
        click.confirm(f"Delete {spec_id.upper()}?", abort=True)
    if store.delete_spec(spec_id):
        console.print(f"[green]✓[/green] Deleted {spec_id.upper()}.")
    else:
        console.print(f"[red]Spec {spec_id.upper()} not found.[/red]")


@spec.command("link")
@click.argument("spec_id")
@click.option("--commit", "-c", required=True, help="Full or short commit SHA")
def link(spec_id, commit):
    """Link a git commit to a spec."""
    if store.link_commit(spec_id, commit):
        console.print(f"[green]✓[/green] Linked {commit[:8]} to {spec_id.upper()}.")
    else:
        console.print(f"[red]Spec {spec_id.upper()} not found.[/red]")


@spec.command("export")
@click.option("--format", "fmt", type=click.Choice(["json", "md"]), default="md")
@click.option("--output", "-o", default="", help="Output file path (default: stdout)")
def export(fmt, output):
    """Export all specs to JSON or Markdown."""
    specs = store.all_specs()
    if fmt == "json":
        content = json.dumps(specs, indent=2)
    else:
        lines = ["# Specs\n"]
        for s in specs:
            icon = {"done": "✅", "pending": "⬜", "in_progress": "🔄", "blocked": "🚫"}.get(
                s["status"], "⬜"
            )
            lines.append(f"## {icon} {s['id']}: {s['title']}\n")
            lines.append(f"**Status:** {s['status']} | **Priority:** {s['priority']}\n")
            if s.get("tags"):
                lines.append(f"**Tags:** {', '.join(s['tags'])}\n")
            if s.get("description"):
                lines.append(f"\n{s['description']}\n")
            if s.get("notes"):
                lines.append(f"\n> {s['notes']}\n")
            if s.get("commits"):
                lines.append(f"\n**Commits:** {', '.join(c[:8] for c in s['commits'])}\n")
            lines.append("\n---\n")
        content = "\n".join(lines)

    if output:
        with open(output, "w") as f:
            f.write(content)
        console.print(f"[green]✓[/green] Exported to {output}")
    else:
        click.echo(content)
