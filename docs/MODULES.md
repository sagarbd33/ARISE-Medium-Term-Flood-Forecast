# MODULES.md — Source Code Reference

This document describes each Python module in `src/`, its purpose, inputs, outputs, internal logic, and any operational caveats.

The modules are listed in execution order (as orchestrated by `Daily_Forecast_Runner.py`).

---

## Master Orchestrator

### `Daily_Forecast_Runner.py`

**Purpose:** Daily scheduler that runs the full ARISE Medium-Term pipeline at 08:30 IST every day.

**Key features:**
- Suppresses TensorFlow oneDNN warnings and Python `UserWarning` / `FutureWarning`.
- Uses `colorama` for colour-coded console output: blue (running), green (completed), red (error), cyan (overall start/end).
- Writes timestamped entries to `forecast_run_log.txt`.
- Two execution phases separated by the HEC-HMS Jython executable:
  - **Phase 1** — 7 Python modules (ECMWF → bias correction → DSS write).
  - **`Run_All_HEC_HMS.exe`** — runs four `.hms` projects via Jython.
  - **Phase 2** — 4 Python modules (GRU correction → stage conversion → results).
- Wraps each module in try/except to keep the pipeline running even if one stage fails.
- Inserts a 2-second sleep between modules to avoid file-lock races on shared CSVs.

**Schedule:** `schedule.every().day.at("08:30:00").do(run_forecast)`. The wait loop logs a status line every 60 seconds.

**Inputs:** None directly — invokes 11 other modules.

**Outputs:** `forecast_run_log.txt` (run trace), plus all downstream artefacts of the called modules.

---

## Phase 1 — Meteorological Acquisition & Pre-Processing

### `New_ECMWF_Ensemble_Forecast_15Days_Lead.py`

**Purpose:** Downloads the latest ECMWF TIGGE ensemble forecast GRIB file.

**Key features:**
- Reads `tp_Step_1day.csv` to determine the last bias-corrected date in storage; this becomes the `start_date` for the new request.
- `end_date = today − 2 days` (TIGGE has ~36 h release latency).
- Deletes any existing `output_Ensemble_7Days_Lead(ECMWF)_AutoDate.grib` and accompanying `.idx` index file before requesting new data.
- **Interactive credential prompt** — URL (with default), API Key, Email are requested at every run; no credentials are persisted in source.
- Submits a TIGGE retrieval request with:
  - `dataset = "tigge"`, `origin = "ecmf"`, `type = "pf"` (perturbed forecast)
  - 50 ensemble members (`number = 1..50`)
  - Forecast steps: `24/48/72/96/120/144/168` h
  - Parameters: `121` (mn2t6), `122` (mx2t6), `176` (ssr), `228228` (tp)
  - Grid: `0.5°/0.5°`, area: `24.6/91.7/21.7/94.3` (Tlawng basin bounding box)
  - Time of day: `00:00:00`

**Inputs:** existing `tp_Step_1day.csv`; user-typed ECMWF credentials.

**Outputs:** `output_Ensemble_7Days_Lead(ECMWF)_AutoDate.grib`.

---

### `Tigge_EnsembleForecast_Extraction_HECHMSML.py`

**Purpose:** Extracts ensemble-mean meteorological variables from the GRIB file at 12 station locations.

**Key features:**
- Opens GRIB with `cfgrib` + `xarray`.
- Verifies required variables present: `tp`, `mx2t6`, `mn2t6`, `ssr`.
- Computes ensemble mean across `number` dimension (`ds.mean(dim='number', skipna=True)`).
- Loads station metadata from `Rainfall_Lat_Lon.csv`; finds nearest grid point per station via Euclidean distance in lat-lon space.
- **Unit conversions** applied to each station's extracted slice:
  - `mx2t6 -= 273.15` and `mn2t6 -= 273.15` (Kelvin → °C)
  - `ssr /= 86_400_000` (W/m²·s → kWh/m²/day)
  - Average temperature: `At = (mx2t6 + mn2t6) / 2`
- **Step-wise delta computation** — TIGGE precipitation and radiation are cumulative from forecast initialisation, so `Step_3day` value is calculated as `tp[step3] − tp[step1]`, etc.
- Writes one CSV per variable per step into `Stepwise_Combined_CSVs_Ensemble_Mean/`, e.g. `tp_Step_3day.csv`, `mx2t6_Step_5day.csv`.
- **Append-only update** — existing CSVs are read, new rows merged on `Date`, duplicates dropped (keeping first), result re-sorted and written back.
- Negative precipitation values are clipped to 0.

**Inputs:** GRIB file; `Rainfall_Lat_Lon.csv` (12 stations: Aizawl, Sialsuk, Neihbawi, Kolasib, Thingdawl, Lunglei, Hnahthial, Haulawng, Mamit, kawrtethawveng, Zawlnuam, Serchhip).

**Outputs:** Station-wise CSVs in `Stepwise_Combined_CSVs_Ensemble_Mean/` for each `{tp, At, ssr, mx2t6, mn2t6} × {1day, 3day, 5day, 7day}` combination.

---

### `Forecast_Weightage_Calculations.py`

**Purpose:** Aggregates station-level meteorological data to 12 sub-watersheds using **Thiessen polygon area weights** (derived once in ArcGIS from the 12-station Thiessen tessellation overlaid on the sub-watershed delineation).

**Key features:**
- Iterates over every CSV in `Stepwise_Combined_CSVs_Ensemble_Mean/`.
- Renames `valid_time` → `Date` if present.
- Applies hard-coded area-weight formulas for `Sub1..Sub12`. For example:
  ```
  Sub1 = (210.7367526·Haulawng + 3.964544686·Hnahthial
        + 3.821651695·Zawlnuam + 132.9233174·Lunglei
        + 71.71401451·Sialsuk) / 423.1602809
  ```
  Each numerator coefficient is the area (km²) of overlap between the station's Thiessen polygon and that sub-watershed; the denominator is the total sub-watershed area.
- Sub9 and Sub12 are entirely within the Kolasib polygon, hence `Sub9 = Sub12 = Kolasib`.
- Computes basin-wide `Avg = mean(Sub1..Sub12)`.
- Saves to `Stepwise_Combined_CSVs_Ensemble_Mean/Weightage/<filename>_weightage.csv`.

**Inputs:** All station-wise step-wise CSVs from previous step.

**Outputs:** Sub-watershed-aggregated CSVs in `Weightage/`.

> **Note for replication:** The hard-coded weights are basin-specific. To deploy elsewhere, recompute Thiessen polygon × sub-watershed area intersections in GIS and replace the coefficients.

---

### `Bias_Corrected_Data_all.py`

**Purpose:** Applies pre-trained XGBoost bias-correction models to all 5 meteorological variables for 4 lead times.

**Key features:**
- Loops over 5 categories: `Average Temp`, `Total Precipitation`, `Min Temp`, `Max Temp`, `Solar Radiation`.
- For each category × lead time × column (sub-watershed or station), loads a `.pkl` XGBoost model from `Bias Correction Model (XGBoost)/`.
- Features used at inference (matching training): `Forecast`, `Forecast_Lag1`, `DayOfYear`.
- Prediction is the **bias residual**; the corrected value is `Forecast + bias_pred`.
- For precipitation, applies `clip(lower=0)` to prevent physically impossible negative rainfall after correction.
- Total of **84 models loaded per run**: 4 lead times × (12 sub-watersheds for Avg Temp + 13 station/avg cols for precip + 1 avg col each for min/max temp + 1 for solar = 21 columns).
- Output structure mirrors input: `Bias Corrected Data/<Category>/<filename>.csv`.

**Inputs:** Sub-watershed weightage CSVs; pre-trained models in `Bias Correction Model (XGBoost)/`.

**Outputs:** Bias-corrected CSVs in `Bias Corrected Data/`.

> **Model file naming convention:** `{lead}day_{col}_Tuned_XGBoost_BiasCorrection.pkl` (per-station for precip and temperature; Avg-only for min temp, max temp, and solar).

---

## Phase 2 — HEC-HMS Hydrological Simulation

### `HEC_HMS_DSS.py`

**Purpose:** Writes bias-corrected precipitation, temperature, and observed discharge into HEC-DSS time-series files for each of the four forecast horizons.

**Key features:**
- Uses **`pydsstools`** (HEC-DSS Python interface) — Windows-only binary.
- Reads observed discharge once from `Observed Discharge/Discharge Obs.csv` (column `Bairabi`).
- For each step (1/3/5/7 day) writes three pathname classes to the corresponding `.dss` file:
  - **Precipitation:** `//<STATION>/PRECIP-INC/<startDate>/1DAY/GAGE/`, type `PER-CUM`, units `MM`, interval 1440 min.
  - **Temperature:** `//SUB<i>/TEMPERATURE/<startDate>/1DAY/GAGE/`, type `PER-AVER`, units `C`.
  - **Discharge:** `//BAIRABI/FLOW/<startDate>/1DAY/GAGE/`, type `INST-VAL`, units `CMS`.
- Calls `fid.deletePathname(pathname)` before each `put_ts` to avoid duplicate entries.

**Inputs:** Bias-corrected precipitation (12 stations) and temperature (12 sub-watersheds); observed discharge.

**Outputs:** `1Day_Forecast.dss`, `3Day_Forecast.dss`, `5Day_Forecast.dss`, `7Day_Forecast.dss`.

---

### `HEC_HMS_DSS_Calibration.py`

**Purpose:** Updates the `Calibration.control` file inside each `<n>Day_Forecast` folder with the actual start/end dates of the corresponding precipitation CSV.

**Key features:**
- Date formatting uses Windows-only `%#d` (no leading zero) — e.g. `7 June 2026, 00:00`.
- Reads `Calibration.control` line-by-line, rewrites only the four lines: `Start Date:`, `Start Time:`, `End Date:`, `End Time:`.
- Preserves all other lines (basin/model linkage, time step, output flags).

**Inputs:** Bias-corrected `tp_Step_<n>day.csv`; existing `.control` files.

**Outputs:** Modified `.control` files in-place (no backup).

---

### `HEC_HMS_DSS_Gauge.py`

**Purpose:** Updates the `.gage` file (DSS-linked gauge metadata) for each forecast project so that variant blocks reference the correct date range.

**Key features:**
- Cross-platform `format_date()` helper handles `%#d` on Windows and `%-d` on POSIX.
- Loads observed-discharge date range once; loads precipitation date range per step.
- Parses `.gage` line-by-line tracking the current gauge name and whether parsing is inside a `Variant:` ... `End Variant:` block.
- Special-cases the Bairabi gauge (discharge dates); all other gauges receive precipitation dates.

**Inputs:** Bias-corrected `tp_Step_<n>day.csv`; observed discharge; existing `.gage` files.

**Outputs:** Modified `.gage` files in-place.

---

### `Run_All_HEC_HMS.py`

**Purpose:** Driver script (compiled to `Run_All_HEC_HMS.exe`) that invokes the HEC-HMS Jython engine for each of the four `.hms` projects.

**Key features:**
- Uses `subprocess.run` with `shell=True` and `cwd = HEC-HMS install dir`.
- Command pattern: `"<HEC-HMS-4.10>\hec-hms.exe" -script "Run_<n>day.py"`.
- Captures stdout/stderr and prints success or failure per simulation.

**Why a separate compiled executable?** HEC-HMS 4.10 ships its own embedded Jython environment which is incompatible with CPython at runtime. Wrapping the Jython call in a child process via this driver keeps the main Python ecosystem clean.

### `Run_1day.py`, `Run_3day.py`, `Run_5day.py`, `Run_7day.py`

Each script is run inside HEC-HMS's Jython interpreter:

```python
from hms.model import Project
from hms import Hms

myProject = Project.open('C:/.../<n>Day_Forecast/<n>Day_Forecast.hms')
myProject.computeRun('Cal')   # Cal = pre-defined simulation name
myProject.close()
Hms.shutdownEngine()
```

**Important:** These scripts use HEC-HMS's `hms.*` API (Jython-only). They will not execute under CPython.

---

## Phase 3 — Hybrid GRU Correction & Stage Conversion

### `CSV_Creation_For_HEC_HMS_GRU.py`

**Purpose:** Builds the multivariate training/inference CSV that the GRU model consumes.

**Key features:**
- For each forecast horizon, dynamically constructs the DSS pathname:
  ```
  //OUTLET/FLOW/31May2017 - <last_date_str>/1DAY/RUN:CAL/
  ```
  The end date is `last_date_of_precip_csv - 1 day` (string-formatted as e.g. `31Dec2024`).
- Reads simulated discharge from `Cal.dss` via `pydsstools`.
- Merges, for each step's CSV: precipitation `Avg`, `tmin Avg`, `tmax Avg`, `srad Avg`, simulated Q, observed Q (column `Bairabi`).
- Final column order matches GRU training expectation; last column is the target (observed Q).

**Outputs:** `HEC-HMS-GRU ECMWF_<step>_BiasCorrected (Ensemble).csv` in `Bias Corrected Data/HEC-HMS-GRU/`.

---

### `Hybrid_HEC_HMS_GRU_Final_Prediction.py`

**Purpose:** Runs the four trained GRU models (one per lead time) on the prepared CSVs.

**Key features:**
- Registers the Keras `Orthogonal` initializer with `get_custom_objects()` (required when loading models trained on older TF versions).
- Sequence preparation: a sliding window of **`n_steps = 15`** days; features are all columns except the last; target is the last column at `end_ix - 1`.
- Loads scalers (X and y) from a single pickle with `encoding='latin1'` for cross-version compatibility.
- Inverse-transforms predictions to original discharge units (m³/s).
- Saves predictions with `Date` and `Predicted` columns to `Hybrid Results/Predictions_GRU_<n>day.csv`.

**Pre-trained model files:**
- `{n}day_Model_GRU.keras` — Keras saved-model format
- `{n}day_Scaler_GRU.pkl` — `(scaler_X, scaler_y)` tuple

---

### `DischargeToStage_Conversion_GRU.py`

**Purpose:** Converts predicted discharge to river stage at the Bairabi gauge using a pre-trained XGBoost model per lead time.

**Key features:**
- Loads pre-trained models named `{n}day_Tuned_XGBoost.pkl`.
- Features replicate training: `Predicted` (current Q), `Predicted_Lag1` (yesterday's Q), `DayOfYear`.
- The XGBoost model predicts a **residual** which is added to `Predicted` to give the final value.

> Variable name caveat — the script reuses `Predicted` as both input discharge and output stage column. Downstream `Results_Hybrid_HEC_HMS_GRU.py` interprets the output column as stage (m), discharging the dual meaning.

**Outputs:** `Stage Results/Predictions_Stage_XGBoost_<n>day.csv`.

---

### `Results_Hybrid_HEC_HMS_GRU.py`

**Purpose:** Computes performance metrics, applies the five-tier danger-level classification, and writes the daily flood bulletin.

**Key features:**

- Hard-coded **danger-level thresholds** per lead time (95th-percentile-derived):

  ```python
  DANGER_THRESHOLDS = {
      1: {"Normal": 11.454, "Watch": 12.794, "Warning": 13.961, "Severe Warning": 14.585},
      3: {"Normal": 11.551, "Watch": 12.889, "Warning": 14.022, "Severe Warning": 14.433},
      5: {"Normal": 11.531, "Watch": 12.883, "Warning": 14.111, "Severe Warning": 14.657},
      7: {"Normal": 11.470, "Watch": 12.915, "Warning": 14.040, "Severe Warning": 14.514},
  }
  ```

  Anything ≥ Severe Warning threshold is classified as **Extreme Danger**.

- Computes six metrics for each lead time using observed-vs-predicted discharge:
  **NSE, RMSE, MAE, RMSLE, PBIAS, RSR**.

- Constructs the bulletin header:
  ```
  1 to 7 Day Lead Streamflow Forecast Based on ECMWF Ensemble:
  ```
  followed by lines like:
  ```
  2026-05-25 - Discharge: 84.523412 m^3/s & Stage: 13.745 m | Danger Level: Warning (3 Day Lead Forecast for 2026-05-22)
  ```

- Writes the full bulletin (predictions + metrics table + threshold legend) to:
  ```
  Hybrid Results/ECMWF_Streamflow_Forecast_Summary.txt
  ```

**Inputs:** Predictions from previous two steps + observed discharge.

**Outputs:** `ECMWF_Streamflow_Forecast_Summary.txt`.

---

## Data Files

### `Rainfall_Lat_Lon.csv`

Coordinates of the 12 IWRD meteorological stations used throughout the pipeline:

| # | Station | Lat | Lon |
|---|---|---|---|
| 1 | Aizawl | 23.72963 | 92.71692 |
| 2 | Sialsuk | 23.39851 | 92.74931 |
| 3 | Neihbawi | 23.83338 | 92.74357 |
| 4 | Kolasib | 24.22473 | 92.67724 |
| 5 | Thingdawl | 23.63461 | 92.722 |
| 6 | Lunglei | 22.89051 | 92.74385 |
| 7 | Hnahthial | 22.96554 | 92.92777 |
| 8 | Haulawng | 23.05182 | 92.77177 |
| 9 | Mamit | 23.91605 | 92.48445 |
| 10 | kawrtethawveng | 23.87045 | 92.37453 |
| 11 | Zawlnuam | 24.13378 | 92.33922 |
| 12 | Serchhip | 23.34311 | 92.85069 |

---

## Runtime Profile

From `examples/sample_forecast_run_log.txt` (real operational run, 21 Nov 2025):

| Module | Wall-clock duration |
|---|---|
| `New_ECMWF_Ensemble_Forecast_15Days_Lead` | ~50 s (network-bound) |
| `Tigge_EnsembleForecast_Extraction_HECHMSML` | ~10 s |
| `Forecast_Weightage_Calculations` | ~6 s |
| `Bias_Corrected_Data_all` | ~8 s |
| `HEC_HMS_DSS` | ~3–7 s |
| `HEC_HMS_DSS_Calibration` | ~2 s |
| `HEC_HMS_DSS_Gauge` | ~2 s |
| `Run_All_HEC_HMS.exe` | ~30–70 s |
| `CSV_Creation_For_HEC_HMS_GRU` | ~3 s |
| `Hybrid_HEC_HMS_GRU_Final_Prediction` | ~10–17 s |
| `DischargeToStage_Conversion_GRU` | ~2–3 s |
| `Results_Hybrid_HEC_HMS_GRU` | ~2 s |
| **Total** | **~2–4 min per daily cycle** |
