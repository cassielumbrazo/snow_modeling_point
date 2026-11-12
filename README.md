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


## Base precipitation-threshold sensitivity (soil disabled)

[`sites/all_sites/6_compare_snowpack_base_thresh07.ipynb`](sites/all_sites/6_compare_snowpack_base_thresh07.ipynb)
compares `base` (+1.2°C), `base_thresh10` (+1.0°C), and `base_thresh07`
(+0.7°C) for PPSA, TRAM, and HEEN with both lapse-rate forcing datasets.
The notebook retains its filename and the same comparison windows listed above.
Solid, dotted, and dashed styles distinguish the three thresholds. Seasonal
statistics compare each sensitivity with the shared control and include a direct
three-threshold table; baseline seasons are counted once in that table.

All experiments preserve `SNP_SOIL = false`, `SOIL_FLUX = false`,
`GEO_HEAT = 0.06`, zero-layer initial profiles, and the constant 273.15 K
ground-temperature generator. Phase partitioning uses the working MeteoIO
`Generators` syntax: `PRECSPLITTING`, `THRESH`, with `snow = 274.15`
for +1.0°C or `273.85` for +0.7°C. Other active settings are preserved.

Each sensitivity has six configs named
`<forcing>_<experiment>_<site>_<period>.ini` in the existing model site's
`config/` directory, outputs ending in `_<experiment>.*`, a matching
`<experiment>_runs.json` manifest, and `run_<experiment>.sh` site script.
Original outputs and inputs are preserved. For a fresh +1.0°C setup:

```bash
python sites/all_sites/_base_threshold_sensitivity.py prepare --experiment base_thresh10
python sites/all_sites/_base_threshold_sensitivity.py run --experiment base_thresh10 --workers 6 --empty-column-guard-sites tram
```

Use `--experiment base_thresh07` for +0.7°C (also the default). Run with the
`jif_snow_modeling` environment. Existing sensitivity products are protected
against overwriting. Use the Python run command above for TRAM so the guard
is enabled; the simple site shell scripts invoke SNOWPACK directly.

The TRAM sensitivity runs use the build-specific empty-column vapor-transport
guard described in `sites/all_sites/numerics/README.md`; status records include
its command and application count. The +0.7°C retries matched all pre-crash
HS, SWE, rainfall, and snowfall values. The shared comparison omits the extra
05:00 control initialization record at PPSA/TRAM HRRR (new runs start at their
profile date, 06:00); displayed years are unaffected.

The notebook displays plots and tables inline without automatic figure exports.
Optional diagnostic artifacts belong in ignored `temporary/base_thresh10/` or
`temporary/base_thresh07/`.


## Small-domain forecast-hour comparison

[`small_juneau_domain/3_compare_hrrrak_forecast_hours_ppsa.ipynb`](small_juneau_domain/3_compare_hrrrak_forecast_hours_ppsa.ipynb)
compares the processed native-grid `f123`, `f567`, `f6to11`, and
`f6to29` mosaics for the available WY2024/WY2025 periods at the grid cell nearest
PPSA. It includes eight inline figures: lead schedules, daily forcing overviews,
hourly storm windows, f6to11-minus-f567 differences, PPSA temperature/RH checks,
and precipitation totals on common observed hours. Settings expose point
coordinates, colors, windows, and the optional temperature lapse rate.

The audit uses stored valid times and forecast leads. The WY2025 file labeled
`f678` actually contains leads 5–7; it is flagged in the inventory and excluded from all plots and comparison
statistics. The older WY2025 f567 test subset matches the selected later version at
the extracted point and is excluded from plots. Cropped/reprojected test files
are not counted as separate forecast options.

PPSA validation uses the raw Synoptic CSV: exact hourly temperature/RH and gauge
increments with gaps/resets retained as missing. HRRR precipitation follows the
existing forcing convention of instantaneous `precip_rate * 3600`, explicitly
labeled as an estimated hourly amount. Statistics use common valid timestamps;
totals are matched-hour sums, not complete water-year totals. Native wind
direction is grid-relative. Run with the JIF kernel; source datasets remain
read-only. Diagnostics belong in ignored `temporary/forecast_comparison/`.
