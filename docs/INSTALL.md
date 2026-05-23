# INSTALL.md — Installation Guide

Two installation paths are supported.

| Path | Audience | Use case |
|---|---|---|
| **A. End-user installer** | IWRD / DDMA / SEOC operators | Daily operational deployment on Windows |
| **B. Developer setup** | Researchers, reviewers | Inspecting, modifying, or replicating the methodology |

---

## A. End-User Installer (Windows, Operational)

### A.1 Prerequisites

| Requirement | Minimum | Recommended |
|---|---|---|
| OS | Windows 10 (64-bit) | Windows 11 (64-bit) |
| Disk free at `C:\Users\` | 2 GB | 5 GB |
| RAM | 8 GB | 16 GB |
| Privileges | Administrator (for install + VC++ Redist) | Administrator |
| Network | HTTPS to `api.ecmwf.int` | Stable broadband |
| ECMWF account | Free academic registration at https://www.ecmwf.int/ | — |

### A.2 What the Installer Provides

The pre-built **`ARISE - Medium Term Flood Forecast Installer.exe`** (≈ 2 GB) ships with:

| Component | Purpose |
|---|---|
| `ARISE - Medium Term Flood Forecast.exe` | PyInstaller-bundled `Daily_Forecast_Runner.py` plus all Python deps |
| `Run_All_HEC_HMS.exe` | HEC-HMS Jython driver |
| `_internal/` | Frozen Python runtime + libraries |
| `HEC-HMS/` | HEC-HMS 4.10 binaries and the four basin projects (`1Day_Forecast`, `3Day_Forecast`, `5Day_Forecast`, `7Day_Forecast`) |
| `Stepwise_Combined_CSVs_Ensemble_Mean/` | Pre-trained XGBoost & GRU models, bias-corrected reference data, observed discharge |
| `ECMWF_Ensemble/` | Empty directory; populated daily by `New_ECMWF_Ensemble_Forecast_15Days_Lead.py` |
| `Run_1day.py / Run_3day.py / Run_5day.py / Run_7day.py` | HEC-HMS Jython scripts |
| `Rainfall_Lat_Lon.csv` | 12-station coordinate file |
| `VC_redist.x64.exe` | Microsoft Visual C++ Redistributable (silently installed) |

### A.3 Installation Steps

1. Download **`ARISE - Medium Term Flood Forecast Installer.exe`** (≈ 2 GB) from the **Zenodo archive** linked in the manuscript (see [`docs/RELEASES.md`](RELEASES.md) for why the installer is hosted on Zenodo rather than GitHub).
2. Right-click → **Run as administrator**.
3. The installer:
   - Silently runs `VC_redist.x64.exe` first.
   - Extracts all bundled files into `C:\Users\Medium Term Flood Forecast\` (this path is fixed — see warning below).
   - Creates a desktop shortcut `ARISE - Medium Term Flood Forecast`.
4. Launch the desktop shortcut. The Python scheduler starts and idles, printing:
   ```
   Scheduler started. Waiting for 08:30:00 daily...
   [yyyy-mm-dd HH:MM:SS] Waiting...
   ```
5. **First-run credential prompt (only after the first 08:30 IST run) asks for URL / Key / Email; values are saved to C:\Users\Medium Term Flood Forecast\.ecmwfapirc and auto-loaded silently on every subsequent run:
   ```
   === Enter ECMWF API credentials ===
   URL (press Enter for default https://api.ecmwf.int/v1):
   Key: <paste your ECMWF API key>
   Email: <your ECMWF-registered email>
   ```
   These prompts re-appear on each daily run. They are **not stored** for security reasons; if persistent credentials are desired, replace the `input()` calls with a read of `~/.ecmwfapirc`.

> ⚠️ **Installation directory is hard-coded.** Internal scripts reference `C:\Users\Medium Term Flood Forecast\` extensively. The Inno Setup installer disables both the path edit box and the Browse button to prevent users from changing it. To deploy at a different location, the Python source code must be modified before re-building.

### A.4 Verifying the Installation

After the first successful daily run, you should see:
- Console showing 12 green `Completed:` lines and one cyan `Forecast execution completed.`
- `C:\Users\Medium Term Flood Forecast\forecast_run_log.txt` populated with timestamps.
- `Stepwise_Combined_CSVs_Ensemble_Mean\Bias Corrected Data\HEC-HMS-GRU\Hybrid Results\ECMWF_Streamflow_Forecast_Summary.txt` containing the latest bulletin.

### A.5 Uninstalling

Control Panel → Programs → **ARISE - Medium Term Flood Forecast** → Uninstall.

The directory `C:\Users\Medium Term Flood Forecast\` is **not** automatically removed because it contains operational logs and may be wanted for archival. Delete it manually if no longer needed.

---

## B. Developer Setup (From Source)

### B.1 Prerequisites

| Requirement | Notes |
|---|---|
| Python | 3.10 or 3.11 (3.12 untested with `pydsstools`) |
| Git | Any recent version |
| HEC-HMS 4.10 | Windows only; for Phase 2 execution |
| eccodes | Best installed via conda |
| Conda / Miniforge | Strongly recommended for clean dependency resolution |

### B.2 Clone and Install

```bash
git clone https://github.com/sagarbd33/ARISE-Medium-Term-Flood-Forecast.git
cd ARISE-Medium-Term-Flood-Forecast

# Create environment
conda create -n arise python=3.11 -y
conda activate arise

# eccodes (binary backend for cfgrib) — easier via conda
conda install -c conda-forge eccodes -y

# Python packages
pip install -r requirements.txt
```

### B.3 ECMWF API Configuration

Either:

- **Interactive once — let the script prompt you on first run; credentials are saved to C:\Users\Medium Term Flood Forecast\.ecmwfapirc and reused automatically thereafter; or
- **Persistent** — create `%USERPROFILE%\.ecmwfapirc` (Windows) or `~/.ecmwfapirc` (Linux/macOS):
  ```json
  {
    "url"   : "https://api.ecmwf.int/v1",
    "key"   : "YOUR_API_KEY_HERE",
    "email" : "your.email@example.com"
  }
  ```
  Then modify `New_ECMWF_Ensemble_Forecast_15Days_Lead.py` to construct `ECMWFDataServer()` with no arguments.

### B.4 Required Local Files

The repository ships with source code only. For a working pipeline you additionally need (request from corresponding author, see README §6):

1. **HEC-HMS project files** under `HEC-HMS/<1|3|5|7>Day_Forecast/` — each containing `.hms`, `.basin`, `.met`, `.control`, `.gage`, `.run`, `.dss`, etc.
2. **Trained models:**
   ```
   Stepwise_Combined_CSVs_Ensemble_Mean/
   ├── Bias Correction Model (XGBoost)/
   │   ├── Average Temp/{1,3,5,7}day_{Sub1..Sub12}_Tuned_XGBoost_BiasCorrection.pkl   (48 files)
   │   ├── Total Precipitation/{1,3,5,7}day_{12 stations + Avg}_Tuned_XGBoost_BiasCorrection.pkl   (52 files)
   │   ├── Min Temp/{1,3,5,7}day_Avg_Tuned_XGBoost_BiasCorrection.pkl    (4 files)
   │   ├── Max Temp/{1,3,5,7}day_Avg_Tuned_XGBoost_BiasCorrection.pkl    (4 files)
   │   └── Solar Radiation/{1,3,5,7}day_Avg_Tuned_XGBoost_BiasCorrection.pkl   (4 files)
   └── Bias Corrected Data/
       └── HEC-HMS-GRU/
           ├── 1-3-5-7 Day HEC-HMS-GRU Model/{1,3,5,7}day_Model_GRU.keras + {1,3,5,7}day_Scaler_GRU.pkl
           └── Hybrid Results/1-3-5-7 Day Stage XGBoast Model/{1,3,5,7}day_Tuned_XGBoost.pkl
   ```
3. **Observed discharge:**
   ```
   Stepwise_Combined_CSVs_Ensemble_Mean/Observed Discharge/Discharge Obs.csv
   ```
   with columns `Date,Bairabi[,Reiek-kai]`.

### B.5 Running

#### Full pipeline (requires Windows + HEC-HMS):

```bash
python src/Daily_Forecast_Runner.py
```

The scheduler will wait until 08:30 IST. For an immediate test run, edit the bottom of `Daily_Forecast_Runner.py`:

```python
if __name__ == "__main__":
    run_forecast()    # immediate run, no schedule
```

#### Individual modules:

Each module in `src/` exposes a `run()` function and an `__main__` guard, so any of them can be executed in isolation, e.g.:

```bash
python src/Bias_Corrected_Data_all.py
python src/Tigge_EnsembleForecast_Extraction_HECHMSML.py
```

This is the recommended workflow for debugging or for re-running a single stage after a failure.

### B.6 Path Configuration

All scripts currently hard-code `C:\Users\Medium Term Flood Forecast\` as the base directory. To run elsewhere:

```bash
# Find all hard-coded paths:
grep -rn "Medium Term Flood Forecast" src/

# Replace base path globally (Linux/macOS, dry-run shown):
find src/ -name "*.py" -exec sed -i.bak 's|C:\\Users\\Medium Term Flood Forecast|/path/to/your/dir|g' {} +
```

A future version (v2.0) will externalise these paths into a `config.yaml`.

---

## C. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: ecmwfapi` | Missing package | `pip install ecmwf-api-client` |
| GRIB decode error or `eccodes not found` | Missing native binary | `conda install -c conda-forge eccodes` |
| `pydsstools` install fails on Linux/macOS | Windows-only binary | Run Phase 2 on Windows only |
| `HMS engine not found` | HEC-HMS 4.10 missing or path wrong | Install HEC-HMS 4.10; update `hms_dir` in `Run_All_HEC_HMS.py` |
| `ECMWF auth error` | Wrong key or expired | Regenerate at https://api.ecmwf.int/v1/key/ |
| `Could not load … Forecast.dss` | DSS path mismatch | Verify `1Day_Forecast.dss` etc. exist under each `HEC-HMS/<n>Day_Forecast/` |
| Date-format error in `HEC_HMS_DSS_Calibration.py` | Running on POSIX | `%#d` is Windows-only; replace with `%-d` on Linux/macOS |
| GRU `load_model` fails with `unknown initializer` | TF version mismatch | The script registers `Orthogonal` explicitly; if other initializers fail, add similarly |
| `Pickle UnicodeDecodeError` on scaler load | Different OS originated | Already mitigated via `encoding='latin1'` |
| Scheduler keeps printing `Waiting...` and never fires | Wrong system time / time zone | Verify Windows time zone is IST or adjust `schedule.every().day.at(...)` |
