import click
from rich.console import Console

from forge.commands.spec import spec
from forge.commands.commits import commits
from forge.commands.graph import graph
from forge.commands.context import context
from forge.commands.compress import compress
from forge.commands.prompt import prompt
from forge.commands.stats import stats
from forge.commands.docs import docs
from forge.commands.run import run
from forge.commands.bridge import sync, task, chat

console = Console()


@click.group()
@click.version_option("0.1.0", prog_name="forge")
def cli():
    """forge — specs-driven development, wired into Claude CLI.

    \b
    Core workflow:
      forge init --scaffold              set up forge in your project
      forge docs edit tasks              describe what to build
      forge chat                         open Claude with full context loaded
      forge task "implement X"           one-shot task, no session needed

    \b
    Context management:
      forge sync                         write docs → CLAUDE.md (auto-loaded)
      forge docs scaffold / edit / list  manage your spec documents
      forge run --preview                inspect token count before sending

    \b
    Project tracking:
      forge spec add / list / done       track specs as SPEC-001, SPEC-002…
      forge commits log                  see AI vs manual commits
      forge stats                        project dashboard
    """
    pass


@cli.command("init")
@click.option("--github-token", default="", help="GitHub personal access token (optional)")
@click.option("--scaffold", is_flag=True, default=False,
              help="Also run `forge docs scaffold` after init")
def init(github_token, scaffold):
    """Initialise forge in the current directory."""
    from forge.core.store import init_store, save_config, load_config
    store = init_store()
    if github_token:
        cfg = load_config()
        cfg["github_token"] = github_token
        save_config(cfg)
    console.print(f"[green]✓[/green] Initialised forge at [bold]{store}[/bold]")

    if scaffold:
        from forge.commands.docs import scaffold as scaffold_cmd
        console.print()
        ctx = click.get_current_context()
        ctx.invoke(scaffold_cmd, include_all=False, force=False)
    else:
        console.print(
            "\n[dim]Next steps:[/dim]\n"
            "  forge docs scaffold        create spec documents\n"
            "  forge docs edit tasks      describe what to build\n"
            "  forge docs edit skills     set your tech stack\n"
            "  forge chat                 open Claude with full context\n"
        )


@cli.command("config")
@click.option("--github-token", default=None, help="Set GitHub personal access token")
@click.option(
    "--ai-signature", "ai_signatures", multiple=True,
    help="Add extra AI signature pattern (regex). Can be repeated."
)
@click.option("--show", is_flag=True, help="Print current config")
def config_cmd(github_token, ai_signatures, show):
    """View or update forge configuration."""
    from forge.core.store import load_config, save_config
    import json as _json
    try:
        cfg = load_config()
    except FileNotFoundError:
        console.print("[red]Run `forge init` first.[/red]")
        return

    if show:
        console.print(_json.dumps(cfg, indent=2))
        return

    if github_token is not None:
        cfg["github_token"] = github_token
    if ai_signatures:
        existing = cfg.get("ai_signatures", [])
        for sig in ai_signatures:
            if sig not in existing:
                existing.append(sig)
        cfg["ai_signatures"] = existing

    save_config(cfg)
    console.print("[green]✓[/green] Config updated.")


cli.add_command(spec)
cli.add_command(commits)
cli.add_command(graph)
cli.add_command(context)
cli.add_command(compress)
cli.add_command(prompt)
cli.add_command(stats)
cli.add_command(docs)
cli.add_command(run)
cli.add_command(sync)
cli.add_command(task)
cli.add_command(chat)
