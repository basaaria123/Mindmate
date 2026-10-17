#!/usr/bin/env python3
"""One-command database reset to the seeded demo persona.

Usage:
    python scripts/reset_demo.py            # wipe and reseed DATABASE_URL
    python scripts/reset_demo.py --seed-only  # seed only if the database is empty
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.db import get_session_factory, init_db, models  # noqa: E402
from app.services.seed import reset_demo, seed  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Reset the MindMate database to the demo persona.")
    parser.add_argument("--seed-only", action="store_true", help="Seed only when no user exists; never wipe.")
    args = parser.parse_args()

    init_db()
    session = get_session_factory()()
    try:
        if args.seed_only:
            if session.scalar(select(models.User).limit(1)) is not None:
                print("Database already has data; nothing to do.")
                return 0
            summary = seed(session)
        else:
            summary = reset_demo(session)
    finally:
        session.close()
    print("Demo database ready:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
