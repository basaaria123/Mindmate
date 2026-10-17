"""Success criteria 4: every memory item is viewable, editable and deletable, and
deleted items never appear in later prompts, plans or rationales."""

from app.db import models
from app.memory import service as memory_service
from app.memory.refs import InvalidReference, validate_refs
from app.memory.retrieval import retrieve_for_task
from app.services.plan_service import replan
from app.services.practice_service import evaluate


def test_deleted_decision_is_absent_from_prompts_and_rationale(seeded, user):
    decisions = [i for i in memory_service.list_items(seeded, user.id, types={"decision"})]
    assert decisions
    target = decisions[0]
    ref = target.ref_id

    memory_service.soft_delete_item(seeded, target)
    seeded.commit()

    bundle = retrieve_for_task(seeded, user, "planner")
    assert ref not in bundle.all_refs()
    assert all(d["ref"] != ref for d in bundle.decisions)

    outcome = replan(seeded, user)
    assert ref not in outcome["rationale"]
    assert ref not in outcome["refs"]

    try:
        validate_refs(seeded, [ref])
    except InvalidReference:
        pass
    else:
        raise AssertionError("deleted references must be rejected")


def test_deleted_weakness_no_longer_boosts_plan(seeded, user):
    result = evaluate(seeded, user, answer="Accuracy is fine I think.", topic="Model evaluation")
    weakness_ref = result["weakness_ref"]
    item = next(i for i in memory_service.list_items(seeded, user.id, types={"weakness"}) if i.ref_id == weakness_ref)
    memory_service.soft_delete_item(seeded, item)
    seeded.commit()
    outcome = replan(seeded, user)
    assert weakness_ref not in outcome["refs"]
    assert all(not t["must_keep"] or weakness_ref not in t["refs"] for t in outcome["plan"]["tasks"])


def test_edit_updates_entity_and_memory(seeded, user):
    item = next(i for i in memory_service.list_items(seeded, user.id, types={"skill"}) if "SQL" in i.content)
    memory_service.update_item(seeded, item, payload={"level": "intermediate", "confidence": 70})
    seeded.commit()
    skill = seeded.get(models.Skill, int(item.ref_id.split("#")[1]))
    assert skill.level == "intermediate" and skill.confidence == 70
    assert "intermediate" in item.content


def test_purge_removes_rows_for_good(seeded, user):
    item = memory_service.list_items(seeded, user.id, types={"evidence"})[0]
    ref_id = int(item.ref_id.split("#")[1])
    memory_service.soft_delete_item(seeded, item)
    removed = memory_service.purge_deleted(seeded, user.id)
    seeded.commit()
    assert removed == 1
    assert seeded.get(models.Evidence, ref_id) is None
    assert all(i.deleted_at is None for i in memory_service.list_items(seeded, user.id, include_deleted=True))


def test_task_scoped_retrieval_only_returns_needed_kinds(seeded, user):
    fit_bundle = retrieve_for_task(seeded, user, "fit")
    assert fit_bundle.skills and fit_bundle.evidence
    assert fit_bundle.decisions == [] and fit_bundle.constraints == []
    planner_bundle = retrieve_for_task(seeded, user, "planner")
    assert planner_bundle.decisions and planner_bundle.constraints
    assert planner_bundle.evidence == []
