# WORKFLOW.md — Operational Daily Forecast Workflow

This document walks through one complete daily forecast cycle of the **ARISE Medium-Term Flood Forecast Sub-System**, from scheduler trigger to bulletin delivery.

For module-level code details, see [`MODULES.md`](MODULES.md).

---

## 1. Schedule and Trigger

The system is launched once (via desktop shortcut) and idles using the `schedule` library, polling every 60 seconds:

```python
schedule.every().day.at("08:30:00").do(run_forecast)
while True:
    schedule.run_pending()
    time.sleep(60)
```

The 08:30 IST trigger is intentional. ECMWF TIGGE products from the 00:00 UTC base run become available globally at ~02:00 UTC (07:30 IST) and the +36 h delay required by TIGGE means that the previous-day initialisation is downloaded — leaving a ~1 h buffer for upstream data settling.

---

## 2. Forecast Cycle — Phase by Phase

### Phase 1 — Meteorological Acquisition (4 steps)

```
Step 1 ▸ New_ECMWF_Ensemble_Forecast_15Days_Lead.py
         - Reads tp_Step_1day.csv to get last bias-corrected date.
         - Computes end_date = today - 2 days.
         - Loads ECMWF URL/Key/Email from C:\Users\Medium Term Flood Forecast\.ecmwfapirc; prompts only on first run (or if file missing/invalid), then saves for silent reuse.
         - Deletes old GRIB + .idx file.
         - Submits TIGGE retrieval (50 perturbed members, 7 steps × 4 vars).
         - Writes: ECMWF_Ensemble/output_Ensemble_7Days_Lead(ECMWF)_AutoDate.grib
         ≈ 50 s

Step 2 ▸ Tigge_EnsembleForecast_Extraction_HECHMSML.py
         - Opens GRIB with cfgrib/xarray.
         - Computes ensemble mean across number dim.
         - Interpolates to 12 stations via nearest-grid-point.
         - Converts units (K→°C, W/m²·s→kWh/m²/day).
         - Computes step-wise deltas for cumulative variables (tp, ssr).
         - Appends new rows to existing step-wise CSVs.
         - Writes: Stepwise_Combined_CSVs_Ensemble_Mean/{tp,At,ssr,mx2t6,mn2t6}_Step_{1,3,5,7}day.csv
         ≈ 10 s

Step 3 ▸ Forecast_Weightage_Calculations.py
         - Applies Thiessen-polygon area-weighted aggregation across 12 sub-watersheds.
         - Writes: Stepwise_Combined_CSVs_Ensemble_Mean/Weightage/*_weightage.csv
         ≈ 6 s

Step 4 ▸ Bias_Corrected_Data_all.py
         - For each of 5 variable categories × 4 lead times × N columns:
            loads pretrained XGBoost model, predicts residual, corrects.
         - 84 models loaded per run.
         - Clips precipitation to ≥ 0.
         - Writes: Stepwise_Combined_CSVs_Ensemble_Mean/Bias Corrected Data/<Category>/*.csv
         ≈ 8 s
```

### Phase 2 — HEC-HMS Hydrologic Simulation (4 steps)

```
Step 5 ▸ HEC_HMS_DSS.py
         - Reads observed discharge once.
         - For each forecast horizon (1/3/5/7 day):
            • Writes Precipitation pathnames (12 stations) to .dss.
            • Writes Temperature pathnames (12 sub-watersheds) to .dss.
            • Writes Discharge pathname (Bairabi) to .dss.
         - Uses pydsstools (Windows-only).
         ≈ 3–7 s

Step 6 ▸ HEC_HMS_DSS_Calibration.py
         - Reads precipitation CSV date range per horizon.
         - Updates only Start/End Date/Time lines in Calibration.control.
         ≈ 2 s

Step 7 ▸ HEC_HMS_DSS_Gauge.py
         - For each .gage file:
            • Tracks current gauge name and Variant block.
            • Sets Bairabi gauge dates from discharge CSV.
            • Sets all other gauges from precipitation CSV.
         ≈ 2 s

Step 8 ▸ Run_All_HEC_HMS.exe  (subprocess launched by Daily_Forecast_Runner.py)
         - Internally calls hec-hms.exe -script Run_<n>day.py × 4
         - Each Run_<n>day.py opens its .hms project and runs the 'Cal' simulation.
         - Outputs simulated discharge into Cal.dss within each project.
         ≈ 30–70 s
```

### Phase 3 — Hybrid GRU + Stage + Bulletin (4 steps)

```
Step 9 ▸ CSV_Creation_For_HEC_HMS_GRU.py
         - Dynamically builds DSS pathname: //OUTLET/FLOW/31May2017 - <last>/1DAY/RUN:CAL/
         - Reads simulated Q from Cal.dss.
         - Merges with bias-corrected met (precip, tmin, tmax, srad) and observed Q.
         - Writes: Bias Corrected Data/HEC-HMS-GRU/HEC-HMS-GRU ECMWF_<step>_BiasCorrected (Ensemble).csv
         ≈ 3 s

Step 10 ▸ Hybrid_HEC_HMS_GRU_Final_Prediction.py
         - Registers Keras Orthogonal initializer (for older-TF model compat).
         - For each lead time:
            • Builds 15-step sliding windows.
            • Loads (scaler_X, scaler_y) and Keras GRU model.
            • Predicts → inverse-transforms → saves Date+Predicted.
         - Writes: Hybrid Results/Predictions_GRU_<n>day.csv
         ≈ 10–17 s

Step 11 ▸ DischargeToStage_Conversion_GRU.py
         - For each lead time:
            • Builds features: Predicted, Predicted_Lag1, DayOfYear.
            • Loads XGBoost stage-residual model.
            • Adds predicted residual to Predicted (now meaning stage in m).
         - Writes: Hybrid Results/Stage Results/Predictions_Stage_XGBoost_<n>day.csv
         ≈ 2–3 s

Step 12 ▸ Results_Hybrid_HEC_HMS_GRU.py
         - Computes NSE, RMSE, MAE, RMSLE, PBIAS, RSR per lead time.
         - Classifies latest forecast stage into 5-tier danger level.
         - Writes: Hybrid Results/ECMWF_Streamflow_Forecast_Summary.txt
         ≈ 2 s
```

---

## 3. The Bulletin

A typical output bulletin (`ECMWF_Streamflow_Forecast_Summary.txt`) looks like:

```
1 to 7 Day Lead Streamflow Forecast Based on ECMWF Ensemble:
2026-05-23 - Discharge: 67.812345 m^3/s & Stage: 12.847 m | Danger Level: Watch  (1 Day Lead Forecast for 2026-05-22)
2026-05-25 - Discharge: 84.523412 m^3/s & Stage: 13.745 m | Danger Level: Warning (3 Day Lead Forecast for 2026-05-22)
2026-05-27 - Discharge: 92.118203 m^3/s & Stage: 14.011 m | Danger Level: Warning (5 Day Lead Forecast for 2026-05-22)
2026-05-29 - Discharge: 88.412095 m^3/s & Stage: 13.892 m | Danger Level: Warning (7 Day Lead Forecast for 2026-05-22)

Performance evaluation based on observed discharge from 2017-05-31 to 2022-12-31

----------------------------------------------------------------
Lead         NSE       RMSE        MAE      RMSLE        PBIAS        RSR
----------------------------------------------------------------
1-Day      0.7700    20.4100    12.0500    0.4800       0.2500     0.4795
3-Day      0.7630    20.5200    12.2800    0.4900      -0.9300     0.4870
5-Day      0.7440    21.3200    12.8500    0.5100      -1.2800     0.5060
7-Day      0.7350    21.6900    13.0700    0.5300      -0.6300     0.5148
----------------------------------------------------------------

Danger Level Classification Thresholds (Stage in metres):
Lead     Normal (<50th)      Watch (50–75th)     Warning (75–90th)    Severe Warn (90–95th)    Extreme Danger (>95th)
1 day    < 11.454            11.454 – 12.794     12.794 – 13.961      13.961 – 14.585          > 14.585
3 day    < 11.551            11.551 – 12.889     12.889 – 14.022      14.022 – 14.433          > 14.433
5 day    < 11.531            11.531 – 12.883     12.883 – 14.111      14.111 – 14.657          > 14.657
7 day    < 11.470            11.470 – 12.915     12.915 – 14.040      14.040 – 14.514          > 14.514
```

This file (along with a structured Excel bulletin produced by IWRD operators) is then disseminated to:

- District Disaster Management Authorities (DDMAs)
- State Emergency Operation Centres (SEOCs)
- Internal IWRD officers

---

## 4. Five-Tier Danger Level Classification (Unified across G2G + Medium-Term)

| Tier | Percentile range | Stage range (Bairabi, m, mean) | Operational meaning |
|---|---|---|---|
| **Normal** | < P50 | < 11.5 | No flood risk; baseline monitoring |
| **Watch** | P50 – P75 | 11.5 – 12.9 | Water rising; routine watch |
| **Warning** | P75 – P90 | 12.9 – 14.0 | Preparedness; pre-positioning of supplies |
| **Severe Warning** | P90 – P95 | 14.0 – 14.6 | Evacuation planning; advisories |
| **Extreme Danger** | ≥ P95 | > 14.6 | Emergency action; full mobilisation |

The use of a single set of communicated thresholds across all four ARISE forecast horizons (1, 3, 5, 7 day) — despite tiny ~0.1–0.2 m differences in raw percentile values — is a deliberate design choice for operational clarity: a duty officer should not need to interpret different threshold tables per lead time.

---

## 5. Error Handling and Logging

- `Daily_Forecast_Runner.run_module()` wraps every module call in try/except. A failure in one module is logged in red but does **not** abort the pipeline; subsequent modules continue with whatever inputs are available.
- All events (start, completed, errors) are written to `forecast_run_log.txt` with `[YYYY-MM-DD HH:MM:SS]` prefixes.
- The console additionally uses `colorama` colours:
  - **Blue** — module start
  - **Green** — module completed
  - **Red** — exception
  - **Cyan** — forecast cycle start/end
  - **Yellow** — scheduler messages

Example log excerpt (real run, 2025-11-21):
```
[2025-11-21 08:30:46] Forecast started.
[2025-11-21 08:30:46] Running: New_ECMWF_Ensemble_Forecast_15Days_Lead
[2025-11-21 08:31:37] Completed: New_ECMWF_Ensemble_Forecast_15Days_Lead
[2025-11-21 08:31:39] Running: Tigge_EnsembleForecast_Extraction_HECHMSML
[2025-11-21 08:31:51] Completed: Tigge_EnsembleForecast_Extraction_HECHMSML
...
[2025-11-21 08:34:16] Forecast execution completed.
```

See [`examples/sample_forecast_run_log.txt`](../examples/sample_forecast_run_log.txt) for full multi-day logs.

---

## 6. Manual Re-Runs and Partial Pipelines

Operators occasionally need to:
- **Re-run a single failed stage.** Each module's `__main__` block allows direct invocation, e.g. `python src/Bias_Corrected_Data_all.py`.
- **Re-run with a corrected ECMWF date.** Edit the `start_date` line in `New_ECMWF_Ensemble_Forecast_15Days_Lead.py` or temporarily delete entries from `tp_Step_1day.csv` to roll back the auto-detected anchor date.
- **Test the danger-level classification with synthetic stages.** Import `classify_danger_level()` from `Results_Hybrid_HEC_HMS_GRU.py` and call directly:
  ```python
  from Results_Hybrid_HEC_HMS_GRU import classify_danger_level
  classify_danger_level(13.8, lead_days=3)  # → 'Warning'
  ```
