import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_release_policy import load, load_index, validate
from release_versions import render


def policy(track="beta", **changes):
    channel = {"latestVersion": "2.3.0", "minimumVersion": "2.1.0",
               "updateUrl": "https://apps.apple.com/app/id123456789" if track == "public" else "https://testflight.apple.com/join/AbCdEf12",
               "updatePolicy": "optional" if track == "public" else "required", "blockedRanges": []}
    if track == "alpha":
        channel.update(latestBuild=4, minimumBuild=1)
    channel.update(changes)
    return {"schemaVersion": 3, "revision": 7, "track": track, "ios": channel, "android": None}


class ReleasePolicyV3Tests(unittest.TestCase):
    def test_beta_public_have_version_only_authority_and_alpha_has_build_authority(self):
        for track in ("beta", "public"):
            validate(policy(track))
            for field in ("latestBuild", "minimumBuild"):
                with self.subTest(track=track, field=field), self.assertRaises(ValueError):
                    validate(policy(track, **{field: 1}))
        validate(policy("alpha"))
        invalid = policy("alpha")
        del invalid["ios"]["latestBuild"]
        with self.assertRaises(ValueError):
            validate(invalid)

    def test_numeric_version_ranges_ignore_builds_for_beta_and_public(self):
        for track in ("beta", "public"):
            value = policy(track, latestVersion="1.10.0", minimumVersion="1.1.0",
                           blockedRanges=[{"fromVersion": "1.2.0", "throughVersion": "1.9.0", "reason": "security"}])
            validate(value)
            value["ios"]["blockedRanges"][0]["fromBuild"] = 99
            with self.assertRaises(ValueError):
                validate(value)
        with self.assertRaises(ValueError):
            validate(policy(minimumVersion="2.4.0"))

    def test_alpha_same_version_build_boundaries_and_invalid_overlap_are_rejected(self):
        value = policy("alpha", latestVersion="2.3.0", minimumVersion="2.3.0",
                       blockedRanges=[{"fromVersion": "2.3.0", "fromBuild": 2, "throughVersion": "2.3.0", "throughBuild": 3, "reason": "security"}])
        validate(value)
        value["ios"]["blockedRanges"][0]["throughBuild"] = 4
        with self.assertRaises(ValueError):
            validate(value)

    def test_track_source_unknown_fields_and_duplicate_keys_are_rejected(self):
        with self.assertRaises(ValueError):
            validate(policy(), "public")
        for changes in ({"updatePolicy": "optional"}, {"updateUrl": "https://example.com/app"}, {"surprise": True}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate(policy(**changes))
        with self.assertRaises(ValueError):
            validate(policy("public", updatePolicy="required"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_text(json.dumps(policy()).replace('"revision": 7', '"revision": 7, "revision": 8'))
            with self.assertRaises(ValueError):
                load(path)

    def fixture_root(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "releases").mkdir()
        for track in ("alpha", "beta", "public"):
            value = policy(track)
            if track != "beta":
                value["ios"] = None
            (root / f"releases/{track}.json").write_text(json.dumps(value))
        (root / "releases/index.json").write_text(json.dumps({"schemaVersion": 1, "revision": 1,
            "beta": {"version": "2.3.0", "minimumVersion": "2.1.0", "status": "testing"}, "public": {"version": "2.0.0", "minimumVersion": "2.0.0", "status": "inReview"}}))
        return root

    def test_review_metadata_does_not_add_status_or_unavailable_app_links(self):
        root = self.fixture_root()
        index, policies = load_index(root)
        source = render(root)
        self.assertIn("2.0.0", source)
        self.assertNotIn("In review", source)
        self.assertNotIn("Status", source)
        self.assertIn("Latest version", source)
        self.assertIn("Minimum supported version", source)
        self.assertLess(source.index('id="release-versions"'), source.index('id="beta-versions"'))
        self.assertNotIn("Open App Store", source)
        self.assertNotIn("Build", source)
        self.assertNotIn("<a ", source)
        self.assertIsNone(policies["public"]["ios"])
        index["public"]["status"] = "available"
        (root / "releases/index.json").write_text(json.dumps(index))
        with self.assertRaises(ValueError):
            load_index(root)

    def test_obtainable_status_requires_matching_policy_and_future_versions_need_no_test_edits(self):
        root = self.fixture_root()
        index, policies = load_index(root)
        index["beta"]["version"] = "12.7.0"
        index["beta"]["minimumVersion"] = "12.1.0"
        policies["beta"]["ios"].update(latestVersion="12.7.0", minimumVersion="12.1.0")
        (root / "releases/index.json").write_text(json.dumps(index))
        with self.assertRaises(ValueError):
            load_index(root)
        (root / "releases/beta.json").write_text(json.dumps(policies["beta"]))
        self.assertIn("12.7.0", render(root))

    def test_browser_runtime_rejects_invalid_refreshes_and_updates_from_json(self):
        node = os.environ.get("NODE_BIN") or shutil.which("node")
        if not node:
            bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
            if bundled.is_file():
                node = str(bundled)
        self.assertTrue(node, "Node.js is required for browser-runtime tests; set NODE_BIN if needed")
        root = self.fixture_root()
        fallback = root / "fallback.html"
        fallback.write_text(render(root))
        result = subprocess.run([node, str(ROOT / "tests/versions_runtime.cjs"),
                                 str(ROOT / "versions.js"), str(fallback)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("JSON-only updates replace old fallback details", result.stdout)

    def test_production_build_keeps_legacy_bytes_and_copies_only_allowlisted_new_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", "dist", "__pycache__"))
            before = {name: (root / name).read_bytes() for name in ("client-support.json", "client-release.json", "internal/client-support.json", "internal/client-release.json")}
            (root / "releases/private.txt").write_text("not a publication input")
            result = subprocess.run([sys.executable, "scripts/build.py"], cwd=root, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            output = root / "dist"
            self.assertEqual(sorted(p.name for p in (output / "releases").iterdir()), ["alpha.json", "beta.json", "index.json", "public.json"])
            self.assertIn('<script src="/versions.js" defer>', (output / "versions/index.html").read_text())
            self.assertNotIn('<script', (output / "privacy/index.html").read_text())
            for name, raw in before.items():
                self.assertEqual((output / name).read_bytes(), raw)
            self.assertIn("script-src 'self'; connect-src 'self'", (output / "_headers").read_text())


if __name__ == "__main__":
    unittest.main()
