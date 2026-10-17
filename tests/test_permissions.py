"""Success criterion 5: no irreversible action without user confirmation;
actions are limited to drafts and tasks."""

from app.permissions import PermissionLevel, check_permission


def test_read_only_allowed():
    decision = check_permission("read_profile")
    assert decision.allowed and decision.level is PermissionLevel.READ_ONLY


def test_task_writes_require_opt_in():
    assert check_permission("create_task", allow_task_writes=True).allowed
    assert not check_permission("create_task", allow_task_writes=False).allowed
    assert not check_permission("create_reminder").allowed  # not in the MVP


def test_application_actions_are_draft_only():
    draft = check_permission("draft_application")
    assert draft.allowed and draft.draft_only
    submit = check_permission("submit_application", user_confirmed=True)
    assert not submit.allowed and submit.requires_confirmation
    assert not check_permission("send_message", user_confirmed=True).allowed


def test_delete_all_memory_needs_confirmation():
    assert not check_permission("delete_all_memory").allowed
    assert check_permission("delete_all_memory", user_confirmed=True).allowed


def test_unknown_action_denied():
    assert not check_permission("format_disk").allowed


def test_actions_api_never_submits(seeded_client):
    denied = seeded_client.post("/actions", json={"action": "submit_application", "confirmed": True})
    assert denied.status_code == 403

    draft = seeded_client.post("/actions", json={"action": "draft_application", "payload": {"opportunity": "opp#1"}, "refs": ["opp#1"]})
    assert draft.status_code == 201
    body = draft.json()
    assert body["status"] == "draft" and body["refs"] == ["opp#1"]

    confirmed = seeded_client.post(f"/actions/{body['id']}/confirm")
    assert confirmed.json()["status"] == "confirmed"
    assert "manually" in confirmed.json()["next_step"]

    bad_refs = seeded_client.post("/actions", json={"action": "draft_application", "refs": ["opp#999"]})
    assert bad_refs.status_code == 422

    events = seeded_client.get("/agent/events?agent=permissions").json()["events"]
    assert any("denied" in e["summary"] for e in events)
