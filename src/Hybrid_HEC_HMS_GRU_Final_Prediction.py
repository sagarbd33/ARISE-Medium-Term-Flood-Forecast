# -*- coding: utf-8 -*-
"""
Created on Sat Jul 26 15:41:36 2025
@author: AE-lab
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import get_custom_objects
from tensorflow.keras.initializers import Orthogonal
import pickle
import os

def run():
    # === Register initializer ===
    get_custom_objects().update({'Orthogonal': Orthogonal()})
    
    # === Define constants ===
    n_steps = 15
    days = [1, 3, 5, 7]
    
    # === Base directory paths ===
    base_dir = r"C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Bias Corrected Data\HEC-HMS-GRU"
    model_dir = os.path.join(base_dir, "1-3-5-7 Day HEC-HMS-GRU Model")
    output_dir = os.path.join(base_dir, "Hybrid Results")
    os.makedirs(output_dir, exist_ok=True)
    
    # === Function to prepare sequences ===
    def prepare_multivariate_data(data, n_steps):
        X, y = [], []
        for i in range(len(data) - n_steps):
            end_ix = i + n_steps
            seq_x = data.iloc[i:end_ix, :-1]  # input features
            seq_y = data.iloc[end_ix - 1, -1]  # target (last column)
            X.append(seq_x.values)
            y.append(seq_y)
        return np.array(X), np.array(y)
    
    # === Main loop for each model/day ===
    for day in days:
        print(f"\n--- Processing {day}-Day GRU Model ---")
    
        try:
            # === Define dynamic file paths ===
            model_path = os.path.join(model_dir, f"{day}day_Model_GRU.keras")
            scaler_path = os.path.join(model_dir, f"{day}day_Scaler_GRU.pkl")
            csv_path = os.path.join(base_dir, f"HEC-HMS-GRU ECMWF_{day}day_BiasCorrected (Ensemble).csv")
            output_csv = os.path.join(output_dir, f"Predictions_GRU_{day}day.csv")
    
            # === Load input CSV ===
            df = pd.read_csv(csv_path, parse_dates=['Date'], index_col='Date')
            print(f"Loaded data: {df.shape}, Columns: {df.columns.tolist()}")
    
            # === Prepare data ===
            X, y = prepare_multivariate_data(df, n_steps)
    
            # === Load scalers ===
            with open(scaler_path, 'rb') as f:
                scaler_X, scaler_y = pickle.load(f, encoding='latin1')  # Fix for compatibility
    
            # === Scale inputs ===
            X_scaled = scaler_X.transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
    
            # === Load model ===
            model = load_model(model_path)
    
            # === Make prediction ===
            y_pred_scaled = model.predict(X_scaled)
            y_pred_inv = scaler_y.inverse_transform(y_pred_scaled)
    
            # === Create output DataFrame ===
            prediction_dates = df.index[n_steps:]
            df_out = pd.DataFrame({
                'Date': prediction_dates,
                'Predicted': np.ravel(y_pred_inv)
            })
            df_out.to_csv(output_csv, index=False)
            print(f"Saved predictions to: {output_csv}")
    
            # # === Plot predictions ===
            # plt.figure(figsize=(18, 8))
            # plt.plot(prediction_dates, y_pred_inv, label=f'Predicted - {day} Day', color='blue')
            # plt.title(f"GRU Prediction - {day} Day Lead", fontsize=16)
            # plt.xlabel("Date", fontsize=14)
            # plt.ylabel("Predicted Discharge", fontsize=14)
            # plt.xticks(rotation=45)
            # plt.legend()
            # plt.grid(True)
            # plt.tight_layout()
            # plt.show()
    
        except Exception as e:
            print(f"Error in processing {day}-day model: {e}")

if __name__ == "__main__":
    run()