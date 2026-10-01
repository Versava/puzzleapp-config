import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from development_transition import load_transition, manifest_hash, validate_publication
from validate_manifest import validate_extension


class DevelopmentTransitionTests(unittest.TestCase):
    def setUp(self):
        self.ack = load_transition(ROOT / "development-transition.json")
        self.current = copy.deepcopy(self.ack["replacementManifest"])
        self.previous = json.loads(
            (ROOT / "tests/fixtures/development-previous-manifest.json").read_text()
        )

    def test_exact_approved_artifacts_pass_but_normal_extension_stays_strict(self):
        with self.assertRaises(ValueError):
            validate_extension(self.previous, self.current)
        validate_publication(self.previous, self.current, self.ack)
        self.assertIn(manifest_hash(self.previous), self.ack["previousManifestSha256"])
        self.assertEqual(self.current["windows"][0]["edition"], "local-v4")
        self.assertEqual(len(self.current["windows"]), 1)

    def test_unknown_source_or_changed_target_cannot_use_acknowledgement(self):
        source = copy.deepcopy(self.previous)
        source["updates"]["ios"]["url"] = "https://apps.apple.com/app/changed"
        with self.assertRaisesRegex(ValueError, "acknowledged development source"):
            validate_publication(source, self.current, self.ack)
        for field in ("edition", "minBuild"):
            target = copy.deepcopy(self.current)
            target["windows"][-1][field] = "local-v5" if field == "edition" else {"ios": 11, "android": 10}
            with self.assertRaises(ValueError):
                validate_publication(self.previous, target, self.ack)

    def test_narrowed_exception_cannot_change_dates_outside_its_interval(self):
        changed = copy.deepcopy(self.ack)
        changed["from"] = "2026-09-28"
        with self.assertRaisesRegex(ValueError, "outside its approved interval"):
            validate_publication(self.previous, changed["replacementManifest"], changed)

    def test_later_extension_works_but_cannot_rewrite_the_acknowledged_release(self):
        extension = copy.deepcopy(self.current)
        extension["revision"] = self.current['revision'] + 1
        extension["validThrough"] = "2027-01-01"
        extension["windows"].append({"from": "2027-01-01", "through": "2027-01-01", "edition": "local-v5", "minBuild": {"ios": 11, "android": 11}})
        validate_publication(self.previous, extension, self.ack)
        extension["windows"][0]["edition"] = "local-v5"
        with self.assertRaises(ValueError):
            validate_publication(self.previous, extension, self.ack)

    def test_mismatched_replacement_hash_and_duplicate_fields_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ack.json"
            changed = copy.deepcopy(self.ack)
            changed["replacementManifestSha256"] = "0" * 64
            path.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, "replacement hash"):
                load_transition(path)
            path.write_text(json.dumps(self.ack).replace('"schemaVersion": 1', '"schemaVersion": 1, "schemaVersion": 1', 1))
            with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
                load_transition(path)
