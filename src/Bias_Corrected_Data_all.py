# -*- coding: utf-8 -*-
"""
Created on Wed Jun 11 2025
Unified Bias Correction Script using XGBoost
"""

import pandas as pd
import joblib
import numpy as np
import os

def run():
    # Common configurations
    lead_days = [1, 3, 5, 7]
    
    base_input_dir = r'C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Weightage'
    base_output_dir = r'C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Bias Corrected Data'
    base_model_dir = r'C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Bias Correction Model (XGBoost)'
    
    # Category-specific configurations
    categories = [
        {
            "name": "Average Temp",
            "input_prefix": "At_Step_",
            "input_suffix": "_weightage.csv",
            "model_dir": "Average Temp",
            "columns": [f"Sub{sub}" for sub in range(1, 13)],
            "model_name": lambda lead, col: f"{lead}day_{col}_Tuned_XGBoost_BiasCorrection.pkl",
            "output_filename": lambda lead: f"At_Step_{lead}day.csv",
            "clip_zero": False
        },
        {
            "name": "Total Precipitation",
            "input_prefix": "tp_Step_",
            "input_suffix": "_weightage.csv",
            "model_dir": "Total Precipitation",
            "columns": ["Aizawl", "Sialsuk", "Neihbawi", "Kolasib", "Thingdawl",
                        "Lunglei", "Hnahthial", "Haulawng", "Mamit", "kawrtethawveng",
                        "Zawlnuam", "Serchhip", "Avg"],
            "model_name": lambda lead, col: f"{lead}day_{col}_Tuned_XGBoost_BiasCorrection.pkl",
            "output_filename": lambda lead: f"tp_Step_{lead}day.csv",
            "clip_zero": True
        },
        {
            "name": "Min Temp",
            "input_prefix": "mn2t6_Step_",
            "input_suffix": "_weightage.csv",
            "model_dir": "Min Temp",
            "columns": ["Avg"],
            "model_name": lambda lead, col: f"{lead}day_Avg_Tuned_XGBoost_BiasCorrection.pkl",
            "output_filename": lambda lead: f"mn2t6_Step_{lead}day.csv",
            "clip_zero": False
        },
        {
            "name": "Max Temp",
            "input_prefix": "mx2t6_Step_",
            "input_suffix": "_weightage.csv",
            "model_dir": "Max Temp",
            "columns": ["Avg"],
            "model_name": lambda lead, col: f"{lead}day_Avg_Tuned_XGBoost_BiasCorrection.pkl",
            "output_filename": lambda lead: f"mx2t6_Step_{lead}day.csv",
            "clip_zero": False
        },
        {
            "name": "Solar Radiation",
            "input_prefix": "ssr_Step_",
            "input_suffix": "_weightage.csv",
            "model_dir": "Solar Radiation",
            "columns": ["Avg"],
            "model_name": lambda lead, col: f"{lead}day_Avg_Tuned_XGBoost_BiasCorrection.pkl",
            "output_filename": lambda lead: f"ssr_Step_{lead}day.csv",
            "clip_zero": False
        }
    ]
    
    # Loop through each category
    for cat in categories:
        print(f"\nProcessing category: {cat['name']}")
        for lead in lead_days:
            input_file = f"{cat['input_prefix']}{lead}day{cat['input_suffix']}"
            input_path = os.path.join(base_input_dir, input_file)
    
            try:
                df = pd.read_csv(input_path, parse_dates=['Date'], index_col='Date')
            except Exception as e:
                print(f"Could not load {input_path}: {e}")
                continue
    
            corrected_df = pd.DataFrame(index=df.index)
    
            for col in cat['columns']:
                model_filename = cat['model_name'](lead, col)
                model_path = os.path.join(base_model_dir, cat['model_dir'], model_filename)
    
                if not os.path.exists(model_path):
                    print(f"Model missing for {col} at {lead}-day: {model_path}")
                    continue
    
                model = joblib.load(model_path)
                temp_df = df[[col]].rename(columns={col: 'Forecast'}).copy()
                temp_df['Forecast_Lag1'] = temp_df['Forecast'].shift(1)
                temp_df['DayOfYear'] = temp_df.index.dayofyear
                temp_df = temp_df.dropna()
    
                X = temp_df[['Forecast', 'Forecast_Lag1', 'DayOfYear']]
                bias_pred = model.predict(X)
                temp_df[col] = temp_df['Forecast'] + bias_pred
                corrected_df.loc[temp_df.index, col] = temp_df[col]
    
            corrected_df = corrected_df.dropna(how='any')
            if cat['clip_zero']:
                corrected_df = corrected_df.clip(lower=0)
    
            output_dir = os.path.join(base_output_dir, cat['name'])
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, cat['output_filename'](lead))
            corrected_df.to_csv(output_path)
            print(f"Saved: {output_path}")

if __name__ == "__main__":
    run()