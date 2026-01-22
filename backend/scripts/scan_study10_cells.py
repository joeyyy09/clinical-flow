
import pandas as pd
import os

def scan_file():
    filepath = r"c:\Users\megha\clinical-flow\rules\dataset\Study 10_CPID_Input Files - Anonymization\Study 10_CPID_EDC_Metrics_URSV2.0_14-Nov-2025_updated.xlsx"
    print(f"Scanning file: {filepath}")
    
    try:
        # Read without header assumption to get raw grid
        df = pd.read_excel(filepath, header=None)
        
        target = "John Doe"
        found = False
        
        # Iterate over all cells (efficiently as possible)
        # Check columns one by one
        for col_idx, col_name in enumerate(df.columns):
            # Convert column to string
            col_data = df[col_name].astype(str)
            
            # Find matches
            matches = col_data[col_data.str.contains(target, case=False, na=False)]
            
            if not matches.empty:
                found = True
                print(f"\n✅ FOUND '{target}'!")
                print(f"Column Index: {col_idx} (Excel Column: {get_excel_col(col_idx)})")
                
                # Print first 3 rows
                for row_idx in matches.index[:3]:
                    print(f"Row Index: {row_idx} (Excel Row: {row_idx + 1})")
                    
                # Also try to find a header for this column
                # Look at rows 0-4
                print("Potential Headers above this data:")
                for r in range(5):
                    val = df.iloc[r, col_idx]
                    print(f"Row {r+1}: {val}")
                    
                break # Found the column, stop
        
        if not found:
            print(f"\n❌ '{target}' NOT found in the entire grid.")

    except Exception as e:
        print(f"Error: {e}")

def get_excel_col(idx):
    # simple converter 0->A, 25->Z, 26->AA
    n = idx + 1
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string

if __name__ == "__main__":
    scan_file()
