import os
import pandas as pd

def run():
    # Base directories
    precip_dir = r"C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Bias Corrected Data\Total Precipitation"
    discharge_file = r"C:\Users\Medium Term Flood Forecast\Stepwise_Combined_CSVs_Ensemble_Mean\Observed Discharge\Discharge Obs.csv"
    
    # Forecast setup: step name, precip CSV, and corresponding .gage file
    forecast_files = {
        "1Day": {
            "precip_csv": "tp_Step_1day.csv",
            "gage_path": r"C:\Users\Medium Term Flood Forecast\HEC-HMS\1Day_Forecast\1Day_Forecast.gage"
        },
        "3Day": {
            "precip_csv": "tp_Step_3day.csv",
            "gage_path": r"C:\Users\Medium Term Flood Forecast\HEC-HMS\3Day_Forecast\3Day_Forecast.gage"
        },
        "5Day": {
            "precip_csv": "tp_Step_5day.csv",
            "gage_path": r"C:\Users\Medium Term Flood Forecast\HEC-HMS\5Day_Forecast\5Day_Forecast.gage"
        },
        "7Day": {
            "precip_csv": "tp_Step_7day.csv",
            "gage_path": r"C:\Users\Medium Term Flood Forecast\HEC-HMS\7Day_Forecast\7Day_Forecast.gage"
        }
    }
    
    # Helper: format dates with/without dash depending on OS
    def format_date(dt):
        return dt.strftime("%#d %B %Y, 00:00") if os.name == 'nt' else dt.strftime("%-d %B %Y, 00:00")
    
    # Load discharge dates once
    df_discharge = pd.read_csv(discharge_file, parse_dates=["Date"])
    dis_start = format_date(df_discharge["Date"].min())
    dis_end = format_date(df_discharge["Date"].max())
    
    # Update each forecast .gage file
    for step, info in forecast_files.items():
        try:
            # Load precipitation file and get date range
            precip_path = os.path.join(precip_dir, info["precip_csv"])
            df_precip = pd.read_csv(precip_path, parse_dates=["Date"])
            prec_start = format_date(df_precip["Date"].min())
            prec_end = format_date(df_precip["Date"].max())
    
            gage_file = info["gage_path"]
            with open(gage_file, 'r') as file:
                lines = file.readlines()
    
            updated_lines = []
            inside_variant = False
            current_gage = ""
    
            for line in lines:
                stripped = line.strip()
                # Track current gage name
                if stripped.startswith("Gage:"):
                    current_gage = stripped.replace("Gage:", "").strip()
                # Detect inside Variant block
                if stripped.startswith("Variant:"):
                    inside_variant = True
                if stripped.startswith("End Variant:"):
                    inside_variant = False
    
                # If inside variant, adjust start/end based on gage type
                if inside_variant and stripped.startswith("Start Time:"):
                    if current_gage.lower() == "bairabi":
                        updated_lines.append(f"       Start Time: {dis_start}\n")
                    else:
                        updated_lines.append(f"       Start Time: {prec_start}\n")
                elif inside_variant and stripped.startswith("End Time:"):
                    if current_gage.lower() == "bairabi":
                        updated_lines.append(f"       End Time: {dis_end}\n")
                    else:
                        updated_lines.append(f"       End Time: {prec_end}\n")
                else:
                    updated_lines.append(line)
    
            # Save updated .gage file
            with open(gage_file, 'w') as file:
                file.writelines(updated_lines)
    
            print(f"Updated .gage file for {step}: {gage_file}")
    
        except Exception as e:
            print(f"Failed to update .gage file for {step}: {e}")

if __name__ == "__main__":
    run()