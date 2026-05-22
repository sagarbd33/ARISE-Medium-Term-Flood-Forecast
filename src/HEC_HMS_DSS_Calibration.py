# -*- coding: utf-8 -*-
"""
Created on Fri Jun 13 15:58:28 2025

@author: AE-lab
"""

import os
import pandas as pd
from datetime import datetime

def run():
    # Precipitation input base directory
    precip_dir = r"C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Bias Corrected Data\Total Precipitation"
    
    # Forecast step info: (CSV name, Forecast folder name)
    forecast_configs = {
        "1Day": "tp_Step_1day.csv",
        "3Day": "tp_Step_3day.csv",
        "5Day": "tp_Step_5day.csv",
        "7Day": "tp_Step_7day.csv"
    }
    
    # Process each forecast step
    for step, csv_file in forecast_configs.items():
        try:
            precip_path = os.path.join(precip_dir, csv_file)
    
            # Read Date column from CSV
            df = pd.read_csv(precip_path, parse_dates=["Date"])
            start_datetime = df["Date"].min()
            end_datetime = df["Date"].max()
    
            # Format dates and times (Windows-compatible)
            new_start_date = start_datetime.strftime("%#d %B %Y")
            new_start_time = start_datetime.strftime("%H:%M")
            new_end_date = end_datetime.strftime("%#d %B %Y")
            new_end_time = end_datetime.strftime("%H:%M")
    
            # Control file path
            control_file = fr"C:\Users\Medium Term Flood Forecast\HEC-HMS\{step}_Forecast\Calibration.control"
    
            # Read and update control file content
            with open(control_file, 'r') as file:
                lines = file.readlines()
    
            updated_lines = []
            for line in lines:
                if line.strip().startswith("Start Date:"):
                    updated_lines.append(f"     Start Date: {new_start_date}\n")
                elif line.strip().startswith("Start Time:"):
                    updated_lines.append(f"     Start Time: {new_start_time}\n")
                elif line.strip().startswith("End Date:"):
                    updated_lines.append(f"     End Date: {new_end_date}\n")
                elif line.strip().startswith("End Time:"):
                    updated_lines.append(f"     End Time: {new_end_time}\n")
                else:
                    updated_lines.append(line)
    
            # Write back to the file
            with open(control_file, 'w') as file:
                file.writelines(updated_lines)
    
            print(f"Updated control file for {step} forecast.")
        
        except Exception as e:
            print(f"Error updating control file for {step}: {e}")

if __name__ == "__main__":
    run()