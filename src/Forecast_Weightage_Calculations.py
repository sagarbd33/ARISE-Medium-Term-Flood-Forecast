# -*- coding: utf-8 -*-
"""
Created on Mon Jun  9 17:18:52 2025

@author: AE-lab
"""

import pandas as pd
import glob
import os

def run():
    # Input directory with original CSVs
    input_dir = "C:/Users/Medium Term Flood Forecast/Stepwise_Combined_CSVs_Ensemble_Mean"
    
    # Create output directory
    output_dir = os.path.join(input_dir, "Weightage")
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all CSV files in input directory
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    
    for file_path in csv_files:
        # Load CSV file
        df = pd.read_csv(file_path)
    
        # Rename 'valid_time' to 'Date' if it exists
        if 'valid_time' in df.columns:
            df = df.rename(columns={'valid_time': 'Date'})
    
        # Calculate Sub1 to Sub12
        df['Sub1'] = ((210.7367526 * df['Haulawng']) +
                      (3.964544686 * df['Hnahthial']) +
                      (3.821651695 * df['Zawlnuam']) +
                      (132.9233174 * df['Lunglei']) +
                      (71.71401451 * df['Sialsuk'])) / 423.1602809
    
        df['Sub2'] = ((21.96312022 * df['Thingdawl']) +
                      (34.24568445 * df['Zawlnuam']) +
                      (297.8028957 * df['Sialsuk'])) / 354.0117003
    
        df['Sub3'] = ((164.6397638 * df['Thingdawl']) +
                      (7.907731379 * df['Sialsuk'])) / 172.5474952
    
        df['Sub4'] = ((60.46047457 * df['Thingdawl']) +
                      (33.544141 * df['Aizawl'])) / 94.00461557
    
        df['Sub5'] = ((1.255568276 * df['Thingdawl']) +
                      (2.00799651 * df['Neihbawi']) +
                      (152.0099395 * df['Aizawl']) +
                      (20.95262587 * df['Mamit'])) / 176.2261302
    
        df['Sub6'] = ((59.51550677 * df['Kolasib']) +
                      (247.2011454 * df['Neihbawi']) +
                      (34.6702436 * df['Aizawl']) +
                      (167.5708274 * df['Mamit'])) / 508.9577231
    
        df['Sub7'] = ((20.10252579 * df['Haulawng']) +
                      (220.4464799 * df['Thingdawl']) +
                      (309.3575917 * df['Sialsuk']) +
                      (19.70757895 * df['kawrtethawveng']) +
                      (44.25727111 * df['Aizawl']) +
                      (250.1430233 * df['Mamit'])) / 864.0144708
    
        df['Sub8'] = ((164.667085 * df['Kolasib']) +
                      (4.884321419 * df['Serchhip']) +
                      (28.43755577 * df['Mamit'])) / 197.9889622
    
        df['Sub9'] = df['Kolasib']
    
        df['Sub10'] = ((5.078828484 * df['Thingdawl']) +
                       (1.165789103 * df['Kolasib']) +
                       (315.1074521 * df['kawrtethawveng']) +
                       (178.496831 * df['Serchhip']) +
                       (212.7432653 * df['Mamit'])) / 712.592166
    
        df['Sub11'] = ((3.776659526 * df['Kolasib']) +
                       (1.16784357 * df['Serchhip'])) / 4.945358991
    
        df['Sub12'] = df['Kolasib']
    
        # Compute average
        sub_cols = [f'Sub{i}' for i in range(1, 13)]
        df['Avg'] = df[sub_cols].mean(axis=1)
    
        # Create new output file path in 'Weightage' folder
        base_name = os.path.basename(file_path)
        name_without_ext = os.path.splitext(base_name)[0]
        output_file = os.path.join(output_dir, f"{name_without_ext}_weightage.csv")
    
        # Save output file
        df.to_csv(output_file, index=False)
    
    print("All files processed and saved in 'Weightage' folder.")
    
if __name__ == "__main__":
    run()