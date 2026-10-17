"""Permission tiers (proposal section 8).

| Level               | Tools and data                      | Policy                                     |
|---------------------|-------------------------------------|--------------------------------------------|
| read_only           | profile, files, opportunities       | used with consent; never shared externally |
| optional_write      | tasks, reminders                    | explicit opt-in; tasks only in the MVP     |
| application_actions | application drafts                  | draft only; the user submits               |

These checks live outside the model: nothing the model outputs can trigger
an action, and no irreversible action happens without user confirmation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PermissionLevel(str, Enum):
    READ_ONLY = "read_only"
    OPTIONAL_WRITE = "optional_write"
    APPLICATION_ACTIONS = "application_actions"


# Action kinds the agent layer can request. Anything missing here is denied.
ACTION_PERMISSIONS: dict[str, PermissionLevel] = {
    "read_profile": PermissionLevel.READ_ONLY,
    "read_opportunities": PermissionLevel.READ_ONLY,
    "read_memory": PermissionLevel.READ_ONLY,
    "create_task": PermissionLevel.OPTIONAL_WRITE,
    "create_reminder": PermissionLevel.OPTIONAL_WRITE,
    "draft_application": PermissionLevel.APPLICATION_ACTIONS,
    "draft_message": PermissionLevel.APPLICATION_ACTIONS,
    # Irreversible: never performed by the system. Listed so they are denied explicitly.
    "submit_application": PermissionLevel.APPLICATION_ACTIONS,
    "send_message": PermissionLevel.APPLICATION_ACTIONS,
    "delete_all_memory": PermissionLevel.OPTIONAL_WRITE,
}

# Actions with consequences outside MindMate. The MVP never performs these;
# the user does them manually after reviewing the draft.
IRREVERSIBLE_ACTIONS = {"submit_application", "send_message", "delete_all_memory"}

# Only tasks are writable in the MVP; reminders and calendar are later scope.
MVP_WRITE_ALLOWED = {"create_task"}

DRAFT_ACTIONS = {"draft_application", "draft_message"}


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    level: PermissionLevel | None
    reason: str
    requires_confirmation: bool = False
    draft_only: bool = False

    def as_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "level": self.level.value if self.level else None,
            "reason": self.reason,
            "requires_confirmation": self.requires_confirmation,
            "draft_only": self.draft_only,
        }


def check_permission(action: str, *, user_confirmed: bool = False, allow_task_writes: bool = True) -> PermissionDecision:
    """Decide whether ``action`` may run. Deterministic; no model input."""

    level = ACTION_PERMISSIONS.get(action)
    if level is None:
        return PermissionDecision(False, None, f"Unknown action '{action}' is not permitted.")

    if action in IRREVERSIBLE_ACTIONS:
        if action == "delete_all_memory":
            if user_confirmed:
                return PermissionDecision(True, level, "User confirmed deleting all memory.", requires_confirmation=True)
            return PermissionDecision(False, level, "Deleting all memory is irreversible and needs explicit confirmation.", requires_confirmation=True)
        return PermissionDecision(
            False,
            level,
            f"'{action}' has external consequences; MindMate only drafts. The user submits or sends manually.",
            requires_confirmation=True,
            draft_only=True,
        )

    if level is PermissionLevel.READ_ONLY:
        return PermissionDecision(True, level, "Read-only access to the user's own data.")

    if level is PermissionLevel.OPTIONAL_WRITE:
        if action not in MVP_WRITE_ALLOWED:
            return PermissionDecision(False, level, f"'{action}' is not enabled in the MVP (tasks only).")
        if not allow_task_writes:
            return PermissionDecision(False, level, "The user has not opted in to task writes.")
        return PermissionDecision(True, level, "Task writes are opted in; the task is created as a draft the user can edit.")

    # application actions: drafts only
    if action in DRAFT_ACTIONS:
        return PermissionDecision(True, level, "Drafting is allowed; nothing is submitted without the user.", draft_only=True)
    return PermissionDecision(False, level, f"'{action}' is not permitted.")
