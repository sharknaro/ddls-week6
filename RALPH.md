# Ralph Scientific Instruction

## Direction

Survey the owned wells and catalogue distinct organism-like morphotypes across comparable fields: ciliates, flagellates, amoebae, rotifers, algae, diatoms, cyanobacteria, and micro-crustacea. Build a labelled gallery with rough, field-level counts for each morphotype. In parallel, determine whether the late-season community is cyanobacteria-like dominated or remains a mixed phototrophic community containing diatom-like, green-algae/chlorophyte-like, desmid-like, and cyanobacteria-like candidate forms.

The catalogue is a morphology screen, not taxonomic identification. Labels must remain candidate-level unless independently supported. Use `not observed` rather than zero when the survey has not adequately sampled a morphotype.

## Scope and safety

- You are running a continuous discovery loop on a real, live, changing freshwater sample.
- Use only the owned wells and only the microscope operations documented in `SKILL.md`.
- Drive the microscope only through `./snap.py`.
- Never use `/move` for acquisition; use atomic `dx`/`dy` snaps.
- Never exceed documented API or exposure limits.
- Never modify `SKILL.md` or `snap.py`.
- Preserve existing frames, logs, and scientific records.

## Required reading

Before each iteration, read:

- `SKILL.md`
- `RALPH.md`
- `RALPH_PROGRESS.md`
- `OPEN_QUESTIONS.md`
- `STATE.json`, when present

Use prior progress and the gallery inventory to avoid repeating covered ground.

## Iteration procedure

Perform exactly one focused scientific cycle per iteration:

1. Read the current scientific memory, state, and available thumbnail inventory.
2. Determine the field strategy from the direction and prior records.
3. For a fresh field, autofocus first and acquire with atomic `dx`/`dy` through `./snap.py`.
4. Look at every acquired thumbnail and let visible content guide the next field; skip empty fields.
5. For a time-lapse or change-over-time comparison, revisit the exact recorded well and `dx`/`dy` station.
6. At the best or tracked field, acquire a closer BF frame. Add chlorophyll FL at the same spot only when it addresses a live-versus-dead or identity question.
7. Update the morphotype catalogue from the inspected frame: assign visible candidates to the permitted labels, record a rough count per label, and link each label/count to the frame path and field coordinates. Do not count the same object twice across channels or revisits.
8. Keep the number of images small because the microscope is shared.
9. Validate every frame before analysis: confirm plate, well, coordinates, returned position, focus/quality, and that the frame is not blank or unusable.
10. Do not analyse a failed frame. If a frame fails, make at most one appropriate retry and record the failure if it remains unusable.
11. Measure only on the full-resolution image and record at most one meaningful, checkable measurement in micrometres when one exists.
12. Generate exactly one specific, testable hypothesis.
13. Append exactly one dated scientific entry to `RALPH_PROGRESS.md`, including the morphotype labels and rough counts for that field.
14. Append exactly one ranked hypothesis or update to `OPEN_QUESTIONS.md`.

## Scale and measurements

- Read scale from `result.scale.pixel_size_um` in `/v1/status`.
- Record and use the scale once for the field; retain the corresponding FOV.
- Never report raw-pixel measurements.
- Do not apply the full-resolution scale directly to thumbnail pixels. If a thumbnail measurement is unavoidable, convert using its actual resized pixel scale.
- Re-read the cited full-resolution frame before writing any numerical claim.
- If no real visible feature can be measured, record `measurement: none`.

## Fluorescence

- Start FL at `exposure_ms=30`, `intensity=20`.
- A blank-white FL frame indicates overexposure; reduce exposure conservatively.
- Allow at least 30 seconds for an FL request.
- FL supports chlorophyll-bearing status only. It does not prove taxonomy, viability, or photosynthetic rate.
- Confirm BF and FL are from the same plate, well, atomic `dx`/`dy`, and returned position before comparing them.

## Interpretation and reporting

Use cautious candidate-level morphology labels only:

- cyanobacteria-like
- diatom-like
- green-algae/chlorophyte-like
- desmid-like
- other algae-like
- non-phototroph candidate
- uncertain biological object
- debris/artifact candidate

For the requested catalogue, map observations into these broad labels only when morphology supports them:

- `ciliate-like`
- `flagellate-like`
- `amoeba-like`
- `rotifer-like`
- `algae-like`
- `diatom-like`
- `cyanobacteria-like`
- `micro-crustacean-like`

A single object may receive one primary label and one uncertainty note; do not inflate counts by assigning multiple biological labels to the same object.

Never claim genus or species identification from these images alone. Every finding must be marked `candidate`, `confirmed`, `rejected`, or `literature check pending`.

Report comparisons only against comparable observations and state the sample size / number of fields. Do not generalise from a few fields. Distinguish observations from interpretations and hypotheses.

## Durable records

Each progress entry should state:

- UTC date/time
- plate, well, `dx`, and `dy`
- acquisition channels and quality decisions
- returned position and scale when relevant
- visible candidate morphotypes and rough per-field counts for all requested catalogue labels, including `not observed` where appropriate
- frame path(s) supporting each label/count
- FL correspondence when interpretable
- one meaningful measurement or `measurement: none`
- comparison sample size and limitations
- the finding status
- exactly one testable hypothesis and the next iteration’s test
- cumulative labelled-gallery update with unique field identifiers and per-field rough counts; do not treat counts across fields as deduplicated organism totals

Do not emit `CAMPAIGN_DONE` unless the direction is answered and cross-checked across adequate comparable observations.
