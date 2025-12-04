from __future__ import annotations

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Loaded flag to avoid redundant disk reads when the CLI invokes multiple commands in one process.
_DOTENV_LOADED: bool = False
_DOTENV_PATH: Optional[Path] = None


def load_env(dotenv_path: Optional[Path] = None) -> Optional[Path]:
    """
    Load environment variables from a .env file.

    Priority:
    1. Explicit path argument (if given)
    2. Project root (.env next to pyproject.toml)
    3. Current working directory .env (fallback only)
    """
    global _DOTENV_LOADED, _DOTENV_PATH
    if _DOTENV_LOADED:
        return _DOTENV_PATH

    candidates: list[Path] = []
    if dotenv_path:
        candidates.append(dotenv_path)

    project_root = Path(__file__).resolve().parents[2]
    candidates.append(project_root / ".env")
    candidates.append(Path.cwd() / ".env")

    for candidate in candidates:
        if candidate and candidate.exists():
            load_dotenv(candidate)
            _DOTENV_LOADED = True
            _DOTENV_PATH = candidate
            return candidate

    _DOTENV_LOADED = True
    _DOTENV_PATH = None
    return None
