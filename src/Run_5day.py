# -*- coding: utf-8 -*-
"""
Created on Thu Jul 24 15:15:54 2025

@author: AE-lab
"""

from hms.model import Project
from hms import Hms

# Open your .hms project file
myProject = Project.open('C:/Users/Medium Term Flood Forecast/HEC-HMS/5Day_Forecast/5Day_Forecast.hms')

# Run the compute for the specified simulation (e.g., "Cal")
myProject.computeRun('Cal')

# Close the project
myProject.close()

# Shutdown the HMS engine
Hms.shutdownEngine()