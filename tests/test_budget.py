"""Success criterion 2: changing available time (60 -> 30) gives a valid reduced plan."""

from app.services.plan_service import active_plan, replan, serialize_plan
from app.services.practice_service import evaluate


def test_thirty_minute_replan_never_exceeds_budget(seeded, user):
    evaluate(seeded, user, answer="I would check accuracy and that is it.", topic="Model evaluation")
    outcome = replan(seeded, user, available_minutes=30, reason="only 30 minutes today")
    plan = outcome["plan"]
    assert plan["daily_budget_minutes"] == 30
    assert all(minutes <= 30 for minutes in plan["minutes_by_day"].values())
    must_keep = [t for t in plan["tasks"] if t["must_keep"]]
    assert must_keep and all(t["status"] == "todo" for t in must_keep)
    assert "Daily budget changed from 60 to 30" in outcome["rationale"]
    total_before = sum(t["minutes"] for t in serialize_plan(active_plan(seeded, user.id))["tasks"])
    assert total_before > 0


def test_budget_increase_and_plan_versions(seeded, user):
    first = replan(seeded, user, available_minutes=90)
    assert first["plan"]["version"] == 2
    second = replan(seeded, user, available_minutes=45)
    assert second["plan"]["version"] == 3
    assert all(minutes <= 45 for minutes in second["plan"]["minutes_by_day"].values())
    assert second["previous_plan_id"] == first["plan"]["id"]
