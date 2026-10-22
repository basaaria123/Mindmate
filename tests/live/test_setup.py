
import os

from dotenv import load_dotenv
from pydantic import BaseModel


def test_mindmate_setup():
    # Load environment variables from .env
    load_dotenv()

    # Check whether the API key exists without displaying it
    api_key = os.getenv("NEBIUS_API_KEY")

    class MindMateTest(BaseModel):
        project_name: str
        pydantic_working: bool
        dotenv_working: bool
        api_key_configured: bool

    result = MindMateTest(
        project_name="MindMate",
        pydantic_working=True,
        dotenv_working=True,
        api_key_configured=bool(api_key),
    )

    assert result.project_name == "MindMate"
    assert result.pydantic_working is True
    assert result.dotenv_working is True
    assert result.api_key_configured is True
