"""Dependency-free static server for the disposable canvas POC."""

import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).parent


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def log_message(self, format, *args):  # Keep the POC output token-safe.
        print("canvas-poc", format % args)


if __name__ == "__main__":
    host=os.getenv("CANVAS_POC_HOST","0.0.0.0"); port=int(os.getenv("CANVAS_POC_PORT","8090"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"canvas POC listening on http://{host}:{port}/host.html")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
