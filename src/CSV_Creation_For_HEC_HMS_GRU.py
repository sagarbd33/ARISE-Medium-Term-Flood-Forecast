# -*- coding: utf-8 -*-
"""
Created on Fri Jul 25 13:06:29 2025

@author: AE-lab
"""

import pandas as pd
from pydsstools.heclib.dss import HecDss
from datetime import datetime, timedelta
import os

def run():
    # === Common paths ===
    obs_path = r"C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Observed Discharge\Discharge Obs.csv"
    output_dir = r"C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Bias Corrected Data\HEC-HMS-GRU"
    os.makedirs(output_dir, exist_ok=True)
    
    # === Forecast file config (no pathnames yet) ===
    forecast_configs = {
        "1day": {
            "precip": r"tp_Step_1day.csv",
            "tmin": r"mn2t6_Step_1day.csv",
            "tmax": r"mx2t6_Step_1day.csv",
            "srad": r"ssr_Step_1day.csv",
            "dss": r"C:\Users\Medium Term Flood Forecast\HEC-HMS\1Day_Forecast\Cal.dss"
        },
        "3day": {
            "precip": r"tp_Step_3day.csv",
            "tmin": r"mn2t6_Step_3day.csv",
            "tmax": r"mx2t6_Step_3day.csv",
            "srad": r"ssr_Step_3day.csv",
            "dss": r"C:\Users\Medium Term Flood Forecast\HEC-HMS\3Day_Forecast\Cal.dss"
        },
        "5day": {
            "precip": r"tp_Step_5day.csv",
            "tmin": r"mn2t6_Step_5day.csv",
            "tmax": r"mx2t6_Step_5day.csv",
            "srad": r"ssr_Step_5day.csv",
            "dss": r"C:\Users\Medium Term Flood Forecast\HEC-HMS\5Day_Forecast\Cal.dss"
        },
        "7day": {
            "precip": r"tp_Step_7day.csv",
            "tmin": r"mn2t6_Step_7day.csv",
            "tmax": r"mx2t6_Step_7day.csv",
            "srad": r"ssr_Step_7day.csv",
            "dss": r"C:\Users\Medium Term Flood Forecast\HEC-HMS\7Day_Forecast\Cal.dss"
        }
    }
    
    # === Root path for bias corrected data folders ===
    root_path = r"C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Bias Corrected Data"
    
    # === Load observed discharge once ===
    df_obs = pd.read_csv(obs_path, parse_dates=['Date'])
    df_obs = df_obs[['Date', 'Bairabi']].rename(columns={'Bairabi': 'discharge'})
    
    # === Process each forecast ===
    for key, config in forecast_configs.items():
        print(f"Processing {key}...")
    
        # === Load Precipitation to get last date ===
        precip_path = os.path.join(root_path, "Total Precipitation", config["precip"])
        df_precip = pd.read_csv(precip_path, parse_dates=["Date"])
        last_date = df_precip["Date"].max() - timedelta(days=1)
        last_date_str = last_date.strftime("%d%b%Y")  # e.g., "31Dec2024"
    
        # === Dynamically build pathname ===
        pathname = f"//OUTLET/FLOW/31May2017 - {last_date_str}/1DAY/RUN:CAL/"
    
        # === Load and merge climate variables ===
        df_precip = df_precip[['Date', 'Avg']].rename(columns={'Avg': 'precip'})
    
        df_tmin = pd.read_csv(os.path.join(root_path, "Min Temp", config["tmin"]))
        df_precip['tmin'] = df_tmin['Avg']
    
        df_tmax = pd.read_csv(os.path.join(root_path, "Max Temp", config["tmax"]))
        df_precip['tmax'] = df_tmax['Avg']
    
        df_srad = pd.read_csv(os.path.join(root_path, "Solar Radiation", config["srad"]))
        df_precip['srad'] = df_srad['Avg']
    
        # === Read DSS data ===
        fid = HecDss.Open(config["dss"])
        ts = fid.read_ts(pathname)
        fid.close()
    
        df_sim = pd.DataFrame({
            'Date': pd.to_datetime(ts.pytimes),
            'simdischarge': ts.values
        })
    
        # === Merge and Save ===
        df_merged = pd.merge(df_precip, df_sim, on='Date', how='inner')
        df_final = pd.merge(df_merged, df_obs, on='Date', how='left')
    
        filename = f"HEC-HMS-GRU ECMWF_{key}_BiasCorrected (Ensemble).csv"
        output_path = os.path.join(output_dir, filename)
        df_final.to_csv(output_path, index=False)
        print(f"Saved: {output_path}")

if __name__ == "__main__":
    run()