# DEPLOYMENT.md — Building the Installer

This document walks through reproducing the **`ARISE - Medium Term Flood Forecast Installer.exe`** distribution from source.

There are three independent build steps:

1. **PyInstaller build** for `Run_All_HEC_HMS.exe` (the HEC-HMS Jython driver).
2. **PyInstaller build** for `ARISE - Medium Term Flood Forecast.exe` (the main scheduler).
3. **Inno Setup compile** to wrap everything into a single Windows installer.

---

## 0. Prerequisites

| Tool | Version tested | Purpose |
|---|---|---|
| Python | 3.11.x (64-bit) | Source interpreter |
| PyInstaller | 6.16.0 | `.py` → `.exe` |
| Inno Setup Compiler | 6.6.0 | `.iss` → installer |
| HEC-HMS | 4.10 | For the bundled basin projects |
| Microsoft VC++ Redistributable x64 | latest | Required by some compiled wheels (pydsstools, eccodes) |

Install order:
```bat
pip install pyinstaller==6.16.0
:: Inno Setup: download installer from https://jrsoftware.org/isdl.php
```

Verify base directory is exactly `C:\Users\Medium Term Flood Forecast\` — all internal paths assume this.

---

## 1. PyInstaller Build of `Run_All_HEC_HMS.exe`

This is the HEC-HMS Jython driver. Although it is itself a CPython script (`Run_All_HEC_HMS.py`), it spawns the Jython process. Bundle it first.

```bat
cd "C:\Users\Medium Term Flood Forecast"
pyinstaller Run_All_HEC_HMS.py
```

Output:
```
dist\Run_All_HEC_HMS\Run_All_HEC_HMS.exe
dist\Run_All_HEC_HMS\_internal\
```

Move the executable up one level:
```bat
copy "dist\Run_All_HEC_HMS\Run_All_HEC_HMS.exe" "C:\Users\Medium Term Flood Forecast\"
```

> *(Note: the existing `Run_All_HEC_HMS.spec` in `installer/` can be used for a reproducible build via `pyinstaller Run_All_HEC_HMS.spec`.)*

---

## 2. PyInstaller Build of `ARISE - Medium Term Flood Forecast.exe`

This is the main scheduler. The `--name` flag controls the output filename.

```bat
cd "C:\Users\Medium Term Flood Forecast"
pyinstaller --name "ARISE - Medium Term Flood Forecast" Daily_Forecast_Runner.py
```

Output:
```
dist\ARISE - Medium Term Flood Forecast\ARISE - Medium Term Flood Forecast.exe
dist\ARISE - Medium Term Flood Forecast\_internal\
```

Recommended PyInstaller flags:

| Flag | Effect |
|---|---|
| `--name "..."` | Set exe name (mandatory if it must match `.iss`) |
| `--console` | Keep terminal window (required — Phase 1 prompts for ECMWF credentials) |
| `--icon=arise.ico` | Optional custom icon |
| `--noconfirm` | Skip prompt to overwrite previous build |

**Do NOT** use `--onefile` for this project. The bundled HEC-HMS-coupled `pydsstools` / `cfgrib` startup is significantly faster with a folder build, and several runtime files (DSS templates) need to live alongside the exe.

Now copy the build to the operational directory:
```bat
xcopy /E /I /Y "dist\ARISE - Medium Term Flood Forecast" "C:\Users\Medium Term Flood Forecast\"
```

This places:
- `ARISE - Medium Term Flood Forecast.exe` at the root of `C:\Users\Medium Term Flood Forecast\`
- `_internal\` containing the frozen runtime and libraries

> *(The existing `ARISE - Medium Term Flood Forecast.spec` can also be invoked: `pyinstaller "ARISE - Medium Term Flood Forecast.spec"`.)*

---

## 3. Inno Setup Compile

The Inno Setup script `installer/ARISE_Medium_Term_Flood_Forecast.iss` wraps everything.

### 3.1 Script Layout

```ini
[Setup]
AppName              = ARISE - Medium Term Flood Forecast
AppVersion           = 2.1.1
AppPublisher         = AE, NERIST
DefaultDirName       = C:\Users\Medium Term Flood Forecast
DefaultGroupName     = ARISE - Medium Term Flood Forecast
OutputBaseFilename   = ARISE - Medium Term Flood Forecast Installer
Compression          = lzma
SolidCompression     = yes
DisableDirPage       = no
UsePreviousAppDir    = no
DirExistsWarning     = no
```

Key points:
- `DefaultDirName` is `C:\Users\Medium Term Flood Forecast` to match hard-coded paths in source.
- The wizard **shows** the directory page but the [Code] section disables editing/browsing, so the user cannot change it.

```ini
[Code]
procedure InitializeWizard();
begin
  WizardForm.DirEdit.Enabled := False;          // disable text editing
  WizardForm.DirBrowseButton.Enabled := False;  // disable browse button
end;
```

### 3.2 Files Bundled

```ini
[Files]
Source: "VC_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "C:\Users\Medium Term Flood Forecast\ARISE - Medium Term Flood Forecast.exe"; ...
Source: "C:\Users\Medium Term Flood Forecast\_internal\*"; ... recursesubdirs createallsubdirs
Source: "C:\Users\Medium Term Flood Forecast\ECMWF_Ensemble\*"; ...
Source: "C:\Users\Medium Term Flood Forecast\HEC-HMS\*"; ...
Source: "C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\*"; ...
Source: "C:\Users\Medium Term Flood Forecast\Rainfall_Lat_Lon.csv"; ...
Source: "C:\Users\Medium Term Flood Forecast\Run_1day.py"; ...
Source: "C:\Users\Medium Term Flood Forecast\Run_3day.py"; ...
Source: "C:\Users\Medium Term Flood Forecast\Run_5day.py"; ...
Source: "C:\Users\Medium Term Flood Forecast\Run_7day.py"; ...
Source: "C:\Users\Medium Term Flood Forecast\Run_All_HEC_HMS.exe"; ...
```

The four `Run_<n>day.py` files are shipped as Python source because HEC-HMS's Jython runtime interprets them directly (no PyInstaller bundling).

### 3.3 Post-Install Run

```ini
[Run]
Filename: "{tmp}\VC_redist.x64.exe"; \
    StatusMsg: "Installing Microsoft Visual C++ Redistributable (x64)..."; \
    Flags: waituntilterminated shellexec
Filename: "{app}\ARISE - Medium Term Flood Forecast.exe"; \
    Description: "Launch ARISE - Medium Term Flood Forecast"; \
    Flags: nowait postinstall skipifsilent
```

### 3.4 Compile

Open Inno Setup Compiler → File → Open → select `ARISE_Medium_Term_Flood_Forecast.iss` → Build → Compile (F9).

Output:
```
ARISE - Medium Term Flood Forecast Installer.exe   (≈ 2 GB — bundles HEC-HMS engine + DLLs + trained models + Python runtime)
```

> The compiled installer typically exceeds 2 GB. See [`RELEASES.md`](RELEASES.md) for hosting it (Zenodo recommended; GitHub Releases capped at 2 GB).

---

## 4. Version Bumping

To release a new version (e.g. v2.1.1 → v2.2.0):

1. Edit `installer/ARISE_Medium_Term_Flood_Forecast.iss`:
   ```ini
   AppVersion=2.2.0
   ```
2. Update `CITATION.cff` version field if appropriate.
3. Re-run PyInstaller builds (steps 1 and 2).
4. Re-compile Inno Setup.
5. Tag the git release:
   ```bash
   git tag -a v2.2.0 -m "Release 2.2.0: <summary>"
   git push origin v2.2.0
   ```
6. Upload `ARISE - Medium Term Flood Forecast Installer.exe` to the GitHub Release page.

---

## 5. Renaming Conventions Followed

If you rename the executable (e.g. `ARISE - Medium Term Flood Forecast` → `ARISE Flood`), **every** of these references must be updated together:

| File / Section | Reference |
|---|---|
| `pyinstaller --name "..."` | the exe filename |
| `.iss` → `[Setup] AppName` | wizard title |
| `.iss` → `[Setup] DefaultGroupName` | Start-menu group |
| `.iss` → `[Setup] OutputBaseFilename` | installer filename |
| `.iss` → `[Files] Source: "...exe"` | bundled exe path |
| `.iss` → `[Run] Filename: "{app}\...exe"` | post-install launch |
| `.iss` → `[Icons] Filename + Name` | desktop shortcut |

`AppVersion` and `DefaultDirName` can usually stay; the latter especially must remain `C:\Users\Medium Term Flood Forecast` because the source code references it.

> ⚠️ **Windows filename caveat:** colons (`:`) are illegal in filenames. The chosen `ARISE - Medium Term Flood Forecast` uses a hyphen for safe portability.
