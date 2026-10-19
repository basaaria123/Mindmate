#!/usr/bin/env python3
"""Non-destructive production smoke test for a deployed MindMate.

    python scripts/smoke_test.py --backend https://api.example.com --frontend https://mindmate.vercel.app

Checks: backend liveness and readiness (database), configuration, CORS for the
frontend origin, read-only API endpoints, and that the frontend serves the app
and its client-side routes. Nothing is written. For the full demo path (which
resets data) use scripts/demo_check.py with --base-url and --admin-token.
"""

from __future__ import annotations

import argparse
import sys

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--backend", required=True)
    parser.add_argument("--frontend", help="Deployed frontend URL; also used as the CORS origin")
    parser.add_argument("--timeout", type=float, default=20)
    args = parser.parse_args()
    backend = args.backend.rstrip("/")
    frontend = args.frontend.rstrip("/") if args.frontend else None

    results: list[tuple[str, bool, str]] = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        results.append((label, ok, detail))

    with httpx.Client(timeout=args.timeout, follow_redirects=True) as client:
        def get(url: str, **kwargs):
            try:
                return client.get(url, **kwargs)
            except httpx.HTTPError as error:
                return error

        response = get(f"{backend}/health")
        check("backend /health", not isinstance(response, Exception) and response.status_code == 200, str(getattr(response, "status_code", response)))
        response = get(f"{backend}/health/ready")
        ready = not isinstance(response, Exception) and response.status_code == 200
        check("backend /health/ready (database)", ready, response.text[:160] if not isinstance(response, Exception) else str(response))
        if ready:
            checks = response.json().get("checks", {})
            check("Nemotron configured (llm_available)", bool(checks.get("llm_available")), f"demo_cache={checks.get('demo_cache')}")
        for path in ("/profile", "/goals", "/plans", "/opportunities", "/memory", "/agent/events?limit=5"):
            response = get(f"{backend}{path}")
            check(f"GET {path}", not isinstance(response, Exception) and response.status_code == 200, str(getattr(response, "status_code", response)))
        if frontend:
            response = get(f"{backend}/profile", headers={"Origin": frontend})
            allowed = None if isinstance(response, Exception) else response.headers.get("access-control-allow-origin")
            check(f"CORS allows {frontend}", allowed in (frontend, "*"), f"access-control-allow-origin={allowed}")
            response = get(frontend)
            check("frontend serves the app", not isinstance(response, Exception) and response.status_code == 200 and '<div id="root"' in response.text)
            response = get(f"{frontend}/pipeline")
            check("frontend client-side route /pipeline", not isinstance(response, Exception) and response.status_code == 200 and '<div id="root"' in response.text)

    width = max(len(label) for label, _, _ in results)
    failed = 0
    for label, ok, detail in results:
        failed += 0 if ok else 1
        print(f"{'PASS' if ok else 'FAIL'}  {label:<{width}}  {detail}")
    print(f"\n{len(results) - failed}/{len(results)} checks passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
