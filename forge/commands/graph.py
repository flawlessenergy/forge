"""Codebase graph commands via graphify integration."""

import subprocess
import shutil
import click
from rich.console import Console
from rich.panel import Panel

console = Console()

_GRAPHIFY_MISSING = (
    "[yellow]graphify not installed.[/yellow]\n"
    "Install it with:\n"
    "  pip install graphify\n"
    "or: pipx install graphify\n\n"
    "Docs: https://github.com/safishamsi/graphify"
)


def _graphify_available() -> bool:
    return shutil.which("graphify") is not None


def _run_graphify(args: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(
        ["graphify"] + args,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


@click.group()
def graph():
    """Codebase knowledge graph (powered by graphify)."""
    pass


@graph.command("build")
@click.argument("path", default=".")
@click.option("--output", "-o", default="graph.json", show_default=True, help="Output graph file")
@click.option("--html", is_flag=True, help="Also generate interactive HTML visualization")
def build(path, output, html):
    """Build a knowledge graph of the codebase."""
    if not _graphify_available():
        console.print(Panel(_GRAPHIFY_MISSING, title="graphify required", border_style="yellow"))
        return

    args = [path, "--output", output]
    if html:
        args += ["--html"]

    console.print(f"[cyan]Building graph for[/cyan] {path} …")
    code, out, err = _run_graphify(args)

    if code != 0:
        console.print(f"[red]graphify failed:[/red]\n{err}")
        return

    console.print(f"[green]✓[/green] Graph saved to [bold]{output}[/bold]")
    if out:
        console.print(out)


@graph.command("query")
@click.argument("question")
@click.option("--graph-file", "-g", default="graph.json", show_default=True)
def query(question, graph_file):
    """Query the codebase graph with a natural language question."""
    if not _graphify_available():
        console.print(Panel(_GRAPHIFY_MISSING, title="graphify required", border_style="yellow"))
        return

    code, out, err = _run_graphify(["query", question, "--graph", graph_file])
    if code != 0:
        console.print(f"[red]Query failed:[/red]\n{err}")
        return
    console.print(out)


@graph.command("path")
@click.argument("node_a")
@click.argument("node_b")
@click.option("--graph-file", "-g", default="graph.json", show_default=True)
def path_cmd(node_a, node_b, graph_file):
    """Find the shortest path between two nodes in the graph."""
    if not _graphify_available():
        console.print(Panel(_GRAPHIFY_MISSING, title="graphify required", border_style="yellow"))
        return

    code, out, err = _run_graphify(["path", node_a, node_b, "--graph", graph_file])
    if code != 0:
        console.print(f"[red]Path query failed:[/red]\n{err}")
        return
    console.print(out)


@graph.command("context")
@click.argument("topic", default="")
@click.option("--graph-file", "-g", default="graph.json", show_default=True)
@click.option("--compress", "-c", is_flag=True, help="Apply caveman compression to the output")
@click.option("--copy", is_flag=True, help="Copy result to clipboard")
def context(topic, graph_file, compress, copy):
    """
    Extract relevant context from the graph for AI prompting.

    Queries the graph for a topic and returns a compressed summary
    suitable for pasting into a Claude / AI prompt.
    """
    if not _graphify_available():
        # Fallback: simple file tree
        console.print(
            "[yellow]graphify not found — showing basic file tree instead.[/yellow]\n"
        )
        _fallback_tree(compress, copy)
        return

    query_text = topic if topic else "overall architecture and main components"
    code, out, err = _run_graphify(["query", query_text, "--graph", graph_file])
    if code != 0:
        console.print(f"[red]Failed:[/red]\n{err}")
        return

    result = out
    if compress:
        from forge.core.compress import compress as compress_fn, compression_ratio
        compressed = compress_fn(result)
        ratio = compression_ratio(result, compressed)
        result = compressed
        console.print(f"[dim]Compressed {ratio}% token reduction[/dim]\n")

    if copy:
        try:
            import pyperclip
            pyperclip.copy(result)
            console.print("[green]✓[/green] Copied to clipboard.")
        except Exception:
            console.print("[yellow]pyperclip not available — printing instead.[/yellow]")

    click.echo(result)


def _fallback_tree(compress: bool = False, copy: bool = False) -> None:
    """Basic file tree when graphify is not installed."""
    import os

    lines = []
    for root, dirs, files in os.walk("."):
        # Skip hidden and common noise dirs
        dirs[:] = [
            d for d in sorted(dirs)
            if not d.startswith(".") and d not in {"__pycache__", "node_modules", ".git", "venv", ".venv"}
        ]
        level = root.replace(".", "").count(os.sep)
        indent = "  " * level
        lines.append(f"{indent}{os.path.basename(root)}/")
        for f in sorted(files):
            if not f.startswith("."):
                lines.append(f"{indent}  {f}")

    result = "\n".join(lines)

    if compress:
        from forge.core.compress import compress as compress_fn
        result = compress_fn(result)

    if copy:
        try:
            import pyperclip
            pyperclip.copy(result)
            console.print("[green]✓[/green] Copied to clipboard.")
        except Exception:
            pass

    click.echo(result)
