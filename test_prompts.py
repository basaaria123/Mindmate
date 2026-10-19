"""Every prompt file exists, renders with the placeholders its agent supplies, and has no stray placeholders."""

import re
from pathlib import Path
from string import Template

import pytest

from app.utils.prompts import PROMPT_DIR, load_prompt, render_prompt

PLACEHOLDERS = {
    "profile": {"user_message"},
    "opportunity": {"opportunity_text"},
    "fit": {"profile", "opportunity"},
    "gap": {"profile", "opportunity", "fit_assessment"},
    "planner": {"profile", "opportunity", "gap_vector", "goal_id", "decisions", "memories", "daily_budget"},
    "practice": {"topic", "question", "user_answer"},
    "suggestions": {"profile"},
    "practice_questions": {"count", "target_role", "topic", "skills", "gaps", "weaknesses", "allowed_refs"},
    "replan": {"changes", "allowed_refs"},
}


def placeholders(text):
    return {m.group("named") or m.group("braced") for m in Template.pattern.finditer(text) if m.group("named") or m.group("braced")}


@pytest.mark.parametrize("name", sorted(PLACEHOLDERS))
def test_prompt_files_and_placeholders(name):
    assert (PROMPT_DIR / f"{name}.md").exists() and (PROMPT_DIR / f"{name}.system.md").exists()
    assert placeholders(load_prompt(name)) == PLACEHOLDERS[name]
    assert placeholders(load_prompt(f"{name}.system")) == set()
    rendered = render_prompt(name, **{key: f"<{key}>" for key in PLACEHOLDERS[name]})
    assert "${" not in rendered


def test_missing_placeholder_fails_loudly():
    with pytest.raises(KeyError):
        render_prompt("fit", profile="only one value")


def test_no_unused_prompt_files():
    names = {re.sub(r"\.system$", "", p.stem) for p in Path(PROMPT_DIR).glob("*.md")}
    assert names == set(PLACEHOLDERS)
