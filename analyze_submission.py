import zipfile

z = zipfile.ZipFile('submission.zip')
files = [(i.filename, i.file_size/1024/1024) for i in z.filelist if i.file_size > 500000]
files.sort(key=lambda x: x[1], reverse=True)

total_size_mb = sum(f[1] for f in files)
print(f"Large files (>500KB) total: {total_size_mb:.2f} MB\n")
print(f"{'Size (MB)':<12} {'File'}")
print("-" * 80)

for filename, size_mb in files[:40]:
    print(f"{size_mb:>10.2f}   {filename}")

print(f"\nTotal zip size: {sum(i.file_size for i in z.filelist)/1024/1024:.2f} MB")
