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
        self.previous = copy.deepcopy(self.current)
        self.previous["revision"] = 3
        self.previous["windows"][-1]["edition"] = "local-v1"
        self.previous["windows"][-1]["minBuild"] = {"ios": 1, "android": 1}
        self.previous["selections"][-1]["minBuild"] = {"ios": 2, "android": 2}

    def test_exact_approved_artifacts_pass_but_normal_extension_stays_strict(self):
        with self.assertRaises(ValueError):
            validate_extension(self.previous, self.current)
        validate_publication(self.previous, self.current, self.ack)
        revision2 = copy.deepcopy(self.previous)
        revision2["revision"] = 2
        revision2["windows"] = revision2["windows"][1:]
        revision2["selections"] = revision2["selections"][1:]
        validate_publication(revision2, self.current, self.ack)
        self.assertEqual(set(self.ack["previousManifestSha256"]), {manifest_hash(self.previous), manifest_hash(revision2)})

    def test_unknown_source_or_changed_target_cannot_use_acknowledgement(self):
        source = copy.deepcopy(self.previous)
        source["updates"]["ios"]["url"] = "https://apps.apple.com/app/changed"
        with self.assertRaisesRegex(ValueError, "acknowledged development source"):
            validate_publication(source, self.current, self.ack)
        for field in ("edition", "minBuild"):
            target = copy.deepcopy(self.current)
            target["windows"][-1][field] = "local-v3" if field == "edition" else {"ios": 5, "android": 4}
            with self.assertRaises(ValueError):
                validate_publication(self.previous, target, self.ack)

    def test_old_archive_dates_remain_protected_even_inside_acknowledgement(self):
        changed = copy.deepcopy(self.ack)
        changed["replacementManifest"]["windows"][0]["edition"] = "local-v2"
        changed["replacementManifestSha256"] = manifest_hash(changed["replacementManifest"])
        with self.assertRaisesRegex(ValueError, "outside its approved interval"):
            validate_publication(self.previous, changed["replacementManifest"], changed)

    def test_later_extension_works_but_cannot_rewrite_the_acknowledged_release(self):
        extension = copy.deepcopy(self.current)
        extension["revision"] = 5
        extension["validThrough"] = "2027-01-01"
        extension["windows"].append({"from": "2027-01-01", "through": "2027-01-01", "edition": "local-v3", "minBuild": {"ios": 5, "android": 5}})
        validate_publication(self.previous, extension, self.ack)
        extension["windows"][1]["edition"] = "local-v3"
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
