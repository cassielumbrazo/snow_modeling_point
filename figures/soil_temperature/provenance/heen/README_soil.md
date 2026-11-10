# HEEN soil counterparts to final lapse-rate base runs

The soil setup matches PPSA: 28 elements totaling 5 m, bottom-to-top rows, snow-free start. Surface-down spacing: 5 x 0.02, 4 x 0.05, 7 x 0.10, 8 x 0.25, 4 x 0.50 m. Original station metadata, slope, aspect, surface properties and profile dates retained. Soil thickness is along the model column; original 38-degree slopes are retained rather than changed.

Assumed homogeneous mineral LOAM (rg=2.5 mm hydraulic class), mineral density 2600 kg/m3, conductivity 0.9 W/(m K), specific heat 1000 J/(kg K). Nominal input liquid/ice/air/solid fractions 0.25/0/0.149/0.601. Richards class mapping overrides the solid fraction (~0.564885), and REQ_INITIALIZE_SOIL redistributes water hydrostatically. These are idealized assumptions, not measured site soil properties.

Uniform initial temperature 276.097038 K (2.947038 C), hourly mean of the site's complete HRRR lapse-rate calendar years 2020–2023 (35,064 hours; 2024 has missing forcing and is excluded). Both forcing variants use that same initial state, with their own original start dates. First seasons are initialization-sensitive; no spin-up was added or snow parameters tuned.

SNP_SOIL=true, SOIL_FLUX=true, GEO_HEAT=0.06 W/m2 assumed upward at the 5 m lower boundary; WATERTRANSPORTMODEL_SOIL=RICHARDSEQUATION, REQ_INITIALIZE_SOIL=true, SOIL_THERMAL_CONDUCTIVITY=COSENZA2003. The base constant TSG generator is disabled. Forcing, filters, interpolation, snow physics and hourly output remain those of the corresponding base INI.

Run `./run_soil.sh` from this site directory. It changes to config/ and refuses to overwrite existing soil products. All results use EXPERIMENT=soil and write next to base files in output/. Native SMET is the comparison format; hourly PRO retains modeled soil temperature, water and ice. OUT_T=false avoids observation-only TS columns in v3.7 SMET. SNOWPACK 3.7.0 / MeteoIO 2.11.0.

Commands, working directory `/home/cassie/python/models/run_snowpack/sites/heen/config`:

```bash
snowpack -c hrrrak_lapserate_soil_heen_WY2020-WY2025.ini -e 2025-09-01T00:00
snowpack -c met_hrrrak_lapserate_soil_heen_WY2020-WY2022.ini -e 2022-09-30T05:00
```

Endpoints are read from the actual final base files, including partial final water years. Compare on the shared datetime index; a cold-start base may have one extra initial hour before the loaded profile date. The mixed-forcing and HRRR-only runs have different historical coverage, as recorded in soil_runs.json. Source data and base outputs are protected by soil_preserved_inputs_and_base.json. Verification is saved in soil_run_verification.json after runs complete.

References: https://snowpack.slf.ch/Soil-with-Richards-equation/ ; https://snowpack.slf.ch/doc-release/html/smet.html ; https://avacollabra.org/Best-practices-for-configuring-the-SNOWPACK-model/
