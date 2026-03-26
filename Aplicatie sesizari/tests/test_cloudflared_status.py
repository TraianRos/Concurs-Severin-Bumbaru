from pathlib import Path

from app.cloudflared_status import (
    StatusStore,
    extract_quick_tunnel_url,
    render_status_document,
    resolve_status_file,
)


def test_extract_quick_tunnel_url_reads_trycloudflare_link():
    output_line = "INF Quick Tunnel available at https://brisk-ocean-example.trycloudflare.com"

    assert extract_quick_tunnel_url(output_line) == "https://brisk-ocean-example.trycloudflare.com"


def test_resolve_status_file_keeps_absolute_paths_and_resolves_relative_ones(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()

    relative_path = resolve_status_file(project_root, "instance/cloudflared_quick_tunnel.json")
    absolute_path = resolve_status_file(project_root, "/tmp/cloudflared_quick_tunnel.json")

    assert relative_path == project_root / "instance/cloudflared_quick_tunnel.json"
    assert absolute_path == Path("/tmp/cloudflared_quick_tunnel.json")


def test_status_store_persists_payload_and_renderer_exposes_public_url(tmp_path):
    status_file = tmp_path / "cloudflared-status.json"
    store = StatusStore(status_file)
    payload = {
        "public_url": "https://steady-field.trycloudflare.com",
        "public_url_discovered_at": "2026-03-26T00:10:00+00:00",
        "service_status": "ready",
        "target_url": "http://127.0.0.1:5000",
        "updated_at": "2026-03-26T00:10:05+00:00",
        "last_message": "Quick Tunnel activ.",
    }

    store.save(payload)
    loaded_payload = store.load()
    html = render_status_document(loaded_payload)

    assert loaded_payload == payload
    assert "steady-field.trycloudflare.com" in html
    assert "Tunnel activ" in html
