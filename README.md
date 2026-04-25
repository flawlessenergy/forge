# forge

Specs-driven development toolkit, wired into Claude CLI.

You describe your project once in plain markdown files. `forge` compiles them
into a structured context block and injects it directly into your Claude CLI
session — no copy-pasting, no re-explaining your stack every session.

```
forge init --scaffold        set up in your project
forge docs edit tasks        describe what to build
forge chat                   open Claude with full context already loaded
forge task "implement X"     one-shot answer, no session needed
```

---

## Requirements

| Platform | Requirement |
|----------|-------------|
| Linux / macOS | Python 3.10+, Git |
| Windows | Python 3.10+ ([python.org](https://python.org)), Git ([git-scm.com](https://git-scm.com)) |
| All | [Claude CLI](https://claude.ai/code) (for `forge chat` / `forge task`) |

---

## Install

### Linux / macOS

**Option A — clone and run (recommended)**
```bash
git clone https://github.com/atharva336/forge
cd forge
bash install.sh
```

**Option B — one-liner**
```bash
curl -fsSL https://raw.githubusercontent.com/atharva336/forge/main/install.sh | bash
```

The script creates a `.venv` inside the repo, installs the package, and
symlinks `forge` to `~/.local/bin/forge`. If that directory isn't in your
`$PATH` the script offers to add it automatically.

---

### Windows

Open **PowerShell** (Windows Terminal recommended) and run:

**Option A — clone and run (recommended)**
```powershell
git clone https://github.com/atharva336/forge
cd forge
.\install.ps1
```

**Option B — one-liner**
```powershell
irm https://raw.githubusercontent.com/atharva336/forge/main/install.ps1 | iex
```

The script creates a `.venv`, installs the package, places a `forge.cmd`
wrapper in `%USERPROFILE%\.local\bin`, and adds that directory to your user
PATH. **Restart your terminal** after the script finishes.

> **Tip for Windows users:** During Python installation, check
> _"Add Python to PATH"_ on the first installer screen.

---

## Quick start

```bash
cd your-project

forge init --scaffold          # creates .forge/ and starter spec docs
forge docs edit skills         # fill in your tech stack
forge docs edit tasks          # describe what to build today
forge docs status              # check which docs are ready

forge chat                     # open Claude — it already knows your project
forge task "implement TASK-1"  # one-shot task, no interactive session
```

---

## How it works

forge stores spec documents in `.forge/docs/` inside your project:

| File | What you write there |
|------|---------------------|
| `persona.md` | The AI's role — "you are a senior backend engineer…" |
| `constitution.md` | Non-negotiable rules — security, testing, code style |
| `skills.md` | Your tech stack, patterns to follow, things to avoid |
| `tasks.md` | What to build this session — TASK-1, TASK-2… |
| `architecture.md` | System design, data models, API contracts (optional) |
| `context.md` | Project background and constraints (optional) |

When you run `forge chat` or `forge task`, these files are compiled and
compressed, then injected into Claude's system prompt via
`--append-system-prompt-file`. Claude starts the session already knowing your
stack, rules, and tasks.

---

## All commands

### Claude CLI integration

```bash
forge chat                          # interactive session with full context
forge chat "let's start with TASK-1"# open with an initial message
forge chat --continue               # resume last session + reload context
forge task "implement X"            # one-shot task, streams answer and exits
forge task "write tests" -e .py     # only include .py files in context
forge sync                          # write docs to CLAUDE.md (passive loading)
forge sync --strip                  # remove forge section from CLAUDE.md
```

### Spec documents

```bash
forge docs scaffold                 # create starter .md files
forge docs scaffold --all           # include optional files too
forge docs list                     # list files + edit status
forge docs status                   # quick ready/needs-editing summary
forge docs edit tasks               # open in $EDITOR / notepad
forge docs show tasks               # print to terminal
forge docs add ~/my-rules.md        # bring in any external .md file
forge run --preview                 # see token count before sending
forge run                           # compile → clipboard
```

### Spec tracker

```bash
forge spec add "User auth" --priority high --tags auth,api
forge spec list
forge spec start SPEC-001
forge spec done SPEC-001
forge spec note SPEC-001 "use bcrypt"
forge spec export --format md
```

### Commit tracker (AI vs manual)

```bash
forge commits log                   # 🤖 AI or ✍ Manual label per commit
forge commits stats                 # bar chart breakdown
forge commits label abc123 ai       # manually override a label
```

### Other

```bash
forge stats                         # project dashboard
forge compress "your long text"     # strip filler words, save tokens
forge context dump --compress       # dump codebase as compressed text
forge graph build                   # build codebase knowledge graph (needs graphify)
```

---

## Updating

```bash
cd /path/to/forge
git pull
bash install.sh          # Linux/macOS
.\install.ps1            # Windows
```

---

## Uninstall

```bash
# Linux/macOS
rm ~/.local/bin/forge

# Windows (PowerShell)
Remove-Item "$env:USERPROFILE\.local\bin\forge.cmd"
```

Then delete the cloned repo folder.
