# Three-minute demo script (recorded on the deployed app)

Before recording: `python scripts/demo_check.py --base-url <backend> --admin-token <token>` (must pass),
then `POST /admin/reset-demo` once more so the app starts from the seeded persona. Set the browser
window to 1280×800, dismiss the dashboard tour, sign in as `meera@example.edu`.

| Time | Screen and action | What to say |
|---|---|---|
| 0:00–0:20 | **Home.** Goal line "Land an AI/ML internship". Point at the header chip "nemotron \| nebius token factory". | "Today's AI remembers conversations. MindMate remembers context: Meera's goal, her time, and that college exams come before GATE." |
| 0:20–0:45 | **My Memory → Saved Info.** Scroll the list: skills with evidence, the decision "College exams come before GATE preparation" with tag `decision#1`. Show the edit and delete buttons. | "Skills are stored with evidence, and decisions with their reasons. Everything is editable and deletable." |
| 0:45–1:10 | **Opportunities.** Saved roles with fit badges; click **Check fit** on AI/ML Engineering Intern. | "Fit is computed by code from evidence. Every covered requirement cites the evidence, like `ev#1`." |
| 1:10–1:35 | **Skill Gaps.** 67% Moderate fit; Model evaluation is the highest-impact gap. | "Model evaluation is mandatory and has no evidence, so it is the top gap." |
| 1:35–2:00 | **Plan & Progress.** Scroll the 14-day plan: tasks with time, priority and reasons. | "A 14-day plan inside one hour a day, each task saying why it matters." |
| 2:00–2:20 | **Skill Gaps → Start Practice.** Answer: "I would only check the accuracy on the test set and move on." Submit. | "Meera practises a model-evaluation question and answers poorly." |
| 2:20–2:35 | **My Memory → Insights.** "Model evaluation" saved. | "That is her second weak answer on this topic, so MindMate records a weakness, with both answers as evidence." |
| 2:35–2:50 | **Plan & Progress.** Choose **30 min / day**, click **Update my plan**. | "She only has 30 minutes today. The plan rebuilds: model-evaluation practice moves to day 1 and is kept, and the explanation cites the weakness and her own decisions." |
| 2:50–3:00 | **Activity History.** Timestamped trace of what MindMate did. | "Everything is traced. It remembers why. It adapts to you. It stays yours." |

## Fallbacks during recording

* Nebius slow or failing: the backend uses `MINDMATE_DEMO_CACHE=fallback`; recorded answers are labelled in
  the trace. The practice, fit, gap and replan steps above do not depend on the model at all.
* Anything else: the backup screen recording of the full path (no narration) can be narrated instead.
