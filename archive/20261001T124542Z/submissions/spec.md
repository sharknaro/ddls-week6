# Scientific specification

## Exact problem

Determine whether the late-September pond phototrophic community is dominated by cyanobacteria-like morphotypes or retains a diverse mixture of cyanobacteria-like, diatom-like, green-algal/desmid-like, and other phototroph-like forms. At the same time, test how heterogeneous that community is across the two 200-µL subsamples.

This is a characterization and reproducibility problem, not a climate-causation or hospital-effect study. The interview identifies the source as fresh pond water from Sjukhusparken, Solna, collected in late September 2026. Plates A and B are technical replicate loadings from the same collection, not independent locations or independent ecological samples.

## Sample and acquisition setup

- Source: one Sjukhusparken, Solna pond-water collection.
- Subsamples: two 200-µL loadings.
- Plates actually used in the project: A and B.
- Wells actually used: B11 and B12 on each plate.
- Brightfield channel: `BF_LED_matrix_full`, used for primary morphology.
- Chlorophyll-fluorescence channel: `Fluorescence_488_nm_Ex`, used as secondary validation of apparent phototrophs.
- Fixed sentinel fields currently documented in `RALPH.md`: A/B11, A/B12, B/B11, and B/B12, each at `dx=-0.5`, `dy=-0.5`.
- Exploratory fields are controlled by the Ralph slot schedule and must remain inside those four owned wells.

The transcript says the original stage positions were named `squid+3` and `squid+4`, while later operational records use plate identifiers A/B and also document plate-B aliases. This specification follows the actual acquisition records and the owned A/B well allocation; aliases must not be silently treated as independent samples.

## Files and purposes

- `ddls-week6-interview.md`: raw collaborator/interview record and the source of the scientific framing and limitations.
- `RALPH.md`: bounded acquisition schedule, imaging rules, sentinel coordinates, exploratory slots, and stop conditions.
- `RALPH_PROGRESS.md`: dated durable record of acquired fields, metadata checks, quality decisions, measurements, and next slots.
- `OPEN_QUESTIONS.md`: specific testable questions carried forward between iterations.
- `survey_frames/`: primary full-resolution image, thumbnail, metadata, and analysis archive.
- `survey_frames/DATA_INDEX.json`: inventory of survey collections and organizational roots.
- `survey_frames/ralph_long_run/cycle_001_metadata.json`: BF/FL metadata for the first four sentinel acquisitions, including channels, coordinates, positions, scale, and settings.
- `survey_frames/ralph_validation/validation_metadata.json`: metadata for the two-iteration validation campaign.
- `fluorescence/A/fluorescence_analysis.json` and `fluorescence/B/fluorescence_analysis.json`: screening summaries for fluorescence grids. Their bright-pixel fractions are not organism counts or proof of photosynthesis.
- `images/`: exported full-resolution image views.
- `thumbs/`: exported thumbnail views. Thumbnails are for visual inspection, not default measurement.
- `snap.py`: acquisition helper; it must not be modified for this project operation.
- `dashboard.py`: local dashboard for browsing project evidence; it is not a substitute for source metadata.
- `ralph_parameters.json`: validated starting parameter record.
- `SURVEY_FRAMES.md`: survey archive description.
- `results/`: destination for new analyses, derived tables, plots, and reports.

BF/FL pairs are valid only when acquisition metadata supports the same intended plate, well, atomic `dx`/`dy`, and returned stage position. A matching filename or timestamp alone is insufficient.

## Claims currently being tested

### Claim 1 — community composition

**Claim under test:** the late-season community contains a mixture of cyanobacteria-like, diatom-like, green-algal/desmid-like, and other phototroph-like morphotypes rather than being dominated by only one broad group.

**Current objects/fields:** brightfield candidate forms in the owned A/B B11 and B12 wells, including the documented A/B11 sentinel and controlled exploratory fields. The transcript specifically mentions desmid-like and diatom-like observations, while the project hypothesis also includes cyanobacteria-like and other algae-like forms.

**Required evidence:** repeated, valid full-resolution BF observations across multiple fields and both technical replicate plates; candidate morphotype labels with confidence and limitations; paired FL status where available; no claim of taxonomy from morphology alone.

### Claim 2 — chlorophyll-positive fraction or area

**Claim under test:** at least some BF candidate phototroph-like forms are detectably chlorophyll-positive, or the dataset supports only “chlorophyll not detected/inconclusive.”

**Current objects/fields:** BF↔FL paired sentinel fields and controlled exploratory fields, especially the A/B11 validation and high-/low-FL neighborhood records.

**Required evidence:** correct BF↔FL registration, valid non-saturated FL, documented starting and retry settings, a working positive control or an explicit instrument/QC limitation, and a full-resolution FL area/fraction calculation with status-derived scale. Bright pixels may be autofluorescent debris or particles and cannot alone establish identity, viability, or taxonomy.

### Claim 3 — heterogeneity across 200-µL subsamples

**Claim under test:** the community is spatially and/or subsample heterogeneous, or broadly reproducible, across A/B B11/B12 fields.

**Required evidence:** multiple fields per well, repeated fixed sentinel coordinates, controlled exploratory sampling, comparable BF/FL quality, and explicit sampling depth. A and B are technical replicates from one collection; agreement supports technical reproducibility, not population-level ecological replication.

### Claim 4 — temporal change at fixed sentinels

**Claim under test:** morphology or valid FL signal changes over time at fixed sentinel fields.

**Current status:** this is a future longitudinal comparison enabled by the fixed sentinel schedule, not a conclusion from the single late-September collection or the current short record.

**Required evidence:** repeated visits to exactly the same sentinel plate/well/`dx`/`dy`, confirmed returned positions, stable scale and acquisition settings or explicitly recorded changes, paired quality control, and enough timepoints to distinguish change from focus, motion, registration, or illumination variation.

## Interpretation failure modes

The interpretation can fail or be weakened by:

- BF/FL mismatch caused by motion, stage drift, focus change, or incorrect pairing.
- FL saturation, blank-white frames, channel failure, or lack of a positive control.
- Debris, autofluorescent particles, filaments, or aggregates misclassified as organisms.
- Thumbnail/full-resolution scaling errors or hard-coded pixel size.
- Pseudoreplication: treating plates A and B from the same collection as independent ecological samples.
- Insufficient field sampling or unreported missingness.
- Failure to revisit the same sentinel coordinates.
- Invalid plate/well/`dx`/`dy` metadata or returned-position mismatch.
- Confounding z/focus, exposure, intensity, illumination, and changing sample state.
- Treating fluorescence alone as proof of taxonomy, viability, or photosynthetic activity.
- Calling image area “biovolume” without calibrated three-dimensional measurements.

## Definition of done

The project is done when it produces a reproducible, confidence-aware summary containing:

1. Community composition across cyanobacteria-like, diatom-like, green-algal/desmid-like, and other candidate morphotypes.
2. A valid FL-positive fraction or chlorophyll-positive image area where registration, quality, calibration, and scale support it; otherwise a clearly qualified “not detected/inconclusive” result.
3. Morphotype richness and diversity summaries, with any Shannon/evenness calculation based on documented labels and sampling units rather than unsupported image impressions.
4. Within-sample heterogeneity across the two 200-µL technical subsamples and their owned wells, with sampling depth and pseudoreplication limits stated.
5. Temporal comparisons at fixed sentinel fields only after repeated valid visits; no temporal claim from one date.
6. A clear separation between confirmed observations, candidate interpretations, and unsupported claims.
7. Source-linked outputs written to `results/`, with image IDs/paths, plate, well, `dx`, `dy`, channel, settings, scale, quality status, and confidence/limitations preserved.
