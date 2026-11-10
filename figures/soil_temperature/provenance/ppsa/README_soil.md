# PPSA soil simulations: WY2020–WY2025

Two soil counterparts to the existing lapse-rate base simulations. Run from `config/` with `../run_soil.sh`, or run `./run_soil.sh` from this directory. The runner refuses to overwrite existing soil results. It does not overwrite or rerun the base simulations.

## Configurations and products

| Forcing | Configuration | Main comparison output |
|---|---|---|
| HRRR-AK lapse-rate | config/hrrrak_lapserate_soil_ppsa_WY2020-WY2025.ini | output/hrrrak_lapserate_ppsa_WY2020-WY2025_soil.smet |
| Met + HRRR-AK lapse-rate | config/met_hrrrak_lapserate_soil_ppsa_WY2020-WY2025.ini | output/met_hrrrak_lapserate_ppsa_WY2020-WY2025_soil.smet |

Each soil profile is beside its original forcing and zero-layer profile in `input/<forcing>_WY2020-WY2025/`, named `<forcing>_ppsa_WY2020-WY2025_soil.sno`. Original station IDs, profile dates, coordinates, 38-degree slope, aspect and surface properties are retained. Baseline forcing files and snow physics are preserved. EXPERIMENT=soil distinguishes products from EXPERIMENT=base. Runs use SNOWPACK 3.7.0 / MeteoIO 2.11.0, executable `/home/cassie/programs/snowpack/usr/bin/snowpack`.

Both start from profile date 2019-10-01T06:00 UTC and end at 2025-09-01T00:00 UTC, matching the existing base output endpoints. The HRRR-only base cold start includes one extra initial output at 2019-10-01T05:00 UTC; soil output begins at 06:00 UTC because it loads the original profile date. The met-plus-HRRR timestamps match exactly. Compare on the shared datetime index (an inner join), without shifting or padding either series. Thus WY2025 is partial, as in the base runs; the filenames describe the existing project period, not a complete final September.

Exact individual commands (working directory `/home/cassie/python/models/run_snowpack/sites/ppsa/config`):

```bash
snowpack -c hrrrak_lapserate_soil_ppsa_WY2020-WY2025.ini -e 2025-09-01T00:00
snowpack -c met_hrrrak_lapserate_soil_ppsa_WY2020-WY2025.ini -e 2025-09-01T00:00
```

Use `run_soil.sh` for overwrite protection and per-run logs. Native SMET products retain the model's field definitions and unit metadata for loading alongside the base SMETs; no MET-to-SMET conversion is used.

## Soil assumptions

The same idealized homogeneous mineral loam and initial temperature are used in both runs, keeping soil setup consistent between forcing comparisons. This is not a measured PPSA soil profile. 28 elements, bottom-to-top in the input, total 5 m along the model column. Surface-down spacing: 5 x 0.02 m, 4 x 0.05 m, 7 x 0.10 m, 8 x 0.25 m, 4 x 0.50 m. One numerical element per row; zero initial snow. Native PRO heights are vertical and therefore extend to about -6.345 m for this 38-degree slope.

LOAM class rg=2.5 mm; mineral density 2600 kg/m3, conductivity 0.9 W/(m K), specific heat 1000 J/(kg K), following the project's soil example. Input liquid/ice/air/solid fractions are 0.25/0/0.149/0.601. Richards' class mapping overrides the solid fraction to about 0.564885 and the initialization redistributes water hydrostatically (initial log about 0.25 bottom to 0.1842 top); input fractions should not be mistaken for the effective initialized profile.

Uniform initial soil temperature 275.193561 K (2.043561 C), the mean of 35,064 hourly HRRR-AK lapse-rate temperatures in complete calendar years 2020–2023. This common initial state is retained for both forcings; the first season remains initialization-sensitive. Soil physics: SNP_SOIL=true, SOIL_FLUX=true, GEO_HEAT=0.06 W/m2 assumed upward at the 5 m lower boundary, WATERTRANSPORTMODEL_SOIL=RICHARDSEQUATION, REQ_INITIALIZE_SOIL=true, SOIL_THERMAL_CONDUCTIVITY=COSENZA2003. The old constant TSG generator is disabled. No snow physics were tuned.

## Diagnostics and output format

Main timeseries are hourly native SMET, with soil energy and water diagnostics enabled by OUT_SOILEB. Hourly PRO files retain modeled soil temperature, water and ice profiles; SNO and dated backups retain restart states. FIXED_POSITIONS=-0.05 -0.10 -0.20 -0.50 is recorded, but OUT_T=false deliberately suppresses misleading observation-only TS columns in version 3.7 SMET. This build accepts a single TS_FORMAT, so modeled fixed-depth MET output cannot be emitted simultaneously; use the modeled PRO profiles for soil-temperature analysis. The main SMETs are intended for snow-output comparisons.

Both original forcings contain a gap at 2024-05-23T03:00 UTC (HRRR-only missing TA/RH/wind/radiation/pressure; combined forcing has TA/RH but missing wind/radiation/pressure). Source files and existing interpolation are unchanged so soil/base use the same forcing workflow. Check `soil_run_verification.json` for completion, timestep coverage and missing-value verification across this gap.

## Cleanup and preservation

The completed short-test configurations, soil_pilot report/analysis directory, soil_pilot_* output directories, and unused empty soil_full_period directory have been removed. Their scientifically relevant assumptions are retained here. Other sites and unrelated historical files are untouched. The original input profiles, forcing files and all existing base results are protected by the checksum manifest `soil_preserved_inputs_and_base.json`; final validation checks them against disk. Existing unrelated Git changes have not been staged or committed.

## References

- https://snowpack.slf.ch/doc-release/html/smet.html
- https://snowpack.slf.ch/Soil-with-Richards-equation/
- https://avacollabra.org/Best-practices-for-configuring-the-SNOWPACK-model/
- Installed examples: /home/cassie/programs/snowpack/usr/share/doc/snowpack/examples/cfgfiles/io_soil.ini and project examples/soil_example.sno

## Completed-run verification

Both simulations completed successfully: 51,883 continuous hourly records each, 2019-10-01T06:00 to 2025-09-01T00:00 UTC. No solver failures and no missing HS_mod, SWE, TSG, MS_Water_Soil or MS_Ice_Soil values, including the existing forcing gap. Final restart profiles retain 5 m of soil. All 88 protected original input/base files match their pre-run SHA256 checksums. Both soil SWE series differ from their base counterparts on aligned timestamps.

The generic precipitation-reaccumulation warning is retained in both logs; source precipitation is already hourly and the calculation step remains 60 minutes, as in the base workflow. No changes were made to source forcing or its interpolation.

Recheck final products with `/opt/anaconda3/bin/python verify_soil_runs.py` from this directory; details are saved in soil_run_verification.json.
