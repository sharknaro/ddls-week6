# Investigation summary

Updated 2026-10-01 UTC after one additional conservative completion-recon cycle at A/B12. The BF field was usable and raises A/B12 to the requested n=4; all three completion targets now have four usable comparable BF fields. Counts below are rough candidate counts per usable brightfield field; requested biological labels only are included in totals. `not observed` means the sampled fields were inadequate for a reliable absence claim. Counts are field-level and are not deduplicated organism totals across fields.

| Plate | Well | Usable fields | Total microorganism-like candidates | Mean/field | Median | SD (n>=2) | Failed fields | Current ranking |
|---|---|---:|---:|---:|---:|---:|---|---|
| A | B11 | 4 | 1 | 0.25 | 0 | 0.50 | none | 4 (coverage complete; lowest provisional candidate mean) |
| A | B12 | 4 | 3 | 0.75 | 1 | 0.50 | 1 (2026-10-01T21:55Z atomic attempt; no frame) | 2 (coverage complete; candidate mean provisional) |
| B | B11 | 4 | 2 | 0.50 | 0.5 | 1.00 | none | 3 (coverage complete; spatially heterogeneous) |
| B | B12 | 4 | 4 | 1.00 | 1 | 0.58 | none | 1 (highest provisional mean; coverage complete) |

**Denominator and uncertainty:** A/B12, B/B11, and B/B12 each now have n=4 usable comparable BF fields, so denominator matching permits cautious ranking; candidate-level BF counts remain uncertain because fields are spatially heterogeneous, edge-partial, and lack motion/fluorescence confirmation. No taxonomic, viability, or dominance claim is made. A/B11 and B/B11 retain spatial/station dependence. Totals exclude debris/artifact and uncertain biological objects. All successful fields are BF-only and candidate-level; no fluorescence or motion evidence was acquired. A/B11 was not sampled in this completion run. The failed A/B12 attempt has no image-derived candidates and is excluded from usable-field and candidate totals.

## Field catalogue

The pre-existing successful field catalogue is retained in the prior records and now consists of 16 usable fields: A/B11=4, A/B12=4, B/B11=4, B/B12=4. The prior attempted A/B12 field was not usable and has no frame path; the latest B/B12 field is usable.

| Field ID | Plate/well | Usable | Requested catalogue counts (ciliate, flagellate, amoeba, rotifer, algae, diatom, cyanobacteria, micro-crustacean) | Total requested biological | Uncertain biological | Debris/artifact | Frame |
|---|---|---|---|---:|---:|---:|---|
| A_B12_completion_attempt_20261001T215500Z | A/B12 | no | not assessable; no image returned | not assessable | not assessable | not assessable | none (connection reset before frame return) |
| B_B12_dx-0.45_dy-0.35_cycle5 | B/B12 | yes | 0, 0, 0, 1, 0, 0, 0, 0 | 1 | 1 | many aggregates/particles | `frames/ralph_cycle5_B_B12_dx-0.45_dy-0.35/plate_B/well_B12/20261001T200914Z_BF_LED_matrix_full.png` and `_thumb.png` |
| A_B12_dx0.45_dy0.35_cycle6 | A/B12 | yes | 0, 0, 0, 1, 0, 0, 0, 0 | 1 | 1 | many aggregates/particles/filaments | `frames/ralph_cycle6_A_B12_dx0.45_dy0.35/plate_A/well_B12/20261001T201625Z_BF_LED_matrix_full.png` and `_thumb.png` |

All prior field rows and frame paths remain preserved in `RALPH_PROGRESS.md` and the existing frame inventory. The failed A/B12 attempt is not counted as a comparable field. RECON_COVERAGE_COMPLETE

RECON_COVERAGE_COMPLETE


## Latest discovery observation

2026-10-01T21:20:08Z: One BF-only fixed-sentinel revisit at B/B12 dx=0.0, dy=0.0 (`frames/ralph_cycle7_B_B12_sentinel/...`) was sharp and nonblank, with one cautious rotifer-like candidate, two uncertain biological objects, and many aggregates/debris. No phototrophic morphotype was confidently observed. This supports temporal recurrence of a local organism-like pattern but does not establish cyanobacteria-like dominance, taxonomy, viability, or activity.
