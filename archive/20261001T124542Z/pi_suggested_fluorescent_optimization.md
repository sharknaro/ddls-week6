# PI suggested fluorescence optimization proposal

## Objective
Find the lowest fluorescence dose that reveals photosynthetic organisms and cellular structure without saturation, excessive background, or unnecessary photobleaching.

## Required safeguards
- Read `/v1/status?plate=...` before the experiment and record `result.scale.pixel_size_um` and `result.scale.fov_um`.
- Autofocus once per well before the first real snap.
- Use atomic `dx`/`dy` on `/v1/snap`; never use `/v1/move` in the imaging loop.
- Set a 30-second timeout for the first fluorescence snap.
- Start at `exposure_ms=30`, `intensity=20`.
- If a frame is saturated or mostly white, reduce exposure or intensity; never increase them.
- Track `light_budget` after every fluorescence frame.
- Save full-resolution PNGs, thumbnails for inspection, and complete metadata.
- Do not make quantitative measurements from thumbnails using full-resolution scale.

## Pilot design
Use brightfield to select one or more promising fields. At each selected field, acquire:

```text
BF1 → FL setting 1 → FL setting 2 → ... → BF2
```

Keep the same well, plate, `dx`, and `dy` for every acquisition. Confirm matching `position_mm.z` when comparing channels.

Use the following exposure ladder while initially holding intensity at 20:

```text
10 ms × 20
20 ms × 20
30 ms × 20
50 ms × 20
```

Stop increasing exposure once useful structure is visible and highlights approach clipping. If the first frame is saturated, step downward immediately, for example:

```text
15 ms × 20 → 10 ms × 15
```

Change intensity only after exposure has been explored. Increase intensity cautiously only for genuinely dim fields; prefer reducing intensity when background or bleaching is high.

## Selection criteria
Choose the lowest-dose setting that satisfies most of the following:

- Organism-like structures are visible in brightfield and fluorescence.
- Fluorescence is spatially localized rather than diffuse background.
- Internal structure remains visible.
- The frame is not blank-white or strongly clipped.
- Signal-to-background ratio is improved over lower settings.
- BF1 and BF2 remain sufficiently similar for the field comparison.

For full-resolution quantitative review, record:

- Fraction of pixels near maximum intensity
- Median intensity
- 95th-percentile intensity
- Background median
- Signal-to-background ratio
- Fluorescence light budget before and after the frame

## Ralph-loop policy
For each field, maintain a history of attempted settings. Do not repeat settings that were saturated or uninformative unless the field or focus changed. A safe decision policy is:

1. BF reconnaissance.
2. FL at 30 ms × 20.
3. If saturated: halve exposure, then lower intensity if needed.
4. If dim but structured: increase exposure gradually to 40–60 ms, retaining intensity 20.
5. Select the lowest setting with adequate localized signal.
6. Stop testing a field after a good setting is found or after the dose/time budget is reached.

Fluorescence should be reserved for high-scoring brightfield fields rather than used across the entire coarse grid.
