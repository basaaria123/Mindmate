
from app.schemas.memory import MemoryItem
from app.schemas.practice import PracticeEvaluation
from app.services.memory_store import get_memories, save_memory


def create_memory_candidate(
    evaluation: PracticeEvaluation,
    source: str,
    memory_id: str,
) -> MemoryItem | None:
    """Prepare a memory candidate from a practice evaluation.

    This function validates and prepares a candidate only.
    It does not persist the memory.
    """

    if not evaluation.is_store_worthy:
        return None

    if not evaluation.weakness_candidate and not evaluation.feedback.strip():
        return None

    if not memory_id.strip():
        raise ValueError("A memory ID must be supplied by the caller.")

    if not source.strip():
        raise ValueError("A memory source must be supplied by the caller.")

    if evaluation.weakness_candidate:
        memory_type = "weakness"
        content = evaluation.weakness_candidate
        reference_tags = ["practice", "weakness"]
    else:
        memory_type = "learning_insight"
        content = evaluation.feedback
        reference_tags = ["practice", "learning_insight"]

    return MemoryItem(
        memory_id=memory_id,
        memory_type=memory_type,
        content=content,
        reference_tags=reference_tags,
        source=source,
        confidence=min(
            evaluation.correctness,
            evaluation.depth,
            evaluation.clarity,
        ),
    )

def create_and_store_memory(
    evaluation: PracticeEvaluation,
    source: str,
) -> MemoryItem | None:
    """Create a memory candidate, generate its ID, and persist it."""

    if not evaluation.is_store_worthy:
        return None

    if evaluation.weakness_candidate:
        memory_type = "weakness"
    else:
        memory_type = "learning_insight"

    memory_id = generate_memory_id(memory_type)

    memory = create_memory_candidate(
        evaluation=evaluation,
        source=source,
        memory_id=memory_id,
    )

    if memory is None:
        return None

    return save_memory(memory)


def generate_memory_id(memory_type: str) -> str:
    """Generate the next sequential ID for a memory category."""

    prefix_by_type = {
        "weakness": "weakness",
        "decision": "decision",
        "learning_insight": "learning_insight",
    }

    if memory_type not in prefix_by_type:
        raise ValueError(f"Unsupported memory type: {memory_type}")

    prefix = prefix_by_type[memory_type]
    existing_memories = get_memories()
    highest_number = 0

    for memory in existing_memories:
        if memory.memory_type != memory_type:
            continue

        expected_prefix = f"{prefix}#"

        if memory.memory_id.startswith(expected_prefix):
            suffix = memory.memory_id[len(expected_prefix):]

            if suffix.isdigit():
                highest_number = max(highest_number, int(suffix))

    return f"{prefix}#{highest_number + 1:02d}"