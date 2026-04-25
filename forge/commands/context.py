"""Context dump commands: generate compressed codebase context for AI prompting."""

import os
import subprocess
import click
from rich.console import Console
from rich.panel import Panel

console = Console()

_SKIP_DIRS = {
    "__pycache__", "node_modules", ".git", "venv", ".venv",
    ".mypy_cache", ".pytest_cache", "dist", "build", ".forge",
}
_SKIP_EXTS = {
    ".pyc", ".pyo", ".pyd", ".so", ".dylib", ".dll", ".exe",
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico", ".woff",
    ".woff2", ".ttf", ".eot", ".mp3", ".mp4", ".zip", ".tar",
    ".gz", ".lock",
}
_MAX_FILE_BYTES = 50_000  # skip files larger than 50 KB


def _should_include(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext not in _SKIP_EXTS


def _collect_files(root: str = ".") -> list[str]:
    result = []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in sorted(dirs) if d not in _SKIP_DIRS and not d.startswith(".")]
        for f in sorted(files):
            if not f.startswith("."):
                full = os.path.join(dirpath, f)
                if _should_include(full):
                    result.append(full)
    return result


@click.group()
def context():
    """Generate codebase context for AI prompting."""
    pass


@context.command("dump")
@click.option("--compress", "-c", is_flag=True, help="Apply caveman compression")
@click.option("--no-content", is_flag=True, help="File tree only, no file contents")
@click.option("--ext", "-e", multiple=True, help="Only include these extensions (e.g. -e .py -e .ts)")
@click.option("--output", "-o", default="", help="Write to file instead of stdout")
@click.option("--copy", is_flag=True, help="Copy output to clipboard")
@click.option("--tokens", is_flag=True, help="Show estimated token count")
@click.argument("path", default=".")
def dump(compress, no_content, ext, output, copy, tokens, path):
    """
    Dump the entire codebase as a single context block.

    Useful for pasting into Claude to give it full project context
    while keeping token usage low (use --compress to shrink further).
    """
    from forge.core.compress import compress as compress_fn, estimate_tokens, compression_ratio

    files = _collect_files(path)
    if ext:
        files = [f for f in files if os.path.splitext(f)[1].lower() in ext]

    sections = []

    # File tree header
    tree_lines = []
    prev_dir = None
    for f in files:
        d = os.path.dirname(f)
        if d != prev_dir:
            tree_lines.append(f"  {d}/")
            prev_dir = d
        tree_lines.append(f"    {os.path.basename(f)}")
    sections.append("# File tree\n" + "\n".join(tree_lines))

    if not no_content:
        for f in files:
            try:
                size = os.path.getsize(f)
                if size > _MAX_FILE_BYTES:
                    sections.append(f"\n# {f}\n[file too large — {size // 1024} KB, skipped]\n")
                    continue
                with open(f, "r", errors="replace") as fh:
                    content = fh.read()
                if compress:
                    content = compress_fn(content)
                sections.append(f"\n# {f}\n```\n{content}\n```\n")
            except (OSError, PermissionError):
                sections.append(f"\n# {f}\n[could not read]\n")

    result = "\n".join(sections)

    if tokens:
        tok = estimate_tokens(result)
        console.print(f"[dim]~{tok:,} tokens estimated[/dim]")
        if compress:
            orig = "\n".join(sections)  # already compressed above, just note it
            console.print(f"[dim](compression already applied)[/dim]")

    if output:
        with open(output, "w") as fh:
            fh.write(result)
        console.print(f"[green]✓[/green] Context written to {output}")
        return

    if copy:
        try:
            import pyperclip
            pyperclip.copy(result)
            console.print(f"[green]✓[/green] Copied to clipboard ({len(result):,} chars).")
            return
        except Exception:
            console.print("[yellow]pyperclip not available — printing instead.[/yellow]")

    click.echo(result)


@context.command("spec")
@click.argument("spec_id")
@click.option("--compress", "-c", is_flag=True, help="Apply compression")
@click.option("--copy", is_flag=True, help="Copy to clipboard")
def spec_context(spec_id, compress, copy):
    """
    Generate focused context for a specific spec.

    Finds files related to the spec's tags/title and outputs them.
    """
    from forge.core.store import get_spec
    from forge.core.compress import compress as compress_fn, estimate_tokens

    s = get_spec(spec_id)
    if not s:
        console.print(f"[red]Spec {spec_id.upper()} not found.[/red]")
        return

    keywords = [s["title"]] + s.get("tags", [])
    files = _collect_files(".")

    # Score files by keyword matches in their path
    scored = []
    for f in files:
        score = sum(1 for kw in keywords if kw.lower() in f.lower())
        if score > 0:
            scored.append((score, f))
    scored.sort(reverse=True)
    relevant = [f for _, f in scored[:15]] or files[:10]

    sections = [
        f"# Spec: {s['id']} — {s['title']}\n"
        f"Status: {s['status']} | Priority: {s['priority']}\n"
        f"Tags: {', '.join(s.get('tags', []))}\n\n"
        f"{s.get('description', '')}"
    ]

    for f in relevant:
        try:
            with open(f, "r", errors="replace") as fh:
                content = fh.read()
            if compress:
                content = compress_fn(content)
            sections.append(f"\n# {f}\n```\n{content}\n```")
        except (OSError, PermissionError):
            pass

    result = "\n".join(sections)
    tok = estimate_tokens(result)
    console.print(f"[dim]~{tok:,} tokens | {len(relevant)} files[/dim]")

    if copy:
        try:
            import pyperclip
            pyperclip.copy(result)
            console.print("[green]✓[/green] Copied to clipboard.")
            return
        except Exception:
            pass

    click.echo(result)
