# Survey frame storage

All microscope captures belong under `survey_frames/` and are partitioned by plate and well:

```text
survey_frames/
├── plate_A/
│   ├── well_B11/
│   │   ├── YYYY..._BF_LED_matrix_full.png
│   │   ├── YYYY..._BF_LED_matrix_full_thumb.png
│   │   └── ...
│   └── well_B12/
└── plate_B/
    ├── well_B11/
    └── well_B12/
```

Each image filename starts with a UTC timestamp and includes the channel. Full-resolution frames and thumbnails are stored together. Metadata should be saved beside a sequence as `metadata.json`; it should include `well`, `plate`, `dx`, `dy`, `channel`, `exposure_ms`, `intensity`, `timestamp_utc`, `pixel_size_um`, and `fov_um`.

The helpers create directories automatically. `snap.py` defaults to the repository's `survey_frames/` directory and adds `plate_<A|B>/well_<B11|B12>/`. `navigator.py` uses the same structure.
