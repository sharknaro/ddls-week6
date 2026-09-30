---
max_iterations: 120
timeout: 900
completion_promise: "CAMPAIGN_DONE"

commands:
  - name: progress
    run: cat RALPH_PROGRESS.md 2>/dev/null || echo "no findings yet"
    timeout: 15
  - name: gallery
    run: find survey_frames -type f -name '*_thumb.png' -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -40
    timeout: 15
  - name: pace
    run: sleep 900
    timeout: 930

guardrails:
  block_commands:
    - 'rm\s+-rf'
  protected_files:
    - 'SKILL.md'
    - 'snap.py'
---

You are running a conservative overnight microscopy campaign on the user's live pond-water wells only. Use `./snap.py` for imaging. Read `SKILL.txt` if `SKILL.md` is absent, but never modify either operations document. Never access wells outside the user's allocation.

DIRECTION: Characterize the late-season, algae-like microcommunity in the two 200-µL pond subsamples using brightfield morphology, with chlorophyll fluorescence as a secondary validation of apparent phototrophs.

HYPOTHESIS: Plates A and B contain reproducible desmid-like, diatom-like, and possibly other algae-like morphotypes; at least some will be chlorophyll-positive if the fluorescence channel functions and cells retain detectable pigment.

VALIDATION OUTCOME: A and B show broadly similar morphotype presence and relative patterns across several paired fields. Fluorescence confirms some candidates, or, if a positive control works, remains consistently undetected. “Chlorophyll not detected” does not establish that forms are dead or non-photosynthetic.

FIXED SENTINEL SCHEDULE — STRICT 8-ITERATION CYCLE:
- Iteration slot 1: Plate A, well B11, dx=-0.5, dy=-0.5.
- Iteration slot 2: Plate A, well B12, dx=-0.5, dy=-0.5.
- Iteration slot 3: Plate B, well B11, dx=-0.5, dy=-0.5.
- Iteration slot 4: Plate B, well B12, dx=-0.5, dy=-0.5.
- Iteration slots 5–8: controlled exploratory slots defined below.
- Sentinel visits must never be replaced by strongest/weakest-field choices.
- At every sentinel visit acquire exactly BF → FL at the same atomic coordinates. FL is mandatory, not conditional.
- Sentinel FL starts at exposure_ms=30, intensity=20. If saturated, reduce exposure and/or intensity, record the deviation, and retain the visit.
- With approximately 17 minutes per complete iteration including 15-minute pacing and imaging overhead, each sentinel repeats every 8 iterations, approximately every 136 minutes (2 hours 16 minutes).

CONTROLLED EXPLORATORY SLOTS:
- Slot 5: one field in or adjacent to the previously identified high-FL neighborhood, within an owned well and valid round-well coordinates; BF first, conditional FL.
- Slot 6: one field in or adjacent to the previously identified low-FL/control neighborhood; BF first, conditional FL.
- Slot 7: one previously unseen valid coordinate in an owned well; BF first, conditional FL.
- Slot 8: revisit the most informative exploratory field from the immediately previous cycle; BF first, conditional FL.
- Exploratory slots must not alter the sentinel coordinates or cadence, must not use a large grid, and must not wander freely.
- If a neighborhood or informative exploratory field is not documented, use a conservative documented coordinate and record why; never invent an unvalidated well.

VALIDATED IMAGING RULES:
- Call `GET /v1/status?plate=...` first for each plate/session. Read nested `result.scale.pixel_size_um` and `result.scale.fov_um`; never hard-code scale.
- Autofocus before the first real snap in each field.
- Use atomic `/snap` with exact `dx`/`dy`; never use `/move` or move-then-snap.
- Start fluorescence at `exposure_ms=30`, `intensity=20`. A blank-white or saturated FL frame means overexposure: reduce settings, never increase them.
- Save every frame at full resolution and save a thumbnail beside it. Use thumbnails only for visual inspection.
- Perform all size, area, and speed measurements on full-resolution images using the status-derived scale. If a thumbnail is ever measured, use its correctly adjusted scale and explicitly record that conversion.
- Perform one manual spot-check of each reported size measurement before relying on it.
- Validate returned plate, well, atomic dx/dy, position, z, and image quality before analysis.
- Never overwrite existing frames. Use unique UTC timestamps and preserve metadata.
- Log every sentinel and exploratory result, including failures and deviations, to `RALPH_PROGRESS.md`.
- Append specific testable ideas to `OPEN_QUESTIONS.md` without replacing prior entries.

ITERATION PROCEDURE — ONE SHORT CYCLE:
1. Read `RALPH_PROGRESS.md` and the thumbnail/image inventory.
2. Determine the current 8-cycle slot and select the fixed sentinel or controlled exploratory field.
3. Call status first and record pixel size and FOV.
4. Autofocus the selected field.
5. Acquire the required BF frame using atomic snap coordinates; acquire mandatory sentinel FL or conditional exploratory FL.
6. Inspect thumbnails; reject blank, failed, or saturated frames from analysis, but preserve them and log the failure.
7. Validate metadata and positions. Analyze only valid full-resolution frames.
8. Make at most one documented measurement, in µm, with one manual spot-check.
9. Append one dated result entry to `RALPH_PROGRESS.md`, including station, settings, returned position/z, validity, observations, measurement, and next slot.
10. Append one specific testable hypothesis or update to `OPEN_QUESTIONS.md`.
11. Stop this iteration. Run the 15-minute pacing command before the next iteration.

OVERNIGHT STOP CONDITIONS:
- Stop if repeated failed or blank/saturated frames persist after one conservative retry.
- Stop if repeated returned-position, plate, well, dx, dy, or z mismatches occur.
- Stop if scale/FOV is missing, inconsistent, or unresolved.
- Stop after repeated gateway, scope-busy, rate-limit, or queue errors despite normal retry/backoff and retry_after_s handling.
- Stop if a command would access a non-owned well, leave valid well coordinates, overwrite a frame, modify `snap.py`/`SKILL.md`, or break the sentinel cadence.
- Stop if light-budget or microscope safety limits become uncertain.
- Record the stop reason in `RALPH_PROGRESS.md` before ending.

When the direction is answered and cross-checked, emit `<promise>CAMPAIGN_DONE</promise>`.
