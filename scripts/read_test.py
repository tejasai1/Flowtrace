import sys

from flowtrace.reader import read_repository

path = sys.argv[1] if len(sys.argv) > 1 else "."
files = read_repository(path)

print(f"Read {len(files)} files from {path}\n")
for f in files:
    print(f"  [{f.kind:6}] {f.language:12} {f.path}  ({len(f.content)} chars)")