import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_manifest import load as load_manifest
from validate_client_release import load as load_release


class InternalConfigurationTests(unittest.TestCase):
    def test_internal_generator_reset_does_not_require_external_testers_to_upgrade(self):
        public = load_manifest(ROOT / "manifest.json")
        internal = load_manifest(ROOT / "internal/manifest.json")
        public_policy = load_release(ROOT / "client-release.json")
        internal_policy = load_release(ROOT / "internal/client-release.json")
        self.assertEqual(public["windows"][0]["edition"], "local-v4")
        self.assertEqual(public_policy["ios"]["minimumBuild"], 10)
        self.assertEqual(internal_policy["ios"]["latestBuild"], 12)
        self.assertEqual(internal_policy["ios"]["minimumBuild"], 12)
        self.assertEqual(internal["windows"], [{
            "from": "0001-01-01", "through": "2026-12-31",
            "edition": "local-v5", "minBuild": {"ios": 11, "android": 11},
        }])
        self.assertEqual(internal["selections"][0]["edition"], "daily-mix-v2")

    def test_internal_metadata_contains_configuration_only(self):
        actual = {p.name for p in (ROOT / "internal").iterdir() if p.is_file()}
        self.assertEqual(actual, {"manifest.json", "client-release.json"})
        for filename in actual:
            text = (ROOT / "internal" / filename).read_text()
            self.assertIsInstance(json.loads(text), dict)
            for prohibited in ("identityToken", "ADMIN_TOKEN", "accountId", "solution"):
                self.assertNotIn(prohibited, text)


if __name__ == "__main__":
    unittest.main()
