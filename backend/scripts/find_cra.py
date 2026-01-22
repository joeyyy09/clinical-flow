
import os
import pandas as pd
import glob

def find_cra():
    # Base directory for dataset
    base_dir = r"c:\Users\megha\clinical-flow\rules\dataset"
    search_terms = ["John Doe", "Jane Smith"]
    
    print(f"Searching for {search_terms} in {base_dir}...")
    
    # Recursively find all xlsx files
    files = glob.glob(os.path.join(base_dir, "**/*.xlsx"), recursive=True)
    
    for filepath in files:
        try:
            # Read all sheets
            xls = pd.ExcelFile(filepath)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                
                # Convert whole dataframe to string to search
                # This is expensive but exact
                for term in search_terms:
                    # Check if term exists in the dataframe
                    mask = df.astype(str).apply(lambda x: x.str.contains(term, case=False, na=False))
                    if mask.any().any():
                        print(f"\n[FOUND!] Term: '{term}'")
                        print(f"File: {os.path.basename(filepath)}")
                        print(f"Path: {filepath}")
                        print(f"Sheet: {sheet_name}")
                        
                        # Find exact column
                        for col in df.columns:
                            if df[col].astype(str).str.contains(term, case=False).any():
                                print(f"Column: {col}")
                                # Print first few matches
                                matches = df[df[col].astype(str).str.contains(term, case=False)]
                                print(f"Row Indices (0-based): {matches.index.tolist()[:5]}")
                                return # Stop after finding one file to avoid spamming 
                                
        except Exception as e:
            pass # Skip corrupted files

if __name__ == "__main__":
    find_cra()
