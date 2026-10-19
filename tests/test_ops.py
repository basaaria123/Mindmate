"""Operations: readiness check, legacy JSON memory import, swappable demo persona, rehearsal script."""

import json
import subprocess
import sys
from pathlib import Path

from app.schemas.memory import MemoryItem

ROOT = Path(__file__).resolve().parents[1]


def test_readiness_reports_database_and_mode(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready" and body["checks"]["database"] == "ok"
    assert body["checks"]["llm_available"] is False and body["checks"]["demo_cache"] == "off"


def test_readiness_fails_when_database_is_unreachable(client, monkeypatch):
    from app.db import reset_engine

    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://nobody:wrong@127.0.0.1:1/none")
    reset_engine()
    response = client.get("/health/ready")
    assert response.status_code == 503 and response.json()["checks"]["database"].startswith("error")


def test_legacy_json_memory_is_imported_once(seeded_client, tmp_path, monkeypatch):
    legacy_file = tmp_path / "memories.json"
    items = [
        MemoryItem(memory_id="weakness#01", memory_type="weakness", content="Model evaluation", reference_tags=["practice"], source="practice:Model evaluation", confidence=40),
        MemoryItem(memory_id="decision#01", memory_type="decision", content="Exams before GATE", source="chat", confidence=90),
        MemoryItem(memory_id="learning_insight#01", memory_type="learning_insight", content="Explains with examples well", source="practice:SQL", confidence=70),
    ]
    legacy_file.write_text(json.dumps([i.model_dump() for i in items]))
    monkeypatch.setattr("app.services.memory_store.MEMORY_FILE", legacy_file)

    first = seeded_client.post("/memory/import-legacy").json()
    assert first["imported"] == ["weakness#01", "decision#01", "learning_insight#01"]
    assert any(w["topic"] == "Model evaluation" for w in seeded_client.get("/weaknesses").json()["weaknesses"])
    assert any(d["statement"] == "Exams before GATE" for d in seeded_client.get("/decisions").json()["decisions"])
    replan = seeded_client.post("/plans/replan", json={}).json()
    assert any(ref.startswith("weakness#") for ref in replan["refs"])  # imported weakness now drives the plan

    second = seeded_client.post("/memory/import-legacy").json()
    assert second["imported"] == [] and second["skipped"] == 3


def test_persona_can_be_swapped_without_code(client, tmp_path, monkeypatch):
    persona = json.loads((ROOT / "data" / "seed_persona.json").read_text())
    persona["user"]["name"] = "Arjun"
    persona["opportunities"] = [{"title": "Clinical Data Intern", "org": "City Hospital", "type": "internship", "deadline_in_days": 20,
                                 "requirements": [{"name": "SQL", "weight": "High", "mandatory": True}]}]
    path = tmp_path / "persona.json"
    path.write_text(json.dumps(persona))
    monkeypatch.setenv("MINDMATE_SEED_PERSONA", str(path))
    assert client.post("/admin/reset-demo").status_code == 200
    assert client.get("/profile").json()["name"] == "Arjun"
    assert [o["title"] for o in client.get("/opportunities").json()["opportunities"]] == ["Clinical Data Intern"]


def test_demo_check_script_passes(tmp_path):
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin", "DATABASE_URL": f"sqlite:///{tmp_path}/demo.db", "MINDMATE_LLM_MODE": "off", "PYTHONPATH": str(ROOT)}
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "demo_check.py")], capture_output=True, text=True, env=env, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "All demo checks passed." in result.stdout


def test_evaluation_runner_offline(tmp_path):
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin", "DATABASE_URL": f"sqlite:///{tmp_path}/eval.db", "PYTHONPATH": str(ROOT)}
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "run_eval.py"), "--json"], capture_output=True, text=True, env=env, timeout=120)
    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["mode"] == "deterministic" and len(summary["practice_scores"]) == 10 and len(summary["extracted"]) == 10
    assert 0 <= summary["extraction_precision"] <= 1 and 0 <= summary["extraction_recall"] <= 1
