import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_release import check_release
from legal_site import FILES, load_editions, render_document


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.in_article = False
        self.article = []
        self.ids = []
        self.targets = []
        self.tags = []
        self.attributes = []
        self.feed(source)

    def handle_starttag(self, tag, attributes):
        values = dict(attributes)
        self.tags.append(tag)
        self.attributes.extend(values)
        if tag == "article" and "data-policy-document" in values:
            self.in_article = True
        if "id" in values:
            self.ids.append(values["id"])
        for key in ("href", "src"):
            if key in values:
                self.targets.append(values[key])

    def handle_endtag(self, tag):
        if self.in_article and tag in ("p", "li", "h1", "h2", "h3"):
            self.article.append(" ")
        if tag == "article":
            self.in_article = False

    def handle_data(self, value):
        if self.in_article:
            self.article.append(value)


def normalized(value):
    return " ".join(value.split())


class LegalSiteTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "source"
        self.root.mkdir()
        for name in (
            "manifest.json", "manifest.schema.json", "client-release.json", "index.html", "404.html",
            "_headers", "styles.css", "brand.svg",
        ):
            shutil.copyfile(ROOT / name, self.root / name)
        shutil.copytree(ROOT / "legal", self.root / "legal")
        shutil.copytree(ROOT / "scripts", self.root / "scripts")
        shutil.copytree(ROOT / "internal", self.root / "internal")
        self.current, self.editions = load_editions(self.root)
        self.edition = self.current["betaEdition"]

    def build(self):
        subprocess.run(
            [sys.executable, "scripts/build.py"], cwd=self.root,
            capture_output=True, check=True,
        )
        return self.root / "dist"

    def test_actual_frozen_documents_preserve_all_words_in_every_reading_route(self):
        output = self.build()
        for edition, (manifest, _) in self.editions.items():
            channel = manifest["channel"]
            for kind, filename in FILES[channel].items():
                source = (self.root / "legal" / edition / filename).read_text()
                expected = normalized(re.sub(r"^#{1,3} ", "", source, flags=re.M))
                routes = [f"legal/{edition}/{kind}"]
                if self.current[f"{channel}Edition"] == edition:
                    routes.append(kind if channel == "public" else f"{channel}/{kind}")
                for route in routes:
                    with self.subTest(route=route):
                        content = (output / route / "index.html").read_text()
                        page = Page(content)
                        self.assertEqual(normalized("".join(page.article)), expected)
                        self.assertEqual(len(page.ids), len(set(page.ids)))
                        self.assertIn(f'data-policy-channel="{channel}"', content)
                        self.assertEqual('content="noindex, follow"' in content, channel != "public")
                        self.assertIn(f'<title>{source.splitlines()[0][2:]} | Daily Pause</title>', content)
        # Public URLs are independent agreements, never aliases of test terms.
        self.assertIn('Daily Pause Terms of Use', (output / "terms/index.html").read_text())
        self.assertNotIn('data-policy-channel="beta"', (output / "terms/index.html").read_text())

    def test_changed_source_is_rejected_before_replacing_previous_output(self):
        output = self.build()
        previous = (output / "beta/terms/index.html").read_bytes()
        path = self.root / "legal" / self.edition / "terms-beta.md"
        path.write_bytes(path.read_bytes() + b"\nChanged statement.\n")
        with self.assertRaisesRegex(ValueError, "Frozen legal source changed"):
            load_editions(self.root)
        with self.assertRaises(subprocess.CalledProcessError):
            self.build()
        self.assertEqual((output / "beta/terms/index.html").read_bytes(), previous)

    def test_current_currency_edition_retains_beta_two_and_exposes_disabled_checkout(self):
        previous = self.root / "legal/2026-10-01-beta.2"
        expected = {
            "terms-beta.md": "bdeec8d7c9e110507f68532d3aff4afaa2a1b71c9f810b61e1ebede59ab957cc",
            "privacy-beta.md": "9b927248cfa17148fe67b695fc2a39048887d8e9cca9bce65508256dd4d94238",
        }
        for name, checksum in expected.items():
            self.assertEqual(hashlib.sha256((previous / name).read_bytes()).hexdigest(), checksum)
        self.assertEqual(self.edition, "2026-10-03-beta.8")
        output = self.build()
        current = (output / "beta/terms/index.html").read_text()
        old = (output / "legal/2026-10-01-beta.2/terms/index.html").read_text()
        self.assertIn("2026-10-03-beta.8", current)
        self.assertIn("2026-10-01-beta.2", old)
        self.assertNotIn("Each puzzle question allows at most three hints", old)
        self.assertIn("Each further hint costs one new diamond", current)
        for route in ("beta", "support"):
            status = (output / route / "index.html").read_text()
            self.assertIn("Remove Ads checkout is disabled", status)
            self.assertIn("without real charges", status)
            self.assertNotIn("Real purchases and publisher ads are disabled.", status)

    def test_currency_edition_retains_beta_three_and_discloses_new_records(self):
        previous = self.root / "legal/2026-10-01-beta.3"
        expected = {
            "terms-beta.md": "8556c88ece2dd479114c34377c52499f421cb8b7a41e77d2000edfcd40846478",
            "privacy-beta.md": "1b9fa4ea7a0cafcecea0ddbd8110354e9d86ff2cd1041888077cd2dea133e8f1",
        }
        for name, checksum in expected.items():
            self.assertEqual(hashlib.sha256((previous / name).read_bytes()).hexdigest(), checksum)
        output = self.build()
        terms = normalized((output / "beta/terms/index.html").read_text())
        privacy = normalized((output / "beta/privacy/index.html").read_text())
        historical = (output / "legal/2026-10-01-beta.3/terms/index.html").read_text()
        self.assertIn("ten new diamonds for each group of seven", terms)
        self.assertIn("New diamond-to-star exchanges are unavailable", terms)
        self.assertIn("96 released packs", terms)
        self.assertIn("Individual cash-pack and Remove Ads checkout remain disabled", terms)
        self.assertIn("verified completed puzzle dates", privacy)
        self.assertIn("signed Apple transaction evidence", privacy)
        self.assertIn("Keychain delivery journal", privacy)
        self.assertNotIn("one diamond for each group of 14 consecutive", historical)

    def test_pack_offer_edition_retains_beta_four_and_matches_current_redemption_records(self):
        previous = self.root / "legal/2026-10-02-beta.4"
        expected = {
            "terms-beta.md": "0ab65d34db4af55b773031dc3f6cc20cfb759cbe5a22d1025448ffbc679484c6",
            "privacy-beta.md": "cb63c74a4d4b0295fc4254869c8ad9be77483a4ccdfc4f7b8b6a2e439fb8a69d",
            "manifest.json": "a155232ffe59eb2ed054e18f3abf58276bf3fb35f5353806d9eb01d3198f2cab",
        }
        for name, checksum in expected.items():
            self.assertEqual(hashlib.sha256((previous / name).read_bytes()).hexdigest(), checksum)
        output = self.build()
        terms = normalized((output / "beta/terms/index.html").read_text())
        privacy = normalized((output / "beta/privacy/index.html").read_text())
        historical = normalized((output / "legal/2026-10-02-beta.4/terms/index.html").read_text())
        self.assertIn("2026-10-03-beta.8", terms)
        self.assertIn("96 released packs across eight games", terms)
        self.assertIn("for 50 stars or 20 new diamonds", terms)
        self.assertIn("for 100 stars or 50 new diamonds", terms)
        self.assertIn("for 150 stars or 90 new diamonds", terms)
        self.assertIn("rejects a changed revision or price", terms)
        self.assertIn("confirmed offer revision", privacy)
        self.assertIn("corresponding diamond ledger debit", privacy)
        self.assertIn("selected pack sort order is saved in device preferences", privacy)
        self.assertIn("This presentation setting is not sent to our account service", privacy)
        self.assertNotIn("Direct diamond pack prices are not configured", terms)
        self.assertIn("20-star unlock", historical)
        self.assertIn("Direct diamond pack prices are not configured", historical)

    def test_subscription_edition_retains_beta_five_and_limits_testing_to_sandbox(self):
        previous = self.root / "legal/2026-10-03-beta.5"
        expected = {
            "terms-beta.md": "245637d97c1bafddedf5ab3c7b01e13b719f7b0b0737a52613210b7bf8767db4",
            "privacy-beta.md": "d5ab43536b847939239837bbe8ac2d4588604e09f1aae54fc3a2362c6220c04c",
            "manifest.json": "bd618c11a0fbee65eb148bde7f7c549226a002de9faf9ced621fe7a8129db52d",
        }
        for name, checksum in expected.items():
            self.assertEqual(hashlib.sha256((previous / name).read_bytes()).hexdigest(), checksum)
        output = self.build()
        terms = normalized((output / "beta/terms/index.html").read_text())
        privacy = normalized((output / "beta/privacy/index.html").read_text())
        self.assertIn("controlled testing of the monthly Daily Pause Plus", terms)
        self.assertIn("without charging real money", terms)
        self.assertIn("two new diamonds for each eligible UTC calendar date", terms)
        self.assertIn("does not include all-pack access", terms)
        self.assertIn("An ordinary restore does not override a refund", terms)
        self.assertIn("refund-reversal evidence", privacy)
        self.assertIn("does not guarantee recovery of every missed provider notification", privacy)
        historical = normalized((output / "legal/2026-10-03-beta.5/terms/index.html").read_text())
        self.assertIn("The Beta does not enrol you in a paid subscription", historical)
        self.assertNotIn("controlled testing of the monthly Daily Pause Plus", historical)

    def test_banked_diamond_edition_retains_beta_six_and_separates_free_paid_claims(self):
        previous = self.root / "legal/2026-10-03-beta.6"
        expected = {
            "terms-beta.md": "0e199264015cf0705dffdd43172e0511c151efffec69d9ab96da53ef837da2b7",
            "privacy-beta.md": "c4a63dc5b1e00487fc0c65eb6d90ef5abfb66d4da2bc1f5a687a26b1e83c2e4d",
            "manifest.json": "239edfd2a9ca83397f6a1008e857a24b9c92e0803f12c426546f6be4d67d658c",
        }
        for name, checksum in expected.items():
            self.assertEqual(hashlib.sha256((previous / name).read_bytes()).hexdigest(), checksum)
        output = self.build()
        terms = normalized((output / "beta/terms/index.html").read_text())
        privacy = normalized((output / "beta/privacy/index.html").read_text())
        self.assertIn("2026-10-03-beta.8", terms)
        self.assertIn("each previously confirmed diamond into ten new diamonds", terms)
        self.assertIn("manual claim of one free star", terms)
        self.assertIn("An unclaimed free daily star expires", terms)
        self.assertIn("net.versava.puzzleapp.plus_diamonds_monthly", terms)
        self.assertIn("two new diamonds for each eligible UTC calendar date", terms)
        self.assertIn("Missed dates do not expire", terms)
        self.assertIn("does not forfeit the banked allowance", terms)
        self.assertIn("does not include all-pack access, automatic-ad removal or free unlimited hints", terms)
        self.assertIn("audited adjustment adds nine times the existing confirmed balance", privacy)
        self.assertIn("a manual claim can collect unclaimed covered dates", privacy.lower())
        historical = normalized((output / "legal/2026-10-03-beta.6/terms/index.html").read_text())
        self.assertIn("all offered packs, Past daily puzzles", historical)
        self.assertIn("for 50 stars or one diamond", historical)
        self.assertNotIn("plus_diamonds_monthly", historical)

    def test_extended_hint_edition_retains_beta_seven_and_verifies_plus_caps(self):
        previous = self.root / "legal/2026-10-03-beta.7"
        for name, checksum in {
            "terms-beta.md": "3712234c8290c55ea12c518c26f0dd71139649d3b649dcbbb9336ee398112570",
            "privacy-beta.md": "5821dd62ff13221417fadd7d51250ab457dbeba697da54c37cd7cef91d002213",
        }.items():
            self.assertEqual(hashlib.sha256((previous / name).read_bytes()).hexdigest(), checksum)
        output = self.build()
        terms = normalized((output / "beta/terms/index.html").read_text())
        privacy = normalized((output / "beta/privacy/index.html").read_text())
        self.assertIn("Each further hint costs one new diamond", terms)
        self.assertIn("Neither a video nor Plus covers the diamond cost", terms)
        self.assertIn("permanent whole-day unlock for each selected supported Past date", terms)
        self.assertIn("shares the same limit as its verified rewarded-ad alternative", terms)
        self.assertIn("Banked paid daily diamonds remain separate", terms)
        self.assertIn("Production currency purchases remain disabled", terms)
        self.assertIn("A Plus claim does not create a fictitious Google ad event", privacy)
        self.assertIn("hints from the fourth onwards require a diamond-funded grant", privacy)
        old = normalized((output / "legal/2026-10-03-beta.7/terms/index.html").read_text())
        self.assertIn("Each puzzle question allows at most three hints", old)
        self.assertIn("one confirmed new diamond for one star", old)
        self.assertNotIn("Each further hint costs one new diamond", old)

    def test_unreviewed_source_files_are_not_published(self):
        (self.root / "unreviewed-internal.txt").write_text("Not website content.")
        (self.root / "legal" / self.edition / "unreviewed-internal.txt").write_text("Not a policy.")
        output = self.build()
        actual = {str(path.relative_to(output)) for path in output.rglob("*") if path.is_file()}
        expected = {
            "manifest.json", "manifest.schema.json", "client-release.json", "index.html", "404.html",
            "_headers", "styles.css", "brand.svg", "legal/current.json",
            "internal/manifest.json", "internal/manifest-v5.json", "internal/client-release.json",
            "alpha/terms/index.html", "alpha/privacy/index.html",
            "beta/index.html", "beta/terms/index.html", "beta/privacy/index.html",
            "terms/index.html", "privacy/index.html", "support/index.html", "legal/index.html",
        }
        for edition, (manifest, _) in self.editions.items():
            expected.update(f"legal/{edition}/{name}" for name in (
                "index.html", "manifest.json", *FILES[manifest["channel"]].values(),
                "terms/index.html", "privacy/index.html",
            ))
        self.assertEqual(actual, expected)

    def test_source_html_is_text_and_cannot_introduce_script_or_event_handlers(self):
        source = '# Notice <script>alert("x")</script>\n\n<script>alert("x")</script>\n<img src=x onerror="alert(1)">\n'
        rendered, _ = render_document(source)
        page = Page(f'<article data-policy-document="terms">{rendered}</article>')
        expected = normalized(re.sub(r"^# ", "", source, flags=re.M))
        self.assertEqual(normalized("".join(page.article)), expected)
        self.assertNotIn("script", page.tags)
        self.assertNotIn("img", page.tags)
        self.assertFalse(any(name.startswith("on") for name in page.attributes))

    def test_all_internal_routes_assets_and_section_links_resolve_without_scripts(self):
        output = self.build()
        for path in output.rglob("*.html"):
            page = Page(path.read_text())
            with self.subTest(page=path.relative_to(output)):
                self.assertFalse(set(page.tags) & {"script", "iframe", "form", "input", "button"})
                self.assertFalse(any(name.startswith("on") for name in page.attributes))
                for target in page.targets:
                    uri = urlsplit(target)
                    if uri.scheme:
                        self.assertIn(uri.scheme, {"https", "mailto"})
                        if uri.scheme == "https":
                            self.assertEqual(uri.netloc, "puzzle.versava.net")
                        continue
                    self.assertFalse(uri.netloc)
                    if uri.path:
                        resolved = output / uri.path.lstrip("/")
                        if uri.path.endswith("/"):
                            resolved /= "index.html"
                        self.assertTrue(resolved.is_file(), target)
                    if uri.fragment:
                        self.assertIn(uri.fragment, page.ids)

    def test_policy_metadata_cannot_redirect_publication_to_an_unreviewed_file(self):
        manifest_path = self.root / "legal" / self.edition / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["documents"]["terms"]["file"] = "../../unreviewed-internal.txt"
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "Invalid legal source entry"):
            load_editions(self.root)

    def test_git_history_rejects_source_and_hash_rewrite_or_removal(self):
        def git(*args):
            return subprocess.run(
                ["git", "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args],
                cwd=self.root, capture_output=True, check=True,
            ).stdout

        git("init", "-q", "-b", "main")
        git("config", "user.name", "Legal edition test")
        git("config", "user.email", "legal-test@example.invalid")
        git("add", "manifest.json", "legal")
        git("commit", "-q", "-m", "First published edition")
        self.assertEqual(check_release(self.root), 1)
        source = self.root / "legal" / self.edition / "terms-beta.md"
        manifest_path = source.parent / "manifest.json"
        original_source, original_manifest = source.read_bytes(), manifest_path.read_bytes()
        source.write_bytes(original_source + b"\nReplacement statement.\n")
        manifest = json.loads(original_manifest)
        manifest["documents"]["terms"]["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest))
        # Matching hashes are insufficient: previously published bytes must stay.
        load_editions(self.root)
        with self.assertRaisesRegex(ValueError, "Frozen legal edition was rewritten"):
            check_release(self.root)
        git("add", "legal")
        git("commit", "-q", "-m", "Rewrite source and matching hash")
        baseline = git("rev-parse", "HEAD").decode().strip()
        with self.assertRaisesRegex(ValueError, "Frozen legal edition was rewritten"):
            check_release(self.root, baseline_ref=baseline)
        # Removing a source is rejected even when the newest commit's hash
        # manifest otherwise matches the working tree.
        source.unlink()
        with self.assertRaisesRegex(ValueError, "Retain published legal source"):
            check_release(self.root)


if __name__ == "__main__":
    unittest.main()
