#!/usr/bin/env python3
"""Rehearse the scripted demo path and check the success criteria.

Usage:
    python scripts/demo_check.py                      # in-process app on a temporary SQLite database
    python scripts/demo_check.py --base-url URL       # a running deployment (staging or production)
    python scripts/demo_check.py --base-url URL --admin-token TOKEN

Steps (demo script, proposal section 14): reset to the persona, fit for the target
opportunity, gap ranking, a weak practice answer, the weakness in memory, a
30-minute replan, the trace. Checks success criteria 1, 2, 3 and 7 and exits
non-zero if any check fails. Without --base-url nothing outside this machine is touched.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

WEAK_ANSWER = "I would look at the accuracy on the test set and, if it is low, try another model."
REPLAN_TARGET_SECONDS = 15.0


def make_client(base_url: str | None, admin_token: str | None):
    headers = {"X-Admin-Token": admin_token} if admin_token else {}
    if base_url:
        import httpx

        return httpx.Client(base_url=base_url.rstrip("/"), headers=headers, timeout=120), None
    tmp = tempfile.mkdtemp(prefix="mindmate-demo-")
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{tmp}/demo.db")
    os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "0")
    os.environ.setdefault("MINDMATE_AUTO_SEED", "false")
    from fastapi.testclient import TestClient

    import main

    client = TestClient(main.app, headers=headers)
    client.__enter__()
    return client, client


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", help="Deployed backend URL; omit to run in-process")
    parser.add_argument("--admin-token", default=os.getenv("MINDMATE_ADMIN_TOKEN"))
    parser.add_argument("--opportunity", type=int, default=1)
    args = parser.parse_args()

    client, context = make_client(args.base_url, args.admin_token)
    timings: list[tuple[str, float, str]] = []
    failures: list[str] = []

    def step(label, method, path, **kwargs):
        started = time.perf_counter()
        response = client.request(method, path, **kwargs)
        elapsed = time.perf_counter() - started
        ok = response.status_code < 400
        timings.append((label, elapsed, str(response.status_code)))
        if not ok:
            failures.append(f"{label}: HTTP {response.status_code} {response.text[:200]}")
            raise SystemExit(report(timings, failures))
        return response.json()

    def check(condition: bool, message: str):
        if not condition:
            failures.append(message)

    try:
        step("Reset to demo persona", "POST", "/admin/reset-demo")
        fit = step("Fit for target opportunity", "POST", f"/opportunities/{args.opportunity}/fit", json={})
        gaps = step("Gap ranking", "POST", "/skills/gaps", json={"opportunity_id": args.opportunity})["gaps"]
        before = step("Plan before practice", "GET", "/plans")["active"]
        practice = step("Weak practice answer", "POST", "/practice/evaluate", json={"answer": WEAK_ANSWER, "topic": "Model evaluation"})
        memory = step("Memory after practice", "GET", "/memory")
        replan = step("Replan at 30 min/day", "POST", "/plans/replan", json={"available_minutes": 30, "reason": "only 30 minutes today"})
        events = step("Trace", "GET", "/agent/events?limit=50")["events"]
    finally:
        if context is not None:
            context.__exit__(None, None, None)

    weakness_ref = practice.get("weakness_ref")
    check(fit.get("score") is not None and fit.get("top_gap"), "Fit returned no score or top gap")
    check(bool(gaps), "Gap ranking returned no gaps")
    check(practice.get("weakness_recorded") is True, "Criterion 1: the weak answer did not record a weakness")
    check(f"Practice focus: {practice.get('weakness')}" in memory.get("memoryNotes", []), "Memory screen would not show the weakness as saved")
    plan = replan["plan"]
    check(all(m <= 30 for m in plan["minutes_by_day"].values()), "Criterion 2: a day exceeds the 30-minute budget")
    check(any(t["must_keep"] for t in plan["tasks"]), "Criterion 2: no must-keep task survived the reduced budget")
    check(bool(weakness_ref) and weakness_ref in replan["rationale"], "Criterion 1/3: the replan rationale does not cite the weakness")
    check(replan["diff"]["before"] != replan["diff"]["after"], "Criterion 1: the plan order did not change")
    day_one_before = [t["title"] for t in before["tasks"] if t["day_number"] == 1]
    day_one_after = [t["title"] for t in plan["tasks"] if t["day_number"] == 1]
    replan_seconds = next(seconds for label, seconds, _ in timings if label.startswith("Replan"))
    check(replan_seconds <= REPLAN_TARGET_SECONDS, f"Criterion 7: replan took {replan_seconds:.1f}s (target {REPLAN_TARGET_SECONDS:.0f}s)")
    check(any(e["action"] == "replan" for e in events), "Trace has no replan event")

    print(f"Fit: {fit['score']}% ({fit['band']}), top gap: {fit['top_gap']}")
    print(f"Practice: score {practice['score']}, weakness {weakness_ref}")
    print(f"Day 1 before: {day_one_before}")
    print(f"Day 1 after:  {day_one_after}")
    print(f"Rationale: {replan['rationale'][:240]}...")
    return report(timings, failures)


def report(timings, failures) -> int:
    print("\nStep timings")
    for label, seconds, status in timings:
        print(f"  {label:<30} {seconds * 1000:8.0f} ms  HTTP {status}")
    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("\nAll demo checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
