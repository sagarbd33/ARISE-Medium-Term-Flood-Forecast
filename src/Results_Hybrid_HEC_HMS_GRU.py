# -*- coding: utf-8 -*-
"""
Created on Sat Aug  2 17:08:29 2025

@author: AE-lab
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from sklearn.metrics import mean_squared_log_error

# === Danger Level Thresholds per Lead Time (in metres) ===
# Based on percentile analysis of stage predictions
DANGER_THRESHOLDS = {
    1: {"Normal": 11.454, "Watch": 12.794, "Warning": 13.961, "Severe Warning": 14.585},
    3: {"Normal": 11.551, "Watch": 12.889, "Warning": 14.022, "Severe Warning": 14.433},
    5: {"Normal": 11.531, "Watch": 12.883, "Warning": 14.111, "Severe Warning": 14.657},
    7: {"Normal": 11.470, "Watch": 12.915, "Warning": 14.040, "Severe Warning": 14.514},
}

def classify_danger_level(stage_value, lead_days):
    """
    Classify the flood danger level based on the predicted stage value
    and corresponding lead-time-specific percentile thresholds.

    Levels:
      - Normal         : stage < 50th percentile
      - Watch          : 50th–75th percentile
      - Warning        : 75th–90th percentile
      - Severe Warning : 90th–95th percentile
      - Extreme Danger : > 95th percentile

    Parameters
    ----------
    stage_value : float
        Predicted water stage in metres.
    lead_days : int
        Forecast lead time (1, 3, 5, or 7 days).

    Returns
    -------
    str
        One of the five danger-level labels.
    """
    thresholds = DANGER_THRESHOLDS[lead_days]

    if stage_value < thresholds["Normal"]:
        return "Normal"
    elif stage_value < thresholds["Watch"]:
        return "Watch"
    elif stage_value < thresholds["Warning"]:
        return "Warning"
    elif stage_value < thresholds["Severe Warning"]:
        return "Severe Warning"
    else:
        return "Extreme Danger"


def run():
    # === Base folder paths ===
    base_path = r"C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Bias Corrected Data\HEC-HMS-GRU\Hybrid Results"
    stage_path = os.path.join(base_path, "Stage Results")

    # === File info: (discharge_file, stage_file, lead_time_days) ===
    files_info = [
        ("Predictions_GRU_1day.csv", "Predictions_Stage_XGBoost_1day.csv", 1),
        ("Predictions_GRU_3day.csv", "Predictions_Stage_XGBoost_3day.csv", 3),
        ("Predictions_GRU_5day.csv", "Predictions_Stage_XGBoost_5day.csv", 5),
        ("Predictions_GRU_7day.csv", "Predictions_Stage_XGBoost_7day.csv", 7),
    ]

    # === Observed data path ===
    obs_path = r"C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Observed Discharge\Discharge Obs.csv"
    df_obs = pd.read_csv(obs_path)
    df_obs['Date'] = pd.to_datetime(df_obs['Date'])

    # Read 1-day file to get base date
    df_1day = pd.read_csv(os.path.join(base_path, "Predictions_GRU_1day.csv"))
    base_date_str = df_1day['Date'].iloc[-1]
    base_date = datetime.strptime(base_date_str, "%Y-%m-%d")

    # Forecast issued date (1 day before the prediction date)
    issued_date = base_date - timedelta(days=1)
    issued_date_str = issued_date.strftime("%Y-%m-%d")

    # Header
    header = "1 to 7 Day Lead Streamflow Forecast Based on ECMWF Ensemble:"
    print(header)
    results = [header]

    # === Function to compute metrics ===
    def compute_metrics(y_actual, y_pred):
        rmse = np.sqrt(np.mean((y_actual - y_pred) ** 2))
        std_dev = np.std(y_actual)
        rsr = rmse / std_dev
        nse = 1 - (np.sum((y_actual - y_pred) ** 2) /
                   np.sum((y_actual - np.mean(y_actual)) ** 2))
        mae = np.mean(np.abs(y_actual - y_pred))
        rmsle = np.sqrt(mean_squared_log_error(y_actual, y_pred))
        pbias = 100 * np.sum(y_pred - y_actual) / np.sum(y_actual)
        return nse, rmse, mae, rmsle, pbias, rsr

    # Store metrics for table printing later
    metrics_rows = []

    # Process each forecast file
    for discharge_file, stage_file, lead in files_info:
        # Read discharge predictions
        df_pred = pd.read_csv(os.path.join(base_path, discharge_file))
        df_pred['Date'] = pd.to_datetime(df_pred['Date'])

        # Merge with observed data
        df_merged = pd.merge(df_pred, df_obs, on='Date', how='inner')
        y_actual = df_merged['Bairabi'].values
        y_pred = df_merged['Predicted'].values

        # Compute metrics
        nse, rmse, mae, rmsle, pbias, rsr = compute_metrics(y_actual, y_pred)

        # Last forecast value for discharge
        forecast_value_discharge = df_pred['Predicted'].iloc[-1]

        # Read stage predictions & get last value
        df_stage = pd.read_csv(os.path.join(stage_path, stage_file))
        forecast_value_stage = df_stage['Predicted'].iloc[-1]

        # Classify danger level based on forecasted stage and lead time
        danger_level = classify_danger_level(forecast_value_stage, lead)

        # Forecast date
        forecast_date = issued_date + timedelta(days=lead)
        forecast_date_str = forecast_date.strftime("%Y-%m-%d")

        # Create output line with discharge, stage, and danger level only
        line = (
            f"{forecast_date_str} - Discharge: {forecast_value_discharge:.6f} m^3/s & "
            f"Stage: {forecast_value_stage:.3f} m "
            f"| Danger Level: {danger_level} "
            f"({lead} Day Lead Forecast for {issued_date_str})"
        )

        print(line)
        results.append(line)

        # Store metrics for table
        metrics_rows.append({
            "Lead": f"{lead}-Day",
            "NSE": nse,
            "RMSE": rmse,
            "MAE": mae,
            "RMSLE": rmsle,
            "PBIAS": pbias,
            "RSR": rsr,
        })

    # === Performance Metrics Table ===
    obs_start_date = df_obs['Date'].min().strftime("%Y-%m-%d")
    obs_end_date = df_obs['Date'].max().strftime("%Y-%m-%d")

    results.append("")
    duration_line = (
        f"Performance evaluation based on observed discharge "
        f"from {obs_start_date} to {obs_end_date}"
    )
    print("\n" + duration_line)
    results.append(duration_line)

    # Build and print metrics table
    results.append("")
    col_w = {"Lead": 8, "NSE": 10, "RMSE": 10, "MAE": 10, "RMSLE": 10, "PBIAS": 12, "RSR": 10}
    header_row = (f"{'Lead':<{col_w['Lead']}} {'NSE':>{col_w['NSE']}} {'RMSE':>{col_w['RMSE']}} "
                  f"{'MAE':>{col_w['MAE']}} {'RMSLE':>{col_w['RMSLE']}} "
                  f"{'PBIAS':>{col_w['PBIAS']}} {'RSR':>{col_w['RSR']}}")
    sep_row = "-" * len(header_row)

    print(sep_row)
    print(header_row)
    print(sep_row)
    results.append(sep_row)
    results.append(header_row)
    results.append(sep_row)

    for r in metrics_rows:
        data_row = (f"{r['Lead']:<{col_w['Lead']}} {r['NSE']:>{col_w['NSE']}.4f} "
                    f"{r['RMSE']:>{col_w['RMSE']}.4f} {r['MAE']:>{col_w['MAE']}.4f} "
                    f"{r['RMSLE']:>{col_w['RMSLE']}.4f} {r['PBIAS']:>{col_w['PBIAS']}.4f} "
                    f"{r['RSR']:>{col_w['RSR']}.4f}")
        print(data_row)
        results.append(data_row)

    print(sep_row)
    results.append(sep_row)

    # === Append danger level legend ===
    results.append("")
    results.append("Danger Level Classification Thresholds (Stage in metres):")
    results.append(f"{'Lead':<8} {'Normal (<50th)':<18} {'Watch (50–75th)':<18} "
                   f"{'Warning (75–90th)':<20} {'Severe Warn (90–95th)':<24} Extreme Danger (>95th)")
    for lead_day, thresh in DANGER_THRESHOLDS.items():
        results.append(
            f"{str(lead_day)+' day':<8} "
            f"{'< '+str(thresh['Normal']):<18} "
            f"{str(thresh['Normal'])+' – '+str(thresh['Watch']):<18} "
            f"{str(thresh['Watch'])+' – '+str(thresh['Warning']):<20} "
            f"{str(thresh['Warning'])+' – '+str(thresh['Severe Warning']):<24} "
            f"> {thresh['Severe Warning']}"
        )

    # Save output to text file
    output_txt_path = os.path.join(base_path, "ECMWF_Streamflow_Forecast_Summary.txt")
    with open(output_txt_path, "w") as f:
        for line in results:
            f.write(line + "\n")

    print(f"\nForecast summary saved to: {output_txt_path}")


if __name__ == "__main__":
    run()
