# RELEASES.md — Hosting Large Binaries Outside the Repository

The pre-built **`ARISE - Medium Term Flood Forecast Installer.exe`** is approximately **> 2 GB** because it bundles:

- The PyInstaller-frozen Python runtime + all wheels (TensorFlow, XGBoost, cfgrib, pydsstools, …)
- HEC-HMS 4.10 binaries
- All trained XGBoost (84 `.pkl`) and GRU (`.keras` + `.pkl`) models
- HEC-HMS basin / .control / .gage / .dss project files for the four forecast horizons
- Microsoft Visual C++ Redistributable x64

GitHub limits and the right place to host each artefact:

| Storage | Hard limit | Verdict for our installer |
|---|---|---|
| Repository file (commit) | 100 MB per file | ❌ Far too small |
| Git LFS (free tier) | 2 GB per file, 1 GB storage / month bandwidth | ❌ File too large + tiny bandwidth |
| GitHub Releases | **2 GB per file**, unlimited files per release | ⚠️ Marginal — works for files **at or below 2 GB**; rejects above |
| GitHub Packages | Container/package focused | ❌ Wrong tool |
| Zenodo | **50 GB per file**, unlimited storage | ✅ **Recommended** — gives a citable DOI |
| OSF (Open Science Framework) | 5 GB per file (free), 1 TB total | ✅ Good academic alternative |
| Google Drive / OneDrive | 15 GB+ | ✅ Works, but no DOI, no academic provenance |
| Self-hosted institutional server | unlimited | ✅ If NERIST/IWRD provide hosting |

---

## Recommended: Zenodo (with DOI)

**Why Zenodo for *Journal of Hydrology* submission:**
- Free, no size limit at 2 GB (single files up to 50 GB allowed).
- Each upload mints a **persistent DOI** — exactly what JoH reviewers prefer over raw GitHub links.
- One-click integration with GitHub: every git tag auto-archives to Zenodo.
- Operated by **CERN** + funded by EU — long-term preservation.

### Step-by-Step

#### Option A — manual upload (fastest)

1. Sign up at **https://zenodo.org/** (free; use ORCID or GitHub login).
2. Top-right → **+ New upload**.
3. Choose **Software** as resource type.
4. Drag-drop `ARISE - Medium Term Flood Forecast Installer.exe`.
5. Fill metadata:
   - **Title:** `ARISE - Medium Term Flood Forecast Installer (v2.1.1)`
   - **Authors:** Sagar Debbarma; Sameer Mandal; Arnab Bandyopadhyay; Aditi Bhadra (with ORCIDs if available)
   - **Description:** Copy abstract from the paper (or first section of README).
   - **Keywords:** flood forecasting, ECMWF, HEC-HMS, GRU, XGBoost, Northeast India
   - **License:** MIT
   - **Version:** 2.1.1
   - **Related identifiers:** Link to GitHub repo URL (relation: "is supplement to").
6. **Publish.** You receive a DOI like `10.5281/zenodo.20357890`.

#### Option B — GitHub ↔ Zenodo automatic linking

1. Push the v2.1.1 source code to GitHub.
2. Log in to https://zenodo.org/account/settings/github/ with your GitHub account.
3. **Flip the switch** ON for `ARISE-Medium-Term-Flood-Forecast`.
4. On GitHub: **Releases → Draft a new release → Tag v2.1.1**.
5. Attach the >2 GB installer to the release ⚠️ *only if the file is ≤ 2 GB*. If it is over 2 GB, do **Option A** for the installer and let GitHub-Zenodo handle just the source code archive.
6. Zenodo auto-archives a snapshot of the repo and issues a DOI per release.

### Final paper citation block

After Zenodo DOI is minted:

> **Availability of data and materials**
>
> The Central Water Commission of India has the discharge data which supports the findings of this research. The availability of the data is subject to restrictions. With the consent of the Headquarter of the CWC located in New Delhi, the data is accessible to the authors. Other data used in this research are freely accessible in the public domain.
>
> The source code of the ARISE Medium-Term Flood Forecast sub-system (v2.1.1), along with installation guides, module-level documentation, and deployment scripts, is openly available on GitHub at https://github.com/sagarbd33/ARISE-Medium-Term-Flood-Forecast and archived on Zenodo at https://doi.org/10.5281/zenodo.20357890. The pre-built Windows installer `ARISE - Medium Term Flood Forecast Installer.exe` (≈ 2 GB) is hosted on the same Zenodo record.

---

## Alternatives (if Zenodo doesn't suit)

### B. OSF (Open Science Framework)

1. Sign up at https://osf.io/ (institutional or ORCID login).
2. Create a project → Add component (Software).
3. Upload installer + link to GitHub repo.
4. Make public; you get an OSF DOI (`10.17605/OSF.IO/XXXXX`).
5. Free, 5 GB per file, 50 GB total project size.

### C. NERIST / IWRD Institutional Hosting

If your department has a public-facing web server, ask IT to host the installer at a stable URL like:

```
https://aerdownloads.nerist.ac.in/arise/v2.1.1/ARISE-Medium-Term-Flood-Forecast-Installer.exe
```

This is the most "institutional" option but lacks DOI provenance.

### D. Google Drive (current setup)

Already in use per your paper draft (`https://drive.google.com/file/d/...`).

Acceptable but not preferred because:
- No DOI / persistent identifier.
- Drive links can break if account is suspended or quota exceeded.
- Reviewers may flag "not archival" during peer review.

If keeping Drive, at minimum: enable "anyone with link" and set ownership to a long-lived institutional account, not a personal one.

---

## What Goes Where — Quick Reference

| Artefact | Size | Recommended host |
|---|---|---|
| Source code (`src/`, `docs/`, `installer/.iss`, `LICENSE`, `README.md`, `CITATION.cff`) | < 1 MB | **GitHub repo (commit)** |
| `Run_All_HEC_HMS.exe` (1.7 MB) | < 100 MB | **GitHub Release** |
| `ARISE - Medium Term Flood Forecast.exe` (50 MB) | < 100 MB | **GitHub Release** |
| `_internal/` PyInstaller runtime (~500 MB) | < 2 GB | **GitHub Release** as `.zip` |
| HEC-HMS basin projects (~200 MB) | < 100 MB? | **GitHub Release** as `.zip` if compressible |
| Trained XGBoost + GRU models (~65 MB) | < 100 MB | **GitHub Release** as `.zip` |
| **`ARISE - Medium Term Flood Forecast Installer.exe`** (> 2 GB) | **> 2 GB** | **Zenodo** ✅ (DOI), or OSF, or institutional server |

---

## Summary for Your Paper

For the *Journal of Hydrology* "Availability of data" section, use this two-pronged citation:

1. **GitHub URL** → for browsing/cloning the source code (cited primarily).
2. **Zenodo DOI** → for the persistent archive + the >2 GB installer (cited as the citable artefact).

This is the now-standard pattern for hydrology software papers (e.g. CAMELS-DK, LISFLOOD, GloFAS).
