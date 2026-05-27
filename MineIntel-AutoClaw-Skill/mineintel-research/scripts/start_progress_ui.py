#!/usr/bin/env python3
"""Start a local progress UI server and open it in the browser."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urlparse
from pathlib import Path
import mimetypes

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


BASE_DIR = Path(__file__).resolve().parents[1]
PACKAGE_DIR = BASE_DIR.parent
UI_DIR = PACKAGE_DIR / "demo-ui"
STATE_PATH = UI_DIR / "progress_state.json"
UPDATE_SCRIPT = Path(__file__).resolve().parent / "progress_update.py"


def port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def ensure_initial_state(task: str, reset: bool, major: str, field: str, scene: str, formats: str) -> None:
    cmd = [
        sys.executable,
        str(UPDATE_SCRIPT),
        "--task",
        task,
        "--step",
        "confirm",
        "--status",
        "running",
        "--percent",
        "5",
        "--message",
        "任务已启动，正在确认专业和研究领域。",
    ]
    if reset:
        cmd.append("--reset")
    for key, value in (("--major", major), ("--field", field), ("--scene", scene), ("--formats", formats)):
        if value:
            cmd.extend([key, value])
    subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class ProgressHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(UI_DIR), **kwargs)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/state":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if STATE_PATH.exists():
                data = STATE_PATH.read_bytes()
            else:
                data = b'{"status":"idle","message":"waiting"}'
            self.wfile.write(data)
            return
        if parsed.path == "/download":
            self.send_download(parsed.query)
            return
        if parsed.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
            return
        super().do_GET()

    def send_download(self, query: str) -> None:
        params = parse_qs(query)
        raw_path = params.get("path", [""])[0]
        if not raw_path:
            self.send_error(400, "missing path")
            return
        path = Path(unquote(raw_path)).resolve()
        try:
            path.relative_to(PACKAGE_DIR.resolve())
        except ValueError:
            self.send_error(403, "file is outside skill package")
            return
        if not path.exists() or not path.is_file():
            self.send_error(404, "file not found")
            return
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(path.stat().st_size))
        ascii_name = path.name.encode("ascii", errors="ignore").decode("ascii") or "download"
        self.send_header("Content-Disposition", f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(path.name)}")
        self.end_headers()
        with path.open("rb") as f:
            while True:
                chunk = f.read(1024 * 256)
                if not chunk:
                    break
                self.wfile.write(chunk)


def serve(port: int) -> None:
    UI_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", port), ProgressHandler)
    server.serve_forever()


def start_server(port: int) -> None:
    if port_open(port):
        return
    cmd = [sys.executable, str(Path(__file__).resolve()), "--serve", "--port", str(port)]
    kwargs = {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL,
        "cwd": str(PACKAGE_DIR),
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    subprocess.Popen(cmd, **kwargs)
    time.sleep(0.6)


def main() -> int:
    parser = argparse.ArgumentParser(description="Open MineIntel progress UI.")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--task", default="MineIntel 矿业科研调研任务")
    parser.add_argument("--reset", action="store_true", default=True)
    parser.add_argument("--major", default="")
    parser.add_argument("--field", default="")
    parser.add_argument("--scene", default="")
    parser.add_argument("--formats", default="HTML 完整报告 / 文献综述 LaTeX / PDF")
    args = parser.parse_args()

    if args.serve:
        serve(args.port)
        return 0

    if not UI_DIR.exists():
        print(json.dumps({"status": "error", "message": "demo-ui directory not found", "ui_dir": str(UI_DIR)}, ensure_ascii=False, indent=2))
        return 1

    ensure_initial_state(args.task, reset=args.reset, major=args.major, field=args.field, scene=args.scene, formats=args.formats)
    start_server(args.port)
    url = f"http://127.0.0.1:{args.port}/index.html"
    opened = webbrowser.open(url, new=1, autoraise=True)
    print(
        json.dumps(
            {
                "status": "success" if opened else "warning",
                "url": url,
                "state_path": str(STATE_PATH),
                "message": "已打开 MineIntel 实时进度 UI。" if opened else "浏览器未确认打开，请手动访问 url。",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
