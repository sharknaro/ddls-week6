# RALPH — One-Iteration Scientific Instruction

## DIRECTION

Characterize the visible late-season phototrophic microcommunity in the separately seeded pond-water samples on plates A and B. Determine whether observed fields are dominated by cyanobacteria-like morphology or contain a diverse mixture of cyanobacteria-like, diatom-like, chlorophyte/desmid-like and other candidate phototrophs. Also examine variation among owned wells/fields and changes through time.

## OWNED SITES

Only:

- A/B11
- A/B12
- B/B11
- B/B12

Never use any other well.

## 8-SLOT SAMPLING CYCLE

1. A/B11, `dx=-0.5`, `dy=-0.5` — fixed sentinel
2. A/B12, `dx=-0.5`, `dy=-0.5` — fixed sentinel
3. B/B11, `dx=-0.5`, `dy=-0.5` — fixed sentinel
4. B/B12, `dx=-0.5`, `dy=-0.5` — fixed sentinel
5. documented high-interest exploratory field
6. documented contrasting exploratory field at a DIFFERENT coordinate
7. one previously unseen valid coordinate
8. revisit the most informative exploratory field

Sentinel coordinates never change.

## ONE ITERATION

1. Read `RALPH_PROGRESS.md`, `OPEN_QUESTIONS.md`, and `STATE.json`. `STATE.json` is the sole machine-readable source of iteration and slot state. `RALPH_PROGRESS.md` is the scientific notebook, not the scheduler. `RUN_STATUS.md` is dashboard output only and must never determine the next slot.
2. Determine the current slot from `STATE.json` only. Never infer slot state from filenames or grep text from `RALPH_PROGRESS.md`.
3. Image exactly one field.
4. Sentinel: paired BF→FL.
5. Exploratory: BF first; add FL only when useful for distinguishing chlorophyll-bearing candidates.
6. Inspect thumbnail visually.
7. Use full-resolution image for measurements.
8. Record at most one meaningful biological measurement if one exists.
9. Record candidate morphotypes visible in that field.
10. Where interpretable, record how many candidate BF objects/forms have corresponding FL signal.
11. Compare only with comparable previous observations.
12. State sample size / number of fields.
13. Generate exactly one testable hypothesis.
14. Append exactly one dated entry to `RALPH_PROGRESS.md`.
15. Append exactly one ranked hypothesis/update to `OPEN_QUESTIONS.md`.
16. After a successful scientific iteration, update `STATE.json` atomically: increment `campaign_iteration`, set `last_completed_slot` to the completed slot, advance `next_slot`, and after slot 8 return `next_slot` to 1 and increment `cycle`. Update `RUN_STATUS.md` only as dashboard output; it must not be used to schedule the next slot.

## INTERPRETATION

Use morphology labels only:

- cyanobacteria-like
- diatom-like
- chlorophyte/green-algae-like
- desmid-like
- other algae-like
- non-phototroph candidate
- uncertain biological object
- debris/artifact candidate

Never claim genus/species identification from these images alone.

FL supports chlorophyll-bearing status only. It is not proof of taxonomy, viability or photosynthetic rate.

## SATURATION

Saturation is image QC, not an ecological result.

If the biological region being measured is materially clipped, make exactly one conservative reduced-exposure retry.

A few isolated saturated pixels do not automatically invalidate the entire image.

Never use % saturated pixels as a community-composition or chlorophyll-abundance metric.

## MEASUREMENTS

Never report a generic `100 px = X µm` check.

Measure only a real visible object or feature. If no meaningful feature can be measured, record `measurement: none`.

## HONESTY

Every finding must be marked:

- candidate
- confirmed
- rejected
- literature check pending

Do not generalize from a few fields.
