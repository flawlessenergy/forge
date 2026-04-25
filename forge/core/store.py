"""JSON-backed storage for specs and sessions, stored in .forge/ at project root."""

import json
import os
from pathlib import Path
from datetime import datetime, timezone

FORGE_DIR = ".forge"
SPECS_FILE = "specs.json"
LABELS_FILE = "commit_labels.json"
CONFIG_FILE = "config.json"


def _find_root() -> Path:
    """Walk up from cwd to find .forge directory; fall back to cwd."""
    path = Path.cwd()
    while path != path.parent:
        if (path / FORGE_DIR).exists():
            return path / FORGE_DIR
        path = path.parent
    return Path.cwd() / FORGE_DIR


def get_store() -> Path:
    return _find_root()


def init_store() -> Path:
    store = Path.cwd() / FORGE_DIR
    store.mkdir(exist_ok=True)
    db_path = store / SPECS_FILE
    if not db_path.exists():
        db_path.write_text(json.dumps({"next_id": 1, "specs": []}, indent=2))
    cfg_path = store / CONFIG_FILE
    if not cfg_path.exists():
        cfg_path.write_text(json.dumps({"ai_signatures": [], "github_token": ""}, indent=2))
    return store


def _load_db() -> dict:
    path = get_store() / SPECS_FILE
    if not path.exists():
        raise FileNotFoundError(
            "No .forge directory found. Run `forge init` first."
        )
    return json.loads(path.read_text())


def _save_db(db: dict) -> None:
    path = get_store() / SPECS_FILE
    path.write_text(json.dumps(db, indent=2))


def load_config() -> dict:
    path = get_store() / CONFIG_FILE
    if not path.exists():
        return {"ai_signatures": [], "github_token": ""}
    return json.loads(path.read_text())


def save_config(cfg: dict) -> None:
    path = get_store() / CONFIG_FILE
    path.write_text(json.dumps(cfg, indent=2))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def all_specs() -> list[dict]:
    return _load_db()["specs"]


def get_spec(spec_id: str) -> dict | None:
    for s in all_specs():
        if s["id"] == spec_id.upper():
            return s
    return None


def add_spec(title: str, desc: str, tags: list[str], priority: str) -> dict:
    db = _load_db()
    n = db["next_id"]
    spec = {
        "id": f"SPEC-{n:03d}",
        "title": title,
        "description": desc,
        "status": "pending",
        "priority": priority,
        "tags": tags,
        "commits": [],
        "notes": "",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    db["specs"].append(spec)
    db["next_id"] = n + 1
    _save_db(db)
    return spec


def update_spec(spec_id: str, **kwargs) -> dict | None:
    db = _load_db()
    for s in db["specs"]:
        if s["id"] == spec_id.upper():
            s.update(kwargs)
            s["updated_at"] = now_iso()
            _save_db(db)
            return s
    return None


def delete_spec(spec_id: str) -> bool:
    db = _load_db()
    before = len(db["specs"])
    db["specs"] = [s for s in db["specs"] if s["id"] != spec_id.upper()]
    if len(db["specs"]) < before:
        _save_db(db)
        return True
    return False


def link_commit(spec_id: str, sha: str) -> bool:
    db = _load_db()
    for s in db["specs"]:
        if s["id"] == spec_id.upper():
            if sha not in s["commits"]:
                s["commits"].append(sha)
                s["updated_at"] = now_iso()
            _save_db(db)
            return True
    return False


def load_commit_labels() -> dict:
    path = get_store() / LABELS_FILE
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_commit_labels(labels: dict) -> None:
    path = get_store() / LABELS_FILE
    path.write_text(json.dumps(labels, indent=2))
