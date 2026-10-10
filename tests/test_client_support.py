import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_client_support import load, validate


class ClientSupportTest(unittest.TestCase):
    def setUp(self):
        self.policy = load(Path(__file__).resolve().parents[1] / "client-support.json")

    def range(self, start=37, end=38):
        return {"fromVersion": "0.1.0", "fromBuild": start, "throughVersion": "0.1.0",
                "throughBuild": end, "reason": "security"}

    def staged(self):
        value = copy.deepcopy(self.policy)
        value["ios"].update(latestBuild=40, minimumBuild=36, blockedRanges=[self.range()])
        return value

    def test_published_channels_are_separate_and_valid(self):
        root = Path(__file__).resolve().parents[1]
        for path in (root / "client-support.json", root / "internal/client-support.json"):
            policy = load(path)
            self.assertEqual(policy["schemaVersion"], 2)
            self.assertEqual(policy["ios"]["blockedRanges"], [])
        legacy = __import__("validate_client_release").load(root / "client-release.json")
        self.assertEqual(legacy["schemaVersion"], 1)
        self.assertNotIn("blockedRanges", legacy["ios"])

    def test_hole_below_latest_does_not_require_raising_minimum(self):
        self.assertEqual(validate(self.staged())["ios"]["minimumBuild"], 36)

    def test_rejects_reversed_overlapping_unsorted_or_latest_blocking_ranges(self):
        for ranges in ([self.range(38, 37)], [self.range(37, 38), self.range(38, 39)],
                       [self.range(39, 39), self.range(37, 38)], [self.range(37, 40)]):
            value = self.staged()
            value["ios"]["blockedRanges"] = ranges
            with self.subTest(ranges=ranges), self.assertRaises(ValueError):
                validate(value)

    def test_range_versions_compare_numerically(self):
        value = self.staged()
        value["ios"].update(latestVersion="1.10.0", latestBuild=1)
        item = value["ios"]["blockedRanges"][0]
        item.update(fromVersion="1.2.0", fromBuild=1, throughVersion="1.9.0", throughBuild=99)
        validate(value)
        item["throughVersion"] = "1.11.0"
        with self.assertRaises(ValueError):
            validate(value)

    def test_rejects_unknown_or_malformed_ranges_and_unsafe_update(self):
        for field, invalid in (("fromBuild", True), ("throughBuild", 0), ("fromVersion", "1.0"),
                               ("reason", "free text")):
            value = self.staged()
            value["ios"]["blockedRanges"][0][field] = invalid
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate(value)

    def test_duplicate_security_fields_are_rejected(self):
        import json
        raw = json.dumps(self.policy).replace('"blockedRanges": []', '"blockedRanges": [], "blockedRanges": []')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "support.json"
            path.write_text(raw)
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                load(path)
        for change in ({"blockedRanges": None}, {"blockedRanges": [self.range()] * 33},
                       {"updateUrl": "https://example.com/upgrade"}, {"unexpected": True},
                       {"updatePolicy": "unknown"}, {"updatePolicy": True}):
            value = self.staged()
            value["ios"].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate(value)


if __name__ == "__main__":
    unittest.main()
