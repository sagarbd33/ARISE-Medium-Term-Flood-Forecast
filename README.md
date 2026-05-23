# ARISE: Automated River Intelligence System for Early-Warning
### Medium-Term Flood Forecast Sub-System (3-, 5-, and 7-day lead times)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)](#)
[![Version](https://img.shields.io/badge/version-2.1.0-green.svg)](#)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20356274.svg)](https://doi.org/10.5281/zenodo.20356274)
[![Status](https://img.shields.io/badge/status-operational-brightgreen.svg)](#)

---

## 1. Overview

**ARISE** is an automated hybrid flood forecasting and early-warning system, operationally deployed in the **Tlawng River Basin, Mizoram, Northeast India**, under the **World Bank-funded National Hydrology Project (NHP)**, in coordination with the **Irrigation and Water Resources Department (IWRD), Government of Mizoram**.

ARISE comprises two sub-systems sharing a unified five-tier danger-level classification:

| Sub-system | Lead time | Driver | Code in this repo |
|---|---|---|---|
| **G2G (Gauge-to-Gauge) Short-Term** | 1 day (24 h) | LSTM on real-time upstream stage (FTP) | *Separate package — not included here* |
| **NWP-Driven Medium-Term** | 3, 5, 7 days | ECMWF ensemble + XGBoost bias correction + HEC-HMS + GRU + XGBoost stage conversion | ✅ **This repository** |

This repository hosts the source code, installer build files, and supporting documentation for the **NWP-Driven Medium-Term Sub-System**, packaged as the desktop application *ARISE - Medium Term Flood Forecast (v2.1.1)*.

The associated manuscript is currently under review at the *Journal of Hydrology*:

> Debbarma, S., Mandal, S., Bandyopadhyay, A., & Bhadra, A. (under review).
> *ARISE: A Novel Automated Hybrid System for Multi-Timescale Flood Forecasting
> and Operational Early Warning in Northeast India.* **Journal of Hydrology.**

---

## 2. Scientific Highlights

- **Cross-season validation** across 2018, 2024, and 2025 flood events: every Extreme Danger peak was pre-signalled at Warning level or above within each forecast horizon.
- **Forecast accuracy** (Bairabi outlet, Tlawng River):
  - Streamflow NSE: **0.763 (3-day)**, **0.744 (5-day)**, **0.735 (7-day)** with PBIAS within ±1.5%.
  - Stage NSE: **0.762 / 0.746 / 0.726** for 3/5/7-day with RMSE 0.78–0.84 m.
- **Bias correction**: 84 station-specific XGBoost models reduce systematic biases — most dramatically for solar radiation (PBIAS −95% → ~0%) and maximum temperature (PBIAS −28% → ~0%).
- **Operational warning window** extended from the existing 12–24 h (CWC national system) to **7 days**.
- Fully automated daily pipeline at **08:30 IST** on a standard Windows computer at IWRD.

---

## 3. Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                  PHASE 1: METEOROLOGICAL ACQUISITION                │
├─────────────────────────────────────────────────────────────────────┤
│  ECMWF TIGGE Portal (51-member ensemble)                            │
│        │                                                            │
│        ▼ [New_ECMWF_Ensemble_Forecast_15Days_Lead.py]               │
│  Download GRIB (params 121/122/176/228228; steps 24..168 h;         │
│                 area 24.6/91.7/21.7/94.3)                           │
│        │                                                            │
│        ▼ [Tigge_EnsembleForecast_Extraction_HECHMSML.py]            │
│  Ensemble mean → 12 station CSVs (unit-converted, step-wise delta)  │
│        │                                                            │
│        ▼ [Forecast_Weightage_Calculations.py]                       │
│  Thiessen-weighted aggregation to 12 sub-watersheds                 │
│        │                                                            │
│        ▼ [Bias_Corrected_Data_all.py]                               │
│  XGBoost bias correction (variable × station × lead time)           │
└─────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 2: HEC-HMS HYDROLOGIC SIM                  │
├─────────────────────────────────────────────────────────────────────┤
│  [HEC_HMS_DSS.py]         → Write bias-corrected data into .dss     │
│  [HEC_HMS_DSS_Calibration.py] → Update .control with new dates      │
│  [HEC_HMS_DSS_Gauge.py]   → Update .gage variant blocks             │
│        │                                                            │
│        ▼ [Run_All_HEC_HMS.exe → Run_1day.py / 3day / 5day / 7day]   │
│  HEC-HMS 4.10 Jython engine runs four projects sequentially         │
└─────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────────┐
│              PHASE 3: HYBRID GRU + STAGE CONVERSION                 │
├─────────────────────────────────────────────────────────────────────┤
│  [CSV_Creation_For_HEC_HMS_GRU.py]                                  │
│  Merge HEC-HMS sim Q + bias-corrected met + observed Q              │
│        │                                                            │
│        ▼ [Hybrid_HEC_HMS_GRU_Final_Prediction.py]                   │
│  GRU residual correction (15-day hindcast window; 4 trained models) │
│        │                                                            │
│        ▼ [DischargeToStage_Conversion_GRU.py]                       │
│  XGBoost: Q + Q_lag1 + DayOfYear → stage (m)                        │
│        │                                                            │
│        ▼ [Results_Hybrid_HEC_HMS_GRU.py]                            │
│  Compute NSE/RMSE/MAE/RMSLE/PBIAS/RSR; classify 5-tier danger;      │
│  write text summary + bulletin                                      │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
        Daily flood bulletin → IWRD / DDMA / SEOC (08:30 IST)
```

All 12 steps above are orchestrated by `Daily_Forecast_Runner.py`, which is scheduled to fire daily at **08:30 IST**.

---

## 4. Repository Structure

```
ARISE-Medium-Term-Flood-Forecast/
│
├── README.md                       ← This file
├── LICENSE                         ← MIT licence
├── CITATION.cff                    ← GitHub "Cite this repository" widget
├── requirements.txt                ← Python dependencies
├── .gitignore                      ← Excludes credentials, big binaries, logs
│
├── src/                            ← All Python source modules (17 files)
│   ├── Daily_Forecast_Runner.py    ← Master scheduler (08:30 IST daily)
│   │
│   ├── New_ECMWF_Ensemble_Forecast_15Days_Lead.py  ← Phase 1, Step 1
│   ├── Tigge_EnsembleForecast_Extraction_HECHMSML.py ← Phase 1, Step 2
│   ├── Forecast_Weightage_Calculations.py          ← Phase 1, Step 3
│   ├── Bias_Corrected_Data_all.py                  ← Phase 1, Step 4
│   │
│   ├── HEC_HMS_DSS.py                              ← Phase 2, Step 5
│   ├── HEC_HMS_DSS_Calibration.py                  ← Phase 2, Step 6
│   ├── HEC_HMS_DSS_Gauge.py                        ← Phase 2, Step 7
│   ├── Run_All_HEC_HMS.py                          ← Phase 2, Step 8 (driver)
│   ├── Run_1day.py / Run_3day.py / Run_5day.py / Run_7day.py ← HEC-HMS Jython
│   │
│   ├── CSV_Creation_For_HEC_HMS_GRU.py             ← Phase 3, Step 9
│   ├── Hybrid_HEC_HMS_GRU_Final_Prediction.py      ← Phase 3, Step 10
│   ├── DischargeToStage_Conversion_GRU.py          ← Phase 3, Step 11
│   ├── Results_Hybrid_HEC_HMS_GRU.py               ← Phase 3, Step 12
│   │
│   └── Rainfall_Lat_Lon.csv                        ← 12 station coordinates
│
├── data/
│   └── Rainfall_Lat_Lon.csv                        ← Reference copy (same)
│
├── installer/                                      ← Build artefacts
│   ├── ARISE_Medium_Term_Flood_Forecast.iss        ← Inno Setup script
│   ├── ARISE - Medium Term Flood Forecast.spec     ← PyInstaller spec (runner)
│   └── Run_All_HEC_HMS.spec                        ← PyInstaller spec (HMS driver)
│
├── examples/
│   └── sample_forecast_run_log.txt                 ← Real operational log
│
└── docs/
    ├── INSTALL.md                                  ← Installation guide
    ├── WORKFLOW.md                                 ← Module-by-module details
    ├── MODULES.md                                  ← Code reference per module
    ├── DEPLOYMENT.md                               ← PyInstaller + Inno Setup
    ├── RELEASES.md                                 ← How/where to host the >2GB installer
    └── DATA.md                                     ← Data sources, formats
```

---

## 5. Quick Start

### 5.1 End-user installation (Windows, operational deployment)

1. Download **`ARISE - Medium Term Flood Forecast Installer.exe`** (≈ 2 GB) from the Zenodo archive: **https://doi.org/10.5281/zenodo.20356274** (v2.1.1).
2. Right-click → **Run as administrator**.
3. The installer auto-deploys Microsoft VC++ Redistributable (x64), the PyInstaller-bundled executable, HEC-HMS project files, pre-trained models, and a desktop shortcut.
4. Installation directory is fixed at **`C:\Users\Medium Term Flood Forecast\`** (paths are hard-coded inside scripts; this constraint will be removed in v3.0).
5. Launch the desktop shortcut. The scheduler starts and idles until 08:30 IST.
6. On the first forecast call, you are prompted to enter your **ECMWF API URL, Key, and Email** interactively. These are not stored; they are requested again on the next run.

> **Why Zenodo and not GitHub?** The installer is > 2 GB (bundles HEC-HMS engine + all DLLs + 84 XGBoost models + 4 GRU models + Python runtime). GitHub Releases caps single files at 2 GB. See [`docs/RELEASES.md`](docs/RELEASES.md) for the full hosting workflow.

### 5.2 Developer setup (from source)

```bash
git clone https://github.com/sagarbd33/ARISE-Medium-Term-Flood-Forecast.git
cd ARISE-Medium-Term-Flood-Forecast

# Create environment (conda is recommended for eccodes)
conda create -n arise python=3.11 -y
conda activate arise
conda install -c conda-forge eccodes -y
pip install -r requirements.txt
```

To run the full daily pipeline (requires HEC-HMS 4.10 on Windows + trained models + observed-discharge CSV + .hms project files):

```bash
python src/Daily_Forecast_Runner.py
```

To run any individual stage in isolation, simply execute its `.py` file — each module has a stand-alone `run()` function plus an `if __name__ == "__main__"` entry point.

Full documentation: see [`docs/INSTALL.md`](docs/INSTALL.md), [`docs/WORKFLOW.md`](docs/WORKFLOW.md), [`docs/MODULES.md`](docs/MODULES.md).

---

## 6. Data and Model Files

The repository contains **source code only**. The following artefacts are required for actual forecasting and are **not redistributed here** due to size and/or institutional data-sharing restrictions:

| Artefact | Size | Source | Distribution |
|---|---|---|---|
| Pre-trained XGBoost bias-correction models (84 `.pkl`) | ~50 MB | Authors | GitHub Release on request |
| Pre-trained GRU models (`.keras`) and scalers (`.pkl`) | ~10 MB | Authors | GitHub Release on request |
| Pre-trained XGBoost stage-conversion models (`.pkl`) | ~5 MB | Authors | GitHub Release on request |
| HEC-HMS 4.10 project files (`.hms`, `.basin`, `.control`, `.gage`, `.dss`) | ~200 MB | Authors | GitHub Release on request |
| Observed discharge (`Discharge Obs.csv`) | small | **Central Water Commission, India** | Restricted — CWC HQ consent required |
| ECMWF TIGGE GRIB data | varies | **ECMWF TIGGE Portal** | Open research licence |
| ERA5 solar radiation | varies | **Copernicus C3S** | Open access |
| CPC min/max temperature | varies | **NOAA CPC** | Open access |
| DEM | ~50 MB | **USGS Earth Explorer** | Open access |
| LULC | ~20 MB | **Esri Sentinel-2 land cover** | Open access |

Trained models and HEC-HMS project files are bundled in the pre-built Windows installer hosted on Zenodo: **https://doi.org/10.5281/zenodo.20356274** (v2.1.1). For source-only researchers, please write to the corresponding author.

---

## 7. Citation

If you use this code or the methodology, please cite:

```bibtex
@article{debbarma2026arise,
  title   = {ARISE: A Novel Automated Hybrid System for Multi-Timescale Flood
             Forecasting and Operational Early Warning in Northeast India},
  author  = {Debbarma, Sagar and Mandal, Sameer and Bandyopadhyay, Arnab and Bhadra, Aditi},
  journal = {Journal of Hydrology},
  year    = {2026},
  note    = {Under review}
}

@software{arise_repo_2026,
  author       = {Debbarma, Sagar and Mandal, Sameer and Bandyopadhyay, Arnab and Bhadra, Aditi},
  title        = {ARISE Medium-Term Flood Forecast Sub-System (v2.1.0)},
  year         = {2026},
  url          = {https://github.com/sagarbd33/ARISE-Medium-Term-Flood-Forecast},
  doi          = {10.5281/zenodo.20356274},
  version      = {2.1.1},
  publisher    = {Zenodo}
}
```

**APA-style citation (auto-generated by Zenodo):**

> Debbarma, S. (2026). *ARISE - Medium Term Flood Forecast Installer (v2.1.1)* (Version 2.1.1) [Software]. Zenodo. https://doi.org/10.5281/zenodo.20356274

A formal `CITATION.cff` is provided for the GitHub citation widget; it will be updated with volume/issue/DOI once the manuscript is accepted.

---

## 8. Authors

| Role | Name | Email |
|---|---|---|
| Data acquisition · Methodology · Manuscript preparation | **Sagar Debbarma** | sagarbd33@gmail.com |
| Methodology | **Sameer Mandal** | smandal52@gmail.com |
| Supervision · Manuscript editing · Communicating · Grant recipient | **Arnab Bandyopadhyay** *(Corresponding Author)* | arnabbandyo@yahoo.co.in |
| Supervision · Conceptualization · Grant recipient | **Aditi Bhadra** | aditibhadra@yahoo.co.in |

**Affiliation:** Department of Agricultural Engineering, **North Eastern Regional Institute of Science and Technology (NERIST)**, Nirjuli (Itanagar), Arunachal Pradesh, India.

---

## 9. Acknowledgements

The authors thank the officials and staff of:
- **Central Water Commission**, Government of India
- **Agriculture Department of Mizoram**
- **Irrigation and Water Resources Department of Mizoram**
- **Mizoram State Meteorological Centre**

for their assistance with data and related matters. Special thanks to **Ms. P.C. Vanlalnunchhani** for liaison work with Mizoram Government officials.

This work was financially supported by the **Irrigation and Water Resources Department of Mizoram via the National Hydrology Project, Government of India**.

---

## 10. Licence

Released under the **MIT Licence** — see [`LICENSE`](LICENSE).

If you use the software in academic work, please also cite the associated publication (see Section 7).
