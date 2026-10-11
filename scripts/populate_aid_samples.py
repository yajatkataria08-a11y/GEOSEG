import shutil
from pathlib import Path
from src.datasets.aid import normalize_class_name

def populate():
    aid_cache = Path(r"C:\Users\palas\.cache\kagglehub\datasets\jiayuanchengala\aid-scene-classification-datasets\versions\1\AID")
    target_data = Path("data/aid/samples")
    target_frontend = Path("frontend/public/previews/aid")
    target_data.mkdir(parents=True, exist_ok=True)
    target_frontend.mkdir(parents=True, exist_ok=True)

    if not aid_cache.exists():
        print(f"AID cache not found at {aid_cache}")
        return

    count = 0
    for folder in sorted(aid_cache.iterdir()):
        if not folder.is_dir():
            continue
        cls_norm = normalize_class_name(folder.name)
        images = list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg")) + list(folder.glob("*.png"))
        if not images:
            continue
        first_img = images[0]
        dest_filename = f"aid_{cls_norm}_01.jpg"
        
        # Copy to data/aid/samples
        shutil.copy2(first_img, target_data / dest_filename)
        # Also copy to frontend/public/previews/aid
        shutil.copy2(first_img, target_frontend / dest_filename)
        count += 1
        print(f"Copied {folder.name} -> {dest_filename}")

    print(f"\nSuccessfully populated {count} AID sample scenes!")

if __name__ == "__main__":
    populate()
