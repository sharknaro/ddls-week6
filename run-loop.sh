#!/usr/bin/env bash
set -Eeuo pipefail

# Ralph fallback runner: 120 total iterations, with 4 sentinel iterations already complete.
# This script launches one fresh Pi session per iteration and sleeps between sessions.
# It does not modify snap.py or SKILL.md.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOTAL_ITERATIONS=120
COMPLETED_ITERATIONS=4
REMAINING_ITERATIONS=$((TOTAL_ITERATIONS - COMPLETED_ITERATIONS))
PACE_SECONDS=900

cd "$ROOT_DIR"

for ((run=1; run<=REMAINING_ITERATIONS; run++)); do
  progress_snapshot="$(cat RALPH_PROGRESS.md 2>/dev/null || printf 'no findings yet')"
  gallery_snapshot="$(find survey_frames -type f -name '*_thumb.png' -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -40)"

  prompt=$(cat <<EOF
You are one fresh Ralph validation session in project: $ROOT_DIR.

This is fallback iteration $run of $REMAINING_ITERATIONS after four completed iterations. The campaign cap is exactly 120 total iterations; do not exceed it. Read RALPH.md completely and obey it. Read SKILL.txt only if SKILL.md is absent. Never modify snap.py or SKILL.md.

Use RALPH_PROGRESS.md as durable memory and determine the next approved slot from its dated entries. Use this thumbnail inventory as gallery evidence:
$gallery_snapshot

Persistent progress:
$progress_snapshot

Run exactly one short cycle, then stop this Pi session:
- Preserve the strict 8-slot schedule in RALPH.md.
- Sentinel slots are fixed and mandatory:
  1. plate A, well B11, dx=-0.5, dy=-0.5
  2. plate A, well B12, dx=-0.5, dy=-0.5
  3. plate B, well B11, dx=-0.5, dy=-0.5
  4. plate B, well B12, dx=-0.5, dy=-0.5
  Sentinel acquisition is BF then mandatory FL at the same atomic coordinates.
- Exploratory slots remain exactly the controlled slots in RALPH.md: high-FL neighborhood, low-FL/control neighborhood, one previously unseen owned coordinate, then the most informative exploratory-field revisit.
- Never leave owned wells: only B11/B12 on plates A/B.
- Call status first and read result.scale.pixel_size_um and result.scale.fov_um.
- Autofocus before the first real snap in the field.
- Use atomic /snap with dx/dy; never move then snap.
- Start FL at exposure_ms=30 and intensity=20. If the FL thumbnail is saturated or blank-white, perform exactly one conservative retry with reduced exposure and/or intensity, record both the original and changed settings, and save the retry as a unique frame. Use the retry for analysis only if it is valid; if it remains saturated or blank-white, log the FL frame and retry as unusable and continue without quantitative FL analysis.
- Save unique full-resolution frames plus thumbnails below survey_frames; never overwrite existing frames.
- Inspect the thumbnail. Do not analyze blank, failed, or saturated frames.
- Perform at most one measurement, in micrometres, from the full-resolution frame using status-derived scale; manually spot-check it.
- Validate plate, well, dx, dy, returned position/z, image quality, and scale.
- Append exactly one dated result to RALPH_PROGRESS.md and one specific testable update to OPEN_QUESTIONS.md.
- Stop immediately after this one cycle.

Stop and log the stop reason in RALPH_PROGRESS.md if repeated failed frames, repeated position mismatches, unresolved scale/FOV, repeated gateway/scope errors after normal retry/backoff, invalid coordinates, overwrite risk, safety/light-budget uncertainty, or any protected-file modification would occur.

Do not run a grid, broad survey, or extra repeats. Do not emit CAMPAIGN_DONE unless the complete campaign direction is actually answered and cross-checked.
EOF
)

  pi --print "$prompt"
  sleep "$PACE_SECONDS"
done

printf 'Fallback complete: launched %d fresh Pi sessions; total campaign cap was %d iterations.\n' "$REMAINING_ITERATIONS" "$TOTAL_ITERATIONS"
