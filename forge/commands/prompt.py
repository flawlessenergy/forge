"""AI prompt builder: combines spec + compressed codebase context into a ready-to-use prompt."""

import click
from rich.console import Console
from rich.panel import Panel

console = Console()

_PROMPT_TEMPLATE = """\
## Spec: {spec_id} — {title}
**Status:** {status} | **Priority:** {priority}
**Tags:** {tags}

### Description
{description}

{notes_block}\
### Codebase Context
{context}

### Task
Implement the spec above. Use the codebase context to understand existing patterns.
Maintain consistency with the existing code style. Return only the changed files.
"""


@click.group()
def prompt():
    """Build AI prompts from specs and codebase context."""
    pass


@prompt.command("build")
@click.argument("spec_id")
@click.option("--compress", "-c", is_flag=True, default=True, show_default=True,
              help="Compress context to reduce tokens")
@click.option("--no-compress", is_flag=True, help="Disable compression")
@click.option("--copy", is_flag=True, help="Copy prompt to clipboard")
@click.option("--output", "-o", default="", help="Save prompt to file")
@click.option("--context-files", "-f", multiple=True,
              help="Specific files to include (default: auto-detect from spec tags)")
@click.option("--max-files", default=10, show_default=True,
              help="Max context files to include")
def build(spec_id, compress, no_compress, copy, output, context_files, max_files):
    """
    Build a structured AI prompt for a spec.

    Combines the spec description with relevant codebase files,
    applies compression, and outputs a ready-to-paste prompt.

    Example:
      forge prompt build SPEC-001 --copy
      forge prompt build SPEC-001 -o prompt.md --no-compress
    """
    from forge.core.store import get_spec
    from forge.core.compress import compress as compress_fn, estimate_tokens

    s = get_spec(spec_id)
    if not s:
        console.print(f"[red]Spec {spec_id.upper()} not found.[/red]")
        return

    should_compress = compress and not no_compress

    # Collect context files
    import os
    from forge.commands.context import _collect_files

    if context_files:
        files = list(context_files)
    else:
        keywords = [s["title"]] + s.get("tags", [])
        all_files = _collect_files(".")
        scored = []
        for f in all_files:
            score = sum(1 for kw in keywords if kw.lower() in f.lower())
            if score > 0:
                scored.append((score, f))
        scored.sort(reverse=True)
        files = [f for _, f in scored[:max_files]]

    # Build context block
    ctx_parts = []
    for f in files:
        try:
            with open(f, "r", errors="replace") as fh:
                content = fh.read()
            if should_compress:
                content = compress_fn(content)
            ctx_parts.append(f"**{f}**\n```\n{content}\n```")
        except (OSError, PermissionError):
            ctx_parts.append(f"**{f}** — [could not read]")

    if not ctx_parts:
        context_str = "_No relevant files found. Consider adding --context-files._"
    else:
        context_str = "\n\n".join(ctx_parts)

    if should_compress:
        context_str = compress_fn(context_str)

    notes_block = ""
    if s.get("notes"):
        notes = compress_fn(s["notes"]) if should_compress else s["notes"]
        notes_block = f"### Notes\n{notes}\n\n"

    description = s.get("description", "")
    if should_compress:
        description = compress_fn(description)

    result = _PROMPT_TEMPLATE.format(
        spec_id=s["id"],
        title=s["title"],
        status=s["status"],
        priority=s["priority"],
        tags=", ".join(s.get("tags", [])) or "—",
        description=description or "_No description._",
        notes_block=notes_block,
        context=context_str,
    )

    tok = estimate_tokens(result)
    console.print(
        f"[dim]Prompt ready — ~{tok:,} tokens | {len(files)} context files "
        f"| compression {'on' if should_compress else 'off'}[/dim]\n"
    )

    if output:
        with open(output, "w") as fh:
            fh.write(result)
        console.print(f"[green]✓[/green] Saved to {output}")
        return

    if copy:
        try:
            import pyperclip
            pyperclip.copy(result)
            console.print("[green]✓[/green] Copied to clipboard.")
            return
        except Exception:
            console.print("[yellow]pyperclip unavailable — printing instead.[/yellow]")

    click.echo(result)


@prompt.command("template")
@click.argument("spec_id")
@click.option("--style",
              type=click.Choice(["implement", "review", "refactor", "debug", "test"]),
              default="implement",
              show_default=True)
@click.option("--copy", is_flag=True)
def template(spec_id, style, copy):
    """
    Generate a task-specific prompt template for a spec.

    Styles: implement, review, refactor, debug, test
    """
    from forge.core.store import get_spec
    s = get_spec(spec_id)
    if not s:
        console.print(f"[red]Spec {spec_id.upper()} not found.[/red]")
        return

    templates = {
        "implement": (
            f"Implement {s['id']}: {s['title']}\n\n"
            f"{s.get('description', '')}\n\n"
            "Requirements:\n- Follow existing code patterns\n"
            "- Write tests for new code\n- Return only changed files"
        ),
        "review": (
            f"Review the implementation of {s['id']}: {s['title']}\n\n"
            "Check for:\n- Correctness\n- Edge cases\n- Performance issues\n"
            "- Security vulnerabilities\n- Code style consistency"
        ),
        "refactor": (
            f"Refactor the code related to {s['id']}: {s['title']}\n\n"
            "Goals:\n- Improve readability\n- Reduce duplication\n"
            "- Maintain existing behavior (no feature changes)"
        ),
        "debug": (
            f"Debug {s['id']}: {s['title']}\n\n"
            f"{s.get('description', '')}\n\n"
            "Find and fix the root cause. Explain what was wrong."
        ),
        "test": (
            f"Write tests for {s['id']}: {s['title']}\n\n"
            f"{s.get('description', '')}\n\n"
            "Cover: happy path, edge cases, error conditions."
        ),
    }

    result = templates[style]
    if copy:
        try:
            import pyperclip
            pyperclip.copy(result)
            console.print("[green]✓[/green] Copied to clipboard.")
            return
        except Exception:
            pass
    click.echo(result)
