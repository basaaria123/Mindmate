# Demo video: shot list and voiceover (target 1:45, hard limit 3:00)

Recorded on the **live deployment**: Vercel frontend + Render backend (https://mindmate-backend-yw5d.onrender.com) with a real Token Factory key.
Labels below are the exact on-screen text in the app.

## Before you record (10 minutes)

1. Run `./scripts/smoke_test.sh https://<backend>`. It must end with `SMOKE TEST PASSED`; if it fails,
   do not record.
2. Reset the persona so the story starts clean:
   `curl -X POST https://<backend>/admin/reset-demo -H "X-Admin-Token: <MINDMATE_ADMIN_TOKEN>"`.
3. Open the Vercel site in a 1920×1080 browser window (the header chip is hidden below laptop width) and
   check that the header chip reads **`nemotron | nebius token factory`** with a green dot.
4. Warm up, so the AI Activity page already shows a Nano call: on **Opportunities**, paste any posting,
   click **Analyze with AI** and check that the result is not labelled "Offline analysis". Pasting a
   posting is the extraction step that runs on Nemotron Nano.
5. Open these tabs in order: MindMate **Home**, Nebius **Token Factory** console (models page, key
   hidden), MindMate **Tasks & Practice**, **AI Activity**, **Plan & Progress**, Token Factory
   **usage/dashboard** page, `app/services/llm_client.py` (lines 9–19) and `app/permissions.py`
   (lines 1–11) in your editor or on GitHub.
6. Have the weak answer ready to paste: *"I would just check accuracy on the test set and pick the model
   with the higher number."*

## Shot list and voiceover

| Time | Screen | Action | Voiceover | On-screen caption |
|---|---|---|---|---|
| 0:00–0:10 | MindMate **Home** (Meera's goal and next tasks) | Slow scroll; cursor on the header chip | "Students preparing for internships re-explain their goals to every chatbot, and nothing they practise changes their plan. MindMate remembers why, adapts to you, and stays yours." | MindMate: it remembers why. It adapts to you. It stays yours. |
| 0:10–0:25 | Nebius **Token Factory** console | Show the two Nemotron models the app uses; API key hidden or blurred | "MindMate runs ten agents on NVIDIA Nemotron through Nebius Token Factory: Nemotron Nano for fast extraction, Nemotron Ultra for reasoning over your memory." | Nebius Token Factory · Nemotron 3 Ultra + Nano |
| 0:25–0:55 | **Tasks & Practice** → practice dialog → **AI Activity** | Open the practice task *Mock interview: model evaluation questions*, paste the weak answer, click **Submit answer**, wait for the score. Click **Save to My Memory**. Open **AI Activity**. **Pause 2 s** on the model-call lines. | "Meera answers a model-evaluation question badly. Nemotron Ultra grades it, and because this is her second weak answer on the topic, MindMate records a weakness. The AI Activity page shows every model call with the model and how long it took." | Nemotron Nano: extraction · Nemotron Ultra: reasoning (point at the matching lines) |
| 0:55–1:20 | **Plan & Progress** | Set **Time today** from *60 min / day* to *30 min / day*, click **Update my plan**. Show **What changed and why** and the **Before** / **After** lists. **Pause 2 s** on the explanation. | "Her week gets busy, so she drops to thirty minutes a day. The scheduler refits the plan in code. Model-evaluation practice moves to day one, and Nemotron explains why, citing the weakness and her own decisions, like exams before GATE." | Replanned: 60 → 30 min/day · cites weakness#1 and decision#… (use the IDs on screen) |
| 1:20–1:35 | Token Factory **usage/dashboard** | Refresh; show the new requests from the last minute. **Pause 2 s.** | "And here are those requests arriving on Nebius Token Factory." | Live requests on Nebius Token Factory |
| 1:35–1:50 | `llm_client.py` lines 9–19 (5 s), then `permissions.py` lines 1–11, then MindMate **Home** | Hold on the model IDs and base URL; then the permission table | "One OpenAI-compatible endpoint, two Nemotron models. Code makes the decisions, Nemotron explains them, and MindMate only drafts: it never submits anything for you. Your memory, your plan, your call." | Models propose. Code decides. You stay in control. |

**Running time:** 1:50 as written. To reach 1:45, trim the Home scroll at the start by 5 seconds.

### Notes for each shot

- **Practice (0:25).** Whether a weakness is recorded depends on Nemotron's score: it needs a score
  below 60, and the seeded persona already has one earlier answer at 42. If the score comes out 60 or
  higher, submit a second weak answer off-camera and re-record the shot. [CONFIRM on the live deployment.]
- **AI Activity (0:45).** Lines read like
  `practice agent: nvidia/Nemotron-3-Ultra-550b-a55b answered in …s.` and
  `opportunity agent: nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B answered in …s.` Show the real seconds; do
  not edit them.
- **Replan (0:55).** The explanation text is written by the Replanning agent (Nemotron Ultra) when live.
  If it reads like a code-written list ("Moved '…' from day 3 to day 1 because…"), the agent fell back:
  check AI Activity for `model_fallback` and re-record.

## Recording rules

- **Live mode only.** The header chip must show `nemotron | nebius token factory`. No offline mocks, no
  "Offline analysis" labels, no recorded answers (`MINDMATE_DEMO_CACHE` must be `off`; `/health` shows
  it). If any of these appear in a take, discard the take.
- **Hide every key.** Blur or crop the Token Factory API key, `.env` files and any terminal that prints
  environment variables. Never show `.env.production`.
- **Pause two seconds on proof screens:** AI Activity model lines, the replan explanation, and the Token
  Factory requests.
- 1080p, browser zoom 100%, notifications off, cursor highlighting on. Record the voiceover separately if
  that is easier, and add captions.
- Keep it **3:00 or less** (aim for 1:45).
- Upload to YouTube as **Public** (not Unlisted or Private). Put the repo and live demo URLs in the
  description. Test the link in a signed-out browser window.

## YouTube

**Title:** MindMate: a personal AI agent that remembers why, built with NVIDIA Nemotron on Nebius Token Factory

**Description:**

```
MindMate is a private personal AI agent for students preparing for internships. It keeps an editable
memory of your goals, decisions, skills and weaknesses, grades your interview practice, and rebuilds your
study plan when your time or results change, citing the memory behind every change.

Built for the NVIDIA x Nebius Global AI Hackathon 2026 (Personal AI track).

How it uses NVIDIA and Nebius:
- Ten agents on NVIDIA Nemotron through Nebius Token Factory (one OpenAI-compatible endpoint)
- Nemotron 3 Nano for fast extraction (profile, postings, suggestions)
- Nemotron 3 Ultra for reasoning over memory (fit, gaps, planning, practice grading, replan explanations)
- Deterministic code makes the decisions; every model call is logged with the model and latency
- Backend on Render (Docker + PostgreSQL); models on Nebius Token Factory

In this video:
0:00 The problem
0:10 Nemotron models on Nebius Token Factory
0:25 A weak practice answer graded by Nemotron Ultra; AI Activity
0:55 Dropping to 30 minutes a day: the replan and its explanation
1:20 The requests on Token Factory
1:35 Model configuration and permission tiers

Live demo: https://mindmate-lyart.vercel.app
Code (MIT): https://github.com/basaaria123/Mindmate
```
