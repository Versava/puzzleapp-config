"""Build an allowlisted, static-only publication directory."""

import json
from pathlib import Path
import shutil

from validate_manifest import load

ROOT = Path(__file__).resolve().parent.parent
load(ROOT / "manifest.json")
OUTPUT = ROOT / "dist"
if OUTPUT.exists():
    shutil.rmtree(OUTPUT)
OUTPUT.mkdir()
for name in ("manifest.json", "manifest.schema.json", "index.html", "404.html", "_headers"):
    shutil.copyfile(ROOT / name, OUTPUT / name)
print(json.dumps({"publishedFiles": sorted(path.name for path in OUTPUT.iterdir())}))
