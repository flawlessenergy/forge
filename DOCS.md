# forge — Command Reference

Complete reference for all `forge` commands.

---

## Table of Contents

1. [Setup](#1-setup)
   - [forge init](#forge-init)
   - [forge config](#forge-config)
2. [Claude CLI Integration](#2-claude-cli-integration) ← *start here*
   - [forge chat](#forge-chat)
   - [forge task](#forge-task)
   - [forge sync](#forge-sync)
3. [Spec Documents](#3-spec-documents)
   - [forge docs scaffold](#forge-docs-scaffold)
   - [forge docs list](#forge-docs-list)
   - [forge docs status](#forge-docs-status)
   - [forge docs edit](#forge-docs-edit)
   - [forge docs show](#forge-docs-show)
   - [forge docs add](#forge-docs-add)
   - [forge docs remove](#forge-docs-remove)
4. [Prompt Compilation](#4-prompt-compilation)
   - [forge run](#forge-run)
5. [Spec Tracker](#5-spec-tracker)
   - [forge spec add](#forge-spec-add)
   - [forge spec list](#forge-spec-list)
   - [forge spec show](#forge-spec-show)
   - [forge spec start / done / block](#forge-spec-start--done--block)
   - [forge spec note](#forge-spec-note)
   - [forge spec link](#forge-spec-link)
   - [forge spec delete](#forge-spec-delete)
   - [forge spec export](#forge-spec-export)
6. [Commit Tracker](#6-commit-tracker)
   - [forge commits log](#forge-commits-log)
   - [forge commits stats](#forge-commits-stats)
   - [forge commits show](#forge-commits-show)
   - [forge commits label](#forge-commits-label)
   - [forge commits diff](#forge-commits-diff)
7. [Codebase Tools](#7-codebase-tools)
   - [forge context dump](#forge-context-dump)
   - [forge context spec](#forge-context-spec)
   - [forge graph build](#forge-graph-build)
   - [forge graph query](#forge-graph-query)
   - [forge graph context](#forge-graph-context)
8. [Utilities](#8-utilities)
   - [forge compress](#forge-compress)
   - [forge prompt build](#forge-prompt-build)
   - [forge prompt template](#forge-prompt-template)
   - [forge stats](#forge-stats)

---

## 1. Setup

### `forge init`

Initialises forge in the current project. Creates a `.forge/` directory with
`specs.json` and `config.json`.

```
forge init [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--scaffold` | Also run `forge docs scaffold` immediately after init |
| `--github-token TOKEN` | Store a GitHub personal access token in config |

**Examples**
```bash
# Basic init
forge init

# Init and create all starter spec documents in one step
forge init --scaffold
```

> Run this once per project from the project root. All other forge commands
> look for `.forge/` by walking up from the current directory.

---

### `forge config`

View or update forge project settings stored in `.forge/config.json`.

```
forge config [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--show` | Print the current config as JSON |
| `--github-token TOKEN` | Set or update the GitHub token |
| `--ai-signature PATTERN` | Add an extra regex pattern used to detect AI commits (repeatable) |

**Examples**
```bash
# Print current config
forge config --show

# Add a GitHub token
forge config --github-token ghp_xxxxxxxxxxxx

# Teach forge to detect commits from a custom AI tool
forge config --ai-signature "\[gpt\]" --ai-signature "openai-codex"
```

---

## 2. Claude CLI Integration

These are the three commands you use every day. They compile your spec docs
and inject them directly into Claude CLI — no copy-pasting.

---

### `forge chat`

Opens an interactive Claude CLI session with your full spec context already
loaded into the system prompt. Claude knows your project from message one.

```
forge chat [MESSAGE] [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `MESSAGE` | Optional opening message sent to Claude |
| `--compress / --no-compress` | Apply token compression to context (default: on) |
| `--no-context` | Include spec docs only — skip codebase files |
| `-e, --ext .EXT` | Only include files with this extension (repeatable) |
| `--max-files N` | Max codebase files to include (default: 20) |
| `-m, --model ALIAS` | Claude model to use (`sonnet`, `opus`, `haiku`) |
| `--continue` | Resume the most recent Claude conversation |
| `-n, --name NAME` | Give this session a display name |

**Examples**
```bash
# Open a session — Claude already knows your stack and tasks
forge chat

# Start with an opening message
forge chat "let's build TASK-1 from the spec"

# Docs only — no source files in context (faster for planning)
forge chat --no-context

# Resume last session with fresh context
forge chat --continue

# Only include Python files in context
forge chat -e .py -e .ts

# Name the session for easy resuming later
forge chat --name "auth-sprint"

# Use a specific model
forge chat --model opus
```

---

### `forge task`

Runs a single one-shot task through `claude -p`. Context goes into the system
prompt; your description is the user message. Claude answers and exits — no
interactive session.

```
forge task DESCRIPTION [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `DESCRIPTION` | What you want Claude to do (required) |
| `--compress / --no-compress` | Apply token compression (default: on) |
| `--no-context` | Docs only — skip codebase files |
| `-e, --ext .EXT` | Only include files with this extension (repeatable) |
| `--max-files N` | Max codebase files to include (default: 20) |
| `-m, --model ALIAS` | Claude model alias |
| `--output-format` | `text` (default), `json`, or `stream-json` |

**Examples**
```bash
# Implement a task — Claude reads your full spec context automatically
forge task "implement the login endpoint from TASK-1"

# Only scan Python files (faster, fewer tokens)
forge task "write pytest tests for auth.py" -e .py

# Quick question with no codebase (just the docs)
forge task "what are the security rules in the constitution?" --no-context

# Use a more powerful model for complex work
forge task "refactor the entire auth module" --model opus

# Get structured JSON output (useful for scripting)
forge task "list all files that need changes" --output-format json
```

---

### `forge sync`

Compiles your spec docs and writes them into `CLAUDE.md` between
`<!-- forge:start -->` and `<!-- forge:end -->` markers. Claude CLI reads
`CLAUDE.md` automatically at every session start.

Use this when you want context loaded passively — just run `claude` afterwards
without any forge flags.

```
forge sync [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--compress / --no-compress` | Apply compression (default: on) |
| `--no-context` | Docs only — skip codebase files |
| `--dry-run` | Print what would be written without touching `CLAUDE.md` |
| `--strip` | Remove the forge section from `CLAUDE.md` |

**Examples**
```bash
# Write docs to CLAUDE.md, then just run `claude` as normal
forge sync
claude

# Preview what would be written without changing the file
forge sync --dry-run

# Docs only — no source files
forge sync --no-context

# Remove the forge section (keeps your own CLAUDE.md content)
forge sync --strip
```

> **Your own `CLAUDE.md` content is never touched.** forge only manages the
> section between the two marker comments. Write whatever you like above or
> below them.

---

## 3. Spec Documents

Spec documents live in `.forge/docs/` and describe your project to Claude.
Edit them in any text editor; they are plain markdown files.

| File | Purpose |
|------|---------|
| `persona.md` | The AI's role — "you are a senior backend engineer…" |
| `constitution.md` | Non-negotiable rules the AI must follow |
| `skills.md` | Your tech stack, patterns to use, things to avoid |
| `tasks.md` | What to build — TASK-1, TASK-2… |
| `architecture.md` | System design, data models, API contracts *(optional)* |
| `context.md` | Project background and constraints *(optional)* |

---

### `forge docs scaffold`

Creates starter spec documents from built-in templates.

```
forge docs scaffold [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--all` | Also create optional files (`architecture.md`, `context.md`) |
| `--force` | Overwrite files that already exist |

**Examples**
```bash
# Create the four required docs
forge docs scaffold

# Create all six docs including optional ones
forge docs scaffold --all

# Re-create from scratch (overwrites your changes)
forge docs scaffold --force
```

---

### `forge docs list`

Lists all documents in `.forge/docs/` with their edit status.

```
forge docs list
```

Status values:

| Status | Meaning |
|--------|---------|
| `✓ edited` | You have changed it from the template — ready to use |
| `~ template` | Still the default placeholder — will be included but is generic |
| `missing` | Does not exist — will not be included |
| `custom` | A file you added yourself (not a standard template) |

---

### `forge docs status`

Quick summary of which docs are ready and which still need editing.

```
forge docs status
```

Shows three groups: **Ready**, **Needs editing**, and **Missing**, with the
exact command to fix each one.

---

### `forge docs edit`

Opens a spec document in your `$EDITOR` (or `VISUAL`). Creates the file from
the template if it does not exist yet.

```
forge docs edit NAME
```

`NAME` can be the full filename (`tasks.md`) or just the stem (`tasks`).

**Examples**
```bash
forge docs edit tasks          # open tasks.md
forge docs edit skills         # open skills.md
forge docs edit constitution   # open constitution.md
forge docs edit persona        # open persona.md
forge docs edit architecture   # open architecture.md (creates if missing)
forge docs edit context        # open context.md
```

> Sets `$EDITOR` in your shell profile to control which editor opens.
> E.g. `export EDITOR=nano` or `export EDITOR="code --wait"`.

---

### `forge docs show`

Prints the contents of a spec document to the terminal.

```
forge docs show NAME
```

**Examples**
```bash
forge docs show tasks
forge docs show constitution
```

---

### `forge docs add`

Copies any existing markdown file into `.forge/docs/`. Use this to bring in
team standards, `CLAUDE.md` from another project, or any rules file.

```
forge docs add FILEPATH [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `-n, --name NAME` | Override the destination filename |

**Examples**
```bash
# Bring in a team standards file
forge docs add ~/team/coding-standards.md

# Bring in with a custom name
forge docs add ~/CLAUDE.md --name project-rules.md
```

---

### `forge docs remove`

Removes a spec document from `.forge/docs/`.

```
forge docs remove NAME [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `-y, --yes` | Skip confirmation prompt |

**Examples**
```bash
forge docs remove context
forge docs remove old-notes.md --yes
```

---

## 4. Prompt Compilation

### `forge run`

Compiles all spec docs and codebase files into a single structured prompt.
Copies to clipboard by default. Used when you want to paste context manually
or inspect it before sending.

```
forge run [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `-t, --task TEXT` | Override the final instruction line |
| `--compress / --no-compress` | Apply compression (default: on) |
| `--context / --no-context` | Include codebase files (default: on) |
| `-e, --ext .EXT` | Only include files with this extension (repeatable) |
| `--max-files N` | Max codebase files to include (default: 20) |
| `--copy / --no-copy` | Copy to clipboard (default: on) |
| `-o, --output FILE` | Also save to a file |
| `-p, --preview` | Show token table only — do not generate prompt |

**Examples**
```bash
# Compile and copy to clipboard
forge run

# Preview token breakdown without generating
forge run --preview

# Compile with a specific instruction and save to file
forge run --task "implement TASK-1 only" -o prompt.md

# Docs only — no source files
forge run --no-context --copy

# Only Python and TypeScript files
forge run -e .py -e .ts

# Print to terminal instead of clipboard
forge run --no-copy
```

---

## 5. Spec Tracker

Specs are lightweight tickets stored in `.forge/specs.json`. Each gets a
sequential ID: `SPEC-001`, `SPEC-002`, etc.

Status flow: `pending` → `in_progress` → `done` (or `blocked` at any point)

---

### `forge spec add`

Creates a new spec.

```
forge spec add TITLE [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `-d, --desc TEXT` | Description |
| `-p, --priority` | `high`, `medium` (default), or `low` |
| `-t, --tags TEXT` | Comma-separated tags |

**Examples**
```bash
forge spec add "User authentication"
forge spec add "JWT login" --desc "POST /auth/login returns access + refresh tokens" --priority high --tags auth,api
forge spec add "Dark mode toggle" --priority low --tags ui
```

---

### `forge spec list`

Lists all specs in a table.

```
forge spec list [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `-s, --status` | Filter: `pending`, `in_progress`, `done`, `blocked`, `all` (default) |
| `-t, --tag TEXT` | Filter by tag |

**Examples**
```bash
forge spec list
forge spec list --status pending
forge spec list --tag auth
```

---

### `forge spec show`

Shows full details for one spec: description, notes, linked commits.

```
forge spec show SPEC_ID
```

```bash
forge spec show SPEC-001
```

---

### `forge spec start / done / block`

Change the status of a spec.

```
forge spec start SPEC_ID
forge spec done  SPEC_ID
forge spec block SPEC_ID [--reason TEXT]
```

**Examples**
```bash
forge spec start SPEC-001
forge spec done  SPEC-001
forge spec block SPEC-002 --reason "waiting for DB schema from design team"
```

---

### `forge spec note`

Appends a note to a spec (does not overwrite).

```
forge spec note SPEC_ID TEXT
```

```bash
forge spec note SPEC-001 "use bcrypt for password hashing, cost factor 12"
forge spec note SPEC-001 "refresh tokens stored in Redis with 7-day TTL"
```

---

### `forge spec link`

Attaches a git commit SHA to a spec so you can trace which commits
implemented it.

```
forge spec link SPEC_ID --commit SHA
```

```bash
forge spec link SPEC-001 --commit abc1234
forge spec link SPEC-001 --commit abc1234def5678   # full SHA also works
```

---

### `forge spec delete`

Permanently removes a spec.

```
forge spec delete SPEC_ID [--yes]
```

```bash
forge spec delete SPEC-003
forge spec delete SPEC-003 --yes   # skip confirmation
```

---

### `forge spec export`

Exports all specs to a file or stdout.

```
forge spec export [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--format` | `md` (default) or `json` |
| `-o, --output FILE` | Write to file instead of stdout |

**Examples**
```bash
forge spec export                          # markdown to stdout
forge spec export --format json            # JSON to stdout
forge spec export --format md -o specs.md  # save to file
```

---

## 6. Commit Tracker

forge reads your git history and labels each commit as **🤖 AI** or
**✍ Manual** based on signatures in the commit message.

**Auto-detected AI signatures:**
- `Co-Authored-By: Claude` (added by Claude CLI automatically)
- `Co-Authored-By: GitHub Copilot`
- `Co-Authored-By: Cursor`
- `🤖` in the message
- `[claude]`, `[ai]`, `[copilot]` in the message

Add custom patterns with `forge config --ai-signature`.

---

### `forge commits log`

Shows recent commits with AI/manual labels, author, date, and line counts.

```
forge commits log [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `-n, --limit N` | Number of commits to show (default: 20) |
| `--ai-only` | Show only AI commits |
| `--manual-only` | Show only manual commits |
| `-p, --path DIR` | Path to the git repo (default: `.`) |

**Examples**
```bash
forge commits log
forge commits log -n 50
forge commits log --ai-only
forge commits log --manual-only
```

---

### `forge commits stats`

Shows a breakdown of AI vs manual commits with a progress bar and
per-author summary.

```
forge commits stats [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `-n, --limit N` | Commits to analyse (default: 100) |
| `-p, --path DIR` | Path to the git repo |

```bash
forge commits stats
forge commits stats -n 200
```

---

### `forge commits show`

Shows the stat summary and AI/manual label for a single commit.

```
forge commits show SHA [OPTIONS]
```

```bash
forge commits show abc1234
forge commits show abc1234 -p ../other-repo
```

---

### `forge commits label`

Manually overrides the AI/manual label for a commit. Stored in
`.forge/commit_labels.json` and takes priority over auto-detection.

```
forge commits label SHA LABEL
```

`LABEL` must be `ai` or `manual`.

```bash
forge commits label abc1234 ai      # mark as AI
forge commits label def5678 manual  # mark as manual
```

---

### `forge commits diff`

Opens the full diff for a commit in your pager.

```
forge commits diff SHA [OPTIONS]
```

```bash
forge commits diff abc1234
```

---

## 7. Codebase Tools

### `forge context dump`

Dumps the entire codebase as a single text block — file tree followed by
file contents. Useful for giving Claude a full picture of an existing project.

```
forge context dump [OPTIONS] [PATH]
```

| Option | Description |
|--------|-------------|
| `-c, --compress` | Apply compression to file contents |
| `--no-content` | File tree only — no file contents |
| `-e, --ext .EXT` | Only include these extensions (repeatable) |
| `-o, --output FILE` | Write to file instead of stdout |
| `--copy` | Copy to clipboard |
| `--tokens` | Print estimated token count |
| `PATH` | Root directory to scan (default: `.`) |

**Examples**
```bash
# Full codebase → stdout
forge context dump

# Compressed, copied to clipboard
forge context dump --compress --copy

# Python files only, with token count
forge context dump -e .py --tokens

# Save to file
forge context dump -o context.txt

# File tree only (no file contents)
forge context dump --no-content
```

---

### `forge context spec`

Generates context focused on a specific spec — finds the files most likely
related to that spec's title and tags.

```
forge context spec SPEC_ID [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `-c, --compress` | Apply compression |
| `--copy` | Copy to clipboard |

```bash
forge context spec SPEC-001
forge context spec SPEC-001 --compress --copy
```

---

### `forge graph build`

Builds a knowledge graph of the codebase using
[graphify](https://github.com/safishamsi/graphify). Outputs a `graph.json`
file and optionally an interactive HTML visualization.

> Requires `pip install graphify` separately.

```
forge graph build [PATH] [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `-o, --output FILE` | Output graph file (default: `graph.json`) |
| `--html` | Also generate an interactive HTML visualization |

```bash
forge graph build
forge graph build --html
forge graph build ./src -o src-graph.json
```

---

### `forge graph query`

Queries the knowledge graph with a natural language question.

```
forge graph query QUESTION [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `-g, --graph-file FILE` | Graph file to query (default: `graph.json`) |

```bash
forge graph query "what connects AuthService to UserModel"
forge graph query "which files handle database access"
```

---

### `forge graph context`

Extracts relevant context from the graph for AI prompting. Falls back to a
basic file tree if graphify is not installed.

```
forge graph context [TOPIC] [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `-g, --graph-file FILE` | Graph file (default: `graph.json`) |
| `-c, --compress` | Apply compression |
| `--copy` | Copy to clipboard |

```bash
forge graph context "authentication flow" --compress --copy
forge graph context --copy   # overall architecture
```

---

## 8. Utilities

### `forge compress`

Strips predictable grammar from text — articles, connectives, hedge phrases,
filler adverbs — while keeping facts, numbers, names, and constraints.
Achieves ~15–30% token reduction with no external model required.

```
forge compress [TEXT] [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `TEXT` | Text to compress (inline) |
| `-f, --file FILE` | Read from a file instead |
| `-s, --spec SPEC_ID` | Compress a spec's description |
| `-a, --aggressive` | Strip even more aggressively |
| `-c, --copy` | Copy result to clipboard |
| `--stats` | Show token reduction stats (default: on) |

**Examples**
```bash
# Inline text
forge compress "I need to implement a very fast authentication system that is able to handle concurrent users"
# → "I must implement fast authentication system that can handle concurrent users"

# From file
forge compress -f my-prompt.txt --copy

# Compress a spec
forge compress -s SPEC-001

# Aggressive mode
forge compress --aggressive "we are basically looking to essentially refactor the entire codebase"
```

---

### `forge prompt build`

Builds a structured AI prompt for a specific spec — combines the spec
description with relevant codebase files.

```
forge prompt build SPEC_ID [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--compress / --no-compress` | Apply compression (default: on) |
| `--copy` | Copy to clipboard |
| `-o, --output FILE` | Save to file |
| `-f, --context-files FILE` | Specific files to include (repeatable) |
| `--max-files N` | Max context files (default: 10) |

**Examples**
```bash
forge prompt build SPEC-001 --copy
forge prompt build SPEC-001 --no-compress -o prompt.md
forge prompt build SPEC-001 -f src/auth.py -f src/models.py --copy
```

---

### `forge prompt template`

Generates a short task-specific prompt for a spec using a style template.

```
forge prompt template SPEC_ID [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--style` | `implement` (default), `review`, `refactor`, `debug`, `test` |
| `--copy` | Copy to clipboard |

**Examples**
```bash
forge prompt template SPEC-001                      # implement
forge prompt template SPEC-001 --style debug        # debug prompt
forge prompt template SPEC-001 --style test --copy  # test-writing prompt
forge prompt template SPEC-001 --style review       # code review prompt
```

---

### `forge stats`

Shows a full project dashboard in the terminal: spec progress bars, AI vs
manual commit breakdown, and a table of recently updated specs.

```
forge stats [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `-p, --path DIR` | Git repo path (default: `.`) |

```bash
forge stats
forge stats -p ../other-project
```

---

## Typical day workflow

```bash
# Morning: update what you're building today
forge docs edit tasks

# Start a session — Claude reads your full spec context automatically
forge chat "let's implement TASK-1"

# Quick one-off question during the day
forge task "explain what auth.py does" --no-context

# After Claude writes code and you commit
forge commits log              # see which commits were AI
forge spec done SPEC-001       # close the spec

# End of day check
forge stats
```

---

## Flags that work on most commands

| Flag | Effect |
|------|--------|
| `--compress / --no-compress` | Toggle caveman compression on context |
| `--no-context` | Exclude codebase files — docs only |
| `-e .py` | Filter codebase to specific file extensions |
| `--max-files N` | Limit how many codebase files are included |
| `-m / --model` | Choose Claude model (`sonnet`, `opus`, `haiku`) |
| `--copy` | Copy output to clipboard |
| `-o FILE` | Save output to a file |
