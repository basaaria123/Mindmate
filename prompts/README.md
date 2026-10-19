# Prompts

Every agent prompt is a versioned file here, so prompt changes are reviewed like code.

| File | Agent | Model tier |
|---|---|---|
| `profile.md`, `profile.system.md` | Profile: message to `UserProfile` | fast |
| `opportunity.md`, `opportunity.system.md` | Opportunity: posting text to `OpportunitySpec` | fast |
| `fit.md`, `fit.system.md` | Fit: profile vs opportunity | reasoning |
| `gap.md`, `gap.system.md` | Skill gap ranking | reasoning |
| `planner.md`, `planner.system.md` | 14-day plan within the daily budget | reasoning |
| `practice.md`, `practice.system.md` | Practice answer evaluation | reasoning |
| `practice_questions.md`, `practice_questions.system.md` | Mock-interview question generation | reasoning |
| `replan.md`, `replan.system.md` | Plain-language explanation of a plan change | reasoning |
| `suggestions.md`, `suggestions.system.md` | Twelve personalised suggestions | fast |

Rules (proposal, prompt design):

* Placeholders use `${name}` (`string.Template`), so JSON braces in prompts stay literal.
  `render_prompt` raises if a placeholder has no value; `test_prompts.py` checks every file.
* Every prompt asks for JSON only, matching a Pydantic schema in `app/schemas/`, with reference IDs
  for any claim about the user. Agents retry once with the validation error, then reject.
* Prompts receive only the memory retrieved for that task; deleted items are never included.
* Moving the prompts out of the agents did not change a single character the model receives:
  the agents' first-attempt messages were captured before and after and compared byte for byte.
