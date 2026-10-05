"""Tiny local web server for the preview (static files + POST /save/<name>.png to store screenshots).

    python tools/mobforge/serve.py        # serves the repo root on http://127.0.0.1:8765
"""
import http.server
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SHOTS = Path(os.environ.get("MOBFORGE_SHOTS", REPO / "forgedascent/tools/mobforge/shots"))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(REPO), **k)

    def do_POST(self):
        if self.path.startswith("/save/"):
            name = Path(self.path[6:]).name
            SHOTS.mkdir(parents=True, exist_ok=True)
            data = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            (SHOTS / name).write_bytes(data)
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_error(404)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    http.server.ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
