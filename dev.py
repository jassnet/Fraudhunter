#!/usr/bin/env python
"""
Simple dev runner that starts the FastAPI backend and Next.js frontend together.
Usage: python dev.py
Environment:
  BACKEND_PORT   (default: 8000)
  FRONTEND_PORT  (default: 3000)
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"

BACKEND_PORT = os.getenv("BACKEND_PORT", "8001")
FRONTEND_PORT = os.getenv("FRONTEND_PORT", "3000")


def _start_processes() -> Dict[str, subprocess.Popen]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env.setdefault("NEXT_PUBLIC_API_URL", f"http://localhost:{BACKEND_PORT}")

    npm_exe = "npm.cmd" if os.name == "nt" and (FRONTEND_DIR / "package.json").exists() else "npm"

    backend_cmd = [
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
    frontend_cmd = [
        npm_exe,
        "run",
        "dev",
        "--",
        "--hostname",
        "0.0.0.0",
        "--port",
        FRONTEND_PORT,
    ]

    try:
        backend = subprocess.Popen(backend_cmd, cwd=BACKEND_DIR, env=env)
    except FileNotFoundError as exc:  # pragma: no cover - runtime check
        raise SystemExit("Python (uvicorn) is required to start the backend.") from exc

    try:
        frontend = subprocess.Popen(frontend_cmd, cwd=FRONTEND_DIR, env=env)
    except FileNotFoundError as exc:  # pragma: no cover - runtime check
        backend.terminate()
        raise SystemExit("npm is required to start the frontend.") from exc

    return {"backend": backend, "frontend": frontend}


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
    print(f"Starting backend on http://localhost:{BACKEND_PORT}")
    print(f"Starting frontend on http://localhost:{FRONTEND_PORT}")
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
