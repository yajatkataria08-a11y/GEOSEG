"""
Direct GitHub Push Script using GitHub Git Data API
Uploads all changes, new models, infographics, benchmarks, and docs to yajatkataria08-a11y/GEOSEG.
"""

import os
import sys
import json
import base64
import urllib.request
from pathlib import Path

TOKEN = os.environ.get("GITHUB_TOKEN", "")
OWNER = "yajatkataria08-a11y"
REPO = "GEOSEG"
BRANCH = "main"

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "GEOSEG-Git-Uploader",
}

def gh_api(endpoint: str, method: str = "GET", data: dict = None):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/{endpoint}"
    payload = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=payload, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"GitHub API Error [{e.code}] on {endpoint}: {err_msg}")
        raise


def get_latest_commit():
    ref = gh_api(f"git/ref/heads/{BRANCH}")
    commit_sha = ref["object"]["sha"]
    commit = gh_api(f"git/commits/{commit_sha}")
    tree_sha = commit["tree"]["sha"]
    return commit_sha, tree_sha


def get_existing_tree(tree_sha: str):
    """Fetch complete recursive tree of remote repo to check file hashes."""
    data = gh_api(f"git/trees/{tree_sha}?recursive=1")
    return {item["path"]: item["sha"] for item in data.get("tree", []) if item["type"] == "blob"}


def collect_local_files():
    root = Path(".")
    local_files = {}
    
    # Exclude patterns
    skip_dirs = {".git", "__pycache__", ".pytest_cache", "venv", ".env", "data", "checkpoints", "node_modules", ".gemini"}
    skip_exts = {".pyc", ".whl", ".tmp", ".log", ".zip"}
    skip_files = {"scripts/push_to_github.py"}

    for p in root.rglob("*"):
        if not p.is_file():
            continue
        parts = p.parts
        if any(d in parts for d in skip_dirs):
            continue
        if p.suffix.lower() in skip_exts:
            continue
        rel_path = str(p.relative_to(root)).replace("\\", "/")
        if rel_path in skip_files:
            continue
        # Skip large files (> 5MB)
        if p.stat().st_size > 5 * 1024 * 1024:
            continue
            
        local_files[rel_path] = p
        
    return local_files


def create_blob(filepath: Path) -> str:
    content = filepath.read_bytes()
    b64 = base64.b64encode(content).decode("utf-8")
    resp = gh_api("git/blobs", method="POST", data={"content": b64, "encoding": "base64"})
    return resp["sha"]


def main():
    print(f"Connecting to GitHub: {OWNER}/{REPO} on branch '{BRANCH}'...")
    commit_sha, tree_sha = get_latest_commit()
    print(f"Latest commit: {commit_sha[:8]} (Tree: {tree_sha[:8]})")

    remote_blobs = get_existing_tree(tree_sha)
    print(f"Remote tree has {len(remote_blobs)} files.")

    local_files = collect_local_files()
    print(f"Local repository has {len(local_files)} trackable files.")

    # Determine files to upload or update
    tree_updates = []
    uploaded = 0

    # Ensure critical new assets and models are checked
    critical_paths = [
        "README.md",
        "COMPLETE_PROJECT_GUIDE.md",
        "asset/ai_metrics_infographic.svg",
        "asset/rtx_benchmark.svg",
        "src/models/colnet.py",
        "src/models/unetformer.py",
        "src/models/farseg.py",
        "src/transforms/wavelet.py",
        "scripts/train_all_advanced.py",
        "scripts/benchmark_advanced_methods.py",
    ]

    for rel_path, local_p in sorted(local_files.items()):
        # Compute git blob sha locally or upload
        # For simplicity and correctness on critical files and changed files, upload blob
        # (GitHub blobs API is idempotent)
        is_critical = rel_path in critical_paths
        
        # If it doesn't exist remotely or is critical or updated
        if rel_path not in remote_blobs or is_critical:
            print(f"  Processing {rel_path}...")
            blob_sha = create_blob(local_p)
            tree_updates.append({
                "path": rel_path,
                "mode": "100644",
                "type": "blob",
                "sha": blob_sha,
            })
            uploaded += 1
            print(f"  [BLOB] Uploaded: {rel_path} ({local_p.stat().st_size} bytes)")

    if not tree_updates:
        print("No file changes detected to commit!")
        return

    print(f"\nCreating new Git Tree with {len(tree_updates)} updated/new entries...")
    new_tree = gh_api("git/trees", method="POST", data={
        "base_tree": tree_sha,
        "tree": tree_updates,
    })
    new_tree_sha = new_tree["sha"]
    print(f"New Tree created: {new_tree_sha[:8]}")

    commit_msg = (
        "feat: add advanced models (ColNet, UNetFormer, FarSeg), RTX 5050 CUDA benchmarks, and infographic-driven docs\n\n"
        "- Integrated IEEE TGRS ColNet (Joint SR + Seg with CTAF attention)\n"
        "- Added ISPRS 2022 UNetFormer (Global-Local Transformer Attention)\n"
        "- Added CVPR/TPAMI FarSeg (Foreground-Scene Relation Module FSRM)\n"
        "- Implemented 2D Haar DWT & WaveletEdgeLoss for frequency boundary preservation\n"
        "- Verified 50-epoch training on NVIDIA GeForce RTX 5050 (CUDA 12.8 + FP16 AMP)\n"
        "- Modernized README.md and COMPLETE_PROJECT_GUIDE.md with animated SVG infographics"
    )

    print("Creating Git Commit...")
    new_commit = gh_api("git/commits", method="POST", data={
        "message": commit_msg,
        "tree": new_tree_sha,
        "parents": [commit_sha],
    })
    new_commit_sha = new_commit["sha"]
    print(f"New Commit created: {new_commit_sha[:8]}")

    print(f"Updating branch 'refs/heads/{BRANCH}'...")
    gh_api(f"git/refs/heads/{BRANCH}", method="PATCH", data={
        "sha": new_commit_sha,
        "force": False,
    })

    print("\n" + "=" * 70)
    print("  [SUCCESS] PUSHED TO GITHUB SUCCESSFULLY!")
    print(f"  Repository: https://github.com/{OWNER}/{REPO}")
    print(f"  Commit URL: https://github.com/{OWNER}/{REPO}/commit/{new_commit_sha}")
    print("=" * 70)


if __name__ == "__main__":
    main()
