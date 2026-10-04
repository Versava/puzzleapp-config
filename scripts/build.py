"""Build an allowlisted, static-only publication directory."""

import json
from pathlib import Path
import shutil

from validate_manifest import load
from legal_site import build_legal_site, load_editions, render_pages
from validate_client_release import load as load_client_release
from validate_app_ads import load as load_app_ads

ROOT = Path(__file__).resolve().parent.parent
load(ROOT / "manifest.json")
load_client_release(ROOT / "client-release.json")
load(ROOT / "internal/manifest.json")
load(ROOT / "internal/manifest-v5.json")
load(ROOT / "internal/manifest-v6.json")
load(ROOT / "internal/manifest-v7.json")
load_client_release(ROOT / "internal/client-release.json")
app_ads = load_app_ads(ROOT / "app-ads.txt")
# Validate the legal sources/navigation before replacing the old build output.
edition, editions = load_editions(ROOT)
render_pages(ROOT, edition, editions)
OUTPUT = ROOT / "dist"
if OUTPUT.exists():
    shutil.rmtree(OUTPUT)
OUTPUT.mkdir()
for name in ("manifest.json", "manifest.schema.json", "client-release.json", "index.html", "404.html", "_headers", "styles.css", "brand.svg"):
    shutil.copyfile(ROOT / name, OUTPUT / name)
if app_ads is not None:
    (OUTPUT / "app-ads.txt").write_bytes(app_ads)
(OUTPUT / "internal").mkdir()
for name in ("manifest.json", "manifest-v5.json", "manifest-v6.json", "manifest-v7.json", "client-release.json"):
    shutil.copyfile(ROOT / "internal" / name, OUTPUT / "internal" / name)
build_legal_site(ROOT, OUTPUT)
print(json.dumps({"publishedFiles": sorted(str(path.relative_to(OUTPUT)) for path in OUTPUT.rglob("*") if path.is_file())}))
