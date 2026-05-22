# -*- coding: utf-8 -*-
"""
Created on Sun Aug 10 18:30:00 2025
@author: AE-lab
"""

import pandas as pd
import numpy as np
import os
import joblib

def run():
    # === Define constants ===
    days = [1, 3, 5, 7]
    
    # === Base directory paths (UPDATED for XGBoost) ===
    base_dir = r"C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Bias Corrected Data\HEC-HMS-GRU\Hybrid Results"
    model_dir = os.path.join(base_dir, "1-3-5-7 Day Stage XGBoast Model")
    output_dir = os.path.join(base_dir, "Stage Results")
    os.makedirs(output_dir, exist_ok=True)
    
    # === Main loop for each model/day ===
    for day in days:
        print(f"\n--- Processing {day}-Day Stage XGBoost Model ---")
    
        try:
            # === Define dynamic file paths ===
            model_path = os.path.join(model_dir, f"{day}day_Tuned_XGBoost.pkl")
            csv_path = os.path.join(base_dir, f"Predictions_GRU_{day}day.csv")  # raw GRU predictions before bias correction
            output_csv = os.path.join(output_dir, f"Predictions_Stage_XGBoost_{day}day.csv")
    
            # === Load input CSV (only Date & Predicted) ===
            df = pd.read_csv(csv_path, parse_dates=['Date'])
            print(f"Loaded data: {df.shape}, Columns: {df.columns.tolist()}")
    
            # === Feature engineering (same as training) ===
            df['Predicted_Lag1'] = df['Predicted'].shift(1)
            df['DayOfYear'] = df['Date'].dt.dayofyear
            df = df.dropna()  # remove first row with NaN lag
    
            # === Features ===
            X_features = df[['Predicted', 'Predicted_Lag1', 'DayOfYear']]
    
            # === Load tuned XGBoost model ===
            model = joblib.load(model_path)
    
            # === Predict bias and correct forecast ===
            bias_pred = model.predict(X_features)
            df['Predicted'] = df['Predicted'] + bias_pred  # overwrite with corrected values
    
            # === Save output (only Date & Predicted) ===
            df[['Date', 'Predicted']].to_csv(output_csv, index=False)
    
            print(f"Saved corrected predictions to: {output_csv}")
    
        except Exception as e:
            print(f"Error in processing {day}-day stage model: {e}")

if __name__ == "__main__":
    run()