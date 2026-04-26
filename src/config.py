

import pandas as pd
import numpy as np
import re
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent #config.py -> current folder -> project folder
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) #current folder of config files


production_file = os.path.join(CURRENT_DIR, "..", "productions.xlsx")  
vendor_folder = os.path.join(CURRENT_DIR, "..", "vendor")
debug_folder = os.path.join(PROJECT_ROOT, "debugs")  
output_folder = PROJECT_ROOT #/ "outputs" , open if you want to create a specific folder
output_folder.mkdir(parents=True, exist_ok=True)



BIG_M = 99999
START_DATE = pd.to_datetime("22/12/2025", dayfirst=True) #origin 12/12/25, #date_range = pd.date_range(START_DATE, END_DATE, freq="D")
END_DATE   = pd.to_datetime("05/05/2026", dayfirst=True)



SHEET_NAME_INFEASIBLITY = [
    "01_Supply_Demand_Analysis",
    "02_Detail_Item_Analysis",
    "03_Revenue_Analysis",
    "04_Relaxation_Options",
    "00_Model_Info"]