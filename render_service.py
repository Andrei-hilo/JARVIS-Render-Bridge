"""Render-only entry point for the JARVIS BDFD bridge.

Only the authenticated /api/bdfd/* API allow-list is exposed. The full
JARVIS dashboard, settings, Omni Router API, file tools, and admin/self-
upgrade routes are intentionally inaccessible from this public service.
"""
from __future__ import annotations

import os
from pathlib import Path
from flask import jsonify, request

# Render Free has an ephemeral filesystem. A paid persistent disk can be
# mounted at /var/data and selected by setting JARVIS_PERSISTENT_DIR.
data_root = Path(os.environ.get("JARVIS_PERSISTENT_DIR", "/tmp/jarvis-persistent")).expanduser()
gateway_root = Path(os.environ.get("JARVIS_GATEWAY_DIR", "/tmp/jarvis-gateway")).expanduser()
data_root.mkdir(parents=True, exist_ok=True)
gateway_root.mkdir(parents=True, exist_ok=True)
os.environ["JARVIS_PERSISTENT_DIR"] = str(data_root)
os.environ["JARVIS_GATEWAY_DIR"] = str(gateway_root)

bridge_token = os.environ.get("JARVIS_BDFD_TOKEN", "").strip()
if len(bridge_token) < 40:
    raise RuntimeError(
        "Set JARVIS_BDFD_TOKEN in Render Environment. It must be at least 40 characters."
    )

import jarvis as core

# Configure one cloud model provider from Render Environment variables.
# No API key is stored in GitHub or in this project archive.
provider_key = os.environ.get("JARVIS_PROVIDER_API_KEY", "").strip()
provider_model = os.environ.get("JARVIS_PROVIDER_MODEL", "").strip()
provider_base = os.environ.get(
    "JARVIS_PROVIDER_BASE_URL", "https://openrouter.ai/api/v1"
).strip().rstrip("/")
provider_name = os.environ.get("JARVIS_PROVIDER_NAME", "OpenRouter").strip() or "Cloud AI"
provider_id = os.environ.get("JARVIS_PROVIDER_ID", "openrouter").strip().lower() or "openrouter"
provider_kind = os.environ.get("JARVIS_PROVIDER_KIND", "openai").strip().lower()

if provider_key and not provider_model:
    raise RuntimeError("JARVIS_PROVIDER_MODEL is required when JARVIS_PROVIDER_API_KEY is set.")
if provider_key:
    state = core._gateway_read_state()
    configured = core._gateway_validate_providers([{
        "id": provider_id,
        "name": provider_name,
        "base_url": provider_base,
        "api_key": provider_key,
        "model": provider_model,
        "tier": "api",
        "priority": 10,
        "kind": provider_kind,
        "enabled": True,
        "supports_vision": False,
        "supports_tools": True,
    }])
    state["providers"] = configured
    core._gateway_write_state(state)

app = core.app
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024

# A public Render service must only reveal the endpoints required by BDFD.
# The local-only token settings and token-rotation endpoints are excluded.
ALLOWED = {
    ("GET", "/healthz"),
    ("GET", "/api/bdfd/health"),
    ("POST", "/api/bdfd/chat"),
    ("POST", "/api/bdfd/messages"),
    ("POST", "/api/bdfd/outbox"),
    ("GET", "/api/bdfd/outbox/next"),
    ("POST", "/api/bdfd/outbox/ack"),
    ("GET", "/api/bdfd/conversation"),
}

@app.before_request
def render_public_route_guard():
    if (request.method.upper(), request.path) not in ALLOWED:
        return jsonify({"ok": False, "error": "Not found."}), 404
    if request.content_length is not None and request.content_length > 32 * 1024:
        return jsonify({"ok": False, "error": "Request body is too large."}), 413
    return None

@app.after_request
def render_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Frame-Options"] = "DENY"
    return response

@app.get("/healthz")
def render_healthcheck():
    return jsonify({"ok": True, "service": "JARVIS-BDFD-Bridge", "version": core.VERSION})

# Public WSGI object used by Gunicorn.
    # No app.run() here; Render starts this WSGI app with Gunicorn.
