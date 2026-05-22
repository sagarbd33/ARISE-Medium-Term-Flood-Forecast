# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 2025
Final Script: DSS Generation for Multi-step Forecasts
"""

import os
from datetime import datetime
import pandas as pd
from pydsstools.heclib.dss import HecDss
from pydsstools.core import TimeSeriesContainer

def run():
    # Discharge File
    discharge_file = r"C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Observed Discharge\Discharge Obs.csv"
    discharge_station = "Bairabi"
    
    # Forecast configurations
    forecast_configs = {
        'Step_1day': {
            'precip_file': r'C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Bias Corrected Data\Total Precipitation\tp_Step_1day.csv',
            'temp_file': r'C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Bias Corrected Data\Average Temp\At_Step_1day.csv',
            'output_dss': r'C:\Users\Medium Term Flood Forecast\HEC-HMS\1Day_Forecast\1Day_Forecast.dss'
        },
        'Step_3day': {
            'precip_file': r'C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Bias Corrected Data\Total Precipitation\tp_Step_3day.csv',
            'temp_file': r'C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Bias Corrected Data\Average Temp\At_Step_3day.csv',
            'output_dss': r'C:\Users\Medium Term Flood Forecast\HEC-HMS\3Day_Forecast\3Day_Forecast.dss'
        },
        'Step_5day': {
            'precip_file': r'C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Bias Corrected Data\Total Precipitation\tp_Step_5day.csv',
            'temp_file': r'C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Bias Corrected Data\Average Temp\At_Step_5day.csv',
            'output_dss': r'C:\Users\Medium Term Flood Forecast\HEC-HMS\5Day_Forecast\5Day_Forecast.dss'
        },
        'Step_7day': {
            'precip_file': r'C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Bias Corrected Data\Total Precipitation\tp_Step_7day.csv',
            'temp_file': r'C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Bias Corrected Data\Average Temp\At_Step_7day.csv',
            'output_dss': r'C:\Users\Medium Term Flood Forecast\HEC-HMS\7Day_Forecast\7Day_Forecast.dss'
        }
    }
    
    # Station lists
    precip_stations = ["Aizawl", "Sialsuk", "Neihbawi", "Kolasib", "Thingdawl", "Lunglei",
                       "Hnahthial", "Haulawng", "Mamit", "kawrtethawveng", "Zawlnuam", "Serchhip"]
    temp_stations = ["Sub1", "Sub2", "Sub3", "Sub4", "Sub5", "Sub6",
                     "Sub7", "Sub8", "Sub9", "Sub10", "Sub11", "Sub12"]
    
    # Read discharge once
    df_discharge = pd.read_csv(discharge_file, parse_dates=["Date"])
    discharge_start_date = df_discharge["Date"].iloc[0]
    discharge_datetime_str = discharge_start_date.strftime("%d%b%Y %H:%M:%S")
    discharge_partD = discharge_start_date.strftime("%d%b%Y").upper()
    discharge_values = df_discharge[discharge_station].astype(float).fillna(0).values
    
    # Loop through each forecast step
    for step, cfg in forecast_configs.items():
        df_precip = pd.read_csv(cfg['precip_file'], parse_dates=["Date"])
        df_temp = pd.read_csv(cfg['temp_file'], parse_dates=["Date"])
        
        start_date = df_precip["Date"].iloc[0]
        start_datetime_str = start_date.strftime("%d%b%Y %H:%M:%S")
        partD = start_date.strftime("%d%b%Y").upper()
    
        os.makedirs(os.path.dirname(cfg['output_dss']), exist_ok=True)
    
        with HecDss.Open(cfg['output_dss']) as fid:
            # Write Precipitation
            for station in precip_stations:
                if station in df_precip.columns:
                    values = df_precip[station].astype(float).fillna(0).values
                    pathname = f"//{station.upper()}/PRECIP-INC/{partD}/1DAY/GAGE/"
                    tsc = TimeSeriesContainer()
                    tsc.pathname = pathname
                    tsc.startDateTime = start_datetime_str
                    tsc.numberValues = len(values)
                    tsc.units = "MM"
                    tsc.type = "PER-CUM"
                    tsc.interval = 1440
                    tsc.values = values
    
                    fid.deletePathname(pathname)
                    fid.put_ts(tsc)
                    print(f"Precipitation written: {station} for {step}")
    
            # Write Temperature
            for station in temp_stations:
                if station in df_temp.columns:
                    values = df_temp[station].astype(float).fillna(0).values
                    pathname = f"//{station.upper()}/TEMPERATURE/{partD}/1DAY/GAGE/"
                    tsc = TimeSeriesContainer()
                    tsc.pathname = pathname
                    tsc.startDateTime = start_datetime_str
                    tsc.numberValues = len(values)
                    tsc.units = "C"
                    tsc.type = "PER-AVER"
                    tsc.interval = 1440
                    tsc.values = values
    
                    fid.deletePathname(pathname)
                    fid.put_ts(tsc)
                    print(f"Temperature written: {station} for {step}")
    
            # Write Discharge (same for all steps)
            pathname = f"//{discharge_station.upper()}/FLOW/{discharge_partD}/1DAY/GAGE/"
            tsc = TimeSeriesContainer()
            tsc.pathname = pathname
            tsc.startDateTime = discharge_datetime_str
            tsc.numberValues = len(discharge_values)
            tsc.units = "CMS"
            tsc.type = "INST-VAL"
            tsc.interval = 1440
            tsc.values = discharge_values
    
            fid.deletePathname(pathname)
            fid.put_ts(tsc)
            print(f"Discharge written: {discharge_station} for {step}")
    
    print("\nAll DSS files successfully created.")

if __name__ == "__main__":
    run()