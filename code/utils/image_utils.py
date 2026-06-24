import os
from pathlib import Path


def resolve_image_paths(image_paths_str: str, repo_root: str) -> list[str]:
    """Return list of absolute file paths from semicolon-separated relative paths."""
    if not image_paths_str or not image_paths_str.strip():
        return []
    paths = []
    for p in image_paths_str.split(";"):
        p = p.strip()
        if not p:
            continue
        candidate = Path(repo_root) / "dataset" / p
        if candidate.exists():
            paths.append(str(candidate))
        else:
            # Try as-is relative to repo root
            candidate2 = Path(repo_root) / p
            if candidate2.exists():
                paths.append(str(candidate2))
            else:
                print(f"  [image_utils] warning: image not found: {p}")
    return paths


def get_image_ids(image_paths_str: str) -> list[str]:
    """Extract image IDs (filename without extension) from paths string."""
    ids = []
    for p in image_paths_str.split(";"):
        p = p.strip()
        if p:
            ids.append(Path(p).stem)
    return ids


def load_pil_images(abs_paths: list[str]) -> list:
    """Load images as PIL Image objects, skipping missing/corrupt files."""
    import PIL.Image
    images = []
    for path in abs_paths:
        try:
            img = PIL.Image.open(path)
            img.load()
            images.append(img)
        except Exception as e:
            print(f"  [image_utils] failed to load {path}: {e}")
    return images
