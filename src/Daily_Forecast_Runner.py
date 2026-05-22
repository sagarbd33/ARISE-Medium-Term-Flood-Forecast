# -*- coding: utf-8 -*-
"""
Created on Thu Nov 20 18:58:13 2025

@author: AE-lab
"""

import os
import time
import warnings
import schedule
import subprocess
from datetime import datetime

import colorama
from colorama import Fore, Style

# =============== INITIALIZATION ===============
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings("ignore", category=UserWarning)
warnings.simplefilter(action="ignore", category=FutureWarning)
colorama.init(autoreset=True)

# =============== MODULE IMPORTS ===============
# All .py files are located inside: C:\Users\Medium Term Flood Forecast

import New_ECMWF_Ensemble_Forecast_15Days_Lead as ecmwf
import Tigge_EnsembleForecast_Extraction_HECHMSML as tigge
import Forecast_Weightage_Calculations as weightage
import Bias_Corrected_Data_all as bias_correction
import HEC_HMS_DSS as hec_dss
import HEC_HMS_DSS_Calibration as hec_calibration
import HEC_HMS_DSS_Gauge as hec_gauge

import CSV_Creation_For_HEC_HMS_GRU as csv_creation
import Hybrid_HEC_HMS_GRU_Final_Prediction as final_hec
import DischargeToStage_Conversion_GRU as discharge_to_stage
import Results_Hybrid_HEC_HMS_GRU as results_hybrid

# =============== GLOBAL CONFIG ===============
exe_path = r"C:\Users\Medium Term Flood Forecast\Run_All_HEC_HMS.exe"
log_file = "forecast_run_log.txt"

modules_phase1 = [
    (ecmwf, "New_ECMWF_Ensemble_Forecast_15Days_Lead"),
    (tigge, "Tigge_EnsembleForecast_Extraction_HECHMSML"),
    (weightage, "Forecast_Weightage_Calculations"),
    (bias_correction, "Bias_Corrected_Data_all"),
    (hec_dss, "HEC_HMS_DSS"),
    (hec_calibration, "HEC_HMS_DSS_Calibration"),
    (hec_gauge, "HEC_HMS_DSS_Gauge")
]

modules_phase2 = [
    (csv_creation, "CSV_Creation_For_HEC_HMS_GRU"),
    (final_hec, "Hybrid_HEC_HMS_GRU_Final_Prediction"),
    (discharge_to_stage, "DischargeToStage_Conversion_GRU"),
    (results_hybrid, "Results_Hybrid_HEC_HMS_GRU")
]

# =============== FUNCTIONS ===============

def run_module(module, name, delay=2):
    ts_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"{Fore.BLUE}[{ts_start}] Running: {name}{Style.RESET_ALL}")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{ts_start}] Running: {name}\n")

    time.sleep(delay)

    try:
        module.run()
        ts_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{Fore.GREEN}[{ts_end}] Completed: {name}{Style.RESET_ALL}\n")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{ts_end}] Completed: {name}\n")
    except Exception as e:
        print(f"{Fore.RED}Error in {name}: {e}{Style.RESET_ALL}")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"Error in {name}: {e}\n")

    time.sleep(delay)


def run_exe(exe_path, delay=2):
    name = "Run_All_HEC_HMS.exe"
    ts_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"{Fore.BLUE}[{ts_start}] Running: {name}{Style.RESET_ALL}")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{ts_start}] Running: {name}\n")

    try:
        subprocess.run([exe_path], check=False)
        ts_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{Fore.GREEN}[{ts_end}] Completed: {name}{Style.RESET_ALL}\n")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{ts_end}] Completed: {name}\n")
    except Exception as e:
        print(f"{Fore.RED}Error running EXE: {e}{Style.RESET_ALL}")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"Error running EXE: {e}\n")

    time.sleep(delay)


# =============== MAIN FORECAST PIPELINE ===============

def run_forecast():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{Fore.CYAN}[{ts}] Starting Forecast Process{Style.RESET_ALL}\n")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] Forecast started.\n")

    # ---- PHASE 1 ----
    for module, name in modules_phase1:
        run_module(module, name)

    # ---- RUN HEC-HMS EXE ----
    run_exe(exe_path)

    # ---- PHASE 2 ----
    for module, name in modules_phase2:
        run_module(module, name)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.CYAN}[{ts}] Forecast execution completed.{Style.RESET_ALL}\n")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] Forecast execution completed.\n")


# =============== SCHEDULER ===============

if __name__ == "__main__":
    schedule.every().day.at("08:30:00").do(run_forecast)

    print(f"{Fore.YELLOW}Scheduler started. Waiting for 08:30:00 daily...{Style.RESET_ALL}\n")

    while True:
        schedule.run_pending()
        print(f"{Fore.YELLOW}[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Waiting...{Style.RESET_ALL}")
        time.sleep(60)
