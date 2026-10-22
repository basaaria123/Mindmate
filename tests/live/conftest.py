"""Live tests call NVIDIA Nemotron on Nebius Token Factory and spend credits.

They run only when NEBIUS_API_KEY is set (``make test-ai-live``); otherwise each one is
skipped with a reason instead of failing, so ``pytest tests`` stays usable offline.
"""

import os

import pytest
from dotenv import load_dotenv

load_dotenv()


def pytest_collection_modifyitems(config, items):
    if os.getenv("NEBIUS_API_KEY"):
        return
    skip = pytest.mark.skip(reason="NEBIUS_API_KEY is not set; live Nemotron tests skipped")
    for item in items:
        if "tests/live/" in str(item.fspath).replace("\\", "/"):
            item.add_marker(skip)
