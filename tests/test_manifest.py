import copy
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_manifest import load, load_bytes, validate, validate_extension


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.original = {
            "schemaVersion": 1, "revision": 1, "datePolicy": "device-local",
            "validThrough": "2026-12-31",
            "windows": [{"from": "2026-09-28", "through": "2026-12-31",
                         "edition": "local-v1", "minBuild": {"ios": 1, "android": 1}}],
            "updates": {"ios": {"url": None}, "android": {"url": None}},
        }

    def test_current_is_valid(self):
        load(ROOT / "manifest.json")
        validate_extension(self.original, self.original)

    def test_new_edition_can_only_extend_coverage(self):
        new = copy.deepcopy(self.original)
        new["revision"] += 1
        new["validThrough"] = "2027-01-31"
        new["windows"].append({"from": "2027-01-01", "through": "2027-01-31", "edition": "local-v2", "minBuild": {"ios": 2, "android": 2}})
        validate_extension(self.original, new)

    def test_existing_edition_can_extend(self):
        new = copy.deepcopy(self.original)
        new["revision"] += 1
        new["validThrough"] = new["windows"][-1]["through"] = "2027-01-31"
        validate_extension(self.original, new)

    def test_rejects_rewritten_edition_and_minimum_build(self):
        for field in ("edition", "minBuild"):
            new = copy.deepcopy(self.original)
            new["revision"] += 1
            new["windows"][0][field] = "local-v2" if field == "edition" else {"ios": 2, "android": 1}
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_extension(self.original, new)

    def test_rejects_coverage_removal(self):
        new = copy.deepcopy(self.original)
        new["revision"] += 1
        new["validThrough"] = new["windows"][-1]["through"] = "2026-12-30"
        with self.assertRaises(ValueError):
            validate_extension(self.original, new)

    def test_rejects_same_revision_edit(self):
        new = copy.deepcopy(self.original)
        new["updates"]["ios"]["url"] = "https://apps.apple.com/app/id123456"
        with self.assertRaises(ValueError):
            validate_extension(self.original, new)

    def test_rejects_revision_rollback(self):
        old = copy.deepcopy(self.original)
        old["revision"] += 1
        with self.assertRaises(ValueError):
            validate_extension(old, self.original)

    def test_rejects_gap_overlap_invalid_date_and_extra_fields(self):
        for start in ("2026-12-31", "2027-01-02", "2027-02-29"):
            new = copy.deepcopy(self.original)
            new["validThrough"] = "2027-03-01"
            new["windows"].append({"from": start, "through": "2027-03-01", "edition": "local-v2", "minBuild": {"ios": 2, "android": 2}})
            with self.subTest(start=start), self.assertRaises(ValueError):
                validate(new)
        new = copy.deepcopy(self.original)
        new["secret"] = "not-allowed"
        with self.assertRaises(ValueError):
            validate(new)

    def test_rejects_bool_float_and_oversize_numbers(self):
        for value in (True, 1.0, 0, 2147483648):
            new = copy.deepcopy(self.original)
            new["revision"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate(new)

    def test_beta_testflight_links_use_canonical_apple_invite_path(self):
        good = "https://testflight.apple.com/join/CCCawA1Q"
        valid = copy.deepcopy(self.original)
        valid['updates']['ios']['url'] = good
        validate(valid)
        schema = json.loads((ROOT / 'manifest.schema.json').read_text())
        pattern = schema['properties']['updates']['properties']['ios']['properties']['url']['pattern']
        self.assertIsNotNone(re.search(pattern, good))
        for url in ("http://testflight.apple.com/join/CCCawA1Q", "https://testflight.apple.com.evil.invalid/join/CCCawA1Q", "https://user@testflight.apple.com/join/CCCawA1Q", "https://testflight.apple.com:444/join/CCCawA1Q", "https://testflight.apple.com/join/short", "https://testflight.apple.com/foo/CCCawA1Q", "https://testflight.apple.com/join/CCCawA1Q?redirect=evil", "https://testflight.apple.com/join/CCCawA1Q#fragment"):
            invalid = copy.deepcopy(valid)
            invalid['updates']['ios']['url'] = url
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate(invalid)
            self.assertIsNone(re.search(pattern, url))
        valid['updates']['ios']['url'] = None
        valid['updates']['android']['url'] = good
        with self.assertRaises(ValueError):
            validate(valid)

    def test_store_link_host_cannot_be_spoofed(self):
        for url in ("https://apps.apple.com.attacker.invalid/app", "https://user@apps.apple.com/app", "http://apps.apple.com/app", "https://apps.apple.com:444/app"):
            new = copy.deepcopy(self.original)
            new["updates"]["ios"]["url"] = url
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate(new)

    def test_duplicate_json_keys_and_oversized_body_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            path.write_text(json.dumps(self.original).replace('"revision": 1', '"revision": 1, "revision": 2'))
            with self.assertRaises(ValueError):
                load(path)

            path.write_text(" " * 262145)
            with self.assertRaises(ValueError):
                load(path)

    def test_nesting_and_number_spelling_are_bounded_before_decoding(self):
        with self.assertRaisesRegex(ValueError, "nesting is too deep"):
            load_bytes(("[" * 1000 + "0" + "]" * 1000).encode())
        original = json.dumps(self.original)
        for token in ("1.0", "1e0", "NaN", "Infinity"):
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, "integer notation"):
                load_bytes(original.replace('"revision": 1', '"revision": ' + token).encode())
        escaped_duplicate = original.replace('"revision": 1', r'"revision": 1, "\u0072evision": 2')
        with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
            load_bytes(escaped_duplicate.encode())

    def test_store_schema_accepts_official_host_path_query_and_fragment(self):
        schema = json.loads((ROOT / "manifest.schema.json").read_text())
        for platform, host in (("ios", "apps.apple.com"), ("android", "play.google.com")):
            pattern = schema["properties"]["updates"]["properties"][platform]["properties"]["url"]["pattern"]
            for suffix in ("", "/app", "?id=123", "#app", ":443/app"):
                url = "https://" + host + suffix
                new = copy.deepcopy(self.original)
                new["updates"][platform]["url"] = url
                with self.subTest(url=url):
                    validate(new)
                    self.assertIsNotNone(re.search(pattern, url))
            self.assertIsNone(re.search(pattern, "https://" + host + ".attacker.invalid/app"))


if __name__ == "__main__":
    unittest.main()

class AdditionsTests(unittest.TestCase):
    def setUp(self):
        self.base = {
            'schemaVersion': 1, 'revision': 1, 'datePolicy': 'device-local',
            'validThrough': '2026-12-31',
            'windows': [{'from': '2026-09-28', 'through': '2026-12-31', 'edition': 'local-v1', 'minBuild': {'ios': 1, 'android': 1}}],
            'updates': {'ios': {'url': None}, 'android': {'url': None}},
        }
        self.current = copy.deepcopy(self.base)
        self.current['revision'] = 2
        self.current['additions'] = [{'from': '2026-09-29', 'through': '2026-12-31', 'edition': 'daily-extras-v1', 'minBuild': {'ios': 2, 'android': 2}}]

    def test_legacy_upgrade_and_identical_split_keep_base_and_additions(self):
        with self.assertRaises(ValueError):
            validate_extension(self.base, self.current)
        newer = copy.deepcopy(self.current)
        newer['revision'] = 3
        newer['additions'] = [dict(newer['additions'][0], through='2026-10-01'), dict(newer['additions'][0], **{'from': '2026-10-02'})]
        validate_extension(self.current, newer)
        newer['additions'][1]['from'] = '2026-10-03'
        with self.assertRaises(ValueError):
            validate_extension(self.current, newer)

    def test_additions_cannot_be_removed_shortened_or_rewritten(self):
        for field, value in [('from', '2026-09-30'), ('through', '2026-12-30'), ('edition', 'daily-extras-v2'), ('minBuild', {'ios': 3, 'android': 2})]:
            newer = copy.deepcopy(self.current)
            newer['revision'] = 3
            newer['additions'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_extension(self.current, newer)
        newer = copy.deepcopy(self.current)
        newer['revision'] = 3
        del newer['additions']
        with self.assertRaises(ValueError):
            validate_extension(self.current, newer)

    def test_additions_are_bounded_covered_and_nonoverlapping(self):
        cases = [None, [], self.current['additions'] * 129, self.current['additions'] * 2,
                 [dict(self.current['additions'][0], **{'from': '2026-09-27'})],
                 [dict(self.current['additions'][0], through='2027-01-01')]]
        for additions in cases:
            bad = copy.deepcopy(self.current)
            bad['additions'] = additions
            with self.subTest(additions=additions), self.assertRaises(ValueError):
                validate(bad)

class SelectionsTests(unittest.TestCase):
    def setUp(self):
        fixture = AdditionsTests()
        fixture.setUp()
        self.base = fixture.base
        self.current = fixture.current
        self.current['selections'] = self.current.pop('additions')
        self.current['selections'][0]['edition'] = 'daily-mix-v1'

    def test_selection_upgrade_and_immutable_history(self):
        with self.assertRaises(ValueError):
            validate_extension(self.base, self.current)
        for field, value in [('from', '2026-09-30'), ('through', '2026-12-30'), ('edition', 'daily-mix-v2'), ('minBuild', {'ios': 3, 'android': 2})]:
            newer = copy.deepcopy(self.current)
            newer['revision'] = 3
            newer['selections'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_extension(self.current, newer)
        newer = copy.deepcopy(self.current)
        newer['revision'] = 3
        del newer['selections']
        with self.assertRaises(ValueError):
            validate_extension(self.current, newer)

    def test_selection_and_additions_cannot_overlap(self):
        overlapping = copy.deepcopy(self.current)
        overlapping['additions'] = copy.deepcopy(overlapping['selections'])
        with self.assertRaises(ValueError):
            validate(overlapping)

    def test_additions_are_bounded_covered_and_nonoverlapping(self):
        for windows in [None, [], self.current['selections'] * 129, self.current['selections'] * 2]:
            bad = copy.deepcopy(self.current)
            bad['selections'] = windows
            with self.assertRaises(ValueError):
                validate(bad)

class BackwardCoverageTests(unittest.TestCase):
    def test_prepend_centuries_keeps_every_existing_effective_assignment(self):
        original = load(ROOT / 'manifest.json')
        previous = copy.deepcopy(original)
        previous['revision'] = original['revision'] - 1
        for field in ('windows', 'selections'):
            previous[field][0]['from'] = '2026-09-28'
        validate_extension(previous, original)
        for field in ('windows', 'selections'):
            rewritten = copy.deepcopy(original)
            rewritten[field][-1]['minBuild']['ios'] += 1
            with self.assertRaises(ValueError):
                validate_extension(previous, rewritten)
        self.assertEqual(original['windows'][0]['from'], '0001-01-01')

    def test_optional_absence_is_immutable_and_transitions_are_checked(self):
        fixture = ManifestTests(); fixture.setUp()
        previous = fixture.original
        for field in ('additions', 'selections'):
            current = copy.deepcopy(previous)
            current['revision'] += 1
            current[field] = [dict(current['windows'][0], **{'from': '2026-10-01', 'through': '2026-10-02'})]
            with self.assertRaises(ValueError):
                validate_extension(previous, current)

    def test_full_civil_year_range_and_invalid_year_zero(self):
        current = load(ROOT / 'manifest.json')
        bad = copy.deepcopy(current)
        bad['windows'][0]['from'] = '0000-01-01'
        with self.assertRaises(ValueError): validate(bad)
        future = copy.deepcopy(current)
        future['validThrough'] = future['windows'][-1]['through'] = '9999-12-31'
        validate(future)
