# -*- coding: utf-8 -*-
"""
Created on Tue Apr 29 11:59:43 2025

@author: AE-lab
"""

from ecmwfapi import ECMWFDataServer
import pandas as pd
from datetime import datetime, timedelta
import os

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
    
    # === ECMWF Request (prompt user for credentials each run) ===
    print("\n=== Enter ECMWF API credentials ===")
    url = input("URL (press Enter for default https://api.ecmwf.int/v1): ").strip()
    if not url:
        url = "https://api.ecmwf.int/v1"
    key = input("Key: ").strip()
    email = input("Email: ").strip()

    if not key or not email:
        raise ValueError("Key and Email required. Aborting.")

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
