# -*- coding: utf-8 -*-
"""
Created on Tue Apr 29 11:59:43 2025
Updated  on May  2026 — persistent ECMWF credentials via ~/.ecmwfapirc

@author: AE-lab
"""

from ecmwfapi import ECMWFDataServer
import pandas as pd
from datetime import datetime, timedelta
import os
import json

# ECMWF credentials file inside the ARISE install folder
ECMWF_RC_PATH = r"C:\Users\Medium Term Flood Forecast\.ecmwfapirc"


def load_or_prompt_credentials():
    """
    Load ECMWF credentials from ~/.ecmwfapirc if it exists and is valid.
    Otherwise, prompt the user once and save them for all future runs.
    """
    # ---- 1. Try to load existing creds ----
    if os.path.exists(ECMWF_RC_PATH):
        try:
            with open(ECMWF_RC_PATH, "r", encoding="utf-8") as f:
                creds = json.load(f)
            if creds.get("url") and creds.get("key") and creds.get("email"):
                print(f"[INFO] Loaded ECMWF credentials from {ECMWF_RC_PATH}")
                return creds["url"], creds["key"], creds["email"]
            else:
                print("[WARN] Existing .ecmwfapirc is missing required fields; re-prompting.")
        except (json.JSONDecodeError, OSError) as e:
            print(f"[WARN] Could not read {ECMWF_RC_PATH}: {e}. Re-prompting.")

    # ---- 2. First-run prompt ----
    print("\n=== First-time ECMWF API setup ===")
    print(f"(Credentials will be saved to {ECMWF_RC_PATH} and reused on every future run.)\n")

    url = input("URL (press Enter for default https://api.ecmwf.int/v1): ").strip()
    if not url:
        url = "https://api.ecmwf.int/v1"

    # Plain input() works in Spyder, PyInstaller exe, and standard terminals.
    # (getpass.getpass blocks in Spyder/QtConsole and some packaged-exe environments.)
    key = input("Key: ").strip()
    email = input("Email: ").strip()

    if not key or not email:
        raise ValueError("Key and Email are required. Aborting.")

    creds = {"url": url, "key": key, "email": email}

    # ---- 3. Save for future runs ----
    try:
        with open(ECMWF_RC_PATH, "w", encoding="utf-8") as f:
            json.dump(creds, f, indent=2)
        # Tighten file permissions on POSIX; on Windows the user's home is already ACL-protected
        try:
            os.chmod(ECMWF_RC_PATH, 0o600)
        except Exception:
            pass
        print(f"[INFO] Credentials saved to {ECMWF_RC_PATH}")
    except OSError as e:
        print(f"[WARN] Could not save credentials: {e}. They will be requested again next time.")

    return url, key, email


def run():
    # === Load the last date from the CSV ===
    csv_path = r"C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Bias Corrected Data\Total Precipitation\tp_Step_1day.csv"
    df = pd.read_csv(csv_path)

    # Ensure the 'Date' column is parsed correctly
    df['Date'] = pd.to_datetime(df['Date'])

    # Get last date from CSV
    start_date = df['Date'].iloc[-1].strftime('%Y-%m-%d')

    # Get system date minus 2 days
    end_date = (datetime.today() - timedelta(days=2)).strftime('%Y-%m-%d')

    # === Define GRIB paths ===
    grib_path = r"C:\Users\Medium Term Flood Forecast\ECMWF_Ensemble\output_Ensemble_7Days_Lead(ECMWF)_AutoDate.grib"

    # Delete GRIB and associated .idx file if they exist
    if os.path.exists(grib_path):
        os.remove(grib_path)
        print("Deleted old GRIB file.")

    idx_files = [f for f in os.listdir(os.path.dirname(grib_path)) if f.startswith(os.path.basename(grib_path))]
    for idx_file in idx_files:
        full_path = os.path.join(os.path.dirname(grib_path), idx_file)
        if full_path.endswith('.idx'):
            os.remove(full_path)
            print("Deleted associated index file:", idx_file)

    # === ECMWF Request (auto-loads creds from ~/.ecmwfapirc; prompts only on first run) ===
    url, key, email = load_or_prompt_credentials()

    server = ECMWFDataServer(
        url=url,
        key=key,
        email=email
    )

    server.retrieve({
        "class": "ti",
        "dataset": "tigge",
        "date": f"{start_date}/to/{end_date}",
        "expver": "prod",
        "grid": "0.5/0.5",
        "levtype": "sfc",
        "number": "/".join(str(i) for i in range(1, 51)),  # Ensemble numbers 1 to 50
        "origin": "ecmf",
        "param": "121/122/176/228228",
        "step": "24/48/72/96/120/144/168",
        "time": "00:00:00",
        "type": "pf",
        "area": "24.6/91.7/21.7/94.3",
        "target": grib_path
    })


if __name__ == "__main__":
    run()
