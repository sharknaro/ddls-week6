#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PI_EXECUTABLE="/c/Users/bakar/AppData/Roaming/npm/pi"
PACE_SECONDS=600
CAMPAIGN_DEADLINE="${CAMPAIGN_DEADLINE:-2026-10-02T11:00:00Z}"
STATE_PATH="$ROOT_DIR/STATE.json"
VALIDATION_ITERATIONS=2

cd "$ROOT_DIR"

read_state() {
  uv run python - "$STATE_PATH" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
for key in ("campaign_iteration", "cycle", "next_slot"):
    if key not in data:
        raise SystemExit(f"STATE.json missing required key: {key}")
print(json.dumps(data, sort_keys=True, separators=(",", ":")))
PY
}

state_at_start="$(read_state)"
starting_iteration="$(printf '%s' "$state_at_start" | uv run python -c 'import json,sys; print(json.load(sys.stdin)["campaign_iteration"])')"
successful_iterations=0

while true; do
  if (( successful_iterations >= VALIDATION_ITERATIONS )); then
    printf '%s\n' 'Two-iteration validation complete.'
    exit 0
  fi

  state_before="$(read_state)"
  iteration="$(printf '%s' "$state_before" | uv run python -c 'import json,sys; print(json.load(sys.stdin)["campaign_iteration"])')"
  expected_iteration=$((starting_iteration + successful_iterations))
  if (( iteration != expected_iteration )); then
    printf 'Unexpected starting state for validation: expected %s, found %s\n' "$expected_iteration" "$iteration" >&2
    exit 1
  fi

  now_epoch="$(date -u +%s)"
  deadline_epoch="$(date -u -d "$CAMPAIGN_DEADLINE" +%s)"
  if (( now_epoch >= deadline_epoch )); then
    break
  fi

  printf '[%s] Pi launch iteration %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$iteration"
  set +e
  timeout --signal=TERM --kill-after=30s 1800s "$PI_EXECUTABLE" --print 'Read RALPH.md completely. Read STATE.json, RALPH_PROGRESS.md and OPEN_QUESTIONS.md. Perform exactly one approved scientific iteration using snap.py. Append exactly one progress entry and exactly one hypothesis/update. Advance STATE.json only after a successful acquisition/logging cycle. Then stop this Pi session.'
  pi_exit=$?
  set -e
  printf '[%s] Pi exit iteration %s status %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$iteration" "$pi_exit"

  if (( pi_exit != 0 )); then
    exit "$pi_exit"
  fi

  state_after="$(read_state)"
  iteration_after="$(printf '%s' "$state_after" | uv run python -c 'import json,sys; print(json.load(sys.stdin)["campaign_iteration"])')"
  if (( iteration_after != iteration + 1 )); then
    printf 'STATE.json did not advance exactly one iteration (before=%s after=%s)\n' "$iteration" "$iteration_after" >&2
    exit 1
  fi
  successful_iterations=$((successful_iterations + 1))

  if (( successful_iterations >= VALIDATION_ITERATIONS )); then
    printf '%s\n' 'Two-iteration validation complete.'
    exit 0
  fi

  now_epoch="$(date -u +%s)"
  remaining=$((deadline_epoch - now_epoch))
  if (( remaining <= 0 )); then
    break
  fi
  sleep_seconds="$(( remaining < PACE_SECONDS ? remaining : PACE_SECONDS ))"
  printf '[%s] sleep start %s seconds\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$sleep_seconds"
  sleep "$sleep_seconds"
  printf '[%s] sleep end\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
done
