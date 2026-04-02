import os
import zipfile
import sys

# Configuration
OUTPUT_FILENAME = 'submission.zip'
MAX_FILE_SIZE_MB = 20  # Global limit for any single file
strict_limit_folders = {'rules', 'uploads'}
STRICT_FILE_SIZE_MB = 1 # Stricter limit for data/rules folders

IGNORE_DIRS = {
    '.git', 'node_modules', 'venv', '.venv', 'env', '__pycache__', 
    '.idea', '.vscode', 'dist', 'build', 'coverage', 'tmp', 'temp',
    'Screen Recordings', 'data'  # Exclude data folder - judges will upload their own
}
IGNORE_EXTS = {'.pyc', '.pyo', '.pyd', '.log', '.idb', '.pdb', '.db-journal', '.mp4', '.zip'}
# Specific strict exclusions if needed (relative paths)
EXCLUDE_PATHS = {
    'submission.zip', 
    'cleanup_submission.py',
    'check_size.py',
    'size_report.txt',
    'analyze_zip.py',
    'analysis_results.txt',
    'backend/clinical_trials.db' # Explicitly exclude the big DB
}

def create_submission_zip():
    cwd = os.getcwd()
    zip_filename = os.path.join(cwd, OUTPUT_FILENAME)
    
    print(f"Preparing to zip contents of: {cwd}")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(cwd):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, cwd)
                
                # Check exclusions
                if rel_path.replace('\\', '/') in EXCLUDE_PATHS:
                    print(f"Skipping excluded path: {rel_path}")
                    continue
                if file in EXCLUDE_PATHS: # check filename match too
                     print(f"Skipping excluded file: {file}")
                     continue

                if any(file.endswith(ext) for ext in IGNORE_EXTS):
                    continue
                
                # Dynamic Logic: Check if we are in a 'data' or 'rules' folder
                # and apply stricter size limits
                is_strict_folder = any(f in rel_path.split(os.sep) for f in strict_limit_folders)
                
                # Size check
                try:
                    size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    
                    limit = STRICT_FILE_SIZE_MB if is_strict_folder else MAX_FILE_SIZE_MB
                    
                    if size_mb > limit:
                        print(f"WARNING: Skipping large file {rel_path} ({size_mb:.2f} MB > {limit} MB)")
                        continue
                except OSError:
                    print(f"Error accessing {rel_path}, skipping.")
                    continue
                
                print(f"Adding: {rel_path}")
                zipf.write(file_path, rel_path)
                
    print(f"\nSuccessfully created {OUTPUT_FILENAME}")
    try:
        final_size = os.path.getsize(zip_filename) / (1024 * 1024)
        print(f"Final Zip Size: {final_size:.2f} MB")
    except:
        pass

if __name__ == "__main__":
    create_submission_zip()
