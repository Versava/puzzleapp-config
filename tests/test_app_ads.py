from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_app_ads import load


class AppAdsSourceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "app-ads.txt"

    def test_absent_declaration_is_not_published(self):
        self.assertIsNone(load(self.source))

    def test_single_direct_owned_publisher_row_is_retained_exactly(self):
        # Certificate IDs must come from the provider; this fixture uses the
        # documented optional-field syntax and does not invent one.
        content = b"google.com, pub-8798981282479093, DIRECT\n"
        self.source.write_bytes(content)
        self.assertEqual(load(self.source), content)

    def test_unknown_sellers_markup_duplicate_rows_and_non_ascii_are_rejected(self):
        for content in (
            b"google.com, pub-0000000000000000, DIRECT\n",
            b"google.com, pub-8798981282479093, RESELLER\n",
            b"<html>google.com, pub-8798981282479093, DIRECT</html>\n",
            b"google.com, pub-8798981282479093, DIRECT\n" * 2,
            b"google.com, pub-8798981282479093, DIRECT, unverified-id\n",
            b"google.com, pub-8798981282479093, DIRECT\n\xff",
        ):
            with self.subTest(content=content):
                self.source.write_bytes(content)
                with self.assertRaises(ValueError):
                    load(self.source)

    def test_symlink_and_oversized_sources_are_rejected(self):
        target = self.root / "other.txt"
        target.write_text("Not a reviewed seller file")
        self.source.symlink_to(target)
        with self.assertRaises(ValueError):
            load(self.source)
        self.source.unlink()
        self.source.write_bytes(b"x" * 4097)
        with self.assertRaises(ValueError):
            load(self.source)
