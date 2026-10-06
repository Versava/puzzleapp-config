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
        if (ROOT / "app-ads.txt").is_file():
            shutil.copyfile(ROOT / "app-ads.txt", self.root / "app-ads.txt")
        shutil.copytree(ROOT / "legal", self.root / "legal")
        shutil.copytree(ROOT / "scripts", self.root / "scripts")
        shutil.copytree(ROOT / "internal", self.root / "internal")
        self.current, self.editions = load_editions(self.root)
        self.edition = self.current["betaEdition"]

    def test_autofill_regional_value_edition_retains_published_beta_fifteen(self):
        previous = self.root / "legal/2026-10-05-beta.15"
        for name, checksum in {
            "terms-beta.md": "f90e35cf6c318c4ee50d7b3fde7932dfc35f7d3e6124b3e92d60e8098beeda2c",
            "privacy-beta.md": "6b886036e74411a9fb9a949e3a6b20773aea61e13ba92c459bd85144e5361a7a",
        }.items():
            self.assertEqual(hashlib.sha256((previous / name).read_bytes()).hexdigest(), checksum)
        self.assertEqual(self.edition, "2026-10-06-beta.18")
        output = self.build()
        terms = normalized(" ".join(Page((output / "beta/terms/index.html").read_text()).article))
        privacy = normalized(" ".join(Page((output / "beta/privacy/index.html").read_text()).article))
        self.assertIn("costs three diamonds from its first use", terms)
        self.assertIn("never changes fixed clues", terms)
        self.assertIn("grants no move and charges nothing", terms)
        self.assertIn("does not refund an already delivered use", terms)
        self.assertIn("same storefront's diamond-bundle price", terms)
        self.assertIn("not a live currency exchange rate", terms)
        self.assertIn("canonical state hash, before-and-after board or path state", privacy)
        self.assertIn("account exports until deletion", privacy)
        self.assertIn("currency code, storefront identifier", privacy)

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

    def test_reviewed_seller_source_is_copied_as_exact_plain_text(self):
        source = b"google.com, pub-8798981282479093, DIRECT\n"
        (self.root / "app-ads.txt").write_bytes(source)
        output = self.build()
        self.assertEqual((output / "app-ads.txt").read_bytes(), source)
        self.assertIn(
            "/app-ads.txt\n  Content-Type: text/plain; charset=utf-8",
            (output / "_headers").read_text(),
        )

    def test_unreviewed_seller_fails_before_replacing_previous_output(self):
        output = self.build()
        previous = (output / "beta/terms/index.html").read_bytes()
        (self.root / "app-ads.txt").write_bytes(b"<html>Unreviewed seller</html>\n")
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
        self.assertEqual(self.edition, "2026-10-06-beta.18")
        output = self.build()
        current = (output / "beta/terms/index.html").read_text()
        old = (output / "legal/2026-10-01-beta.2/terms/index.html").read_text()
        self.assertIn("2026-10-06-beta.18", current)
        self.assertIn("2026-10-01-beta.2", old)
        self.assertNotIn("Each puzzle question allows at most three hints", old)
        self.assertIn("each later Hint costs one diamond", current)
        for route in ("beta", "support"):
            status = (output / route / "index.html").read_text()
            self.assertIn("one-time Remove Ads product", status)
            self.assertIn("Production Remove Ads checkout remains disabled", status)
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
        self.assertIn("Individual cash-pack checkout remains disabled", terms)
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
        self.assertIn("2026-10-06-beta.18", terms)
        self.assertIn("96 released packs across eight games", terms)
        self.assertIn("Each pack has one required price", terms)
        self.assertIn("A combined price requires both displayed amounts", terms)
        self.assertIn("charges neither amount", terms)
        self.assertIn("rejects a changed offer", terms)
        self.assertIn("confirmed offer revision", privacy)
        self.assertIn("A combined grant creates both wallet debits in the same transaction", privacy)
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
        self.assertIn("2026-10-06-beta.18", terms)
        self.assertIn("each previously confirmed diamond into ten new diamonds", terms)
        self.assertIn("manual claim of one free star", terms)
        self.assertIn("An unclaimed free daily star expires", terms)
        self.assertIn("net.versava.puzzleapp.plus_diamonds_monthly", terms)
        self.assertIn("two new diamonds for each eligible UTC calendar date", terms)
        self.assertIn("Missed dates do not expire", terms)
        self.assertIn("does not forfeit the banked allowance", terms)
        self.assertIn("does not include all-pack access, automatic-ad removal or free unlimited Hints or Autofill", terms)
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
        self.assertIn("each later Hint costs one diamond", terms)
        self.assertIn("Neither a video nor Plus covers later Hints or Autofill", terms)
        self.assertIn("permanent whole-day unlock for each selected supported Past date", terms)
        self.assertIn("shares the same limit as its verified rewarded-ad alternative", terms)
        self.assertIn("Banked paid daily diamonds remain separate", terms)
        self.assertIn("Production currency purchases remain disabled", terms)
        self.assertIn("A Plus claim does not create a fictitious Google ad event", privacy)
        self.assertIn("new assistance purchases use diamonds", privacy)
        old = normalized((output / "legal/2026-10-03-beta.7/terms/index.html").read_text())
        self.assertIn("Each puzzle question allows at most three hints", old)
        self.assertIn("one confirmed new diamond for one star", old)
        self.assertNotIn("each later Hint costs one diamond", old)

    def test_fixed_price_edition_retains_beta_eight_and_separates_remove_ads_sandbox(self):
        previous = self.root / "legal/2026-10-03-beta.8"
        for name, checksum in {
            "terms-beta.md": "72f79c2bed44f6adcba9521243f47feafe9d99539807f89dff0d98f0348d2b40",
            "privacy-beta.md": "17c26bb3291f9cb52a12ec791515a5373a939503efb06dbba7cfa961f6eef436",
        }.items():
            self.assertEqual(hashlib.sha256((previous / name).read_bytes()).hexdigest(), checksum)
        output = self.build()
        terms = normalized((output / "beta/terms/index.html").read_text())
        privacy = normalized((output / "beta/privacy/index.html").read_text())
        self.assertIn("2026-10-06-beta.18", terms)
        self.assertIn("A combined price requires both displayed amounts", terms)
        self.assertIn("grants nothing and charges neither amount", terms)
        self.assertIn("one-time Remove Ads product may be tested only in designated Sandbox builds", terms)
        self.assertIn("Production Remove Ads checkout remains disabled", terms)
        self.assertIn("applicable currency version and a retry reference", privacy)
        self.assertIn("Ad-serving controls are separate from purchase controls", privacy)
        old = normalized((output / "legal/2026-10-03-beta.8/terms/index.html").read_text())
        self.assertIn("for 50 stars or 20 new diamonds", old)
        self.assertIn("Individual cash-pack and Remove Ads checkout remain disabled", old)
        self.assertNotIn("A combined price requires both displayed amounts", old)

    def test_bonus_totals_retain_beta_nine_and_original_fulfillment_quantities(self):
        previous = self.root / "legal/2026-10-03-beta.9"
        for name, checksum in {
            "terms-beta.md": "9e5f43db00d7ceecae6813df4704e1cf3fb7025f2936f942c2105beb0f05cdb4",
            "privacy-beta.md": "2850703566c95813b5a7473e8e175bb7e7f52d2ad64e98709100e46f09ceb06e",
        }.items():
            self.assertEqual(hashlib.sha256((previous / name).read_bytes()).hexdigest(), checksum)
        output = self.build()
        terms = normalized((output / "beta/terms/index.html").read_text())
        privacy = normalized((output / "beta/privacy/index.html").read_text())
        self.assertIn("50, 200 or 500 stars", terms)
        self.assertIn("10, 40 or 100 diamonds", terms)
        self.assertIn("150 stars plus 50 bonus", terms)
        self.assertIn("€1.99, €4.99 and €9.99", terms)
        self.assertIn("An included bonus is part of the displayed total", terms)
        self.assertIn("Previously confirmed transactions retain their recorded quantity", terms)
        self.assertIn("does not rewrite them", privacy)
        old = normalized((output / "legal/2026-10-03-beta.9/terms/index.html").read_text())
        self.assertIn("A combined price requires both displayed amounts", old)
        self.assertNotIn("50, 200 or 500 stars", old)

    def test_unreviewed_source_files_are_not_published(self):
        (self.root / "unreviewed-internal.txt").write_text("Not website content.")
        (self.root / "legal" / self.edition / "unreviewed-internal.txt").write_text("Not a policy.")
        output = self.build()
        actual = {str(path.relative_to(output)) for path in output.rglob("*") if path.is_file()}
        expected = {
            "manifest.json", "manifest.schema.json", "client-release.json", "index.html", "404.html",
            "_headers", "styles.css", "brand.svg", "legal/current.json",
            "internal/manifest.json", "internal/manifest-v5.json", "internal/manifest-v6.json", "internal/manifest-v7.json", "internal/client-release.json",
            "alpha/terms/index.html", "alpha/privacy/index.html",
            "beta/index.html", "beta/terms/index.html", "beta/privacy/index.html",
            "terms/index.html", "privacy/index.html", "support/index.html", "legal/index.html",
        }
        if (ROOT / "app-ads.txt").is_file():
            expected.add("app-ads.txt")
        for edition, (manifest, _) in self.editions.items():
            expected.update(f"legal/{edition}/{name}" for name in (
                "index.html", "manifest.json", *FILES[manifest["channel"]].values(),
                "terms/index.html", "privacy/index.html",
            ))
        self.assertEqual(actual, expected)

    def test_publisher_beta_edition_retains_beta_ten_and_discloses_consent_and_scoped_rewards(self):
        previous = self.root / "legal/2026-10-03-beta.10"
        for name, checksum in {
            "terms-beta.md": "295ea1d1d5951bdbe333eeb4993760617518d9ecbe0748d23dc4e6de8e73778e",
            "privacy-beta.md": "7132bee3b31b694eca1aa593723eded43c06204b54b3563b93531e22edd3c9d5",
        }.items():
            self.assertEqual(hashlib.sha256((previous / name).read_bytes()).hexdigest(), checksum)
        self.assertEqual(self.edition, "2026-10-06-beta.18")
        output = self.build()
        terms = normalized(" ".join(Page((output / "beta/terms/index.html").read_text()).article))
        privacy = normalized(" ".join(Page((output / "beta/privacy/index.html").read_text()).article))
        self.assertIn("publisher banner ads", terms)
        self.assertIn("optional rewarded videos", terms)
        self.assertIn("Production paid purchases, paid pack checkout and Production paid subscriptions remain disabled", terms)
        self.assertIn("consent and refusal choices", privacy)
        self.assertIn("non-personalised ads", privacy)
        self.assertIn("does not request Apple's cross-app tracking permission", privacy)
        self.assertIn("Ad privacy options in the Store", privacy)
        self.assertIn("Google's signed completion callback", privacy)
        self.assertIn("random, scoped reward reference", privacy)
        self.assertIn("does not contain your Apple name", privacy)
        self.assertIn("Banner views do not earn currency", privacy)
        self.assertIn("A sample video does not credit spendable stars", privacy)
        self.assertNotIn("Publisher advertising and real ad-funded rewards are disabled", privacy)
        for route in ("beta", "support"):
            status = normalized((output / route / "index.html").read_text())
            self.assertIn("publisher banners", status)
            self.assertIn("consent and refusal flow", status)
            self.assertNotIn("subscriptions and publisher ads remain disabled", status)
        historical = normalized((output / "legal/2026-10-03-beta.10/privacy/index.html").read_text())
        self.assertIn("Publisher advertising and real ad-funded rewards are disabled", historical)

    def test_source_html_is_text_and_cannot_introduce_script_or_event_handlers(self):
        source = '# Notice <script>alert("x")</script>\n\n<script>alert("x")</script>\n<img src=x onerror="alert(1)">\n'
        rendered, _ = render_document(source)
        page = Page(f'<article data-policy-document="terms">{rendered}</article>')
        expected = normalized(re.sub(r"^# ", "", source, flags=re.M))
        self.assertEqual(normalized("".join(page.article)), expected)
        self.assertNotIn("script", page.tags)
        self.assertNotIn("img", page.tags)
        self.assertFalse(any(name.startswith("on") for name in page.attributes))

    def test_account_lifecycle_editions_retain_published_history_and_describe_scoped_rights(self):
        for edition, names in {
            "2026-10-03-beta.11": {
                "terms-beta.md": "ea9c0ed03fe89ce250b0c300589ca1ca416e86318487b48791ef578464fd66ad",
                "privacy-beta.md": "808cfccbc7d45b50febbe1960efaebe3cda2ccd0398c4db16053e73586f04d67",
            },
            "2026-09-30-public.1": {
                name: self.editions["2026-09-30-public.1"][0]["documents"][kind]["sha256"]
                for kind, name in FILES["public"].items()
            },
        }.items():
            for name, checksum in names.items():
                self.assertEqual(hashlib.sha256((self.root / "legal" / edition / name).read_bytes()).hexdigest(), checksum)
        self.assertEqual(self.current["publicEdition"], "2026-10-05-public.5")
        output = self.build()
        for channel, route in (("beta", "beta/"), ("public", "")):
            terms = normalized(" ".join(Page((output / f"{route}terms/index.html").read_text()).article))
            privacy = normalized(" ".join(Page((output / f"{route}privacy/index.html").read_text()).article))
            with self.subTest(channel=channel):
                self.assertIn("Delete account", terms)
                self.assertIn("Account → Contact support → Delete account", terms)
                self.assertIn("14-calendar-day grace period", terms)
                self.assertIn("exact deletion date", terms)
                self.assertIn("account remains usable", terms)
                self.assertIn("Stop deletion", terms)
                if channel == "beta":
                    self.assertIn("Manage subscriptions separately", terms)
                else:
                    self.assertIn("Manage or cancel the subscription through Apple's controls", terms)
                self.assertIn("Export my data", privacy)
                self.assertIn("Delete account under Contact support", privacy)
                self.assertIn("exact deletion time 14 calendar days later", privacy)
                self.assertIn("account remains usable", privacy)
                self.assertIn("Stop deletion", privacy)
                self.assertIn("31 days", privacy)
                self.assertIn("up to 30 days", privacy)
                self.assertIn("one month", privacy)
                self.assertIn("human review", privacy)
                self.assertIn("unclaimed banked", terms)
                self.assertIn("Restore Purchases", terms)
                self.assertIn("next UTC date", terms)
                self.assertIn("next UTC date", privacy)
                self.assertIn("purchase/day ledger", privacy)
                self.assertIn("CHOI, Chong Hing", privacy)
                self.assertIn("Fasangartenstr 102, 81549 München", privacy)
                self.assertIn("privacy@versava.net", privacy)
                self.assertIn(
                    '<!--email_off--><a href="mailto:privacy@versava.net">privacy@versava.net</a><!--/email_off-->',
                    (output / f"{route}privacy/index.html").read_text(),
                )
                if channel == "beta":
                    self.assertIn("configured €29.99 euro reference", terms)
                    self.assertIn("costs three diamonds from its first use", terms)
                    self.assertIn("before-and-after board or path state", privacy)
                else:
                    self.assertIn("Bundle value €29.99", terms)
                self.assertIn("not the subscription charge", terms)
                self.assertNotIn("There is currently no automatic account-deletion control", privacy)
        historical = normalized((output / "legal/2026-10-03-beta.11/privacy/index.html").read_text())
        self.assertIn("There is currently no automatic account-deletion control", historical)
        public_terms = normalized((output / "terms/index.html").read_text())
        self.assertIn("two diamonds per eligible UTC date", public_terms)
        self.assertIn("A combined price requires both amounts", public_terms)
        self.assertIn("Apple handles refunds", public_terms)
        support = normalized((output / "support/index.html").read_text())
        self.assertIn("Request my data", support)
        self.assertIn("Account → Contact support → Delete account", support)
        self.assertIn("exact time 14 calendar days later", support)
        self.assertIn("account remains usable", support)
        self.assertIn("Stop deletion", support)
        self.assertIn("Account deletion does not cancel Apple subscription billing", support)
        self.assertIn("manage the subscription separately", support)
        self.assertIn("normal response period is one month", support)
        self.assertIn("New Plus diamond eligibility starts on the next UTC date", support)
        self.assertIn("Fasangartenstr 102, 81549 München", support)
        self.assertIn("privacy@versava.net", support)
        support_source = (output / "support/index.html").read_text()
        self.assertIn(
            '<!--email_off--><h2>Account and privacy requests</h2>',
            support_source,
        )
        self.assertIn('href="mailto:privacy@versava.net"', support_source)

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
