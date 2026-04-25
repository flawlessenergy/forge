"""Manage forge spec documents: scaffold, list, edit, show, status."""

import os
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


def _docs_dir() -> Path:
    from forge.core.store import get_store
    return get_store() / "docs"


def _doc_path(name: str) -> Path:
    return _docs_dir() / name


def _ensure_docs_dir() -> Path:
    d = _docs_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _doc_status(path: Path, template_content: str) -> str:
    """Return 'empty', 'template', or 'edited'."""
    if not path.exists():
        return "missing"
    content = path.read_text().strip()
    if not content:
        return "empty"
    template_lines = set(
        l.strip() for l in template_content.splitlines()
        if l.strip() and not l.startswith("#")
    )
    user_lines = set(
        l.strip() for l in content.splitlines()
        if l.strip() and not l.startswith("#")
    )
    # If most non-heading lines are unchanged, it's still a template
    if not user_lines - template_lines:
        return "template"
    return "edited"


@click.group()
def docs():
    """Manage forge spec documents (persona, constitution, skills, tasks…)."""
    pass


@docs.command("scaffold")
@click.option("--all", "include_all", is_flag=True,
              help="Also create optional files (architecture.md, context.md)")
@click.option("--force", "-f", is_flag=True,
              help="Overwrite existing files")
def scaffold(include_all, force):
    """
    Create starter spec documents in .forge/docs/.

    Required files: persona.md, constitution.md, skills.md, tasks.md
    Optional files: architecture.md, context.md  (use --all to create)

    Edit these files to describe your project, then run `forge run`.
    """
    from forge.core.templates import SCAFFOLD_FILES
    d = _ensure_docs_dir()
    created, skipped = [], []

    for filename, (content, desc, required) in SCAFFOLD_FILES.items():
        if not required and not include_all:
            continue
        path = d / filename
        if path.exists() and not force:
            skipped.append(filename)
            continue
        path.write_text(content)
        created.append((filename, desc))

    for filename, desc in created:
        console.print(f"  [green]created[/green]  {filename}  [dim]{desc}[/dim]")
    for filename in skipped:
        console.print(f"  [dim]exists[/dim]   {filename}  [dim](use --force to overwrite)[/dim]")

    if created:
        console.print(f"\n[bold]Next:[/bold] edit the files in [cyan]{d}[/cyan]")
        console.print("[dim]Then run: forge run[/dim]")
    else:
        console.print("[dim]Nothing to create. Use --force to overwrite existing files.[/dim]")


@docs.command("list")
def list_docs():
    """Show all spec documents with their edit status."""
    from forge.core.templates import SCAFFOLD_FILES
    try:
        d = _docs_dir()
    except FileNotFoundError:
        console.print("[red]Run `forge init` first.[/red]")
        return

    STATUS_STYLE = {
        "edited":   ("[green]✓ edited[/green]",   "green"),
        "template": ("[yellow]~ template[/yellow]", "yellow"),
        "empty":    ("[dim]  empty[/dim]",          "dim"),
        "missing":  ("[red]  missing[/red]",        "red"),
    }

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim")
    table.add_column("File", min_width=20)
    table.add_column("Status", width=14)
    table.add_column("Size", width=8, justify="right")
    table.add_column("Description")

    known = set()
    for filename, (template_content, desc, required) in SCAFFOLD_FILES.items():
        known.add(filename)
        path = d / filename
        status = _doc_status(path, template_content)
        status_str, _ = STATUS_STYLE.get(status, (status, "white"))
        size = f"{path.stat().st_size:,}B" if path.exists() else "—"
        req_marker = "" if required else "[dim]opt[/dim]"
        table.add_row(filename, status_str, size, f"{desc} {req_marker}")

    # Any user-added files not in the template list
    if d.exists():
        for path in sorted(d.glob("*.md")):
            if path.name not in known:
                size = f"{path.stat().st_size:,}B"
                table.add_row(path.name, "[cyan]custom[/cyan]", size, "[dim]user file[/dim]")

    console.print(table)
    console.print(f"[dim]Location: {d}[/dim]")


@docs.command("edit")
@click.argument("name")
def edit(name):
    """
    Open a spec document in $EDITOR.

    NAME can be the full filename (persona.md) or just the stem (persona).

    Example: forge docs edit tasks
    """
    if not name.endswith(".md"):
        name = name + ".md"
    try:
        path = _doc_path(name)
    except FileNotFoundError:
        console.print("[red]Run `forge init` first.[/red]")
        return

    if not path.exists():
        # Auto-scaffold this file if it's a known template
        from forge.core.templates import SCAFFOLD_FILES
        if name in SCAFFOLD_FILES:
            _ensure_docs_dir()
            path.write_text(SCAFFOLD_FILES[name][0])
            console.print(f"[dim]Created {name} from template.[/dim]")
        else:
            _ensure_docs_dir()
            path.write_text(f"# {name.replace('.md','').title()}\n\n")

    editor = os.environ.get("EDITOR", os.environ.get("VISUAL", "vi"))
    os.execlp(editor, editor, str(path))


@docs.command("show")
@click.argument("name")
def show(name):
    """Print the contents of a spec document."""
    if not name.endswith(".md"):
        name = name + ".md"
    try:
        path = _doc_path(name)
    except FileNotFoundError:
        console.print("[red]Run `forge init` first.[/red]")
        return

    if not path.exists():
        console.print(f"[red]{name} not found. Run `forge docs scaffold`.[/red]")
        return

    console.print(Panel(path.read_text(), title=name, border_style="cyan"))


@docs.command("add")
@click.argument("filepath", type=click.Path(exists=True))
@click.option("--name", "-n", default="", help="Override filename in .forge/docs/")
def add(filepath, name):
    """
    Copy an existing markdown file into .forge/docs/.

    Useful for bringing in your own CLAUDE.md, AGENTS.md, etc.

    Example: forge docs add ~/my-team/CLAUDE.md
    """
    src = Path(filepath)
    dest_name = name if name else src.name
    if not dest_name.endswith(".md"):
        dest_name += ".md"

    _ensure_docs_dir()
    dest = _docs_dir() / dest_name
    dest.write_text(src.read_text())
    console.print(f"[green]✓[/green] Added [bold]{dest_name}[/bold] ({dest.stat().st_size:,} bytes)")


@docs.command("remove")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True)
def remove(name, yes):
    """Remove a spec document from .forge/docs/."""
    if not name.endswith(".md"):
        name = name + ".md"
    path = _doc_path(name)
    if not path.exists():
        console.print(f"[red]{name} not found.[/red]")
        return
    if not yes:
        click.confirm(f"Delete {name}?", abort=True)
    path.unlink()
    console.print(f"[green]✓[/green] Removed {name}.")


@docs.command("status")
def status():
    """Quick summary: which docs are filled in and which still need editing."""
    from forge.core.templates import SCAFFOLD_FILES
    try:
        d = _docs_dir()
    except FileNotFoundError:
        console.print("[red]Run `forge init` first.[/red]")
        return

    ready, needs_edit, missing = [], [], []
    for filename, (template_content, desc, required) in SCAFFOLD_FILES.items():
        path = d / filename
        s = _doc_status(path, template_content)
        if s == "edited":
            ready.append(filename)
        elif s in ("template", "empty"):
            needs_edit.append(filename)
        else:
            missing.append(filename)

    if ready:
        console.print("[green]Ready:[/green]")
        for f in ready:
            console.print(f"  ✓ {f}")
    if needs_edit:
        console.print("[yellow]Needs editing:[/yellow]")
        for f in needs_edit:
            console.print(f"  ~ {f}  →  forge docs edit {f.replace('.md','')}")
    if missing:
        console.print("[red]Missing:[/red]")
        for f in missing:
            console.print(f"  ✗ {f}  →  forge docs scaffold")

    total = len(SCAFFOLD_FILES)
    done = len(ready)
    console.print(f"\n[dim]{done}/{total} docs filled in[/dim]")

    if done == total:
        console.print("[green]All docs ready — run: forge run[/green]")
    elif not ready and not needs_edit:
        console.print("[dim]Start with: forge docs scaffold[/dim]")
