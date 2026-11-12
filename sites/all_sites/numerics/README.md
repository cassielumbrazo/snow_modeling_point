# Empty-column vapor transport guard

Reused from `jif_snow_modeling/sites/radar_sites/numerics/` for the same installed
SNOWPACK 3.7.0 library (SHA-256 checked in the runner). Both TRAM base_thresh07
runs segfault without this guard. It returns after surface sublimation only
when no elements remain, before invalid layer-to-layer transfer. It leaves
all nonempty-column calls and model settings unchanged. The instruction offset
is specific to this binary; do not reuse with another build.

The failed outputs and debugger trace are archived in ignored
`temporary/base_thresh07/`. Retry verification compares every pre-crash
HS, SWE, rainfall, and snowfall value exactly. Guard counts and commands are
recorded in each run status. This workaround has not been validated against
an upstream fix and must remain disclosed in analysis/publication provenance.

The +1.0°C TRAM runs also use this guard from the start; counts are recorded
even when zero applications are needed. For a fresh six-run setup, use
`run --experiment base_thresh10 --workers 6 --empty-column-guard-sites tram`
(or `--experiment base_thresh07`).
Existing candidate outputs are protected against overwriting.
