# Modeled ground-temperature analysis

Executed source notebook: `../../sites/all_sites/5_investigate_snowpack_soil_temperature.ipynb`.
The six pre-existing soil simulations are read from `SNOWPACK_SITES`, defaulting
to `/home/cassie/python/models/run_snowpack/sites`. Simulations are not rerun.

Main figures (PNG and PDF):

- `seasonal_overview`: daily 5, 10, 20 and 50 cm temperatures, aligned modeled
  and observed snow depth, and disappearance dates.
- `spring_temperature_depth`: latest complete common spring per site, upper
  metre, common temperature scale centered at 0°C.
- `spring_temperature_water_ice_flux`: matching local temperature, liquid and
  ice fractions, plus downward ground-surface exchange.
- `spring_snow_base_outflow`: virtual lysimeter outflow relative to disappearance.
- `surface_layers_bottom`: ground-contact node, reconstructed buried layer
  temperatures and deepest column node distinguished explicitly.

Tables:

- `meeting_summary.csv`, `meeting_takeaways.md`: findings and contributing counts.
- `season_depth_metrics.csv`: one row per site, forcing, water year and depth,
  including coverage, initialization flags and warming-crossing status.
- `paired_forcing_differences.csv`: mixed minus HRRR, on common calendar dates
  and dates aligned to each run's disappearance.
- `run_inventory.csv`, `initialization_pairs.csv`: effective setup and starting states.
- `physical_diagnostics.csv`, `near_zero_episodes.csv`: local water/ice evidence.
- `exceptions.csv`, `exception_summary.csv`: pre-disappearance warming, shallow
  persistence near zero, and censored deeper crossings.
- `daily_{site}_{forcing}.csv`: extracted daily diagnostics; temperatures in °C,
  local liquid/ice in volume percent, snow depth in cm, SWE in kg/m².
- `representative_depth_response.csv`: selected-spring pre/post means through 1 m.
- `selected_springs.csv`, `observation_audit.csv`, `source_manifest.csv`: selection,
  inspected observations and source provenance.

Depth is perpendicular to the retained 38° slope. PRO's vertical coordinates are
converted before interpolating element values between adjacent soil midpoints.
No temporal interpolation or extrapolation is used. Daily means require 18 hourly
values; full details and seasonal-window requirements are stated in the notebook.
`T_bottom` is the deepest node of the entire 5 m column, not the snow base.

`provenance/` contains copied small input/configuration documents and official
SNOWPACK source snapshots used to verify definitions. Large simulation products
remain in their original locations; their sizes and modification times are listed
in the manifest. Downloaded `master` sources are supporting documentation, not
a claim of an exact executable/source revision match.

Use a Python kernel with numpy, pandas, matplotlib, xarray, netCDF4, nbformat,
nbclient. The existing `interactive` conda environment was used for
execution. Run every notebook cell from inside `snow_modeling_point`; output paths
are resolved from the repository root. Referenced observation paths must also exist.

These are responses of an assumed idealized loam column. Snow-depth observations
do not validate modeled soil temperatures or thaw depth. No matched local ground
temperature observations were found in the inspected station datasets and field
data repository.
