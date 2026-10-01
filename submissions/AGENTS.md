# AGENTS.md

## Operating rules

- Use `uv` for Python: create or reuse the environment with `uv venv`, and run Python commands with `uv run ...`. Do not use bare `python` for project work.
- This folder is a git repository. Commit the current state before any major change, and commit again whenever something starts working. Use short, clear commit messages.
- Never modify `snap.py` or `SKILL.md` during microscopy work. `SKILL.txt` is the available fallback operations document in this checkout.
- Stay within the owned wells: B11 and B12 on plates A and B.

## Data layout

- `survey_frames/` is the primary microscopy archive. It contains full-resolution images, thumbnails, metadata, organized well data, optimization data, fluorescence data, validation runs, and campaign records.
- `fluorescence/` contains fluorescence grids and analysis JSON files. `images/` and `thumbs/` contain exported/flattened views for dashboard and visual inspection; they are not substitutes for acquisition metadata.
- `survey_frames/DATA_INDEX.json` describes the historical, paired, optimization, fluorescence, random-campaign, and organized-well collections.
- `results/` is the output directory for new analyses, reports, tables, and derived artifacts. Preserve source images and metadata in place.

## Image pairing and scale

- BF means `BF_LED_matrix_full`; chlorophyll-FL means `Fluorescence_488_nm_Ex`.
- Pair BF and FL only when metadata shows the same intended plate, well, atomic `dx`/`dy`, and returned position; the long-run metadata demonstrates paired BF→FL records. Confirm the image really belongs to the intended plate/well/dx/dy before analysis.
- Read scale from microscope status metadata at `result.scale.pixel_size_um` (and retain `result.scale.fov_um`). Never hard-code scale.
- Use full-resolution images for measurements. Use thumbnails only for visual inspection. Do not measure thumbnails unless their scale is explicitly and correctly converted.
- Check saturation and image quality before analysis; saturated, blank, failed, or mismatched frames are not quantitative evidence.

## Durable experimental memory

- `RALPH_PROGRESS.md` is durable experimental memory: append dated acquisition results, coordinates, settings, returned positions, scale, quality decisions, measurements, failures, and next steps.
- `OPEN_QUESTIONS.md` stores specific testable hypotheses and updates; append rather than replacing prior questions.
- The controlled Ralph schedule uses fixed sentinel fields and separate exploratory slots. Do not infer a slot or field from a filename alone when progress metadata is available.

## Reporting discipline

Never report a biological conclusion from an image without first reporting relevant confidence and limitations, including:

- BF↔FL registration confidence
- Saturation and image-quality status
- Sampling depth and missingness
- Whether the observation came from a fixed sentinel or an exploratory field
- Whether the image belongs to the intended plate, well, `dx`, and `dy`

Use cautious candidate-level language for morphology and fluorescence. Fluorescence alone does not establish taxonomy, viability, or photosynthetic function.
