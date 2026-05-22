# DATA.md — Data Sources, Formats, and Directory Conventions

This document describes every data file the ARISE Medium-Term Sub-System reads or writes.

---

## 1. External Data Sources

| Source | Provider | URL | Licence | Variable(s) |
|---|---|---|---|---|
| **TIGGE ECMWF ensemble** | ECMWF | https://confluence.ecmwf.int/display/TIGGE | Open research | tp, mx2t6, mn2t6, ssr |
| **CWC discharge** | Central Water Commission, India | (restricted) | Restricted; access requires CWC HQ consent | Daily discharge at Bairabi, Reiek-kai |
| **IWRD station precipitation** | Irrigation and Water Resources Department, Mizoram | (institutional) | Restricted | Daily precipitation at 12 stations |
| **CPC temperature** | NOAA Climate Prediction Center | https://psl.noaa.gov/data/gridded/data.cpc.globaltemp.html | Open | Daily min/max temperature |
| **ERA5 reanalysis** | Copernicus C3S | https://cds.climate.copernicus.eu/ | Open | Solar radiation |
| **DEM** | USGS Earth Explorer | https://earthexplorer.usgs.gov/ | Open | Topography |
| **LULC** | Esri Sentinel-2 Land Cover Explorer | https://livingatlas.arcgis.com/landcoverexplorer | Open | Land cover |
| **Soil texture** | IWRD | (institutional) | Restricted | Soil texture map |

---

## 2. Directory Layout (Runtime / Installed)

```
C:\Users\Medium Term Flood Forecast\
│
├── ARISE - Medium Term Flood Forecast.exe   ← PyInstaller bundle
├── Run_All_HEC_HMS.exe                      ← HEC-HMS Jython driver
├── _internal\                               ← PyInstaller runtime
├── Run_1day.py / Run_3day.py / Run_5day.py / Run_7day.py
├── Rainfall_Lat_Lon.csv
├── forecast_run_log.txt                     ← Run history
│
├── ECMWF_Ensemble\
│   └── output_Ensemble_7Days_Lead(ECMWF)_AutoDate.grib   ← Latest GRIB
│
├── HEC-HMS\
│   ├── HEC-HMS-4.10\                        ← Bundled engine
│   ├── 1Day_Forecast\
│   │   ├── 1Day_Forecast.hms
│   │   ├── 1Day_Forecast.basin
│   │   ├── 1Day_Forecast.gage
│   │   ├── 1Day_Forecast.dss
│   │   ├── Calibration.control
│   │   ├── Cal.dss
│   │   └── …
│   ├── 3Day_Forecast\                       ← Same structure
│   ├── 5Day_Forecast\                       ← Same structure
│   └── 7Day_Forecast\                       ← Same structure
│
└── Stepwise_Combined_CSVs_Ensemble_Mean\
    │
    ├── tp_Step_1day.csv                     ← Raw step-wise CSV (precipitation)
    ├── tp_Step_3day.csv
    ├── tp_Step_5day.csv
    ├── tp_Step_7day.csv
    ├── At_Step_*.csv                        ← Average temperature
    ├── mn2t6_Step_*.csv                     ← Min temperature
    ├── mx2t6_Step_*.csv                     ← Max temperature
    ├── ssr_Step_*.csv                       ← Solar radiation
    │
    ├── Weightage\                           ← Sub-watershed weighted CSVs
    │   ├── tp_Step_1day_weightage.csv
    │   └── …
    │
    ├── Bias Correction Model (XGBoost)\
    │   ├── Average Temp\
    │   │   ├── 1day_Sub1_Tuned_XGBoost_BiasCorrection.pkl
    │   │   └── …  (48 total: 4 leads × 12 sub-watersheds)
    │   ├── Total Precipitation\
    │   │   ├── 1day_Aizawl_Tuned_XGBoost_BiasCorrection.pkl
    │   │   └── …  (52 total: 4 leads × 13 cols)
    │   ├── Min Temp\
    │   │   └── 1day_Avg_Tuned_XGBoost_BiasCorrection.pkl  (4 total)
    │   ├── Max Temp\
    │   │   └── …  (4 total)
    │   └── Solar Radiation\
    │       └── …  (4 total)
    │
    ├── Bias Corrected Data\
    │   ├── Average Temp\
    │   ├── Total Precipitation\
    │   ├── Min Temp\
    │   ├── Max Temp\
    │   ├── Solar Radiation\
    │   └── HEC-HMS-GRU\
    │       ├── HEC-HMS-GRU ECMWF_1day_BiasCorrected (Ensemble).csv
    │       ├── HEC-HMS-GRU ECMWF_3day_BiasCorrected (Ensemble).csv
    │       ├── HEC-HMS-GRU ECMWF_5day_BiasCorrected (Ensemble).csv
    │       ├── HEC-HMS-GRU ECMWF_7day_BiasCorrected (Ensemble).csv
    │       ├── 1-3-5-7 Day HEC-HMS-GRU Model\
    │       │   ├── 1day_Model_GRU.keras
    │       │   ├── 1day_Scaler_GRU.pkl
    │       │   ├── 3day_Model_GRU.keras
    │       │   └── …
    │       └── Hybrid Results\
    │           ├── Predictions_GRU_1day.csv
    │           ├── Predictions_GRU_3day.csv
    │           ├── Predictions_GRU_5day.csv
    │           ├── Predictions_GRU_7day.csv
    │           ├── ECMWF_Streamflow_Forecast_Summary.txt   ← Daily bulletin
    │           ├── 1-3-5-7 Day Stage XGBoast Model\
    │           │   ├── 1day_Tuned_XGBoost.pkl
    │           │   ├── 3day_Tuned_XGBoost.pkl
    │           │   ├── 5day_Tuned_XGBoost.pkl
    │           │   └── 7day_Tuned_XGBoost.pkl
    │           └── Stage Results\
    │               ├── Predictions_Stage_XGBoost_1day.csv
    │               ├── Predictions_Stage_XGBoost_3day.csv
    │               ├── Predictions_Stage_XGBoost_5day.csv
    │               └── Predictions_Stage_XGBoost_7day.csv
    │
    └── Observed Discharge\
        └── Discharge Obs.csv                ← columns: Date, Bairabi[, Reiek-kai]
```

---

## 3. Key File Formats

### 3.1 `Rainfall_Lat_Lon.csv`

```csv
Points,Stations,Lat,Lon
1,Aizawl,23.72963,92.71692
2,Sialsuk,23.39851,92.74931
...
```

Required columns: **Points, Stations, Lat, Lon** (latitude in decimal degrees, +N; longitude in decimal degrees, +E).

### 3.2 Step-wise meteorological CSVs

```csv
Date,Aizawl,Sialsuk,Neihbawi,Kolasib,Thingdawl,Lunglei,Hnahthial,Haulawng,Mamit,kawrtethawveng,Zawlnuam,Serchhip
2017-05-31,0.0,0.0,0.0,...
2017-06-01,12.3,8.7,15.2,...
```

- **Date** in `YYYY-MM-DD` (ISO 8601).
- One column per station (precipitation, max/min temp, solar) or per sub-watershed (after Weightage step: Sub1..Sub12 + Avg).
- Precipitation is **mm/day** (step-wise cumulative subtracted in extraction).
- Temperature is **°C** (Kelvin converted in extraction).
- Solar radiation is **kWh/m²/day**.

### 3.3 Bias-corrected CSVs

Same schema as step-wise CSVs, but rows whose lag input was missing have been dropped via `df.dropna()`. Precipitation values are always ≥ 0.

### 3.4 GRU input CSV (`HEC-HMS-GRU ECMWF_<step>_BiasCorrected (Ensemble).csv`)

```csv
Date,precip,tmin,tmax,srad,simdischarge,discharge
2017-05-31,15.2,18.1,28.4,5.3,42.6,38.7
2017-06-01,...
```

- **precip** = `Avg` from precipitation weightage CSV.
- **tmin / tmax** = `Avg` from min/max temperature weightage CSVs.
- **srad** = `Avg` from solar radiation weightage CSV.
- **simdischarge** = HEC-HMS simulated outflow at Bairabi (from `Cal.dss`, pathname `//OUTLET/FLOW/...`).
- **discharge** = observed Bairabi flow (the GRU target).

### 3.5 Prediction CSVs

`Predictions_GRU_<n>day.csv`:
```csv
Date,Predicted
2017-06-15,46.823
...
```
The `Predicted` column is **discharge in m³/s**.

`Predictions_Stage_XGBoost_<n>day.csv`:
```csv
Date,Predicted
2017-06-15,12.847
...
```
Here the `Predicted` column is **stage in metres** (the script overwrites the discharge column with the converted stage).

### 3.6 HEC-HMS Files (`.dss`, `.control`, `.gage`)

These are proprietary HEC binary/text formats. The relevant lines modified by ARISE scripts are:

- **`.control` (text)**:
  ```
       Start Date: 31 May 2017
       Start Time: 00:00
       End Date: 30 December 2025
       End Time: 00:00
  ```
- **`.gage` (text, within Variant blocks)**:
  ```
       Variant: Variant-1
         ...
         Start Time: 31 May 2017, 00:00
         End Time: 30 December 2025, 00:00
         ...
       End Variant: Variant-1
  ```
- **`.dss` (binary, HEC-DSS)**: time series are written via `pydsstools` with `TimeSeriesContainer` and pathnames of the form `//<STATION>/<PARAMETER>/<startDateUC>/1DAY/GAGE/`.

### 3.7 Daily Bulletin (`ECMWF_Streamflow_Forecast_Summary.txt`)

See [`WORKFLOW.md §3`](WORKFLOW.md) for a full annotated example.

Structure:
1. **Header line** — `1 to 7 Day Lead Streamflow Forecast Based on ECMWF Ensemble:`
2. **Four forecast lines** — one per lead time, each with date, discharge (m³/s), stage (m), and danger level.
3. **Validation period** — date range of observed discharge used for metric computation.
4. **Metrics table** — NSE, RMSE, MAE, RMSLE, PBIAS, RSR per lead time.
5. **Threshold legend** — per-lead-time stage thresholds for each danger tier.

---

## 4. Excluded from Git

The following are deliberately not committed (see `.gitignore`):

- `.grib` / `.grib.idx` — ECMWF binary downloads
- `.dss` — HEC-DSS time-series databases
- `.h5` / `.hdf5` / `.keras` — Trained neural network weights (host on Releases)
- `.pkl` — Trained XGBoost models and scalers (host on Releases)
- `*.exe` — Compiled binaries (host on Releases)
- `forecast_run_log.txt` — Runtime log (`examples/sample_forecast_run_log.txt` is provided instead)
- `Stepwise_Combined_CSVs_Ensemble_Mean/`, `ECMWF_Ensemble/`, `HEC-HMS/` — Operational output directories

For access to trained models and HEC-HMS project files, please contact the corresponding author.
