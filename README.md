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
