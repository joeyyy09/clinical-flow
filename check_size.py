import os

def get_dir_size(start_path):
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    try:
                        total_size += os.path.getsize(fp)
                    except:
                        pass
    except:
        pass
    return total_size

print("--- Backend ---")
base = 'backend'
if os.path.exists(base):
    for d in os.listdir(base):
        path = os.path.join(base, d)
        if os.path.isdir(path):
            print(f"{path}: {get_dir_size(path)/1024/1024:.2f} MB")
        else:
            print(f"{path}: {os.path.getsize(path)/1024/1024:.2f} MB")

print("\n--- Rules ---")
base = 'rules'
if os.path.exists(base):
    for d in os.listdir(base):
        path = os.path.join(base, d)
        if os.path.isdir(path):
            print(f"{path}: {get_dir_size(path)/1024/1024:.2f} MB")
        else:
            print(f"{path}: {os.path.getsize(path)/1024/1024:.2f} MB")
