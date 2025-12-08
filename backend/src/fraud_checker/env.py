from __future__ import annotations

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Loaded flag to avoid redundant disk reads when the CLI invokes multiple commands in one process.
_DOTENV_LOADED: bool = False
_DOTENV_PATH: Optional[Path] = None


def _walk_for_env(start: Path) -> list[Path]:
    """
    Build a list of candidate .env files walking up from the given path.
    This tolerates the repository being nested (e.g. backend/src/...) and
    picks the first existing file.
    """
    candidates: list[Path] = []
    for parent in [start] + list(start.parents):
        candidate = parent / ".env"
        if candidate not in candidates:
            candidates.append(candidate)
    # Fallback to the current working directory.
    cwd_candidate = Path.cwd() / ".env"
    if cwd_candidate not in candidates:
        candidates.append(cwd_candidate)
    return candidates


def load_env(dotenv_path: Optional[Path] = None, force: bool = False) -> Optional[Path]:
    """
    Load environment variables from a .env file.

    Priority:
    1. Explicit path argument (if given)
    2. Closest .env walking up from this file (backend/src/... -> backend -> repo root)
    3. Current working directory .env
    
    Args:
        dotenv_path: Explicit path to .env file
        force: If True, reload even if already loaded
    """
    global _DOTENV_LOADED, _DOTENV_PATH
    if _DOTENV_LOADED and not force:
        return _DOTENV_PATH

    if dotenv_path:
        candidates = [dotenv_path]
    else:
        candidates = _walk_for_env(Path(__file__).resolve())

    for candidate in candidates:
        if candidate and candidate.exists():
            load_dotenv(candidate, override=True)
            _DOTENV_LOADED = True
            _DOTENV_PATH = candidate
            return candidate

    _DOTENV_LOADED = True
    _DOTENV_PATH = None
    return None
