"""Git commit tracking with AI vs manual detection."""

import subprocess
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# Patterns that indicate AI-assisted commits
_DEFAULT_AI_PATTERNS = [
    r"co-authored-by:.*claude",
    r"co-authored-by:.*copilot",
    r"co-authored-by:.*cursor",
    r"co-authored-by:.*codeium",
    r"co-authored-by:.*tabnine",
    r"generated with claude",
    r"🤖",
    r"\[ai\]",
    r"\[claude\]",
    r"\[copilot\]",
]


@dataclass
class Commit:
    sha: str
    short_sha: str
    author_name: str
    author_email: str
    subject: str
    body: str
    date: str
    is_ai: bool = False
    ai_reason: str = ""
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0


def _run(cmd: list[str], cwd: str = ".") -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result.stdout.strip()


def detect_ai(subject: str, body: str, extra_patterns: list[str] = None) -> tuple[bool, str]:
    full_text = (subject + "\n" + body).lower()
    patterns = _DEFAULT_AI_PATTERNS + [p.lower() for p in (extra_patterns or [])]
    for pat in patterns:
        if re.search(pat, full_text):
            return True, pat
    return False, ""


def get_commits(limit: int = 50, repo_path: str = ".") -> list[Commit]:
    sep = "|||FIELD|||"
    end = "|||COMMIT|||"
    fmt = f"%H{sep}%h{sep}%an{sep}%ae{sep}%s{sep}%b{sep}%ad{end}"
    raw = _run(
        ["git", "log", f"--max-count={limit}", f"--format={fmt}", "--date=short"],
        cwd=repo_path,
    )
    if not raw:
        return []

    from forge.core.store import load_config, load_commit_labels
    cfg = load_config()
    extra = cfg.get("ai_signatures", [])

    try:
        labels = load_commit_labels()
    except FileNotFoundError:
        labels = {}

    commits = []
    for block in raw.split(end):
        block = block.strip()
        if not block:
            continue
        parts = block.split(sep)
        if len(parts) < 7:
            continue
        sha, short_sha, an, ae, subject, body, date = parts[:7]

        # Manual override from labels file
        if sha in labels:
            is_ai = labels[sha] == "ai"
            reason = "manually labeled"
        else:
            is_ai, reason = detect_ai(subject, body, extra)

        commits.append(
            Commit(
                sha=sha,
                short_sha=short_sha,
                author_name=an,
                author_email=ae,
                subject=subject,
                body=body,
                date=date,
                is_ai=is_ai,
                ai_reason=reason,
            )
        )

    # Enrich with diff stats
    for c in commits:
        stat = _run(
            ["git", "show", "--stat", "--format=", c.sha],
            cwd=repo_path,
        )
        m_files = re.search(r"(\d+) file", stat)
        m_ins = re.search(r"(\d+) insertion", stat)
        m_del = re.search(r"(\d+) deletion", stat)
        c.files_changed = int(m_files.group(1)) if m_files else 0
        c.insertions = int(m_ins.group(1)) if m_ins else 0
        c.deletions = int(m_del.group(1)) if m_del else 0

    return commits


def is_git_repo(path: str = ".") -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
        cwd=path,
    )
    return result.returncode == 0


def get_repo_info(path: str = ".") -> dict:
    branch = _run(["git", "branch", "--show-current"], cwd=path)
    remote = _run(["git", "remote", "get-url", "origin"], cwd=path)
    total = _run(["git", "rev-list", "--count", "HEAD"], cwd=path)
    return {
        "branch": branch,
        "remote": remote,
        "total_commits": int(total) if total.isdigit() else 0,
    }


def label_commit(sha: str, label: str) -> None:
    """Manually override AI/manual label for a commit. label: 'ai' or 'manual'."""
    from forge.core.store import load_commit_labels, save_commit_labels
    labels = load_commit_labels()
    labels[sha] = label
    save_commit_labels(labels)
