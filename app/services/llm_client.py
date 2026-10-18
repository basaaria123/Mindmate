import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")
NEBIUS_BASE_URL = os.getenv(
    "NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1"
)

# Central model configuration for MindMate.
# Override via environment variables for testing or provider changes.
REASONING_MODEL = os.getenv(
    "MINDMATE_REASONING_MODEL", "nvidia/Nemotron-3-Ultra-550b-a55b"
)
FAST_MODEL = os.getenv(
    "MINDMATE_FAST_MODEL", "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"
)


def create_llm_client() -> OpenAI:
    """Create the central Nebius AI client for MindMate."""

    if not NEBIUS_API_KEY:
        raise RuntimeError(
            "NEBIUS_API_KEY is missing. Check your .env file."
        )

    return OpenAI(
        api_key=NEBIUS_API_KEY,
        base_url=NEBIUS_BASE_URL,
    )


def get_model(task_type: str = "fast") -> str:
    """Choose a model based on the task."""

    if task_type == "reasoning":
        return REASONING_MODEL

    return FAST_MODEL