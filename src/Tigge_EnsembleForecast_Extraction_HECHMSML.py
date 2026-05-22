# -*- coding: utf-8 -*-
"""
Created on Tue Apr 29 11:59:43 2025
Author: AE-lab
Purpose: Extract ensemble mean from TIGGE ECMWF ensemble forecast files
          and save step-wise station-wise CSVs (append-only update)
"""

import cfgrib
import xarray as xr
import pandas as pd
import numpy as np
import os
from glob import glob

def run():
    # Input and Output Paths
    grib_dir = "C:/Users/Medium Term Flood Forecast/ECMWF_Ensemble"  # Directory containing all ensemble .grib files
    stations_csv = "C:/Users/Medium Term Flood Forecast/Rainfall_Lat_Lon.csv"  # Station metadata
    output_dir = "C:/Users/Medium Term Flood Forecast/Stepwise_Combined_CSVs_Ensemble_Mean"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load station locations
    stations_df = pd.read_csv(stations_csv)  # Must have columns: Stations, Lat, Lon
    
    # Collect all GRIB files
    grib_files = sorted(glob(os.path.join(grib_dir, "*.grib")))
    
    # Container for all processed data
    combined_station_stepwise = {}
    
    # Loop through each GRIB file
    for grib_file in grib_files:
        print(f"Processing: {os.path.basename(grib_file)}")
    
        try:
            # Load the dataset using cfgrib engine
            ds = xr.open_dataset(grib_file, engine="cfgrib")
        except Exception as e:
            print(f"Failed to open {grib_file}: {e}")
            continue
    
        # Check if required variables are present
        expected_vars = {'tp', 'mx2t6', 'mn2t6', 'ssr'}
        if not expected_vars.issubset(ds.data_vars):
            print(f"Missing required variables in {grib_file}, skipping.")
            continue
    
        # Calculate ensemble mean
        try:
            ds_mean = ds.mean(dim='number', skipna=True)
        except Exception as e:
            print(f"Failed to compute ensemble mean: {e}")
            continue
    
        # Convert to dataframe
        df = ds_mean.to_dataframe().reset_index()
    
        # Required columns after averaging
        if not {'step', 'latitude', 'longitude', 'valid_time', 'mx2t6', 'mn2t6', 'ssr', 'tp'}.issubset(df.columns):
            print(f"Missing required columns after averaging in {grib_file}, skipping.")
            continue
    
        df = df[['step', 'latitude', 'longitude', 'valid_time', 'mx2t6', 'mn2t6', 'ssr', 'tp']]
    
        # Interpolate to each station
        for _, row in stations_df.iterrows():
            name, lat, lon = row['Stations'], row['Lat'], row['Lon']
            nearest = df.iloc[np.argmin((df['latitude'] - lat)**2 + (df['longitude'] - lon)**2)][['latitude', 'longitude']]
            station_df = df[(df['latitude'] == nearest['latitude']) & (df['longitude'] == nearest['longitude'])].copy()
    
            # Unit conversion
            station_df['mx2t6'] -= 273.15  # K → °C
            station_df['mn2t6'] -= 273.15  # K → °C
            station_df['ssr'] /= 86400000  # W/m²·s → kWh/m²/day
            station_df['At'] = (station_df['mx2t6'] + station_df['mn2t6']) / 2  # Avg Temp
    
            # Keep only required columns
            station_df = station_df[['step', 'valid_time', 'tp', 'At', 'ssr', 'mx2t6', 'mn2t6']]
    
            # Process step-wise values (delta between steps)
            stepwise = combined_station_stepwise.setdefault(name, {})
            steps = sorted(station_df['step'].unique(), key=lambda x: pd.Timedelta(x).days)
    
            for i, step in enumerate(steps):
                df_step = station_df[station_df['step'] == step].sort_values('valid_time').reset_index(drop=True)
                if i > 0:
                    prev = station_df[station_df['step'] == steps[i - 1]].sort_values('valid_time').reset_index(drop=True)
                    if len(df_step) == len(prev):
                        df_step['tp'] -= prev['tp']
                        df_step['ssr'] -= prev['ssr']
                if step in stepwise:
                    stepwise[step] = pd.concat([stepwise[step], df_step]).drop_duplicates(subset='valid_time').reset_index(drop=True)
                else:
                    stepwise[step] = df_step
    
    # Save station-wise step-wise data to CSVs (only append new rows)
    first_station = next(iter(combined_station_stepwise))
    for step in combined_station_stepwise[first_station]:
        data_frames = {v: None for v in ['tp', 'At', 'ssr', 'mx2t6', 'mn2t6']}
        for station, steps in combined_station_stepwise.items():
            if step not in steps:
                continue
            df = steps[step]
            for var in data_frames:
                col = df[['valid_time', var]].rename(columns={'valid_time': 'Date', var: station})
                data_frames[var] = col if data_frames[var] is None else pd.merge(data_frames[var], col, on='Date', how='outer')
    
        step_str = str(step).replace(" days", "day").replace("00:00:00", "").replace(" ", "")
        
        for var, df_out in data_frames.items():
            if df_out is not None:
                output_path = os.path.join(output_dir, f'{var}_Step_{step_str}.csv')
    
                # If the file exists, read old data and append only new dates
                if os.path.exists(output_path):
                    existing_df = pd.read_csv(output_path, parse_dates=['Date'])
    
                    # Combine old and new, drop duplicates
                    updated_df = pd.concat([existing_df, df_out])
                    updated_df = updated_df.drop_duplicates(subset='Date', keep='first').sort_values('Date').reset_index(drop=True)
                else:
                    updated_df = df_out
    
                # Replace negative rainfall with 0
                if var == 'tp':
                    updated_df.iloc[:, 1:] = updated_df.iloc[:, 1:].clip(lower=0)
    
                # Save updated CSV
                updated_df.to_csv(output_path, index=False)
                print(f"Updated: {output_path}")

if __name__ == "__main__":
    run()