import json
import os
import re
import signal
import subprocess
import sys
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

TRYCLOUDFLARE_URL_PATTERN = re.compile(r"https://[-a-z0-9]+\.trycloudflare\.com")


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def extract_quick_tunnel_url(output_line: str) -> str | None:
    match = TRYCLOUDFLARE_URL_PATTERN.search(output_line or "")
    if not match:
        return None
    return match.group(0)


def resolve_status_file(project_root: Path, configured_path: str) -> Path:
    candidate = Path(configured_path)
    if candidate.is_absolute():
        return candidate
    return project_root / candidate


def render_status_document(status: dict) -> str:
    public_url = escape(str(status.get("public_url") or ""))
    service_status = escape(str(status.get("service_status", "starting")))
    last_message = escape(str(status.get("last_message") or "Asteptam output de la cloudflared."))
    discovered_at = escape(str(status.get("public_url_discovered_at") or ""))
    target_url = escape(str(status.get("target_url", "http://127.0.0.1:5000")))
    last_update = escape(str(status.get("updated_at", "necunoscut")))

    if public_url:
        public_url_block = (
            f'<p class="badge success">Tunnel activ</p>'
            f'<p class="url"><a href="{public_url}" target="_blank" rel="noopener">{public_url}</a></p>'
        )
    else:
        public_url_block = '<p class="badge waiting">Tunnel in curs de pornire</p><p class="url muted">URL-ul public nu a fost detectat inca.</p>'

    discovered_line = ""
    if discovered_at:
        discovered_line = f"<p><strong>Detectat la:</strong> {discovered_at}</p>"

    return f"""<!DOCTYPE html>
<html lang="ro">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="15">
    <title>Cloudflared Quick Tunnel</title>
    <style>
        :root {{
            color-scheme: light;
            --bg: #f4efe5;
            --panel: rgba(255, 250, 243, 0.96);
            --ink: #1f2a2e;
            --muted: #5c6a6f;
            --accent: #006a6b;
            --accent-soft: rgba(0, 106, 107, 0.14);
            --warn: #c46a2f;
            --warn-soft: rgba(196, 106, 47, 0.14);
            --border: rgba(31, 42, 46, 0.12);
            --shadow: 0 18px 40px rgba(31, 42, 46, 0.12);
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            min-height: 100vh;
            font-family: "Trebuchet MS", "Verdana", sans-serif;
            color: var(--ink);
            background:
                radial-gradient(circle at top left, rgba(196, 106, 47, 0.18), transparent 28%),
                radial-gradient(circle at top right, rgba(0, 106, 107, 0.18), transparent 25%),
                linear-gradient(180deg, #f8f1e5 0%, var(--bg) 100%);
        }}

        main {{
            width: min(760px, calc(100% - 2rem));
            margin: 3rem auto;
            padding: 1.5rem;
            border: 1px solid var(--border);
            border-radius: 26px;
            background: var(--panel);
            box-shadow: var(--shadow);
        }}

        h1 {{
            margin: 0 0 0.4rem;
        }}

        .eyebrow,
        .muted {{
            color: var(--muted);
        }}

        .eyebrow {{
            margin: 0 0 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-size: 0.75rem;
        }}

        .badge {{
            display: inline-flex;
            margin: 1rem 0 0.4rem;
            padding: 0.55rem 0.9rem;
            border-radius: 999px;
            font-weight: 700;
        }}

        .badge.success {{
            color: var(--accent);
            background: var(--accent-soft);
        }}

        .badge.waiting {{
            color: var(--warn);
            background: var(--warn-soft);
        }}

        .url {{
            margin: 0.35rem 0 1.4rem;
            font-size: clamp(1.05rem, 2vw, 1.35rem);
            word-break: break-word;
        }}

        .url a {{
            color: var(--accent);
            text-decoration: none;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1rem;
            margin-top: 1.5rem;
        }}

        .card {{
            padding: 1rem;
            border: 1px solid var(--border);
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.55);
        }}

        .card p {{
            margin: 0.35rem 0;
        }}
    </style>
</head>
<body>
    <main>
        <p class="eyebrow">Cloudflare Quick Tunnel</p>
        <h1>Aplicație sesizări</h1>
        <p class="muted">Pagina se actualizează automat la 15 secunde și arată URL-ul public curent expus de cloudflared.</p>
        {public_url_block}
        <div class="grid">
            <section class="card">
                <p><strong>Status:</strong> {service_status}</p>
                <p><strong>Target local:</strong> {target_url}</p>
                {discovered_line}
            </section>
            <section class="card">
                <p><strong>Ultimul update:</strong> {last_update}</p>
                <p><strong>Ultimul mesaj:</strong> {last_message}</p>
            </section>
        </div>
    </main>
</body>
</html>"""


class StatusStore:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict:
        if not self.file_path.exists():
            return {}

        try:
            return json.loads(self.file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def save(self, payload: dict) -> None:
        temp_path = self.file_path.with_suffix(f"{self.file_path.suffix}.tmp")
        temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        temp_path.replace(self.file_path)


@dataclass
class RuntimeState:
    target_url: str
    store: StatusStore

    def __post_init__(self) -> None:
        self.lock = threading.Lock()
        initial_status = self.store.load()
        self.status = {
            "public_url": initial_status.get("public_url"),
            "public_url_discovered_at": initial_status.get("public_url_discovered_at"),
            "service_status": "starting",
            "target_url": self.target_url,
            "updated_at": utc_now_iso(),
            "last_message": "Serviciul de quick tunnel porneste.",
        }
        self.store.save(self.status)

    def snapshot(self) -> dict:
        with self.lock:
            return dict(self.status)

    def update(self, **changes) -> dict:
        with self.lock:
            self.status.update(changes)
            self.status["updated_at"] = utc_now_iso()
            self.store.save(self.status)
            return dict(self.status)


def make_handler(runtime: RuntimeState):
    class CloudflaredStatusHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            snapshot = runtime.snapshot()
            if self.path in ["/", "/index.html"]:
                document = render_status_document(snapshot)
                payload = document.encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return

            if self.path == "/status.json":
                payload = json.dumps(snapshot, indent=2, sort_keys=True).encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return

            self.send_error(HTTPStatus.NOT_FOUND)

        def log_message(self, format, *args):
            return

    return CloudflaredStatusHandler


def parse_int(value: str, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def run_cloudflared_quick_tunnel() -> int:
    project_root = Path(__file__).resolve().parents[1]
    target_url = os.environ.get("CLOUDFLARED_TARGET_URL", "http://127.0.0.1:5000")
    status_host = os.environ.get("CLOUDFLARED_STATUS_HOST", "0.0.0.0")
    status_port = parse_int(os.environ.get("CLOUDFLARED_STATUS_PORT", "8081"), 8081)
    status_file_path = resolve_status_file(
        project_root,
        os.environ.get("CLOUDFLARED_STATUS_FILE", "instance/cloudflared_quick_tunnel.json"),
    )
    cloudflared_bin = os.environ.get("CLOUDFLARED_BIN", "/usr/bin/cloudflared")

    runtime = RuntimeState(target_url=target_url, store=StatusStore(status_file_path))
    server = ThreadingHTTPServer((status_host, status_port), make_handler(runtime))
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    command = [cloudflared_bin, "tunnel", "--no-autoupdate", "--url", target_url]
    runtime.update(
        service_status="starting",
        last_message=f"Pornim cloudflared: {' '.join(command)}",
        status_server=f"http://{status_host}:{status_port}",
    )

    print(f"[cloudflared-status] Pornim status server pe {status_host}:{status_port}", flush=True)
    print(f"[cloudflared-status] Pornim cloudflared catre {target_url}", flush=True)

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )

    shutdown_event = threading.Event()

    def handle_signal(signum, _frame):
        if shutdown_event.is_set():
            return

        shutdown_event.set()
        runtime.update(service_status="stopping", last_message=f"Am primit semnalul {signum}. Oprim cloudflared.")
        if process.poll() is None:
            process.terminate()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    try:
        if process.stdout is not None:
            for output_line in process.stdout:
                line = output_line.strip()
                if line:
                    print(line, flush=True)

                public_url = extract_quick_tunnel_url(line)
                if public_url:
                    runtime.update(
                        service_status="ready",
                        public_url=public_url,
                        public_url_discovered_at=utc_now_iso(),
                        last_message="Quick Tunnel activ.",
                    )
                elif line:
                    runtime.update(last_message=line)

        return_code = process.wait()
    finally:
        server.shutdown()
        server.server_close()

    if shutdown_event.is_set():
        runtime.update(service_status="stopped", last_message="Serviciul a fost oprit.")
        return 0

    runtime.update(
        service_status="error",
        public_url=None,
        public_url_discovered_at=None,
        last_message=f"cloudflared s-a oprit cu codul {return_code}.",
    )
    return return_code


if __name__ == "__main__":
    sys.exit(run_cloudflared_quick_tunnel())
