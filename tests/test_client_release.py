import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_client_release import load, validate


class ClientReleaseTest(unittest.TestCase):
    def setUp(self):
        self.policy = load(Path(__file__).resolve().parents[1] / "client-release.json")

    def test_current_beta_policy(self):
        self.assertEqual(self.policy["ios"]["latestVersion"], "0.1.0")
        self.assertEqual(self.policy["revision"], 13)
        self.assertEqual(self.policy["ios"]["latestBuild"], 21)
        self.assertEqual(self.policy["ios"]["minimumBuild"], 21)
        self.assertIsNone(self.policy["android"])

    def test_minimum_cannot_exceed_latest(self):
        value = copy.deepcopy(self.policy)
        value["ios"]["minimumBuild"] = value["ios"]["latestBuild"] + 1
        with self.assertRaises(ValueError):
            validate(value)

    def test_unsafe_destinations_are_rejected(self):
        for url in ("https://example.com/", "http://testflight.apple.com/join/CCCawA1Q",
                    "https://testflight.apple.com/join/CCCawA1Q?redirect=evil",
                    "https://testflight.apple.com:443/join/CCCawA1Q",
                    "https://user@testflight.apple.com/join/CCCawA1Q"):
            value = copy.deepcopy(self.policy)
            value["ios"]["updateUrl"] = url
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate(value)

    def test_boolean_or_negative_builds_are_not_numbers(self):
        for build in (True, 0, -1, 10.5):
            value = copy.deepcopy(self.policy)
            value["ios"]["latestBuild"] = build
            with self.subTest(build=build), self.assertRaises(ValueError):
                validate(value)

    def test_numeric_versions_and_schema_are_validated(self):
        for version in ("0.1", "01.0.0", "0.1.0-beta"):
            value = copy.deepcopy(self.policy)
            value["ios"]["latestVersion"] = version
            with self.subTest(version=version), self.assertRaises(ValueError):
                validate(value)
        value = copy.deepcopy(self.policy)
        value["schemaVersion"] = 2
        with self.assertRaises(ValueError):
            validate(value)


if __name__ == "__main__":
    unittest.main()
