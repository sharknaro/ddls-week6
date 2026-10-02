#!/usr/bin/env bash
set -Eeuo pipefail

MODE="${1:-recon}"
# Discovery is intentionally unbounded; it ends only on a safety stop or Ctrl+C/SIGTERM.
PACE_SECONDS="${PACE_SECONDS:-600}"
SUMMARY_FILE="${SUMMARY_FILE:-INVESTIGATION_SUMMARY.md}"
STATE_FILE="${STATE_FILE:-STATE.json}"
LOCK_DIR=".run-loop.lock"
DEADLINE_UTC="${DEADLINE_UTC:-2026-10-02T11:00:00Z}"
PI_TIMEOUT_SECONDS="${PI_TIMEOUT_SECONDS:-1800}"
MAX_TRANSIENT_FAILURES="${MAX_TRANSIENT_FAILURES:-5}"

PI_EXECUTABLE="/c/Users/bakar/AppData/Roaming/npm/pi"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "Another run-loop.sh process appears to be active; refusing concurrent microscope use." >&2
  exit 1
fi
initialize_state() {
  if [[ -f "$STATE_FILE" ]]; then
    return 0
  fi
  local tmp
  tmp="${STATE_FILE}.tmp.$$"
  cat > "$tmp" <<EOF
{
  "schema_version": 1,
  "phase": "discovery",
  "recon_status": "complete",
  "recon_history_preserved": true,
  "cycle": 0,
  "successful_discovery_cycles": 0,
  "failed_discovery_attempts": 0,
  "last_completed_observation": null,
  "last_updated_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "source_files": ["INVESTIGATION_SUMMARY.md", "RALPH_PROGRESS.md", "OPEN_QUESTIONS.md"]
}
EOF
  mv -f "$tmp" "$STATE_FILE"
}

atomic_state_checkpoint() {
  local tmp
  tmp="${STATE_FILE}.tmp.$$"
  python - "$STATE_FILE" "$tmp" "$cycle" <<'PY'
import json, os, sys
state_path, tmp_path, cycle = sys.argv[1], sys.argv[2], int(sys.argv[3])
try:
    with open(state_path, encoding="utf-8") as fh:
        state = json.load(fh)
except (FileNotFoundError, json.JSONDecodeError):
    state = {"schema_version": 1, "phase": "discovery", "recon_status": "complete", "recon_history_preserved": True}
state["phase"] = "discovery"
state["recon_status"] = "complete"
state["recon_history_preserved"] = True
state["cycle"] = cycle
state["successful_discovery_cycles"] = state.get("successful_discovery_cycles", 0) + 1
state["last_updated_utc"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat().replace("+00:00", "Z")
with open(tmp_path, "w", encoding="utf-8") as fh:
    json.dump(state, fh, indent=2)
    fh.write("\n")
os.replace(tmp_path, state_path)
PY
}

cleanup() {
  local status=$?
  trap - EXIT INT TERM
  printf '\nStopping safely (status=%s); preserving files/state and removing %s.\n' "$status" "$LOCK_DIR" >&2
  rmdir "$LOCK_DIR" 2>/dev/null || true
  exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

if [[ "$MODE" == "recon" ]]; then
  echo "Recon mode is disabled: recon is finished. Use: PACE_SECONDS=600 bash run-loop.sh discovery" >&2
  exit 2
fi
if [[ "$MODE" != "discovery" ]]; then
  echo "Usage: PACE_SECONDS=600 bash run-loop.sh discovery" >&2
  exit 2
fi

initialize_state
cycle="$(python - "$STATE_FILE" <<'PY'
import json, sys
try:
    with open(sys.argv[1], encoding="utf-8") as fh:
        print(json.load(fh).get("cycle", 0))
except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError, ValueError):
    print(0)
PY
)"
transient_failures=0
while :; do
  now_epoch="$(date +%s)"
  deadline_epoch="$(date -d "$DEADLINE_UTC" +%s)"
  if (( now_epoch >= deadline_epoch )); then
    echo "Microscope access deadline reached ($DEADLINE_UTC); stopping before acquisition."
    break
  fi
  cycle=$((cycle + 1))
  progress="$(cat RALPH_PROGRESS.md 2>/dev/null || printf 'no findings yet')"
  prompt="DISCOVERY MODE, cycle ${cycle}. Read SKILL.md and RALPH.md completely, then read STATE/progress/questions/summary and inspect the existing frame inventory before acting. Recon is finished: do not acquire recon fields. Investigate whether the visible late-season phototrophic community across separately seeded plates A and B is cyanobacteria-like dominated or mixed, and how it changes across fields and over time. Perform exactly ONE justified observation, then stop. Use a mix of fixed sentinel revisits for temporal comparison, informative candidate-field revisits, and new exploratory fields only when needed to test an active hypothesis; do not simply increase n. BF morphology is primary evidence. Choose one field based on the active hypothesis and prior records. Autofocus once per selected well/station as needed, then acquire BF first. If—and only if—same-field FL is scientifically useful, acquire FL at identical atomic dx/dy without autofocus between channels; start FL at exposure_ms=30, intensity=20, and treat it only as chlorophyll-associated signal. Never claim taxonomy, viability, photosynthetic activity, or live/dead from FL. Keep labels conservative and candidate-level. Plates A and B are separate samples, not technical replicates. Use only owned wells and ./snap.py; never use /move. Validate plate, well, exact atomic dx/dy, returned position_mm, focus, channel, scale/FOV, and image quality. Failed acquisitions do not advance the scientific count. Respect 429/503 retry_after_s and instrument_busy delays; use no parallel microscope commands. Compare this observation with prior observations, record exactly one concise testable hypothesis, then update STATE/progress/questions/summary before sleeping. Preserve restartability in STATE.json. Stop immediately without further acquisition on microscope access deadline ${DEADLINE_UTC}, unsafe/exhausted FL light budget, or unrecoverable API/safety failure. Do not emit CAMPAIGN_DONE. Prior progress context: ${progress}"
  if timeout --foreground "${PI_TIMEOUT_SECONDS}s" "$PI_EXECUTABLE" -p "$prompt"; then
    atomic_state_checkpoint
    transient_failures=0
  else
    rc=$?
    transient_failures=$((transient_failures + 1))
    printf 'Pi cycle failed (rc=%s; transient failure %s/%s).\n' "$rc" "$transient_failures" "$MAX_TRANSIENT_FAILURES" >&2
    if (( transient_failures >= MAX_TRANSIENT_FAILURES )); then
      echo "Unrecoverable/repeated Pi failure; stopping safely." >&2
      exit 1
    fi
  fi
  now_epoch="$(date +%s)"
  deadline_epoch="$(date -d "$DEADLINE_UTC" +%s)"
  if (( now_epoch >= deadline_epoch )); then
    echo "Microscope access deadline reached; stopping before sleep."
    break
  fi
  sleep "$PACE_SECONDS"
done

cat > "${SUMMARY_FILE}.run-meta" <<EOF
completed_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
mode=${MODE}
pace_seconds=${PACE_SECONDS}
cycles_started=${cycle}
stop_condition=manual Ctrl+C/SIGTERM or deadline/light-budget/unrecoverable-safety stop
EOF
printf 'Stopped %s discovery loop after %s cycles. Summary: %s\n' "$MODE" "$cycle" "$SUMMARY_FILE"
