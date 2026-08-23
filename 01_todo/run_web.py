"""Start the local Django server and open the Todo web interface."""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def wait_for_server(host: str, port: int, process: subprocess.Popen) -> None:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Django server stopped before it was ready")
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("Timed out waiting for the Django server")


def main() -> int:
    parser = argparse.ArgumentParser(description="Open the Todo web interface")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true", help="start the server without opening a browser")
    args = parser.parse_args()

    env = os.environ.copy()
    env.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"], cwd=BASE_DIR, env=env, check=True)
    url = f"http://{args.host}:{args.port}/"
    server = subprocess.Popen([sys.executable, "manage.py", "runserver", f"{args.host}:{args.port}"], cwd=BASE_DIR, env=env)
    try:
        wait_for_server(args.host, args.port, server)
        if not args.no_browser:
            webbrowser.open(url)
        print(f"Todo is running at {url}. Press Ctrl-C to stop.", flush=True)
        return server.wait()
    except KeyboardInterrupt:
        return 0
    finally:
        if server.poll() is None:
            server.terminate()
            server.wait()


if __name__ == "__main__":
    raise SystemExit(main())
