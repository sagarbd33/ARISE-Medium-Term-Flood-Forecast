# -*- coding: utf-8 -*-
"""
Created on Thu Jul 24 15:17:41 2025

@author: AE-lab
"""

# Run_All_HEC_HMS.py
# Automates 1, 3, 5, 7 day simulations via HEC-HMS engine

import subprocess
import os

def run():
    # Step 1: Path to HEC-HMS executable
    hms_dir = r"C:\Users\Medium Term Flood Forecast\HEC-HMS\HEC-HMS-4.10"
    
    # Step 2: List of your simulation scripts
    script_paths = [
        r"C:\Users\Medium Term Flood Forecast\Run_1day.py",
        r"C:\Users\Medium Term Flood Forecast\Run_3day.py",
        r"C:\Users\Medium Term Flood Forecast\Run_5day.py",
        r"C:\Users\Medium Term Flood Forecast\Run_7day.py"
    ]
    
    # Step 3: Run each script using HEC-HMS engine
    for script_path in script_paths:
        script_name = os.path.basename(script_path)
        cmd = f'"{hms_dir}\\hec-hms.exe" -script "{script_path}"'
    
        print(f"\nRunning HEC-HMS simulation: {script_name}")
        result = subprocess.run(cmd, shell=True, cwd=hms_dir, capture_output=True, text=True)
    
        if result.returncode == 0:
            print(f"{script_name} completed successfully.")
        else:
            print(f"{script_name} failed.")
            print("STDOUT:\n", result.stdout)
            print("STDERR:\n", result.stderr)

if __name__ == "__main__":
    run()