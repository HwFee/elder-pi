#!/usr/bin/env python3
import argparse
import http.server
import json
import os
import shutil
import socketserver
import subprocess
import sys
from pathlib import Path

DEFAULT_BACKEND = "http://127.0.0.1:8000"
TOKEN_DIR = Path.home() / ".config" / "elder-pi"
TOKEN_PATH = TOKEN_DIR / "device-token"


class LauncherHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, config=None, **kwargs):
        self.config = config or {}
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path == "/__config__":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(self.config).encode())
            return
        if self.path in ("/", "/index.html"):
            self.serve_index()
            return
        super().do_GET()

    def serve_index(self):
        index_path = self.directory / "index.html"
        if not index_path.exists():
            self.send_error(404, "index.html not found")
            return
        content = index_path.read_text(encoding="utf-8")
        config_json = json.dumps(self.config)
        inject = f"""
<script>
window.__ELDER_PI_CONFIG__ = {config_json};
</script>
"""
        content = content.replace("</head>", inject + "</head>", 1)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def log_message(self, format, *args):
        pass


def load_token():
    if TOKEN_PATH.exists():
        return TOKEN_PATH.read_text(encoding="utf-8").strip()
    return None


def ensure_token_example():
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    example = TOKEN_DIR / "device-token.example"
    if not example.exists():
        example.write_text("your-device-jwt-token-here\n", encoding="utf-8")


def decode_device_id(token):
    try:
        import base64
        payload = token.split(".")[1]
        padded = payload + "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded).decode())
        return data.get("device_id")
    except Exception:
        return None


def find_chrome():
    for name in ("chromium-browser", "chromium", "google-chrome", "google-chrome-stable"):
        path = shutil.which(name)
        if path:
            return path
    return None


def launch_kiosk(url):
    chrome = find_chrome()
    if not chrome:
        print("Chromium/Chrome not found; please open", url, "manually")
        return None
    cmd = [
        chrome,
        "--kiosk",
        "--incognito",
        "--disable-infobars",
        "--noerrdialogs",
        "--no-first-run",
        "--disable-features=TranslateUI",
        url,
    ]
    return subprocess.Popen(cmd)


def main():
    parser = argparse.ArgumentParser(description="Elder Pi client launcher")
    parser.add_argument("--port", type=int, default=3000)
    parser.add_argument("--backend", default=DEFAULT_BACKEND)
    parser.add_argument("--no-kiosk", action="store_true", help="Do not launch Chromium kiosk")
    parser.add_argument("--token-file", type=Path, default=TOKEN_PATH)
    args = parser.parse_args()

    ensure_token_example()

    token = args.token_file.read_text(encoding="utf-8").strip() if args.token_file.exists() else None
    if not token:
        print(f"Device token not found at {args.token_file}")
        print("Create it with: mkdir -p ~/.config/elder-pi && echo YOUR_TOKEN > ~/.config/elder-pi/device-token")
        sys.exit(1)

    device_id = decode_device_id(token)
    config = {
        "deviceToken": token,
        "backendUrl": args.backend,
        "deviceId": device_id,
    }

    client_dir = Path(__file__).resolve().parent
    os.chdir(client_dir)

    handler = lambda *handler_args, **handler_kwargs: LauncherHandler(
        *handler_args, directory=client_dir, config=config, **handler_kwargs
    )

    with socketserver.TCPServer(("127.0.0.1", args.port), handler) as httpd:
        url = f"http://127.0.0.1:{args.port}/"
        print(f"Serving elder-pi-client at {url}")
        print(f"Backend: {args.backend}")
        if device_id:
            print(f"Device: {device_id}")
        if not args.no_kiosk:
            launch_kiosk(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down")


if __name__ == "__main__":
    main()
