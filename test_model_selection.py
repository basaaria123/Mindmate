from app.services.llm_client import create_llm_client, get_model


def test_model_selection():
    fast_model = get_model("fast")
    reasoning_model = get_model("reasoning")

    assert fast_model
    assert reasoning_model
    assert isinstance(fast_model, str)
    assert isinstance(reasoning_model, str)


def test_create_llm_client():
    client = create_llm_client()

    assert client is not None
