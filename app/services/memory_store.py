import json
from pathlib import Path

from app.schemas.memory import MemoryItem


# Store memories in the backend project, outside the app package.
MEMORY_FILE = Path(__file__).resolve().parents[2] / "data" / "memories.json"


def load_memories() -> list[MemoryItem]:
    """Load saved memories. Return an empty list if no store exists yet."""
    if not MEMORY_FILE.exists():
        return []

    with MEMORY_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("The memory store must contain a JSON list.")

    return [MemoryItem.model_validate(item) for item in data]


def save_memory(memory: MemoryItem) -> MemoryItem:
    """Save a memory, refusing to overwrite an existing memory ID."""
    memories = load_memories()

    if any(item.memory_id == memory.memory_id for item in memories):
        raise ValueError(
            f"Memory ID already exists: {memory.memory_id}"
        )

    memories.append(memory)

    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    with MEMORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            [item.model_dump() for item in memories],
            file,
            indent=2,
            ensure_ascii=False,
        )

    return memory


def get_memories() -> list[MemoryItem]:
    """Return all saved memories."""
    return load_memories()