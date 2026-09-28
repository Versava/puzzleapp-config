import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_release import check_release


def original_manifest():
    return {
        "schemaVersion": 1, "revision": 1, "datePolicy": "device-local",
        "validThrough": "2026-12-31",
        "windows": [{"from": "2026-09-28", "through": "2026-12-31",
                     "edition": "local-v1", "minBuild": {"ios": 1, "android": 1}}],
        "updates": {"ios": {"url": None}, "android": {"url": None}},
    }


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "source"
        self.root.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Release gate test")
        self.git("config", "user.email", "release-test@example.invalid")
        (self.root / "README.md").write_text("Scaffold\n")
        self.commit("scaffold")

    def git(self, *args):
        return subprocess.run(
            ["git", "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args],
            cwd=self.root, capture_output=True, check=True,
        ).stdout

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def manifest(self, value):
        (self.root / "manifest.json").write_text(json.dumps(value) + "\n")

    def establish_release(self):
        self.manifest(original_manifest())
        self.commit("published first schedule")

    def hidden_rewrite(self):
        self.establish_release()
        rewritten = original_manifest()
        rewritten["revision"] = 2
        rewritten["windows"][0]["edition"] = "local-v2"
        self.manifest(rewritten)
        self.commit("rewrite already announced days")
        (self.root / "README.md").write_text("Later documentation commit\n")
        self.commit("documentation only")

    def test_valid_extension_and_documentation_commits_are_accepted(self):
        self.establish_release()
        current = original_manifest()
        current["revision"] = 2
        current["validThrough"] = current["windows"][0]["through"] = "2027-01-31"
        self.manifest(current)
        self.commit("extend existing edition")
        (self.root / "README.md").write_text("Updated documentation\n")
        self.commit("documentation only")
        self.assertEqual(check_release(self.root), 2)

    def test_rewrite_followed_by_unrelated_commit_still_fails(self):
        self.hidden_rewrite()
        # HEAD and its immediate parent contain identical, valid JSON. Only
        # checking the earlier published manifest reveals the changed puzzle.
        with self.assertRaisesRegex(ValueError, "Published date assignment changed"):
            check_release(self.root)

    def test_deleting_manifest_does_not_erase_earlier_publication(self):
        self.establish_release()
        (self.root / "manifest.json").unlink()
        self.commit("remove schedule temporarily")
        rewritten = original_manifest()
        rewritten["revision"] = 2
        rewritten["windows"][0]["edition"] = "local-v2"
        self.manifest(rewritten)
        self.commit("reintroduce changed assignment")
        with self.assertRaisesRegex(ValueError, "Published date assignment changed"):
            check_release(self.root)

    def test_historical_manifests_use_the_same_strict_parser(self):
        original = json.dumps(original_manifest())
        (self.root / "manifest.json").write_text(original.replace('"revision": 1', '"revision": 1, "revision": 1'))
        self.commit("ambiguous old JSON")
        self.manifest(original_manifest())
        self.commit("canonical JSON")
        with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
            check_release(self.root)

    def test_historical_size_limit_applies_before_reading_blob(self):
        (self.root / "manifest.json").write_text(" " * 262145)
        self.commit("oversized old JSON")
        self.manifest(original_manifest())
        self.commit("canonical JSON")
        with self.assertRaisesRegex(ValueError, "Historical manifest exceeds size limit"):
            check_release(self.root)

    def test_shallow_clone_fetches_history_and_detects_hidden_rewrite(self):
        self.hidden_rewrite()
        clone = Path(self.temporary.name) / "shallow"
        self.git("clone", "-q", "--depth", "1", self.root.as_uri(), str(clone))
        with self.assertRaisesRegex(ValueError, "Published date assignment changed"):
            check_release(clone)

class BaselineGateTests(ReleaseGateTests):
    def test_explicit_baseline_still_rejects_later_hidden_rewrite(self):
        self.establish_release()
        baseline = self.git('rev-parse', 'HEAD').decode().strip()
        newer = original_manifest()
        newer['revision'] = 2
        newer['windows'][0]['edition'] = 'local-v2'
        self.manifest(newer)
        self.commit('unapproved rewrite after checkpoint')
        with self.assertRaises(ValueError):
            check_release(self.root, baseline_ref=baseline)

    def test_explicit_baseline_excludes_only_earlier_development_mappings(self):
        self.hidden_rewrite()
        baseline = self.git('rev-parse', 'HEAD').decode().strip()
        self.assertEqual(check_release(self.root, baseline_ref=baseline), 1)
        self.git('checkout', '-q', '-b', 'unrelated')
        (self.root / 'other').write_text('branch')
        self.commit('another branch')
        not_mainline = self.git('rev-parse', 'HEAD').decode().strip()
        self.git('checkout', '-q', 'main')
        with self.assertRaisesRegex(ValueError, 'first-parent history'):
            check_release(self.root, baseline_ref=not_mainline)
