"""Demo fallback for the AI endpoints (proposal section 12, "Demo fallbacks").

Set ``MINDMATE_DEMO_CACHE`` to choose how POST /profile, /opportunity, /fit,
/gap, /plan, /suggestions and /practice behave:

* ``off`` (default)  - normal live behaviour.
* ``record``         - call the agents live and save every successful response.
* ``replay``         - never call the model; serve the recorded response for the
                       same request body, else the endpoint's default response.
* ``fallback``       - call live; if the model fails (provider error, missing key,
                       invalid output after retry) serve the recorded response.

Recordings live in ``data/demo_cache/<endpoint>.json`` (``MINDMATE_DEMO_CACHE_DIR``
overrides). The shipped files contain hand-written default responses for the demo
persona, validated against the AI schemas in tests; run once with ``record`` and
a real key to replace them with real Nemotron output. Every cached answer carries
the header ``X-MindMate-Cache`` and is logged to the Trace, so nothing is passed
off as a live model call.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import DATA_DIR

AI_ENDPOINTS = {
    "/profile": "profile",
    "/opportunity": "opportunity",
    "/fit": "fit",
    "/gap": "gap",
    "/plan": "plan",
    "/suggestions": "suggestions",
    "/practice": "practice",
}
MODES = {"off", "record", "replay", "fallback"}
_lock = threading.Lock()


def cache_mode() -> str:
    mode = os.getenv("MINDMATE_DEMO_CACHE", "off").strip().lower() or "off"
    return mode if mode in MODES else "off"


def cache_dir() -> Path:
    return Path(os.getenv("MINDMATE_DEMO_CACHE_DIR") or DATA_DIR / "demo_cache")


def request_key(body: bytes) -> str:
    try:
        normalised = json.dumps(json.loads(body or b"{}"), sort_keys=True, separators=(",", ":"))
    except ValueError:
        normalised = body.decode("utf-8", "replace")
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()[:16]


def _load(name: str) -> dict:
    path = cache_dir() / f"{name}.json"
    if not path.exists():
        return {"entries": {}}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def lookup(name: str, key: str) -> dict | list | None:
    data = _load(name)
    entry = data.get("entries", {}).get(key)
    return entry if entry is not None else data.get("default")


def record(name: str, key: str, response: dict | list) -> None:
    with _lock:
        data = _load(name)
        data.setdefault("entries", {})[key] = response
        data["default"] = response
        data["source"] = "recorded from live Nemotron responses"
        path = cache_dir() / f"{name}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)


def _log(name: str, how: str) -> None:
    try:
        from app.db import get_session_factory
        from app.services.events import log_event

        session = get_session_factory()()
        try:
            log_event(session, agent=name, action=f"demo_cache_{how}",
                      summary=f"{name} agent: served a recorded response ({how}) instead of a live Nemotron call.")
            session.commit()
        finally:
            session.close()
    except Exception:  # noqa: BLE001 - logging must never break the response
        pass


def _is_model_failure(status: int, payload: object) -> bool:
    if status >= 500:
        return True
    # 422 from request validation carries "errors"; 422 from an agent's ValueError does not.
    return status == 422 and isinstance(payload, dict) and "errors" not in payload


class DemoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        name = AI_ENDPOINTS.get(request.url.path)
        mode = cache_mode()
        if request.method != "POST" or name is None or mode == "off":
            return await call_next(request)

        body = await request.body()
        key = request_key(body)

        if mode == "replay":
            cached = lookup(name, key)
            if cached is not None:
                _log(name, "replay")
                return JSONResponse(cached, headers={"X-MindMate-Cache": "replay"})
            return await call_next(request)

        try:
            response = await call_next(request)
            raw = b"".join([chunk async for chunk in response.body_iterator])
            status = response.status_code
            headers = {k: v for k, v in response.headers.items() if k.lower() != "content-length"}
        except Exception:  # noqa: BLE001 - an unhandled agent error is a model failure
            raw, status, headers = b'{"detail": "Internal Server Error"}', 500, {"content-type": "application/json"}

        try:
            payload = json.loads(raw or b"null")
        except ValueError:
            payload = None

        if mode == "record" and status == 200 and payload is not None:
            record(name, key, payload)
            headers["X-MindMate-Cache"] = "recorded"
        elif mode == "fallback" and _is_model_failure(status, payload):
            cached = lookup(name, key)
            if cached is not None:
                _log(name, "fallback")
                return JSONResponse(cached, headers={"X-MindMate-Cache": "fallback"})

        return Response(content=raw, status_code=status, headers=headers, media_type=headers.get("content-type"))
