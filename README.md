# snow_modeling_point
Scripts to set-up point based snow model simulations including, 
* Processing HRRR-AK grib files into netcdfs 
* Creating SNOWPACK and Snow-17 forcing data files
* Reading point simulation output and compare with observations

## Repository organization

- `icefield_domain/`, `large_juneau_domain/`, and `small_juneau_domain/`: domain-specific processing notebooks and scripts.
- `sites/`: individual site folders for forcing and simulation analysis.
- `sites/all_sites/`: shared notebooks comparing forcing, snow-model output, soil effects, figures, and tables across sites.
- `examples/`: model test cases and examples.
- `figures/`: selected final manuscript and presentation figures.
- `temporary/`: local research outputs, diagnostic tables, caches, copied inputs, and export bundles; ignored by Git.
- `previous_scripts/`: earlier notebooks, download scripts, and related notes previously stored in the repository root, retained for reference.

The files in `previous_scripts/` are preserved unchanged. Before rerunning an archived notebook or script, check its data paths and working-directory assumptions because its location has changed.

## Analysis outputs

Analysis notebooks should display figures inline without automatically saving PNGs or PDFs. Export a figure to `figures/` only when it has been explicitly selected as a final manuscript or presentation figure.

The step-5 soil and internal snow-temperature notebooks write supporting tables and caches to `temporary/<analysis>/`. Existing research tables, notes, provenance copies, and ad hoc model export bundles have been moved there for local reference. These files are excluded from future commits. Keep reusable code and lasting research explanations outside `temporary/` when they should be shared.


## Soil precipitation-threshold sensitivity

[`sites/all_sites/6_compare_snowpack_soil_thresh07.ipynb`](sites/all_sites/6_compare_snowpack_soil_thresh07.ipynb)
compares the existing `soil` runs (+1.2°C / 274.35 K air-temperature threshold)
with `soil_thresh07` (+0.7°C / 273.85 K). Both use `PRECSPLITTING` with `THRESH`.
The main figure and statistics use WY2023–WY2025 at PPSA/TRAM and
WY2020–WY2022 at HEEN. Four editable simulation styles distinguish the
forcing datasets and thresholds, with one main-results panel per site.
Forcing, soil profiles, soil/snow physics, output frequency, and simulation
endpoints are preserved. The established 28-layer, 5 m soil column remains on.

| Site | HRRR-AK lapse-rate period | Met + HRRR-AK lapse-rate period | Endpoints |
| --- | --- | --- | --- |
| PPSA | WY2020–WY2025 | WY2020–WY2025 | 2025-09-01 00:00 UTC |
| TRAM | WY2020–WY2025 | WY2023–WY2025 | 2025-09-01 00:00 UTC |
| HEEN | WY2020–WY2025 | WY2020–WY2022 | HRRR: 2025-09-01 00:00; mixed: 2022-09-30 05:00 UTC |

Configurations and site run scripts are in
`/home/cassie/python/models/run_snowpack/sites/<site>/`. Config names follow
`<forcing>_soil_thresh07_<site>_<period>.ini`; result names follow
`<forcing>_<site>_<period>_soil_thresh07.*`. The original forcing and soil
initial profiles are reused. `soil_thresh07_runs.json` records the exact
periods, paths, threshold values, and source/control checksums.

The shared helper can recreate the configurations and run all six cases:

```bash
python sites/all_sites/_threshold_sensitivity.py prepare
python sites/all_sites/_threshold_sensitivity.py run --workers 6
```

Use the JIF snow modeling scientific environment/kernel on this machine.
Each site also has `run_soil_thresh07.sh`. Run scripts refuse to overwrite
existing sensitivity products. Completion status files check matching hourly
coverage and preserved original inputs/controls. The notebook displays plots
and tables inline; generated diagnostics, if exported, belong in ignored
`temporary/soil_thresh07/`.
