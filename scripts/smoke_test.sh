#!/usr/bin/env bash
# Live smoke test for a deployed MindMate backend. It must prove that answers come from
# NVIDIA Nemotron on Nebius Token Factory: any offline, mock or recorded answer is a failure.
#
#   ./scripts/smoke_test.sh https://api.example.com
#
# Checks, in order (stops at the first failure, exit code 1):
#   1. GET  /health         healthy, Nebius key configured, live mode, recorded answers off
#   2. GET  /memory         the memory layer answers and holds items
#   3. POST /opportunity    the Opportunity agent answers from Nemotron (X-MindMate-Source: nemotron)
#   4. POST /plans/replan   30-minute replan fits the budget and its explanation comes from the
#                           Replanning agent (explained_by: replan_agent); the 60-minute budget is
#                           then restored with a second replan
# Finally it prints the model calls from GET /agent/events (agent, model, seconds) as evidence.
# Needs: bash, curl, python3. Writes two plan versions (the replans); nothing else is changed.
set -uo pipefail

BASE="${1:-}"
if [ -z "$BASE" ]; then
  echo "usage: $0 <backend-url>   e.g. $0 https://api.example.com" >&2
  exit 2
fi
BASE="${BASE%/}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass() { printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() {
  printf '\n  \033[1;31mFAIL\033[0m %s\n' "$1" >&2
  [ -n "${2:-}" ] && printf '       %s\n' "$2" >&2
  printf '\nSMOKE TEST FAILED against %s\n' "$BASE" >&2
  exit 1
}

# request METHOD PATH [JSON]  -> body in $TMP/body, headers in $TMP/headers, status in $STATUS
request() {
  local method="$1" path="$2" data="${3:-}"
  local args=(-sS -m 120 -X "$method" -D "$TMP/headers" -o "$TMP/body" -w '%{http_code}' -H 'Accept: application/json')
  [ -n "$data" ] && args+=(-H 'Content-Type: application/json' --data "$data")
  STATUS="$(curl "${args[@]}" "$BASE$path" 2>"$TMP/curl_err")" || STATUS="000"
}

header() { grep -i "^$1:" "$TMP/headers" | head -1 | cut -d: -f2- | tr -d ' \r'; }

# json EXPR -> evaluates a Python expression with the response body bound to `d`
json() { python3 -c "import json,sys; d=json.load(open('$TMP/body')); print($1)" 2>/dev/null; }

echo "MindMate live smoke test: $BASE"

# 1. health ---------------------------------------------------------------------------
request GET /health
[ "$STATUS" = "200" ] || fail "GET /health returned $STATUS" "$(cat "$TMP/curl_err" "$TMP/body" 2>/dev/null | head -c 300)"
[ "$(json 'd.get("status")')" = "healthy" ] || fail "/health status is not healthy" "$(head -c 300 "$TMP/body")"
[ "$(json 'd.get("nebius_key_configured")')" = "True" ] || fail "/health: no NEBIUS_API_KEY configured on the backend (offline mode)"
[ "$(json 'd.get("llm_available")')" = "True" ] || fail "/health: live model calls are off (MINDMATE_LLM_MODE=$(json 'd.get("llm_mode")'))"
[ "$(json 'd.get("demo_cache")')" = "off" ] || fail "/health: recorded-answer demo mode is '$(json 'd.get("demo_cache")')'; set MINDMATE_DEMO_CACHE=off"
pass "GET /health: key configured, live mode, recorded answers off ($(json 'd["models"]["reasoning"]'), $(json 'd["models"]["fast"]'))"

# 2. memory read ------------------------------------------------------------------------
request GET /memory
[ "$STATUS" = "200" ] || fail "GET /memory returned $STATUS" "$(head -c 300 "$TMP/body")"
ITEMS="$(json 'len(d.get("items", []))')"
[ "${ITEMS:-0}" -gt 0 ] || fail "GET /memory returned no items (is the demo persona seeded?)"
pass "GET /memory: $ITEMS memory items"

# 3. AI endpoint: must be a real Nemotron answer -------------------------------------------
POSTING='{"opportunity_text":"AI/ML Engineering Intern at Nimbus Analytics.\nPython and SQL are required. Experience with model evaluation is a plus."}'
request POST /opportunity "$POSTING"
[ "$STATUS" = "200" ] || fail "POST /opportunity returned $STATUS" "$(head -c 300 "$TMP/body")"
SOURCE="$(header x-mindmate-source)"
CACHE="$(header x-mindmate-cache)"
[ -z "$CACHE" ] || fail "POST /opportunity was served from recorded answers (X-MindMate-Cache: $CACHE)"
[ "$SOURCE" = "nemotron" ] || fail "POST /opportunity was answered by '${SOURCE:-unknown}', not Nemotron" "Check NEBIUS_API_KEY, the model IDs and GET /agent/events for model_fallback."
SKILLS="$(json '", ".join(r["skill_name"] for r in d.get("required_skills", []))')"
[ -n "$SKILLS" ] || fail "POST /opportunity: Nemotron returned no required skills"
pass "POST /opportunity: answered by Nemotron (required skills: $SKILLS)"

# 4. replan --------------------------------------------------------------------------------
request POST /plans/replan '{"available_minutes":30,"reason":"smoke test: 30-minute day"}'
[ "$STATUS" = "200" ] || fail "POST /plans/replan returned $STATUS" "$(head -c 300 "$TMP/body")"
OVER="$(json 'max([0]+[sum(t["minutes"] for t in d["plan"]["tasks"] if t["day_number"]==day and t["status"]!="done") for day in {t["day_number"] for t in d["plan"]["tasks"]}])')"
[ -n "$OVER" ] && [ "$OVER" -le 30 ] || fail "replan exceeded the 30-minute budget (busiest day: ${OVER:-unknown} min)"
BY="$(json 'd.get("explained_by")')"
[ "$BY" = "replan_agent" ] || fail "replan explanation was written by '${BY:-unknown}', not the Nemotron Replanning agent"
pass "POST /plans/replan: every day within 30 min; explanation by Nemotron: \"$(json 'd["rationale"][:110]')...\""
request POST /plans/replan '{"available_minutes":60,"reason":"smoke test: restore 60-minute day"}'
[ "$STATUS" = "200" ] || fail "restoring the 60-minute budget returned $STATUS"
pass "60-minute budget restored"

# Evidence: the model calls just made -------------------------------------------------------
request GET "/agent/events?limit=50"
echo
echo "Recent Nemotron calls (GET /agent/events):"
json '"\n".join("  " + e["timestamp"][:19] + "  " + e["summary"] for e in d.get("events", []) if e.get("action") == "model_call")' | head -10
FALLBACKS="$(json 'sum(1 for e in d.get("events", []) if e.get("action") == "model_fallback")')"
[ "${FALLBACKS:-0}" = "0" ] || echo "  note: $FALLBACKS model_fallback event(s) in the last 50 events; inspect GET /agent/events"
echo
echo "SMOKE TEST PASSED against $BASE"
