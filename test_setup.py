import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from .env
load_dotenv()

# Check whether the API key exists without displaying it
api_key = os.getenv("NEBIUS_API_KEY")


class MindMateTest(BaseModel):
    project_name: str
    pydantic_working: bool
    dotenv_working: bool
    api_key_configured: bool


test = MindMateTest(
    project_name="MindMate",
    pydantic_working=True,
    dotenv_working=True,
    api_key_configured=bool(api_key),
)

print(test)