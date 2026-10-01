#!/usr/bin/env bash
set -Eeuo pipefail

MODE="${1:-recon}"
DURATION_SECONDS="${2:-7200}"
# Shared microscope: one command at a time, with a generous pause between cycles.
PACE_SECONDS="${PACE_SECONDS:-120}"
SUMMARY_FILE="${SUMMARY_FILE:-INVESTIGATION_SUMMARY.md}"
LOCK_DIR=".run-loop.lock"

PI_EXECUTABLE="/c/Users/bakar/AppData/Roaming/npm/pi"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "Another run-loop.sh process appears to be active; refusing concurrent microscope use." >&2
  exit 1
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT

start_epoch="$(date +%s)"
end_epoch=$((start_epoch + DURATION_SECONDS))
cycle=0
while (( $(date +%s) < end_epoch )); do
  cycle=$((cycle + 1))
  progress="$(cat RALPH_PROGRESS.md 2>/dev/null || printf 'no findings yet')"
  prompt="Read SKILL.md and RALPH.md completely. Read OPEN_QUESTIONS.md, INVESTIGATION_SUMMARY.md if present, the current RALPH_PROGRESS.md context below, and inspect the existing frame inventory before acting. This is cycle ${cycle} of a ${MODE} investigation. Perform exactly one conservative adaptive scientific cycle because roughly 30 students share the microscopes: never run concurrent commands, never use /move before imaging, respect rate limits and retry_after_s, wait about 20 seconds after instrument_busy, and do not take unnecessary images. Use only owned wells and only ./snap.py. Survey mode objective: for this completion recon, prioritize A/B12, B/B11, and B/B12 until each has at least 4 comparable usable BF fields. Do not sample A/B11 unless required to restore balanced coverage. Use existing progress and summary files to avoid reusing already sampled coordinates where possible. In each recon cycle acquire exactly one autofocus-assisted atomic BF survey snap at one valid coordinate. Do not acquire fluorescence, zoom, time-lapse, or targeted follow-up images. High-count mode objective: use only wells ranked highest in INVESTIGATION_SUMMARY.md, verify the ranking with comparable fresh fields, and investigate whether the apparent difference persists. Start with a deliberate field-selection decision based on coverage and the summary; autofocus the selected well if needed, then take one atomic BF survey snap with explicit plate, well, and dx/dy. Inspect thumbnail and full-resolution image. If blank/unusable, do not take a retry in recon mode; record the failed field and continue later. In high-count mode only, a single minimal follow-up may be justified, but never let follow-up crowd out fair well coverage. Before fluorescence, allow at least 30 seconds, start exposure_ms=30 and intensity=20, and avoid it unless it answers a live/dead question. Validate plate, well, coordinates, returned position_mm, focus, channel, and image quality. Read status-derived scale/FOV. Record at most one full-resolution measurement in micrometres or measurement: none. Assign cautious candidate-level labels and rough counts for every requested catalogue label, explicitly distinguishing biological candidates from debris and marking not observed when sampling is inadequate. Do not count the same object twice across channels or revisits. Append exactly one dated entry to RALPH_PROGRESS.md and exactly one ranked hypothesis/update to OPEN_QUESTIONS.md, with field ID, frame paths, counts, limitations, and next test. Also update INVESTIGATION_SUMMARY.md in a parseable table: for each plate/well, report usable field count, total microorganism-like candidate count (sum of requested biological labels only, excluding debris and uncertain objects unless separately shown), mean, median, standard deviation when n>=2, fields with failures, and the current ranking. Do not claim wells are better unless they have comparable sampling effort; state the denominator and uncertainty. Preserve records and stop after this cycle. Do not emit CAMPAIGN_DONE. Prior progress context: ${progress}"
  "$PI_EXECUTABLE" -p "$prompt"
  if (( $(date +%s) + PACE_SECONDS < end_epoch )); then
    sleep "$PACE_SECONDS"
  else
    break
  fi
done

cat > "${SUMMARY_FILE}.run-meta" <<EOF
completed_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
mode=${MODE}
duration_seconds=${DURATION_SECONDS}
cycles_started=${cycle}
EOF
printf 'Completed %s investigation run (%s seconds, %s cycles started). Summary: %s\n' "$MODE" "$DURATION_SECONDS" "$cycle" "$SUMMARY_FILE"
