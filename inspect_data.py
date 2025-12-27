
import os
import pandas as pd
import glob

# specific file patterns to check
patterns = [
    "*SAE Dashboard*",
    "*Global_Missing_Pages*",
    "*Visit Projection Tracker*",
    "*EDC_Metrics*",
    "*Compiled_EDRR*"
]

base_dir = "/Users/harshithhh/Desktop/Nest-Assignment/data/QC Anonymized Study Files"

def find_first_file(pattern):
    # recursive search
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if any(x in file for x in pattern.replace("*","").split(" ")): # Simple fuzzy match since names vary
                if "SAE Dashboard" in pattern and "SAE Dashboard" in file: return os.path.join(root, file)
                if "Global_Missing_Pages" in pattern and "Global_Missing_Pages" in file: return os.path.join(root, file)
                if "Visit Projection Tracker" in pattern and "Visit Projection Tracker" in file: return os.path.join(root, file)
                if "EDC_Metrics" in pattern and "EDC_Metrics" in file: return os.path.join(root, file)
                if "Compiled_EDRR" in pattern and "Compiled_EDRR" in file: return os.path.join(root, file)
    return None

print("Scanning file headers...")
for p in patterns:
    f = find_first_file(p)
    if f:
        try:
            # Read first few rows just to get columns
            df = pd.read_excel(f, nrows=5)
            print(f"\n--- File Type: {p} ---")
            print(f"File: {os.path.basename(f)}")
            print("Columns:", list(df.columns))
        except Exception as e:
            print(f"Error reading {f}: {e}")
    else:
        print(f"Could not find example for {p}")
