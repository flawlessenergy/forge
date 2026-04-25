"""
Claude CLI integration for forge.

forge sync   — write compiled docs to CLAUDE.md (auto-loaded every session)
forge task   — one-shot task: docs + graph/files → system prompt, task → user message
forge chat   — interactive session with docs + graph/files in system prompt

Context priority (highest to lowest):
  1. graphify graph (graph.json) — focused, token-efficient, task-aware
  2. raw file dump                — fallback when no graph exists
  3. docs only                    -- when --no-context is passed
"""

import os
import shutil
import subprocess
from pathlib import Path

import click
from rich.console import Console

console = Console()

_FORGE_START    = "<!-- forge:start -->"
_FORGE_END      = "<!-- forge:end -->"
_SESSION_FILE   = ".forge/session.md"
_DEFAULT_GRAPH  = "graph.json"


# ── graphify helpers ──────────────────────────────────────────────────────────

def _graphify_cli_available() -> bool:
    return shutil.which("graphify") is not None


def _graph_exists(graph_file: str = _DEFAULT_GRAPH) -> bool:
    return Path(graph_file).exists()


def _query_graph(hint: str, graph_file: str = _DEFAULT_GRAPH) -> str | None:
    """
    Query the graphify graph for context relevant to `hint`.
    Tries Python API first, then CLI subprocess.
    Returns the result string, or None if unavailable.
    """
    if not _graph_exists(graph_file):
        return None

    query = hint.strip() or "overall architecture, main components, key relationships"

    # ── Try Python API (fastest, no subprocess overhead) ──────────────────────
    try:
        from graphify import query_graph as gq  # type: ignore
        result = gq(query)
        if result:
            return str(result)
    except Exception:
        pass

    # ── Try CLI subprocess ─────────────────────────────────────────────────────
    if _graphify_cli_available():
        try:
            result = subprocess.run(
                ["graphify", "query", query, "--graph", graph_file],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, OSError):
            pass

    return None


def _build_graph_hint() -> str:
    return (
        "[dim]Tip: run [bold]forge graph build[/bold] once to index your codebase. "
        "forge will use the graph for focused, token-efficient context instead of "
        "dumping raw files.[/dim]"
    )


# ── core compile ──────────────────────────────────────────────────────────────

def _compile(
    compress: bool = True,
    with_context: bool = True,
    ext: tuple = (),
    max_files: int = 20,
    task_hint: str = "",
    graph_file: str = _DEFAULT_GRAPH,
) -> tuple[str, str]:
    """
    Compile forge docs + codebase context into a single string.

    Returns (content, context_mode) where context_mode is one of:
      "graph"  — used graphify graph (token-efficient)
      "files"  — used raw file dump (fallback)
      "docs"   — docs only, no codebase context
      "empty"  — no docs found
    """
    from forge.commands.run import _load_docs, _collect_context_files
    from forge.core.compress import compress as compress_fn

    doc_sections = _load_docs()
    if not doc_sections:
        return "", "empty"

    parts = []
    for _filename, title, content in doc_sections:
        c = compress_fn(content) if compress else content
        parts.append(f"## {title}\n\n{c}")

    context_mode = "docs"

    if with_context:
        # ── 1. Try graphify graph (preferred) ─────────────────────────────────
        graph_result = _query_graph(task_hint, graph_file)

        if graph_result:
            c = compress_fn(graph_result) if compress else graph_result
            parts.append(f"## Codebase (graph)\n\n{c}")
            context_mode = "graph"

        else:
            # ── 2. Fall back to raw file dump ──────────────────────────────────
            _skip_names = {"CLAUDE.md", "AGENTS.md"}
            ctx_files = [
                (f, c) for f, c in _collect_context_files(
                    root=".", extensions=ext, max_files=max_files
                )
                if os.path.basename(f) not in _skip_names
                and not os.path.normpath(f).startswith(".forge")
            ]
            if ctx_files:
                blocks = []
                for f, content in ctx_files:
                    if content.startswith("["):
                        blocks.append(f"**{f}**\n{content}")
                    else:
                        c = compress_fn(content) if compress else content
                        blocks.append(f"**{f}**\n```\n{c}\n```")
                parts.append("## Codebase\n\n" + "\n\n".join(blocks))
                context_mode = "files"

    return "\n\n---\n\n".join(parts), context_mode


def _write_session_file(content: str) -> Path:
    path = Path(_SESSION_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path.resolve()


def _update_claude_md(content: str) -> tuple[Path, bool]:
    forge_block = (
        f"{_FORGE_START}\n"
        f"<!-- Auto-generated by forge — edit .forge/docs/ not this block -->\n\n"
        f"{content}\n\n"
        f"{_FORGE_END}"
    )
    claude_md = Path("CLAUDE.md")
    created = not claude_md.exists()

    if claude_md.exists():
        existing = claude_md.read_text()
        if _FORGE_START in existing:
            start = existing.find(_FORGE_START)
            end   = existing.find(_FORGE_END, start) + len(_FORGE_END)
            new   = existing[:start] + forge_block + existing[end:]
        else:
            new = forge_block + "\n\n" + existing
    else:
        new = forge_block + "\n"

    claude_md.write_text(new)
    return claude_md, created


def _check_claude() -> None:
    if not shutil.which("claude"):
        console.print(
            "[red]claude CLI not found.[/red]\n"
            "Install it from: https://claude.ai/code"
        )
        raise SystemExit(1)


def _context_mode_line(mode: str, tok: int, compress: bool, graph_file: str) -> str:
    """Print one-line summary of what context mode was used."""
    if mode == "graph":
        return (
            f"[green]forge[/green] → [cyan]graph[/cyan] context  "
            f"[dim]~{tok:,} tokens | {graph_file} | compression {'on' if compress else 'off'}[/dim]"
        )
    elif mode == "files":
        hint = ""
        if not _graph_exists(graph_file):
            hint = "  [dim](run [bold]forge graph build[/bold] to use graph instead)[/dim]"
        return (
            f"[green]forge[/green] → [yellow]file[/yellow] context  "
            f"[dim]~{tok:,} tokens | raw files | compression {'on' if compress else 'off'}[/dim]"
            + hint
        )
    elif mode == "docs":
        return (
            f"[green]forge[/green] → [blue]docs[/blue] only  "
            f"[dim]~{tok:,} tokens | no codebase[/dim]"
        )
    return f"[green]forge[/green] → [dim]~{tok:,} tokens[/dim]"


# ── commands ──────────────────────────────────────────────────────────────────

@click.command("sync")
@click.option("--compress/--no-compress", default=True, show_default=True)
@click.option("--no-context", "skip_context", is_flag=True,
              help="Exclude codebase context")
@click.option("--graph-file", default=_DEFAULT_GRAPH, show_default=True,
              help="graphify graph file to use")
@click.option("--dry-run", is_flag=True,
              help="Print what would be written without touching CLAUDE.md")
@click.option("--strip", is_flag=True,
              help="Remove the forge section from CLAUDE.md")
def sync(compress, skip_context, graph_file, dry_run, strip):
    """
    Write forge docs + codebase context to CLAUDE.md.

    \b
    Claude CLI reads CLAUDE.md at the start of every session.
    Uses graphify graph if graph.json exists; otherwise falls back to raw files.
    Your own CLAUDE.md content is never touched.

    \b
    Examples:
      forge sync                       update CLAUDE.md
      forge sync --no-context          docs only
      forge sync --dry-run             preview without writing
      forge sync --strip               remove forge section
    """
    claude_md = Path("CLAUDE.md")

    if strip:
        if not claude_md.exists() or _FORGE_START not in claude_md.read_text():
            console.print("[dim]No forge section found in CLAUDE.md.[/dim]")
            return
        existing = claude_md.read_text()
        start = existing.find(_FORGE_START)
        end   = existing.find(_FORGE_END, start) + len(_FORGE_END)
        cleaned = (existing[:start] + existing[end:]).strip()
        if not dry_run:
            claude_md.write_text(cleaned + "\n" if cleaned else "")
            console.print("[green]✓[/green] Removed forge section from CLAUDE.md.")
        else:
            console.print("[dim]Would remove forge section from CLAUDE.md.[/dim]")
        return

    try:
        content, mode = _compile(
            compress=compress,
            with_context=not skip_context,
            graph_file=graph_file,
        )
    except FileNotFoundError:
        console.print("[red]Run `forge init` first.[/red]")
        return

    if not content:
        console.print("[yellow]No docs found.[/yellow] Run [bold]forge docs scaffold[/bold] first.")
        return

    if dry_run:
        console.print(content)
        return

    _, created = _update_claude_md(content)
    from forge.core.compress import estimate_tokens
    tok = estimate_tokens(content)
    verb = "created" if created else "updated"
    mode_label = {"graph": "graph", "files": "raw files", "docs": "docs only"}.get(mode, mode)
    console.print(
        f"[green]✓[/green] CLAUDE.md {verb}  "
        f"[dim](~{tok:,} tokens | {mode_label} | compression {'on' if compress else 'off'})[/dim]"
    )
    console.print("[dim]Claude CLI reads this automatically — just run `claude` to start.[/dim]")

    if mode == "files" and not _graph_exists(graph_file):
        console.print(_build_graph_hint())


@click.command("task")
@click.argument("description")
@click.option("--compress/--no-compress", default=True, show_default=True)
@click.option("--no-context", "skip_context", is_flag=True,
              help="Docs only, skip codebase context")
@click.option("--ext", "-e", multiple=True,
              help="Only include these file extensions (e.g. -e .py)")
@click.option("--max-files", default=20, show_default=True)
@click.option("--graph-file", default=_DEFAULT_GRAPH, show_default=True,
              help="graphify graph file to use")
@click.option("--model", "-m", default="", help="Claude model alias (e.g. sonnet, opus)")
@click.option("--output-format", "fmt",
              type=click.Choice(["text", "json", "stream-json"]),
              default="text", show_default=True)
def task(description, compress, skip_context, ext, max_files, graph_file, model, fmt):
    """
    Run a one-shot task through Claude CLI with forge context injected.

    \b
    Context priority:
      1. graphify graph  — focused nodes relevant to your task description
      2. raw file dump   — if no graph.json found
      3. docs only       — if --no-context

    \b
    Examples:
      forge task "implement the login endpoint from TASK-1"
      forge task "write pytest tests for auth.py" -e .py
      forge task "what does models.py do?" --no-context
      forge task "refactor auth.py" --model opus
    """
    _check_claude()

    try:
        content, mode = _compile(
            compress=compress,
            with_context=not skip_context,
            ext=tuple(ext),
            max_files=max_files,
            task_hint=description,       # ← graph query is targeted to this task
            graph_file=graph_file,
        )
    except FileNotFoundError:
        console.print("[red]Run `forge init` first.[/red]")
        return

    from forge.core.compress import estimate_tokens

    if content:
        session_path = _write_session_file(content)
        tok = estimate_tokens(content)
        console.print(_context_mode_line(mode, tok, compress, graph_file))
        console.print()
        cmd = ["claude", "-p", description,
               "--append-system-prompt-file", str(session_path)]
    else:
        console.print("[dim]No forge docs found — sending task without context.[/dim]\n")
        cmd = ["claude", "-p", description]

    if model:
        cmd += ["--model", model]
    if fmt != "text":
        cmd += ["--output-format", fmt]

    if mode == "files" and not _graph_exists(graph_file):
        console.print(_build_graph_hint())

    os.execlp(cmd[0], *cmd)


@click.command("chat")
@click.argument("message", default="")
@click.option("--compress/--no-compress", default=True, show_default=True)
@click.option("--no-context", "skip_context", is_flag=True,
              help="Docs only, skip codebase context")
@click.option("--ext", "-e", multiple=True)
@click.option("--max-files", default=20, show_default=True)
@click.option("--graph-file", default=_DEFAULT_GRAPH, show_default=True,
              help="graphify graph file to use")
@click.option("--model", "-m", default="")
@click.option("--continue", "cont", is_flag=True,
              help="Continue the most recent Claude conversation")
@click.option("--name", "-n", default="", help="Name this session")
def chat(message, compress, skip_context, ext, max_files, graph_file, model, cont, name):
    """
    Open an interactive Claude session with forge context in the system prompt.

    \b
    Context priority:
      1. graphify graph  — focused nodes relevant to your opening message
      2. raw file dump   — if no graph.json found
      3. docs only       — if --no-context

    \b
    Examples:
      forge chat                              full context, no opening message
      forge chat "let's build TASK-1"         graph is queried for TASK-1 relevance
      forge chat --no-context                 docs only
      forge chat --continue                   resume last session
      forge chat --name "auth-sprint"         named session
    """
    _check_claude()

    try:
        content, mode = _compile(
            compress=compress,
            with_context=not skip_context,
            ext=tuple(ext),
            max_files=max_files,
            task_hint=message,            # ← graph query targeted to opening message
            graph_file=graph_file,
        )
    except FileNotFoundError:
        console.print("[red]Run `forge init` first.[/red]")
        return

    from forge.core.compress import estimate_tokens

    cmd = ["claude"]

    if content:
        session_path = _write_session_file(content)
        tok = estimate_tokens(content)
        console.print(_context_mode_line(mode, tok, compress, graph_file))
        cmd += ["--append-system-prompt-file", str(session_path)]
    else:
        console.print(
            "[yellow]No forge docs found.[/yellow] "
            "Run [bold]forge docs scaffold[/bold] to create them."
        )

    if model:
        cmd += ["--model", model]
    if cont:
        cmd += ["--continue"]
    if name:
        cmd += ["--name", name]
    if message:
        cmd.append(message)

    if mode == "files" and not _graph_exists(graph_file):
        console.print(_build_graph_hint())

    console.print()
    os.execlp(cmd[0], *cmd)
