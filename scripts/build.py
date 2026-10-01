"""Build an allowlisted, static-only publication directory."""

import json
from pathlib import Path
import shutil

from validate_manifest import load
from legal_site import build_legal_site, load_editions, render_pages
from validate_client_release import load as load_client_release

ROOT = Path(__file__).resolve().parent.parent
load(ROOT / "manifest.json")
load_client_release(ROOT / "client-release.json")
# Validate the legal sources/navigation before replacing the old build output.
edition, editions = load_editions(ROOT)
render_pages(ROOT, edition, editions)
OUTPUT = ROOT / "dist"
if OUTPUT.exists():
    shutil.rmtree(OUTPUT)
OUTPUT.mkdir()
for name in ("manifest.json", "manifest.schema.json", "client-release.json", "index.html", "404.html", "_headers", "styles.css", "brand.svg"):
    shutil.copyfile(ROOT / name, OUTPUT / name)
build_legal_site(ROOT, OUTPUT)
print(json.dumps({"publishedFiles": sorted(str(path.relative_to(OUTPUT)) for path in OUTPUT.rglob("*") if path.is_file())}))
