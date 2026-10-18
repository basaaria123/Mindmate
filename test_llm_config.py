"""Offline tests for llm_client environment-variable overrides."""

import importlib

import app.services.llm_client as llm_mod


def test_default_models():
    """Without env overrides, defaults match the documented NVIDIA Nemotron models."""
    assert "Nemotron" in llm_mod.REASONING_MODEL
    assert "Nemotron" in llm_mod.FAST_MODEL
    assert llm_mod.REASONING_MODEL != llm_mod.FAST_MODEL


def test_default_base_url():
    assert "tokenfactory.nebius.com" in llm_mod.NEBIUS_BASE_URL


def test_env_override_reasoning_model(monkeypatch):
    monkeypatch.setenv("MINDMATE_REASONING_MODEL", "test/custom-reasoning")
    importlib.reload(llm_mod)
    try:
        assert llm_mod.REASONING_MODEL == "test/custom-reasoning"
    finally:
        monkeypatch.delenv("MINDMATE_REASONING_MODEL", raising=False)
        importlib.reload(llm_mod)


def test_env_override_fast_model(monkeypatch):
    monkeypatch.setenv("MINDMATE_FAST_MODEL", "test/custom-fast")
    importlib.reload(llm_mod)
    try:
        assert llm_mod.FAST_MODEL == "test/custom-fast"
    finally:
        monkeypatch.delenv("MINDMATE_FAST_MODEL", raising=False)
        importlib.reload(llm_mod)


def test_env_override_base_url(monkeypatch):
    monkeypatch.setenv("NEBIUS_BASE_URL", "https://custom.example.com/v1")
    importlib.reload(llm_mod)
    try:
        assert llm_mod.NEBIUS_BASE_URL == "https://custom.example.com/v1"
    finally:
        monkeypatch.delenv("NEBIUS_BASE_URL", raising=False)
        importlib.reload(llm_mod)


def test_get_model_returns_correct_tier():
    assert llm_mod.get_model("reasoning") == llm_mod.REASONING_MODEL
    assert llm_mod.get_model("fast") == llm_mod.FAST_MODEL
    assert llm_mod.get_model() == llm_mod.FAST_MODEL
