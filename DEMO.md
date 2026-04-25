# forge — Demo: Building a Todo CLI from Scratch

This walkthrough shows a complete session using forge to spec, build, and track
a small real project: a command-line todo app called **`td`**.

You will see exactly what to type, what forge outputs, and what Claude produces.

---

## What we're building

A Python CLI tool called `td` with three commands:

```bash
td add "buy milk"       # add a todo, stored in ~/.td.json
td list                 # show all todos with status
td done 1               # mark todo #1 as done
```

Simple enough to finish in one session, real enough to show the full workflow.

---

## Prerequisites

- forge installed (`forge --version`)
- Claude CLI installed (`claude --version`)
- Python 3.10+

---

## Step 1 — Create the project

```bash
mkdir td-app
cd td-app
git init
```

**Terminal output:**
```
Initialized empty Git repository in /home/you/td-app/.git/
```

---

## Step 2 — Initialise forge

```bash
forge init --scaffold
```

**Terminal output:**
```
✓ Initialised forge at /home/you/td-app/.forge

  created  persona.md        AI role and behaviour
  created  constitution.md   Non-negotiable coding rules
  created  skills.md         Tech stack and patterns to follow
  created  tasks.md          Current tasks to implement

Next: edit the files in /home/you/td-app/.forge/docs
Then run: forge run
```

forge created four starter documents in `.forge/docs/`. These are the files
you edit to describe your project to Claude.

---

## Step 3 — Fill in the spec docs

You only need to edit two files for this demo: `skills.md` and `tasks.md`.

### Edit skills.md

```bash
forge docs edit skills
```

Replace the placeholder content with:

```markdown
# Skills & Tech Stack

## Language
- Python 3.11+

## Libraries
- Click for CLI argument parsing
- Rich for coloured terminal output
- Plain JSON file (~/.td.json) for storage — no database

## Patterns
- One function per command
- All storage reads/writes go through a single load() / save() helper
- Exit with a clear error message if the JSON file is corrupted

## Do not use
- SQLite or any database
- External HTTP requests
- Any library not in the stdlib except click and rich
```

### Edit tasks.md

```bash
forge docs edit tasks
```

Replace the placeholder content with:

```markdown
# Tasks

## Goal
Build a minimal CLI todo app called `td`.

## Tasks

### [ ] TASK-1: `td add "description"`
**What:** Add a new todo item and save it to ~/.td.json
**Done when:**
- Running `td add "buy milk"` creates ~/.td.json if it doesn't exist
- The item gets a sequential numeric ID (1, 2, 3…)
- Running `td list` shows the new item

### [ ] TASK-2: `td list`
**What:** Print all todos to the terminal
**Done when:**
- Each todo shows: ID, checkbox ([ ] or [x]), and text
- If there are no todos, print "No todos yet."
- Done items appear with a strikethrough or dimmed style using Rich

### [ ] TASK-3: `td done <id>`
**What:** Mark a todo as done by its ID
**Done when:**
- `td done 1` marks todo #1 as done
- The item shows [x] in `td list` after running
- Prints an error if the ID does not exist
```

### Check status

```bash
forge docs status
```

**Terminal output:**
```
Ready:
  ✓ skills.md
  ✓ tasks.md
Needs editing:
  ~ persona.md       →  forge docs edit persona
  ~ constitution.md  →  forge docs edit constitution

2/6 docs filled in
```

The two files you edited are marked ready. `persona.md` and `constitution.md`
are still the default templates — that is fine, they are usable as-is.

---

## Step 4 — Preview the token cost

Before sending anything to Claude, check how many tokens will be used:

```bash
forge run --preview
```

**Terminal output:**
```
╭──────────────────────┬──────────────────┬──────────────╮
│ Section              │ Source           │  Est. tokens │
├──────────────────────┼──────────────────┼──────────────┤
│ Role                 │ persona.md       │         ~132 │
│ Rules                │ constitution.md  │         ~266 │
│ Tech Stack           │ skills.md        │          ~89 │
│ Tasks                │ tasks.md         │         ~185 │
│ Instruction          │ —                │          ~32 │
╰──────────────────────┴──────────────────┴──────────────╯

  Total est. tokens: ~704  |  Compression: on

Run without --preview to generate and copy the full prompt.
```

~700 tokens for the full context — very lean.

---

## Step 5 — Run the task

### Option A — Interactive session (recommended for back-and-forth)

```bash
forge chat "let's build all three tasks for the td todo app"
```

**Terminal output:**
```
forge → context loaded  ~704 tokens | compression on

> let's build all three tasks for the td todo app
```

Claude opens in an interactive session already knowing your stack, rules, and
tasks. You can ask follow-up questions, request changes, and iterate.

---

### Option B — One-shot task (fastest for a clear spec)

```bash
forge task "implement all three tasks: td add, td list, td done. Return a single td.py file."
```

**Terminal output:**
```
Context: ~704 tokens | 0 lines → system prompt

```

Claude streams its response directly to the terminal. Example response:

---

**Claude's response:**

```
I'll implement the three tasks as a single `td.py` file using Click and Rich.

**td.py**
```python
import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.text import Text

STORE = Path.home() / ".td.json"
console = Console()


def load() -> list[dict]:
    if not STORE.exists():
        return []
    try:
        return json.loads(STORE.read_text())
    except json.JSONDecodeError:
        console.print("[red]Error: ~/.td.json is corrupted. Delete it and start fresh.[/red]")
        sys.exit(1)


def save(todos: list[dict]) -> None:
    STORE.write_text(json.dumps(todos, indent=2))


@click.group()
def cli():
    """td — a minimal todo CLI."""
    pass


@cli.command("add")
@click.argument("text")
def add(text: str) -> None:
    """Add a new todo item."""
    todos = load()
    next_id = max((t["id"] for t in todos), default=0) + 1
    todos.append({"id": next_id, "text": text, "done": False})
    save(todos)
    console.print(f"[green]✓[/green] Added #{next_id}: {text}")


@cli.command("list")
def list_todos() -> None:
    """List all todo items."""
    todos = load()
    if not todos:
        console.print("[dim]No todos yet.[/dim]")
        return
    for t in todos:
        if t["done"]:
            line = Text(f"  [x] #{t['id']}  {t['text']}", style="dim strike")
        else:
            line = Text(f"  [ ] #{t['id']}  {t['text']}")
        console.print(line)


@cli.command("done")
@click.argument("id", type=int)
def mark_done(id: int) -> None:
    """Mark a todo as done."""
    todos = load()
    for t in todos:
        if t["id"] == id:
            t["done"] = True
            save(todos)
            console.print(f"[green]✓[/green] #{id} marked as done.")
            return
    console.print(f"[red]No todo with ID {id}.[/red]")


if __name__ == "__main__":
    cli()
```

**Install and test:**
```bash
pip install click rich
python td.py add "buy milk"
python td.py add "write tests"
python td.py list
python td.py done 1
python td.py list
```
```

---

## Step 6 — Save the file and test it

Copy `td.py` from Claude's response into your project:

```bash
# (paste td.py from Claude's output)

pip install click rich
python td.py add "buy milk"
python td.py add "write tests"
python td.py list
```

**Terminal output:**
```
✓ Added #1: buy milk
✓ Added #2: write tests
  [ ] #1  buy milk
  [ ] #2  write tests
```

```bash
python td.py done 1
python td.py list
```

**Terminal output:**
```
✓ #1 marked as done.
  #1  buy milk       ← dimmed and strikethrough
  [ ] #2  write tests
```

All three tasks working.

---

## Step 7 — Commit the work

```bash
git add td.py
git commit -m "Implement td todo CLI (add, list, done)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

The `Co-Authored-By: Claude` line is what forge uses to detect AI commits.
Claude CLI adds this automatically when it commits; add it manually when you
paste code from a `forge task` session.

---

## Step 8 — Check the commit tracker

```bash
forge commits log
```

**Terminal output:**
```
╭───────────┬─────────────┬────────────┬──────────────────┬──────────────────────────╮
│ SHA       │ Date        │ Type       │ Author           │ Message                  │
├───────────┼─────────────┼────────────┼──────────────────┼──────────────────────────┤
│ a1b2c3d   │ 2026-04-25  │ 🤖 AI      │ you              │ Implement td todo CLI    │
╰───────────┴─────────────┴────────────┴──────────────────┴──────────────────────────╯
Showing 1 commit — 1 AI / 0 manual
```

forge detected the `Co-Authored-By: Claude` signature and labelled it 🤖 AI.

---

## Step 9 — Mark specs as done and track them

First, add the three tasks as tracked specs:

```bash
forge spec add "td add command"  --priority high --tags cli,storage
forge spec add "td list command" --priority high --tags cli
forge spec add "td done command" --priority high --tags cli
```

**Terminal output:**
```
✓ Created SPEC-001: td add command
✓ Created SPEC-002: td list command
✓ Created SPEC-003: td done command
```

Link the commit to each spec:

```bash
forge spec link SPEC-001 --commit a1b2c3d
forge spec link SPEC-002 --commit a1b2c3d
forge spec link SPEC-003 --commit a1b2c3d
```

Mark all three done:

```bash
forge spec done SPEC-001
forge spec done SPEC-002
forge spec done SPEC-003
```

---

## Step 10 — Check the project dashboard

```bash
forge stats
```

**Terminal output:**
```
╭───────────────── Specs ──────────────────╮  ╭──────────────── Commits ─────────────────╮
│   Total:       3                         │  │   Last 1 commit analysed                 │
│   ████████████████████████████████████…  │  │                                          │
│   100% done                              │  │   ████████████████████████████████████…  │
│                                          │  │   100% AI                                │
│   ⬜ Pending:    0                       │  │                                          │
│   ◑ In progress: 0                       │  │   🤖 AI:     1                           │
│   ● Done:        3                       │  │   ✍ Manual:  0                           │
│   ✗ Blocked:     0                       │  │                                          │
│                                          │  │   Branch: main                           │
│   Top tags: cli(3), storage(1)           │  │                                          │
╰──────────────────────────────────────────╯  ╰──────────────────────────────────────────╯
```

3 specs done, 1 AI commit, 0 manual commits. Clean sprint.

---

## What the full session looked like

```
mkdir td-app && cd td-app && git init   # 10 seconds
forge init --scaffold                   # 5 seconds
forge docs edit skills                  # 2 minutes — describe your stack
forge docs edit tasks                   # 3 minutes — describe what to build
forge run --preview                     # 5 seconds — check token cost
forge task "implement all three tasks"  # Claude builds the app
# paste td.py, test it                  # 2 minutes
git add td.py && git commit -m "..."    # 30 seconds
forge commits log                       # 5 seconds
forge spec add / done                   # 1 minute
forge stats                             # 5 seconds
```

**Total time: ~10 minutes.** The spec docs took the longest — and those are
reusable across every future session on this project.

---

## Extending the demo (try these next)

### Ask Claude to add a new feature in the same session

```bash
forge chat --continue "add a `td delete <id>` command that removes a todo permanently"
```

`--continue` resumes the last conversation so Claude remembers the context.

### Ask for tests

```bash
forge task "write pytest tests for td.py covering add, list, and done" -e .py
```

### Ask Claude to review the code

```bash
forge prompt template SPEC-001 --style review --copy
# paste into claude
```

### See only AI commits after several sessions

```bash
forge commits log --ai-only
forge commits stats
```

---

## Key things to notice

| What happened | Why it matters |
|---|---|
| Claude knew the stack from the first message | `skills.md` was in the system prompt |
| Claude followed the constraints (no SQLite, no HTTP) | `constitution.md` rules were enforced |
| The token count was ~700, not 5,000 | Compression stripped filler from the docs |
| The commit was automatically labelled 🤖 AI | `Co-Authored-By: Claude` was detected |
| The whole spec-to-code loop took ~10 minutes | forge removed the context-setup overhead |
