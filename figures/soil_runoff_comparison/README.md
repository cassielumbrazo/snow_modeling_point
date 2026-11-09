# SNOWPACK snowpack-outflow sensitivity analysis

Entry point: `sites/all_sites/3_compare_snowpack_runoff_base_vs_soil.ipynb` (executed end to end). The earlier source notebook, existing simulations, and previous figures are preserved. Only new artifacts in this directory are regenerated.

Main figures (PNG at 300 dpi and vector PDF):
- A_cumulative_spring_outflow: 18 site/year panels, two lapse-rate forcings, base/soil.
- B_paired_seasonal_differences: total mm, T50 days, and complete rolling 24-hour peak mm.
- C_disappearance_vs_T50_shift: paired shifts with zero and 1:1 reference lines. Open symbols mark initial seasons.
- D_selected_physical_diagnostics: largest/smallest |T50 shift| among complete post-initialization water years, including rain, snow states/phase changes, interface temperature, soil storage and distinct boundary fluxes.

Tables:
- seasonal_metrics.csv: tidy paired rows for spring and water-year windows; explicit initial/incomplete flags, known partial totals, base/soil/differences, T10/T50/T90 and 24-hour peaks.
- sensitivity_summary.csv: all spring-complete, first-season-excluded, and complete-WY post-initialization results.
- common_forcing_comparison.csv: rankings recomputed on common years and a four-way hourly intersection.
- selected_case_physics.csv and water_balance_diagnostics.csv: underlying diagnostic quantities and residuals, not inferred infiltration.
- run_audit.csv, field_audit.csv, run_settings.csv, analysis_metadata.json: source checksums, availability, interval/gap/reset checks, area/unit conventions and installed version.
- interpretation.md: numerical paper-facing findings, counterexamples and limitations.

Primary spring window: (March 1 00:00, September 1 00:00] UTC. The supplementary water year is (October 1 00:00, next October 1 00:00]. Flux timestamps are preceding-interval ends. Native snow-base outflow is already horizontal kg/m2 per hourly interval (= mm); precipitation rates require the source-verified slope correction. Snow-free rainfall is not counted as snowmelt. Actual short-lived snowfall within a zero-SWE-to-zero-SWE interval and the final snow-drainage hour are retained. Missing runoff is never filled with zero. Percentile timing is withheld for incomplete/low-volume windows.

Negative MS_Wind is potential erosion in this build, not deposition; only actual positive erosion enters the snow budget. Net snow phase-change energy is interval kJ/m2 on slope area despite the misleading header label; it does not recover gross melt production. Soil-bottom drainage exits the 5 m modeled column and may include antecedent water. The incomplete soil-boundary budget is explicitly unresolved; none of its residual is labeled measured infiltration, lateral runoff or catchment discharge.

See interpretation.md for numerical conclusions. These results are paired model sensitivities under an assumed loam profile, not observed hydrologic changes. No suitable point-lysimeter or gauged discharge series was identified by the documented scoped local search.
