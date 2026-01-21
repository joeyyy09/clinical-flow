
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

base_dir = "data"

def find_first_file(pattern):
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.startswith("~$"): continue
            # Check pattern match
            keyword = pattern.replace("*", "")
            if keyword in file:
                 return os.path.join(root, file)
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
