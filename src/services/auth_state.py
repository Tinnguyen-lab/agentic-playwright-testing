"""Project- and origin-scoped Playwright authentication state.

The JSON contains live session tokens. Keep it under ignored runtime artifacts,
never put its contents in a prompt, database row, log or execution trace.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlsplit


_ROOT = Path(__file__).resolve().parents[2] / "artifacts" / "auth_states"


def state_path(project_id: int, target_url: str) -> Path:
    parts = urlsplit(target_url)
    if (parts.scheme not in {"http", "https"} or not parts.hostname or
            parts.username is not None or parts.password is not None):
        raise ValueError("Authentication state requires an HTTP(S) target URL")
    origin = f"{parts.scheme.lower()}://{parts.netloc.lower()}"
    digest = hashlib.sha256(origin.encode("utf-8")).hexdigest()[:20]
    return _ROOT / f"project-{int(project_id)}" / f"{digest}.json"


def has_state(path: Path) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(data, dict) and (bool(data.get("cookies")) or bool(data.get("origins")))


def promote_state(candidate: Path, destination: Path) -> bool:
    """Publish only a nonempty state; never replace a good state with an empty one."""
    if not has_state(candidate):
        candidate.unlink(missing_ok=True)
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(candidate, destination)
    return True
