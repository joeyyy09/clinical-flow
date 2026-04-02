import os

IGNORE_DIRS = {
    '.git', 'node_modules', 'venv', '.venv', 'env', '__pycache__', 
    '.idea', '.vscode', 'dist', 'build', 'coverage', 'tmp', 'temp',
    'rules', 'data', 'uploads'
}

def analyze_zip_content():
    files_list = []
    total_size = 0
    
    print("Scanning...")
    for root, dirs, files in os.walk('.'):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file == 'clinical_trials.db' or file == 'submission.zip':
                continue
                
            path = os.path.join(root, file)
            try:
                size = os.path.getsize(path)
                files_list.append((path, size))
                total_size += size
            except:
                pass
                
    files_list.sort(key=lambda x: x[1], reverse=True)
    
    print(f"Total Content Size: {total_size/1024/1024:.2f} MB")
    print("\nTop 20 Largest Files:")
    for path, size in files_list[:20]:
        print(f"{size/1024/1024:.2f} MB - {path}")

if __name__ == "__main__":
    analyze_zip_content()
