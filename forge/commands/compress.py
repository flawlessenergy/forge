"""Text compression command — caveman-style filler removal."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text

console = Console()


@click.command("compress")
@click.argument("text", default="")
@click.option("--file", "-f", default="", help="Read from file instead of argument")
@click.option("--spec", "-s", default="", help="Compress a spec's description (by ID)")
@click.option("--aggressive", "-a", is_flag=True, help="More aggressive stripping")
@click.option("--copy", "-c", is_flag=True, help="Copy result to clipboard")
@click.option("--stats", is_flag=True, default=True, show_default=True, help="Show compression stats")
def compress(text, file, spec, aggressive, copy, stats):
    """
    Strip filler words from text to reduce AI prompt tokens.

    Removes articles, connectives, hedge phrases while keeping facts,
    numbers, names, and constraints. ~15-30% token reduction.

    Examples:

      forge compress "I need to implement a very fast auth system"

      forge compress -f prompt.txt --copy

      forge compress -s SPEC-001
    """
    from forge.core.compress import compress as compress_fn, compression_ratio, estimate_tokens

    if spec:
        from forge.core.store import get_spec
        s = get_spec(spec)
        if not s:
            console.print(f"[red]Spec {spec.upper()} not found.[/red]")
            return
        text = f"{s['title']}. {s.get('description', '')} {s.get('notes', '')}".strip()

    elif file:
        try:
            with open(file, "r") as fh:
                text = fh.read()
        except FileNotFoundError:
            console.print(f"[red]File not found: {file}[/red]")
            return

    if not text:
        console.print("[yellow]Nothing to compress. Pass text, -f file, or -s SPEC-ID.[/yellow]")
        return

    compressed = compress_fn(text, aggressive=aggressive)
    ratio = compression_ratio(text, compressed)
    orig_tokens = estimate_tokens(text)
    comp_tokens = estimate_tokens(compressed)

    if stats:
        console.print(
            f"[dim]Original: ~{orig_tokens} tokens → Compressed: ~{comp_tokens} tokens "
            f"([green]{ratio}% reduction[/green])[/dim]\n"
        )

    if copy:
        try:
            import pyperclip
            pyperclip.copy(compressed)
            console.print("[green]✓[/green] Copied to clipboard.")
        except Exception:
            console.print("[yellow]pyperclip unavailable — printing instead.[/yellow]")

    click.echo(compressed)
