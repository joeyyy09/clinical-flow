
import pandas as pd
import os

def check_file():
    # Exact path found in previous step
    filepath = r"c:\Users\megha\clinical-flow\rules\dataset\Study 10_CPID_Input Files - Anonymization\Study 10_CPID_EDC_Metrics_URSV2.0_14-Nov-2025_updated.xlsx"
    
    print(f"Reading file: {filepath}")
    
    try:
        df = pd.read_excel(filepath)
        print(f"Columns found: {list(df.columns)}")
        
        # Look for the column
        target_col = [c for c in df.columns if "Responsible LF" in str(c)]
        
        if target_col:
            col_name = target_col[0]
            print(f"\nFound Target Column: '{col_name}'")
            
            # Check unique values
            unique_vals = df[col_name].dropna().unique().tolist()
            print(f"Unique Values in Column: {unique_vals}")
            
            if "John Doe" in unique_vals:
                print("\n✅ MATCH FOUND: 'John Doe' is in the file.")
            else:
                print("\n❌ NO MATCH: 'John Doe' is NOT in this file.")
        else:
            print("\n❌ Column 'Responsible LF' NOT found.")
            
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    check_file()
