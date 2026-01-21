
import pandas as pd
import glob
import os

files = glob.glob('rules/dataset/STUDY 15_CPID_Input Files - Anonymization/*CPID_EDC_Metrics*.xlsx')
filepath = files[0]

print(f"Reading {filepath}")
df_raw = pd.read_excel(filepath, header=None, nrows=5)
rows = [df_raw.iloc[i].tolist() for i in range(4)]

with open('debug_rows.txt', 'w') as f:
    for i in range(len(rows[0])):
        vals = [str(r[i]).strip().replace('\n', ' ') for r in rows]
        f.write(f"Idx {i}: {vals}\n")

# Check key metrics
print("\nCheck Mapping:")
check = ['Missing Visits', 'Missing Page', '# Total Queries', 'Protocol Deviations', '% Clean Entered CRF']
for c in check:
    # Basic loose match
    matched = [x for x in new_columns if c in x]
    print(f"'{c}' matches: {matched}")
