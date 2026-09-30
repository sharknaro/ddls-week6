# PI suggested step size for a two-day Ralph loop

## Principle
Use a representative well you own to calibrate spatial sampling. Use brightfield for navigation and reserve fluorescence for promising fields.

## Instrument scale
Read `/v1/status?plate=...` at the start of each plate/session and record:

- `result.scale.pixel_size_um`
- `result.scale.fov_um`

Current reference values were `0.376 µm/px` and `783.6 × 783.6 µm`, but never hard-code them for future runs.

## Pilot design
1. Run a 3×3 coarse brightfield grid with `dx,dy ∈ {-0.5, 0, +0.5}`.
2. Take a second brightfield frame at promising points to detect motion.
3. Refine the highest-scoring area with a 3×3 grid at step `0.25`.
4. Compare neighboring fields using full-resolution images, not thumbnails.

## Recommended starting step
Use `step = 0.25–0.35` for a broad two-day survey.

- `0.5`: fast reconnaissance across a well.
- `0.25`: local refinement around dense or interesting regions.
- `0.1–0.15`: close-up tracking/time series only.

Interpretation of neighboring-field overlap:

- `<10%`: step may be too large.
- `10–30%`: useful target range.
- `>30–50%`: step may be unnecessarily small.

## Suggested two-day workload per well
Day 1:

- 9 coarse BF frames
- 2–3 repeat BF frames at high-scoring fields
- Fluorescence on the top 2–3 fields

Day 2:

- Local 0.25-step refinement around the best region
- Time series at the best field
- BF–FL–BF paired comparisons

Keep the loop bounded and save state after each iteration. A state record should include plate, well, step, completed coordinates/scores, best field, pixel size, FOV, and timestamps.

## Acquisition rules
- Autofocus once per well before the first real snap.
- Use atomic `dx`/`dy` on `/v1/snap`; never use move-then-snap.
- Read scale from status rather than hard-coding it.
- Use brightfield for navigation and fluorescence only for selected candidates.
- Save full-resolution images and thumbnails separately; never make quantitative measurements from thumbnail pixels using the full-resolution scale.
- Respect 429/503 retry-after delays and shared-scope rate limits.
