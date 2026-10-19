#!/usr/bin/env python3
"""Run the evaluation set (data/eval) and report agreement with the expected labels.

    python scripts/run_eval.py           # deterministic rubric and keyword extraction (offline)
    python scripts/run_eval.py --live    # Practice and Opportunity agents on Nemotron (needs NEBIUS_API_KEY)

Practice: an answer counts as weak when its score is below WEAKNESS_SCORE_THRESHOLD
(default 60); accuracy is the share of answers whose weak/strong label matches.
Postings: precision and recall of extracted required skills against expected_required.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load(name: str) -> dict:
    return json.loads((ROOT / "data" / "eval" / name).read_text(encoding="utf-8"))


def norm(name: str) -> str:
    return name.strip().lower()


def matches(expected: str, extracted: list[str]) -> bool:
    from app.scoring.fit import skill_matches

    return any(skill_matches(expected, name) for name in extracted)


def practice_scores(live: bool) -> list[tuple[dict, int]]:
    from app.services.practice_service import deterministic_rubric, overall_score, question_bank

    bank = question_bank()
    results = []
    for item in load("practice_answers.json")["answers"]:
        entry = [q for q in bank if q["topic"] == item["topic"]][item["question_index"]]
        if live:
            from app.agents.practice_agent import evaluate_practice

            evaluation = evaluate_practice(question=entry["question"], user_answer=item["answer"], topic=item["topic"])
            rubric = {"correctness": evaluation.correctness, "depth": evaluation.depth, "clarity": evaluation.clarity}
        else:
            rubric = deterministic_rubric(item["answer"], entry)[0]
        results.append((item, overall_score(rubric)))
    return results


def posting_skills(live: bool) -> list[tuple[dict, list[str]]]:
    results = []
    if live:
        from app.agents.opportunity_agent import extract_opportunity

        for item in load("postings.json")["postings"]:
            spec = extract_opportunity(item["text"])
            results.append((item, [r.skill_name for r in spec.required_skills if r.is_mandatory or r.importance == "High"]))
        return results

    os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.mkdtemp()}/eval.db")
    from app.db import get_session_factory, init_db, models
    from app.services.opportunity_service import deterministic_extract

    init_db(True)
    session = get_session_factory()()
    user = models.User(name="eval")
    session.add(user)
    session.flush()
    for item in load("postings.json")["postings"]:
        data = deterministic_extract(session, user, item["text"])
        results.append((item, [r["name"] for r in data["requirements"] if r["weight"] == "High"]))
    session.close()
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--live", action="store_true", help="call the Nemotron agents instead of the deterministic code")
    parser.add_argument("--json", action="store_true", help="print machine-readable results")
    args = parser.parse_args()
    threshold = int(os.getenv("WEAKNESS_SCORE_THRESHOLD", "60"))

    practice = practice_scores(args.live)
    agree = sum((score < threshold) == item["expect_weak"] for item, score in practice)

    postings = posting_skills(args.live)
    true_positive = extracted_total = expected_total = 0
    for item, extracted in postings:
        expected_total += len(item["expected_required"])
        extracted_total += len(extracted)
        true_positive += sum(matches(skill, extracted) for skill in item["expected_required"])
    precision = true_positive / extracted_total if extracted_total else 0.0
    recall = true_positive / expected_total if expected_total else 0.0

    summary = {
        "mode": "live" if args.live else "deterministic",
        "practice_label_accuracy": round(agree / len(practice), 2),
        "practice_scores": {item["id"]: score for item, score in practice},
        "extraction_precision": round(precision, 2),
        "extraction_recall": round(recall, 2),
        "extracted": {item["id"]: skills for item, skills in postings},
    }
    if args.json:
        print(json.dumps(summary, indent=2))
        return 0

    print(f"Mode: {summary['mode']}")
    print(f"Practice: {agree}/{len(practice)} weak/strong labels match (threshold {threshold})")
    for item, score in practice:
        flag = "ok " if (score < threshold) == item["expect_weak"] else "MISS"
        print(f"  {flag} {item['id']} {item['topic']:<32} score {score:3d}  expected {'weak' if item['expect_weak'] else 'strong'}")
    print(f"Extraction: precision {precision:.2f}, recall {recall:.2f}")
    for item, extracted in postings:
        missing = [s for s in item["expected_required"] if not matches(s, extracted)]
        print(f"  {item['id']} extracted {extracted}" + (f"  missing {missing}" if missing else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
