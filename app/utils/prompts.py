"""Versioned prompt templates (prompts/*.md).

Prompts live in files so changes show up in code review (proposal, prompt
design rules). Templates use ``${name}`` placeholders (string.Template), which
leaves the JSON braces in the prompts untouched. ``render_prompt`` fails loudly
if a placeholder has no value, so a renamed variable cannot ship silently.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from string import Template

PROMPT_DIR = Path(__file__).resolve().parents[2] / "prompts"


@lru_cache(maxsize=64)
def load_prompt(name: str) -> str:
    """Return the raw text of prompts/<name>.md."""

    return (PROMPT_DIR / f"{name}.md").read_text(encoding="utf-8")


def render_prompt(name: str, **values: object) -> str:
    """Fill a prompt template; every ${placeholder} must be supplied."""

    return Template(load_prompt(name)).substitute({key: str(value) for key, value in values.items()})
