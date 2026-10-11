import urllib.request
import zipfile
import io
import os
import shutil
from pathlib import Path

def main():
    dest = Path("d:/COODING/Projects/Project Exibition/nodejs")
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True, exist_ok=True)

    url = "https://nodejs.org/dist/v20.18.0/node-v20.18.0-win-x64.zip"
    print("Downloading official Node.js v20.18.0 LTS (~30MB)...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        data = resp.read()

    print(f"Downloaded {len(data):,} bytes. Extracting cleanly...")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for member in z.namelist():
            parts = member.split('/', 1)
            if len(parts) > 1 and parts[1]:
                target = dest / parts[1]
                if member.endswith('/'):
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(member) as src, open(target, "wb") as dst:
                        shutil.copyfileobj(src, dst)

    print("\nNode.js and NPM extracted successfully!")
    node_exe = dest / "node.exe"
    npm_cmd = dest / "npm.cmd"
    print(f"Node path: {node_exe}")
    print(f"NPM path : {npm_cmd}")
    
    os.system(f'"{node_exe}" -v')
    os.system(f'"{npm_cmd}" -v')

if __name__ == "__main__":
    main()
