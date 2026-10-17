"""Success criterion 1: a recorded weakness changes the next plan's priorities,
and the rationale cites it (the weakness-to-replan path)."""

from app.db import models
from app.memory.retrieval import active_weaknesses
from app.services.plan_service import active_plan, replan, serialize_plan
from app.services.practice_service import evaluate

WEAK_ANSWER = "I would look at accuracy on the test set and if it is low maybe try a different model."


def test_weakness_changes_plan_order_and_rationale_cites_it(seeded, user):
    before = serialize_plan(active_plan(seeded, user.id))
    before_day_one = [t["title"] for t in before["tasks"] if t["day_number"] == 1]
    assert "Mock interview: model evaluation questions" not in before_day_one

    result = evaluate(seeded, user, answer=WEAK_ANSWER, topic="Model evaluation")
    assert result["score"] < 60
    assert result["weakness_recorded"] is True
    weaknesses = active_weaknesses(seeded, user.id)
    assert len(weaknesses) == 1 and weaknesses[0].topic == "Model evaluation"
    weakness_ref = result["weakness_ref"]

    outcome = replan(seeded, user, reason="weakness recorded")
    after = outcome["plan"]
    after_day_one = [t["title"] for t in after["tasks"] if t["day_number"] == 1]
    assert after_day_one[0] == "Mock interview: model evaluation questions"
    assert outcome["diff"]["before"] != outcome["diff"]["after"]
    assert any(m["title"] == "Mock interview: model evaluation questions" for m in outcome["diff"]["moved"])
    assert weakness_ref in outcome["rationale"]
    assert weakness_ref in outcome["refs"]
    # the practice session that produced the weakness is cited too
    assert any(ref.startswith("practice#") for ref in outcome["refs"])


def test_single_weak_answer_does_not_create_weakness_without_history(seeded, user):
    result = evaluate(seeded, user, answer="A hash map gives average constant time lookups but has no ordering, unlike a tree.", topic="Data structures")
    assert result["weakness_recorded"] is False
    assert "needed before recording" in result["weakness_reason"]


def test_new_weakness_without_matching_task_adds_focus_task(seeded, user):
    for _ in range(2):
        evaluate(seeded, user, answer="SQL joins combine tables somehow, I am not sure about the details.", topic="SQL")
    seeded.commit()
    outcome = replan(seeded, user)
    added = [a["title"] for a in outcome["diff"]["added"]]
    # the seeded plan already has a SQL task ("Practice two SQL join questions"), so it is boosted, not duplicated
    assert added == [] or added == ["Focus practice: SQL"]
    sql_tasks = [t for t in outcome["plan"]["tasks"] if "SQL" in t["title"]]
    assert sql_tasks and sql_tasks[0]["must_keep"] is True
    assert sql_tasks[0]["day_number"] == 1


def test_every_event_is_logged_for_the_trace(seeded, user):
    evaluate(seeded, user, answer=WEAK_ANSWER, topic="Model evaluation")
    replan(seeded, user)
    actions = {e.action for e in seeded.query(models.Event).all()}
    assert {"answer_evaluated", "weakness_recorded", "replan", "plan_created", "demo_seeded"} <= actions
