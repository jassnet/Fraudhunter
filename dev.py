#!/usr/bin/env python
"""
Simple dev runner that starts the FastAPI backend, Next.js frontend, and a local queue worker together.
Usage: python dev.py
Environment:
  BACKEND_PORT   (default: 8001)
  FRONTEND_PORT  (default: 3000)
  WORKER_ENABLED (default: true)
  WORKER_MAX_JOBS (default: 5)
  WORKER_POLL_SECONDS (default: 5)
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"


def _load_repo_dotenv() -> None:
    """Load repo-root .env into this process so child processes inherit DATABASE_URL, FC_ADMIN_API_KEY, etc."""
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(env_file)

BACKEND_PORT = os.getenv("BACKEND_PORT", "8001")
FRONTEND_PORT = os.getenv("FRONTEND_PORT", "3000")


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _worker_enabled() -> bool:
    return _env_bool("WORKER_ENABLED", True)


def _worker_max_jobs() -> str:
    return os.getenv("WORKER_MAX_JOBS", "5")


def _worker_poll_seconds() -> str:
    return os.getenv("WORKER_POLL_SECONDS", "5")


def _build_backend_cmd() -> list[str]:
    return [
        sys.executable,
        "-m",
        "uvicorn",
        "fraud_checker.api:app",
        "--reload",
        "--app-dir",
        str(BACKEND_DIR / "src"),
        "--port",
        BACKEND_PORT,
    ]


def _build_frontend_cmd(npm_exe: str) -> list[str]:
    return [
        npm_exe,
        "run",
        "dev",
        "--",
        "--hostname",
        "0.0.0.0",
        "--port",
        FRONTEND_PORT,
    ]


def _build_worker_cmd() -> list[str]:
    worker_script = textwrap.dedent(
        f"""
        import time

        from fraud_checker.env import load_env
        from fraud_checker.services.jobs import process_queued_jobs

        load_env()

        while True:
            try:
                processed = process_queued_jobs(max_jobs={_worker_max_jobs()})
                if processed:
                    print(f"[worker] processed {{processed}} queued job(s)", flush=True)
            except Exception as exc:
                print(
                    f"[worker] run-worker failed; will retry in {_worker_poll_seconds()}s: {{exc}}",
                    flush=True,
                )
            time.sleep({_worker_poll_seconds()})
        """
    ).strip()
    return [sys.executable, "-u", "-c", worker_script]


def _start_processes() -> Dict[str, subprocess.Popen]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env.setdefault("NEXT_PUBLIC_API_URL", f"http://localhost:{BACKEND_PORT}")
    env.setdefault("FC_ENV", "dev")
    env.setdefault("FC_READ_API_KEY", "dev-read-secret")
    env.setdefault("FC_DEV_CONSOLE_USER", "local-dev-admin")
    env.setdefault("FC_DEV_CONSOLE_EMAIL", "local-dev-admin@example.com")

    npm_exe = "npm.cmd" if os.name == "nt" and (FRONTEND_DIR / "package.json").exists() else "npm"
    backend_cmd = _build_backend_cmd()
    frontend_cmd = _build_frontend_cmd(npm_exe)

    try:
        backend = subprocess.Popen(backend_cmd, cwd=BACKEND_DIR, env=env)
    except FileNotFoundError as exc:  # pragma: no cover - runtime check
        raise SystemExit("Python (uvicorn) is required to start the backend.") from exc

    try:
        frontend = subprocess.Popen(frontend_cmd, cwd=FRONTEND_DIR, env=env)
    except FileNotFoundError as exc:  # pragma: no cover - runtime check
        backend.terminate()
        raise SystemExit("npm is required to start the frontend.") from exc

    processes = {"backend": backend, "frontend": frontend}
    if _worker_enabled():
        worker = subprocess.Popen(_build_worker_cmd(), cwd=BACKEND_DIR, env=env)
        processes["worker"] = worker

    return processes


def _shutdown(procs: Dict[str, subprocess.Popen], *, quiet: bool = False) -> None:
    for name, proc in procs.items():
        if proc.poll() is None:
            if not quiet:
                print(f"Stopping {name}...")
            proc.terminate()

    deadline = time.time() + 10
    for proc in procs.values():
        if proc.poll() is None:
            try:
                proc.wait(timeout=max(0, deadline - time.time()))
            except subprocess.TimeoutExpired:
                proc.kill()


def main() -> None:
    _load_repo_dotenv()
    print(f"Starting backend on http://localhost:{BACKEND_PORT}")
    print(f"Starting frontend on http://localhost:{FRONTEND_PORT}")
    if _worker_enabled():
        print(
            "Starting local worker loop "
            f"(max_jobs={_worker_max_jobs()}, poll={_worker_poll_seconds()}s)"
        )
    procs = _start_processes()

    def handle_signal(signum, frame):
        print("\nShutting down...")
        _shutdown(procs)
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        while True:
            for name, proc in list(procs.items()):
                code = proc.poll()
                if code is not None:
                    print(f"{name} exited with code {code}")
                    _shutdown(procs, quiet=True)
                    sys.exit(code or 0)
            time.sleep(1)
    except KeyboardInterrupt:
        handle_signal(None, None)


if __name__ == "__main__":
    main()
