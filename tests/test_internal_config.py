import json
from pathlib import Path
import sys
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_manifest import load as load_manifest
from validate_client_release import load as load_release
from validate_client_support import load as load_support


class InternalConfigurationTests(unittest.TestCase):
    def test_beta_requires_latest_and_matches_legacy_client_policy(self):
        legacy = load_release(ROOT / "internal/client-release.json")
        support = load_support(ROOT / "internal/client-support.json")
        for platform in ("ios", "android"):
            with self.subTest(platform=platform):
                legacy_channel = legacy[platform]
                support_channel = support[platform]
                self.assertEqual(legacy_channel is None, support_channel is None)
                if support_channel is None:
                    continue
                self.assertEqual(
                    {key: support_channel[key] for key in legacy_channel},
                    legacy_channel,
                )
                self.assertEqual(support_channel["updatePolicy"], "required")
                self.assertEqual(
                    (support_channel["minimumVersion"], support_channel["minimumBuild"]),
                    (support_channel["latestVersion"], support_channel["latestBuild"]),
                )
                self.assertEqual(urlsplit(support_channel["updateUrl"]).hostname, "testflight.apple.com")

    def test_published_generator_channels_retain_their_frozen_contracts(self):
        public = load_manifest(ROOT / "manifest.json")
        internal = load_manifest(ROOT / "internal/manifest.json")
        self.assertEqual(public["revision"], 6)
        self.assertEqual(public["windows"][0]["edition"], "local-v4")
        self.assertEqual(internal["windows"], [{
            "from": "0001-01-01", "through": "2026-12-31",
            "edition": "local-v8", "minBuild": {"ios": 29, "android": 29},
        }])
        self.assertEqual(internal["selections"][0]["edition"], "daily-mix-v2")
        retained = load_manifest(ROOT / "internal/manifest-v5.json")
        self.assertEqual(retained["revision"], 7)
        self.assertEqual(retained["windows"][0]["edition"], "local-v5")
        self.assertEqual(retained["windows"][0]["minBuild"]["ios"], 11)
        retained_v6 = load_manifest(ROOT / "internal/manifest-v6.json")
        self.assertEqual(retained_v6["revision"], 8)
        self.assertEqual(retained_v6["windows"][0]["edition"], "local-v6")
        self.assertEqual(retained_v6["windows"][0]["minBuild"]["ios"], 13)
        self.assertEqual(internal["revision"], 10)
        retained_v7 = load_manifest(ROOT / "internal/manifest-v7.json")
        self.assertEqual(retained_v7["revision"], 9)
        self.assertEqual(retained_v7["windows"][0]["edition"], "local-v7")
        self.assertEqual(retained_v7["windows"][0]["minBuild"]["ios"], 26)

    def test_internal_metadata_contains_configuration_only(self):
        actual = {p.name for p in (ROOT / "internal").iterdir() if p.is_file()}
        self.assertEqual(actual, {"manifest.json", "manifest-v5.json", "manifest-v6.json", "manifest-v7.json", "client-release.json", "client-support.json"})
        for filename in actual:
            text = (ROOT / "internal" / filename).read_text()
            self.assertIsInstance(json.loads(text), dict)
            for prohibited in ("identityToken", "ADMIN_TOKEN", "accountId", "solution"):
                self.assertNotIn(prohibited, text)


if __name__ == "__main__":
    unittest.main()
