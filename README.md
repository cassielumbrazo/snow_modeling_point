# snow_modeling_point
Scripts to set-up point based snow model simulations including, 
* Processing HRRR-AK grib files into netcdfs 
* Creating SNOWPACK and Snow-17 forcing data files
* Reading point simulation output and compare with observations

## Repository organization

- `icefield_domain/`, `large_juneau_domain/`, and `small_juneau_domain/`: domain-specific processing notebooks and scripts.
- `sites/`: site-specific forcing and simulation analysis.
- `examples/`: model test cases and examples.
- `figures/`: exported figures.
- `previous_scripts/`: earlier notebooks, download scripts, and related notes previously stored in the repository root, retained for reference.

The files in `previous_scripts/` are preserved unchanged. Before rerunning an archived notebook or script, check its data paths and working-directory assumptions because its location has changed.
