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
from legal_site import FILES, MAX_LEGAL_INFO_BYTES, MAX_LEGAL_SOURCE_BYTES, load_editions, load_reader_drafts, render_document, render_legal_info
from validate_client_release import load as load_client_release
from validate_client_support import load as load_client_support


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
            "manifest.json", "manifest.schema.json", "legal-info.schema.json", "client-release.json", "client-support.json", "index.html", "404.html",
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
        self.assertEqual(self.edition, "2026-10-24-beta.26")
        output = self.build()
        terms = normalized(" ".join(Page((output / "legal/2026-10-06-beta.19/terms/index.html").read_text()).article))
        privacy = normalized(" ".join(Page((output / "legal/2026-10-06-beta.19/privacy/index.html").read_text()).article))
        self.assertIn("costs three diamonds from its first use", terms)
        self.assertIn("never changes fixed clues", terms)
        self.assertIn("does not create a new confirmed move receipt or debit", terms)
        self.assertIn("does not refund an already delivered use", terms)
        self.assertIn("same storefront's diamond-bundle price", terms)
        self.assertIn("not a live currency exchange rate", terms)
        self.assertIn("canonical state hash, before-and-after board or path state", privacy)
        self.assertIn("account exports until deletion", privacy)
        self.assertIn("currency code, storefront identifier", privacy)

    def test_offline_autofill_edition_retains_beta_eighteen_and_requires_provisional_confirmation(self):
        previous = self.root / "legal/2026-10-06-beta.18"
        for name, checksum in {
            "terms-beta.md": "2a83db5352d7d5abb833d60efd956b6864d9d089ef940381ce73c78a6fe70bcf",
            "privacy-beta.md": "1812ec0885719f93e862f10ae7c88290fa1395b368140bb0470b5e00ebb31af5",
        }.items():
            self.assertEqual(hashlib.sha256((previous / name).read_bytes()).hexdigest(), checksum)
        self.assertEqual(self.edition, "2026-10-24-beta.26")
        self.assertEqual(self.current["publicEdition"], "2026-10-24-public.12")
        output = self.build()
        terms = normalized(" ".join(Page((output / "legal/2026-10-06-beta.19/terms/index.html").read_text()).article))
        privacy = normalized(" ".join(Page((output / "legal/2026-10-06-beta.19/privacy/index.html").read_text()).article))
        for statement in (
            "Autofill can prepare one provisional move on the device",
            "Local delivery is not a confirmed service receipt or final debit",
            "after other pending Hint and Autofill costs",
            "preserves its original terms",
            "do not remove its recorded use or payment reservation",
        ):
            self.assertIn(statement, terms)
        for statement in (
            "original before-and-after board or path state",
            "original request protocol",
            "account delivery journal uses Keychain storage",
            "account-bound operation marker",
            "Editing, Undo or Reset does not erase this marker",
        ):
            self.assertIn(statement, privacy)
        self.assertNotIn("Autofill requires online account access", terms)

    def build(self):
        subprocess.run(
            [sys.executable, "scripts/build.py"], cwd=self.root,
            capture_output=True, check=True,
        )
        return self.root / "dist"

    def test_legal_json_contains_exact_verified_sources_for_every_retained_edition(self):
        previous_sources = {
            str(path.relative_to(self.root)): path.read_bytes()
            for path in (self.root / "legal").rglob("*") if path.is_file()
        }
        output = self.build()
        for edition, (manifest, _) in self.editions.items():
            channel = manifest["channel"]
            path = output / f"legal/v1/editions/{edition}.json"
            raw = path.read_bytes()
            payload = json.loads(raw)
            with self.subTest(edition=edition):
                self.assertLessEqual(len(raw), MAX_LEGAL_INFO_BYTES)
                self.assertEqual(set(payload), {"schemaVersion", "channel", "edition", "documents"})
                self.assertEqual(type(payload["schemaVersion"]), int)
                self.assertEqual(payload["schemaVersion"], 1)
                self.assertEqual(payload["channel"], channel)
                self.assertEqual(payload["edition"], edition)
                self.assertEqual(set(payload["documents"]), {"terms", "privacy"})
                for kind, filename in FILES[channel].items():
                    document = payload["documents"][kind]
                    source = self.root / "legal" / edition / filename
                    source_bytes = source.read_bytes()
                    self.assertEqual(set(document), {"title", "format", "text", "sourceUrl", "readerUrl", "sha256"})
                    self.assertEqual(document["title"], source_bytes.decode("utf-8").splitlines()[0][2:])
                    self.assertEqual(document["format"], "markdown")
                    self.assertEqual(document["text"].encode("utf-8"), source_bytes)
                    self.assertEqual(document["sha256"], hashlib.sha256(source_bytes).hexdigest())
                    self.assertEqual(document["sha256"], manifest["documents"][kind]["sha256"])
                    self.assertEqual(document["sourceUrl"], f"https://puzzle.versava.net/legal/{edition}/{filename}")
                    self.assertEqual(document["readerUrl"], f"https://puzzle.versava.net/legal/{edition}/{kind}/")
                    for key in ("sourceUrl", "readerUrl"):
                        relative = urlsplit(document[key]).path.lstrip("/")
                        target = output / relative
                        if relative.endswith("/"):
                            target /= "index.html"
                        self.assertTrue(target.is_file())
        for relative, original in previous_sources.items():
            self.assertEqual((self.root / relative).read_bytes(), original)

    def test_current_legal_json_aliases_are_deterministic_and_channel_specific(self):
        generated = render_legal_info(self.current, self.editions)
        self.assertEqual(generated, render_legal_info(self.current, self.editions))
        output = self.build()
        for channel in ("public", "beta"):
            edition = self.current[f"{channel}Edition"]
            alias = f"legal/v1/{channel}.json"
            with self.subTest(channel=channel):
                self.assertEqual(generated[alias], generated[f"legal/v1/editions/{edition}.json"])
                self.assertEqual((output / alias).read_bytes(), generated[alias])
                payload = json.loads(generated[alias])
                self.assertEqual(payload["channel"], channel)
                self.assertEqual(payload["edition"], edition)
                for kind, document in payload["documents"].items():
                    self.assertTrue(document["sourceUrl"].endswith(f"/{kind}-{channel}.md"))
        self.assertNotIn("legal/v1/alpha.json", generated)
        first = {str(path.relative_to(output)): path.read_bytes() for path in (output / "legal/v1").rglob("*.json")}
        output = self.build()
        self.assertEqual(first, {str(path.relative_to(output)): path.read_bytes() for path in (output / "legal/v1").rglob("*.json")})

    def test_legal_json_schema_and_headers_are_published_without_changing_security(self):
        output = self.build()
        schema = json.loads((output / "legal-info.schema.json").read_bytes())
        self.assertEqual(schema["$id"], "https://puzzle.versava.net/legal-info.schema.json")
        self.assertEqual(schema["required"], ["schemaVersion", "channel", "edition", "documents"])
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(schema["properties"]["documents"]["additionalProperties"])
        self.assertFalse(schema["$defs"]["document"]["additionalProperties"])
        headers = (output / "_headers").read_text()
        self.assertIn("/*\n  Access-Control-Allow-Origin: *", headers)
        self.assertIn("Content-Security-Policy: default-src 'none'; style-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'", headers)
        for channel in ("public", "beta"):
            self.assertIn(f"/legal/v1/{channel}.json\n  Content-Type: application/json; charset=utf-8\n  Cache-Control: public, max-age=300, must-revalidate", headers)
        self.assertIn("/legal/v1/editions/*.json\n  Content-Type: application/json; charset=utf-8\n  Cache-Control: public, max-age=31536000, immutable", headers)
        self.assertIn("/legal-info.schema.json\n  Content-Type: application/schema+json; charset=utf-8", headers)

    def replace_current_terms(self, text):
        folder = self.root / "legal" / self.edition
        (folder / "terms-beta.md").write_bytes(text.encode("utf-8"))
        path = folder / "manifest.json"
        manifest = json.loads(path.read_text())
        manifest["documents"]["terms"]["sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        path.write_text(json.dumps(manifest))

    def test_invalid_legal_json_source_sizes_and_titles_preserve_previous_output(self):
        output = self.build()
        previous = (output / "legal/v1/beta.json").read_bytes()
        original = (self.root / "legal" / self.edition / "terms-beta.md").read_text()
        cases = (
            ("Invalid legal source size", original + "x" * MAX_LEGAL_SOURCE_BYTES),
            ("Legal source must start with a document title", original.replace("# ", "", 1)),
            ("Legal JSON bundle exceeds its size limit", original + "\x00" * 200_000),
        )
        for message, changed in cases:
            with self.subTest(message=message):
                self.replace_current_terms(changed)
                completed = subprocess.run([sys.executable, "scripts/build.py"], cwd=self.root, capture_output=True)
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(message, completed.stderr.decode())
                self.assertEqual((output / "legal/v1/beta.json").read_bytes(), previous)

    def test_cross_channel_current_pointer_cannot_publish_a_legal_json_alias(self):
        output = self.build()
        previous = (output / "legal/v1/beta.json").read_bytes()
        changed = dict(self.current, betaEdition=self.current["publicEdition"])
        (self.root / "legal/current.json").write_text(json.dumps(changed))
        with self.assertRaisesRegex(ValueError, "Current beta edition is missing or uses another channel"):
            load_editions(self.root)
        with self.assertRaises(subprocess.CalledProcessError):
            self.build()
        self.assertEqual((output / "legal/v1/beta.json").read_bytes(), previous)

    def test_actual_frozen_documents_preserve_all_words_in_every_reading_route(self):
        output = self.build()
        reader_drafts = load_reader_drafts(self.root, self.current, self.editions)
        for edition, (manifest, _) in self.editions.items():
            channel = manifest["channel"]
            for kind, filename in FILES[channel].items():
                source = (self.root / "legal" / edition / filename).read_text()
                if channel == "public" and edition in reader_drafts:
                    source = re.sub(r"^Version: [^\n]+ · Updated: (.+)$", r"Updated: \1", source, flags=re.M)
                visible_source = source.replace("[account help](https://puzzle.versava.net/support/)", "account help")
                expected = normalized(re.sub(r"^(?:#{1,3}|-) ", "", visible_source, flags=re.M))
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
                        self.assertIn(f'data-policy-edition="{edition}"', content)
                        self.assertEqual('content="noindex, follow"' in content, channel != "public")
                        self.assertIn(f'<title>{source.splitlines()[0][2:]} | Daily Pause</title>', content)
        # Public URLs are independent agreements, never aliases of test terms.
        self.assertIn('Daily Pause Terms of Use', (output / "terms/index.html").read_text())
        self.assertNotIn('data-policy-channel="beta"', (output / "terms/index.html").read_text())

    def test_public_navigation_cannot_reach_testing_documents(self):
        output = self.build()

        def testing_route(path):
            return path.startswith(("/beta/", "/alpha/")) or any(
                path.startswith(f"/legal/{edition}/")
                for edition, (manifest, _) in self.editions.items()
                if manifest["channel"] != "public"
            )

        for path in output.rglob("*.html"):
            route = "/" + path.relative_to(output).as_posix()
            if testing_route(route):
                continue
            for target in Page(path.read_text()).targets:
                uri = urlsplit(target)
                if uri.scheme not in ("", "http", "https") or uri.netloc not in ("", "puzzle.versava.net"):
                    continue
                with self.subTest(page=route, target=target):
                    self.assertFalse(testing_route(uri.path))

        documents = Page((output / "legal/index.html").read_text()).targets
        self.assertIn("/terms/", documents)
        self.assertIn("/privacy/", documents)
        for edition in self.editions:
            self.assertNotIn(f"/legal/{edition}/", documents)

    def test_testing_documents_stay_available_through_direct_links(self):
        output = self.build()
        for channel in ("beta", "alpha"):
            for kind in ("terms", "privacy"):
                route = f"{channel}/{kind}/index.html"
                source = (output / route).read_text()
                self.assertIn(f'data-policy-channel="{channel}"', source)
                self.assertIn('content="noindex, follow"', source)
                self.assertIn(self.current[f"{channel}Edition"], source)
        beta = Page((output / "beta/index.html").read_text()).targets
        self.assertIn("/beta/terms/", beta)
        self.assertIn("/beta/privacy/", beta)

    def test_current_public_product_and_legal_copy_has_no_testing_references(self):
        output = self.build()
        edition = self.current["publicEdition"]
        routes = (
            "index.html", "404.html", "support/index.html",
            "terms/index.html", "privacy/index.html",
            f"legal/{edition}/terms/index.html", f"legal/{edition}/privacy/index.html",
        )
        for route in routes:
            with self.subTest(route=route):
                content = (output / route).read_text()
                self.assertNotRegex(content, re.compile(r"\b(?:Beta|TestFlight)\b", re.I))
        self.assertEqual(load_reader_drafts(self.root, self.current, self.editions), set())
        for kind in ("terms", "privacy"):
            current = (output / f"{kind}/index.html").read_text()
            self.assertIn(f"Version: {edition}", "".join(Page(current).article))

    def test_only_explicit_current_public_draft_hides_reader_version(self):
        edition = self.current["publicEdition"]
        (self.root / "legal/reader-drafts.json").write_text(json.dumps({
            "schemaVersion": 1, "publicDraftEditions": [edition],
        }))
        self.assertEqual(load_reader_drafts(self.root, self.current, self.editions), {edition})
        output = self.build()
        for kind in ("terms", "privacy"):
            for route in (f"{kind}/index.html", f"legal/{edition}/{kind}/index.html"):
                with self.subTest(route=route):
                    content = (output / route).read_text()
                    article = "".join(Page(content).article)
                    self.assertIn("Updated:", article)
                    self.assertNotIn("Version:", article)
                    self.assertNotIn("Permanent link to this edition", content)
                    self.assertIn(f'data-policy-edition="{edition}"', content)
        for retained, (manifest, _) in self.editions.items():
            if manifest["channel"] == "public" and retained != edition:
                content = (output / f"legal/{retained}/terms/index.html").read_text()
                self.assertIn(f"Version: {retained}", "".join(Page(content).article))
                self.assertIn("Permanent link to this edition", content)
        self.assertFalse((output / "legal/reader-drafts.json").exists())

    def test_issued_current_public_readers_restore_version_without_changing_legal_json(self):
        (self.root / "legal/reader-drafts.json").write_text(json.dumps({
            "schemaVersion": 1, "publicDraftEditions": [self.current["publicEdition"]],
        }))
        output = self.build()
        before_json = (output / "legal/v1/public.json").read_bytes()
        before_manifest = (output / f'legal/{self.current["publicEdition"]}/manifest.json').read_bytes()
        (self.root / "legal/reader-drafts.json").write_text(json.dumps({
            "schemaVersion": 1, "publicDraftEditions": [],
        }))
        output = self.build()
        edition = self.current["publicEdition"]
        for kind in ("terms", "privacy"):
            for route in (f"{kind}/index.html", f"legal/{edition}/{kind}/index.html"):
                with self.subTest(route=route):
                    content = (output / route).read_text()
                    self.assertIn(f"Version: {edition}", "".join(Page(content).article))
                    self.assertIn(f'href="/legal/{edition}/{kind}/">Permanent link to this edition</a>', content)
        self.assertEqual((output / "legal/v1/public.json").read_bytes(), before_json)
        self.assertEqual((output / f"legal/{edition}/manifest.json").read_bytes(), before_manifest)

    def test_later_current_public_edition_is_not_implicitly_a_draft(self):
        previous = self.current["publicEdition"]
        edition = "2026-10-23-public.11"
        folder = self.root / "legal" / edition
        folder.mkdir()
        manifest = dict(self.editions[previous][0], edition=edition, documents={})
        for kind, text in self.editions[previous][1].items():
            text = text.replace(f"Version: {previous}", f"Version: {edition}", 1)
            filename = FILES["public"][kind]
            data = text.encode("utf-8")
            (folder / filename).write_bytes(data)
            manifest["documents"][kind] = {"file": filename, "sha256": hashlib.sha256(data).hexdigest()}
        (folder / "manifest.json").write_text(json.dumps(manifest))
        (self.root / "legal/current.json").write_text(json.dumps(dict(self.current, publicEdition=edition)))
        (self.root / "legal/reader-drafts.json").write_text(json.dumps({
            "schemaVersion": 1, "publicDraftEditions": [],
        }))
        output = self.build()
        for kind in ("terms", "privacy"):
            current = (output / f"{kind}/index.html").read_text()
            retained = (output / f"legal/{previous}/{kind}/index.html").read_text()
            self.assertIn(f"Version: {edition}", "".join(Page(current).article))
            self.assertIn(f"Version: {previous}", "".join(Page(retained).article))
            self.assertIn("Permanent link to this edition", current)
            self.assertIn("Permanent link to this edition", retained)

    def test_invalid_reader_draft_configuration_preserves_previous_output(self):
        output = self.build()
        previous = (output / "terms/index.html").read_bytes()
        public = self.current["publicEdition"]
        historical = next(edition for edition, (manifest, _) in self.editions.items()
                          if manifest["channel"] == "public" and edition != public)
        valid = {"schemaVersion": 1, "publicDraftEditions": [public]}
        cases = (
            ("Invalid legal reader draft configuration", []),
            ("Invalid legal reader draft configuration", dict(valid, extra=True)),
            ("Invalid legal reader draft configuration", dict(valid, schemaVersion=True)),
            ("Invalid legal reader draft configuration", dict(valid, schemaVersion=2)),
            ("Invalid legal reader draft configuration", dict(valid, publicDraftEditions=public)),
            ("Invalid public reader draft edition identifier", dict(valid, publicDraftEditions=[None])),
            ("Invalid public reader draft edition identifier", dict(valid, publicDraftEditions=["../public"])),
            ("Duplicate public reader draft edition", dict(valid, publicDraftEditions=[public, public])),
            ("existing public edition", dict(valid, publicDraftEditions=["2026-10-23-public.999"])),
            ("existing public edition", dict(valid, publicDraftEditions=[self.edition])),
            ("Only the current public edition", dict(valid, publicDraftEditions=[historical])),
        )
        for message, config in cases:
            with self.subTest(config=config):
                (self.root / "legal/reader-drafts.json").write_text(json.dumps(config))
                with self.assertRaisesRegex(ValueError, message):
                    load_reader_drafts(self.root, self.current, self.editions)
                with self.assertRaises(subprocess.CalledProcessError):
                    self.build()
                self.assertEqual((output / "terms/index.html").read_bytes(), previous)

    def test_reader_draft_configuration_rejects_symlinks_before_replacing_output(self):
        output = self.build()
        previous = (output / "terms/index.html").read_bytes()
        path = self.root / "legal/reader-drafts.json"
        target = self.root / "reader-drafts.json"
        path.rename(target)
        path.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "must not be a symlink"):
            load_reader_drafts(self.root, self.current, self.editions)
        with self.assertRaises(subprocess.CalledProcessError):
            self.build()
        self.assertEqual((output / "terms/index.html").read_bytes(), previous)

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

    def test_historical_currency_edition_retains_beta_two_and_exposes_disabled_checkout(self):
        previous = self.root / "legal/2026-10-01-beta.2"
        expected = {
            "terms-beta.md": "bdeec8d7c9e110507f68532d3aff4afaa2a1b71c9f810b61e1ebede59ab957cc",
            "privacy-beta.md": "9b927248cfa17148fe67b695fc2a39048887d8e9cca9bce65508256dd4d94238",
        }
        for name, checksum in expected.items():
            self.assertEqual(hashlib.sha256((previous / name).read_bytes()).hexdigest(), checksum)
        self.assertEqual(self.edition, "2026-10-24-beta.26")
        output = self.build()
        current = (output / "legal/2026-10-06-beta.19/terms/index.html").read_text()
        old = (output / "legal/2026-10-01-beta.2/terms/index.html").read_text()
        self.assertIn("2026-10-06-beta.19", current)
        self.assertIn("2026-10-01-beta.2", old)
        self.assertNotIn("Each puzzle question allows at most three hints", old)
        self.assertIn("each later Hint costs one diamond", current)
        status = (output / "beta/index.html").read_text()
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
        terms = normalized((output / "legal/2026-10-06-beta.19/terms/index.html").read_text())
        privacy = normalized((output / "legal/2026-10-06-beta.19/privacy/index.html").read_text())
        historical = (output / "legal/2026-10-01-beta.3/terms/index.html").read_text()
        self.assertIn("ten new diamonds for each group of seven", terms)
        self.assertIn("New diamond-to-star exchanges are unavailable", terms)
        self.assertIn("96 released packs", terms)
        self.assertIn("Individual cash-pack checkout remains disabled", terms)
        self.assertIn("verified completed puzzle dates", privacy)
        self.assertIn("signed Apple transaction evidence", privacy)
        self.assertIn("Keychain delivery journal", privacy)
        self.assertNotIn("one diamond for each group of 14 consecutive", historical)

    def test_pack_offer_edition_retains_beta_four_and_matches_historical_redemption_records(self):
        previous = self.root / "legal/2026-10-02-beta.4"
        expected = {
            "terms-beta.md": "0ab65d34db4af55b773031dc3f6cc20cfb759cbe5a22d1025448ffbc679484c6",
            "privacy-beta.md": "cb63c74a4d4b0295fc4254869c8ad9be77483a4ccdfc4f7b8b6a2e439fb8a69d",
            "manifest.json": "a155232ffe59eb2ed054e18f3abf58276bf3fb35f5353806d9eb01d3198f2cab",
        }
        for name, checksum in expected.items():
            self.assertEqual(hashlib.sha256((previous / name).read_bytes()).hexdigest(), checksum)
        output = self.build()
        terms = normalized((output / "legal/2026-10-06-beta.19/terms/index.html").read_text())
        privacy = normalized((output / "legal/2026-10-06-beta.19/privacy/index.html").read_text())
        historical = normalized((output / "legal/2026-10-02-beta.4/terms/index.html").read_text())
        self.assertIn("2026-10-06-beta.19", terms)
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
        terms = normalized((output / "legal/2026-10-06-beta.19/terms/index.html").read_text())
        privacy = normalized((output / "legal/2026-10-06-beta.19/privacy/index.html").read_text())
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
        terms = normalized((output / "legal/2026-10-06-beta.19/terms/index.html").read_text())
        privacy = normalized((output / "legal/2026-10-06-beta.19/privacy/index.html").read_text())
        self.assertIn("2026-10-06-beta.19", terms)
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
        terms = normalized((output / "legal/2026-10-06-beta.19/terms/index.html").read_text())
        privacy = normalized((output / "legal/2026-10-06-beta.19/privacy/index.html").read_text())
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
        terms = normalized((output / "legal/2026-10-06-beta.19/terms/index.html").read_text())
        privacy = normalized((output / "legal/2026-10-06-beta.19/privacy/index.html").read_text())
        self.assertIn("2026-10-06-beta.19", terms)
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
        terms = normalized((output / "legal/2026-10-06-beta.19/terms/index.html").read_text())
        privacy = normalized((output / "legal/2026-10-06-beta.19/privacy/index.html").read_text())
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
            "manifest.json", "manifest.schema.json", "legal-info.schema.json", "client-release.json", "client-support.json", "index.html", "404.html",
            "_headers", "styles.css", "brand.svg", "legal/current.json",
            "internal/manifest.json", "internal/manifest-v5.json", "internal/manifest-v6.json", "internal/manifest-v7.json", "internal/client-release.json", "internal/client-support.json",
            "alpha/terms/index.html", "alpha/privacy/index.html",
            "beta/index.html", "beta/terms/index.html", "beta/privacy/index.html",
            "terms/index.html", "privacy/index.html", "support/index.html", "legal/index.html", "versions/index.html",
            "legal/v1/public.json", "legal/v1/beta.json",
        }
        if (ROOT / "app-ads.txt").is_file():
            expected.add("app-ads.txt")
        for edition, (manifest, _) in self.editions.items():
            expected.add(f"legal/v1/editions/{edition}.json")
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
        self.assertEqual(self.edition, "2026-10-24-beta.26")
        output = self.build()
        terms = normalized(" ".join(Page((output / "legal/2026-10-06-beta.19/terms/index.html").read_text()).article))
        privacy = normalized(" ".join(Page((output / "legal/2026-10-06-beta.19/privacy/index.html").read_text()).article))
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
        status = normalized((output / "beta/index.html").read_text())
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

    def test_wrapped_list_items_preserve_structure_escaping_and_email_links(self):
        bullets = (
            '- First <img src=x onerror="bad">\n'
            '  continued at support@versava.net.\n'
            '- Second <script>bad</script>\n'
            '\tcontinued at privacy@versava.net.'
        )
        endings = (
            ("paragraph", "\nFollowing paragraph.", "<p>Following paragraph.</p>"),
            ("heading", "\n## Following heading", '<h2 id="section-following-heading">'),
            ("blank", "\n\nFollowing paragraph.", "<p>Following paragraph.</p>"),
            ("end of file", "", ""),
        )
        for label, ending, following in endings:
            with self.subTest(ending=label):
                rendered, _ = render_document(bullets + ending)
                page = Page(f'<article data-policy-document="privacy">{rendered}</article>')
                self.assertEqual(page.tags.count("ul"), 1)
                self.assertEqual(page.tags.count("li"), 2)
                self.assertIn(
                    '<li>First &lt;img src=x onerror=&quot;bad&quot;&gt; continued at '
                    '<!--email_off--><a href="mailto:support@versava.net">support@versava.net</a><!--/email_off-->.</li>',
                    rendered,
                )
                self.assertIn(
                    '<li>Second &lt;script&gt;bad&lt;/script&gt; continued at '
                    '<!--email_off--><a href="mailto:privacy@versava.net">privacy@versava.net</a><!--/email_off-->.</li>',
                    rendered,
                )
                self.assertEqual(page.targets, ["mailto:support@versava.net", "mailto:privacy@versava.net"])
                self.assertFalse(set(page.tags) & {"img", "script"})
                self.assertFalse(any(name.startswith("on") for name in page.attributes))
                if following:
                    self.assertIn(f"</li>\n</ul>\n{following}", rendered)
                else:
                    self.assertTrue(rendered.endswith("</li>\n</ul>"))

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
        self.assertEqual(self.current["publicEdition"], "2026-10-24-public.12")
        output = self.build()
        for channel, route in (("beta", "beta/"), ("public", "")):
            terms = normalized(" ".join(Page((output / f"{route}terms/index.html").read_text()).article))
            privacy = normalized(" ".join(Page((output / f"{route}privacy/index.html").read_text()).article))
            with self.subTest(channel=channel):
                self.assertIn("initiate deletion in the app without email or staff approval", terms)
                if channel == "beta":
                    self.assertIn("14-calendar-day grace period", terms)
                else:
                    self.assertIn("schedule shown in the app", terms)
                    self.assertIn("During any available grace period", terms)
                self.assertIn("account remains usable", terms)
                self.assertIn("request can be cancelled until finalisation begins", terms)
                self.assertIn("Deletion does not cancel separately billed subscriptions or request a refund", terms)
                self.assertIn("applicable app store or payment provider", terms)
                self.assertNotIn("Apple handles refunds", terms)
                for statement in (
                    "supported account and activity records in a machine-readable format",
                    "Use Request my data in Account → Help & about → Contact support",
                    "Standard exports do not limit valid statutory requests",
                    "reasonably verify identity and authority",
                    "lawful redactions to protect others, security or other protected information",
                    "Requests for account deletion are processed according to the schedule shown in the app",
                    "During any available grace period",
                    "request can be cancelled until finalisation begins",
                    "Final deletion ends account access and removes associated live records",
                    "does not cancel separately billed subscriptions",
                    "providers retain independently under their own privacy policies and legal obligations",
                    "account help",
                    "for cancellation and purchase recovery arrangements",
                ):
                    self.assertIn(statement, privacy)
                self.assertIn("account remains usable", privacy)
                self.assertIn("31 days", privacy)
                self.assertIn("up to 30 days", privacy)
                self.assertIn("one month", privacy)
                self.assertIn("unclaimed allowances", terms)
                self.assertIn("Delivery and restoration require transaction and account verification", terms)
                self.assertIn("next UTC date", terms)
                self.assertIn("CHOI, Chong Hing", privacy)
                self.assertIn("Fasangartenstr 102, 81549 München", privacy)
                self.assertIn("privacy@versava.net", privacy)
                self.assertIn(
                    '<!--email_off--><a href="mailto:privacy@versava.net">privacy@versava.net</a><!--/email_off-->',
                    (output / f"{route}privacy/index.html").read_text(),
                )
                self.assertIn("Price comparisons and stated savings are illustrative", terms)
                self.assertIn("are not cash values, guaranteed personal savings", terms)
                for statement in (
                    "Virtual currency, including but not limited to Stars and Diamonds",
                    "Purchased virtual currency does not expire through ordinary use",
                    "Duplicate processing of the same operation does not create additional entitlements or justify additional charges",
                    "eligible covered dates are banked",
                    "ordinary cancellation or expiry do not forfeit them",
                    "claimable online through the associated account after expiry",
                    "Overlapping coverage does not duplicate allowances",
                    "future dates cannot be claimed early",
                    "currency does not expire merely because the subscription ends",
                    "Consumables, including stated bonuses, are delivered once",
                    "retries or restoration do not replenish spent items",
                    "Refunds remain subject to applicable law and provider procedures",
                    "spending virtual currency does not remove mandatory refund rights",
                    "unspent units reliably attributable", "do not create debt",
                    "or use unrelated balances, purchases, completed progress or owned unlocks for recovery",
                    "Uncertain attribution requires review rather than an automatic debit",
                ):
                    self.assertIn(statement, terms)
                if channel == "beta":
                    self.assertIn("Confirmed permanent content and day unlocks survive ordinary subscription expiry", terms)
                else:
                    self.assertIn("Confirmed permanent content access and other permanent unlocks survive ordinary subscription expiry", terms)
                for statement in (
                    "Cloudflare", "Apple", "Google", "legitimate interests",
                    "Account information", "Gameplay and activity",
                    "Purchase and advertising information", "related estimates",
                    "Technical and security information", "Communications and administration",
                    "Agreement and privacy records",
                    "We obtain personal data from you, your device, your use of the service and relevant providers",
                    "Examples within them include, but are not limited to",
                    "Providers include, but are not limited to",
                    "Non-personalised ads may still use identifiers or storage",
                    "measure and optimise advertising performance and verify rewards",
                    "We apply your advertising privacy choices before requesting ads",
                    "Refusing optional consent does not prevent free puzzle play",
                    "We use service activity and technical information to analyse, improve and personalise the service, including gameplay and benefits",
                    "This can include automated analysis",
                    "do not supply this activity history for third-party targeted advertising",
                    "Provider functions include hosting, storage, security, supported sign-in and payments, advertising, communications and request handling",
                    "applicable transfer requirements and safeguards",
                    "erasure, restriction, portability, objection and consent withdrawal",
                    "up to 31 days after final account deletion",
                    "restricted copies to 30 days from creation",
                    "requires later erasures to be reapplied before restoration",
                    "relevant data-protection regulator",
                    "restricted access and encrypted connections",
                ):
                    self.assertIn(statement, privacy)
                if channel == "beta":
                    self.assertIn("automatic first-party testing telemetry for all participating accounts", terms)
                    self.assertIn("without a separate in-app opt-out", terms)
                    statements = (
                        "First-party testing telemetry is enabled automatically for all participating Beta accounts",
                        "has no separate in-app opt-out",
                        "Processing requiring consent under applicable law or platform rules remains subject to that consent",
                        "supported account and activity records",
                        "Terms acceptance and Privacy acknowledgement do not supply that consent",
                        "Testing telemetry is required for Beta participation",
                        "Advertising permissions and applicable statutory privacy rights remain separate",
                        "this TestFlight collection cannot be disabled",
                        "Feedback and screenshots you submit are voluntary",
                        "do not share them with third parties",
                    )
                else:
                    statements = (
                        "This optional processing relies on your consent, separate from advertising consent",
                        "You can give or withdraw consent in Account → Help & about → Privacy",
                        "Withdrawing consent stops this optional processing in the app",
                        "An offline app request remains pending until successfully sent to our service",
                        "After withdrawal of personalisation consent, existing puzzles and progress may remain as service records",
                    )
                for statement in statements:
                    self.assertIn(statement, privacy)
                self.assertNotIn("There is currently no automatic account-deletion control", privacy)
                self.assertNotIn("GitHub", privacy)
                self.assertNotIn("erase provider-held records", privacy)
                self.assertIn('<a href="/support/">account help</a>', (output / f"{route}privacy/index.html").read_text())
        historical = normalized((output / "legal/2026-10-03-beta.11/privacy/index.html").read_text())
        self.assertIn("There is currently no automatic account-deletion control", historical)
        public_terms = normalized((output / "terms/index.html").read_text())
        self.assertIn("eligible covered dates are banked", public_terms)
        self.assertIn("combined prices require all specified currencies", public_terms)
        self.assertIn("Refunds remain subject to applicable law and provider procedures", public_terms)
        support = normalized((output / "support/index.html").read_text())
        self.assertIn("Request my data", support)
        self.assertIn("Account → Help &amp; about → Contact support → Delete account", support)
        self.assertIn("deletion is scheduled for 14 calendar days later", support)
        self.assertIn("account remains usable", support)
        self.assertIn("Stop deletion", support)
        self.assertIn("Account deletion does not cancel Apple subscription billing", support)
        self.assertIn("manage the subscription separately", support)
        self.assertNotIn("respond within one month", support)
        self.assertIn("Signing out or uninstalling does not cancel a scheduled deletion request", support)
        self.assertIn("New Plus diamond eligibility starts on the next UTC date", support)
        self.assertNotIn("Fasangartenstr 102, 81549 München", support)
        self.assertIn("privacy@versava.net", support)
        support_source = (output / "support/index.html").read_text()
        self.assertIn(
            '<!--email_off--><h2>Account and privacy requests</h2>',
            support_source,
        )
        self.assertIn('href="mailto:privacy@versava.net"', support_source)
        self.assertIn('href="/privacy/">Public Privacy Notice</a>', support_source)
        self.assertIn("Final deletion ends account access and removes balances, progress, unlocks and unclaimed rewards", support)
        self.assertIn("Deleted balances, progress, unlocks, consumables and unclaimed allowances are not restored", support)
        for internal_detail in (
            "private NAS", "internal privacy mailbox", "Preparation remains",
            "records requiring human review", "internal notes", "CHOI, Chong Hing",
        ):
            self.assertNotIn(internal_detail, support)

    def test_concise_current_editions_keep_rights_and_privacy_without_gameplay_spec(self):
        for edition, hashes in {
            "2026-10-06-beta.19": {
                "terms-beta.md": "e612aa8dfff65d0d195dbc3ff4cb49c4fe44e8610099e4202c5d2e7053ddac7a",
                "privacy-beta.md": "64639742303d19462280acb782e47d80478f6b99a7ab4c5547e5ec75f94272fc",
            },
            "2026-10-05-public.5": {
                "terms-public.md": "31b724e02743754904e43657bfd89bca3d6783a146f36abc1e72f734f39ec35f",
                "privacy-public.md": "b92bc052bf72ef27166bcef9ac0acc5cf541d7e2f87ee2e9f59fbdedc4110a19",
            },
        }.items():
            for name, checksum in hashes.items():
                self.assertEqual(hashlib.sha256((self.root / "legal" / edition / name).read_bytes()).hexdigest(), checksum)
        for channel, edition in (("beta", "2026-10-06-beta.20"), ("public", "2026-10-06-public.6")):
            folder = self.root / "legal" / edition
            terms = normalized((folder / f"terms-{channel}.md").read_text())
            privacy = normalized((folder / f"privacy-{channel}.md").read_text())
            with self.subTest(channel=channel):
                self.assertLess(len(terms.split()), 1600)
                self.assertLess(len(privacy.split()), 1800)
                for statement in (
                    "Versava Limited", "support@versava.net", "14-calendar-day grace period",
                    "Stop deletion", "Paid daily allowances are banked", "including after expiry",
                    "do not expire merely because Plus ends", "monthly, auto-renewable", "Purchased stars and diamonds do not expire",
                    "Apple handles refunds", "unspent units", "do not create automatic debt",
                    "mandatory", "A combined price requires both currencies",
                ):
                    self.assertIn(statement, terms)
                for removed in (
                    "30 stars", "one-star", "ten new diamonds", "seven consecutive",
                    "96 released packs", "120 fixed levels", "each later Hint costs",
                    "net.versava.", "original request protocol", "generator versions",
                ):
                    self.assertNotIn(removed, terms)
                for statement in (
                    "CHOI, Chong Hing", "Fasangartenstr 102, 81549 München", "privacy@versava.net",
                    "solved-board evidence", "before-and-after board or path state",
                    "signed verification or refund evidence", "Google", "Cloudflare", "GitHub",
                    "legitimate interests", "International processing", "at most 30 days",
                    "up to 31 days", "up to 30 days", "human review", "one month",
                    "erasure, restriction, portability", "complaint to the relevant regulator",
                    "not advertising consent",
                ):
                    self.assertIn(statement, privacy)
                self.assertNotIn("original request protocol", privacy)
                self.assertNotIn("canonical state hash", privacy)
                self.assertNotIn("30-star", privacy)
                self.assertNotIn("reached to the end", terms)
                self.assertNotIn("reached to the end", privacy)
        beta_terms = normalized((self.root / "legal/2026-10-06-beta.20/terms-beta.md").read_text())
        beta_privacy = normalized((self.root / "legal/2026-10-06-beta.20/privacy-beta.md").read_text())
        self.assertIn("Sandbox transactions do not charge real money", beta_terms)
        self.assertIn("Test records and access are not guaranteed to transfer", beta_terms)
        self.assertIn("testers cannot opt out", beta_privacy)
        self.assertIn("do not share those reports with third parties", beta_privacy)

    def test_request_email_edition_discloses_manual_private_link_and_preserves_old_notices(self):
        previous = {
            "2026-10-06-beta.20": {"terms-beta.md": "4955d9a44341531c91ff98355f5b94eb16f08a12be7353339d672c3a980b9d87", "privacy-beta.md": "0be4de6404485f8b7a1b12d66228fbb7779351b37cd6f3f792e52f7b9e3ee3dd"},
            "2026-10-06-public.6": {"terms-public.md": "a1eff5541097ea3d1c758301f315298b28c2e64bba9bccfcc83db0e6f4306aeb", "privacy-public.md": "cc4f1a0991e48e3554f892ea21a4fd5b5bc18fd8f70c0b1608d009782420e88a"},
            "2026-10-10-beta.21": {"terms-beta.md": "8bff92d3f975ac9ce49443009097c5848868b8cf3f37d6e30f5a6eab07314002", "privacy-beta.md": "a3379ff7eaaae5144cbdb2055c925d61e430f20d21160e7331bec17f2bf0223e"},
            "2026-10-10-public.7": {"terms-public.md": "2765d087b98ce4a9f20329b53a2fec2a764ea7d4a10d33d350f06b29941c0e2c", "privacy-public.md": "24b5a3fc32978dc9b7c4112a15925363016a8a08681d904c1367efa47d228db9"},
        }
        for edition, files in previous.items():
            for name, expected in files.items():
                self.assertEqual(hashlib.sha256((self.root / "legal" / edition / name).read_bytes()).hexdigest(), expected)
        self.assertEqual(self.edition, "2026-10-24-beta.26")
        self.assertEqual(self.current["publicEdition"], "2026-10-24-public.12")
        output = self.build()
        for route in ("privacy/index.html", "beta/privacy/index.html"):
            notice = normalized(" ".join(Page((output / route).read_text()).article))
            with self.subTest(route=route):
                statements = (
                    "Your rights and data requests",
                    "Standard exports do not limit valid statutory requests",
                    "reasonably verify identity and authority",
                    "lawful redactions to protect others, security or other protected information",
                    "privacy@versava.net or use available Account functions",
                    "Contact details supplied for a request are used to handle it, not for marketing or advertising",
                    "We may email a private download link",
                    "Prepared request copies are accessible for at most 30 days from preparation",
                    "ending earlier on final account deletion or a change to the recorded recipient or copy",
                    "excluded from routine backups",
                    "Service interruptions may delay physical removal after access expires",
                    "Keep links private",
                    "expiry or deletion cannot recall emails or copies already saved or shared elsewhere",
                    "we respond within one month or notify you within that period of a lawful extension",
                )
                for statement in statements:
                    self.assertIn(statement, notice)
                for removed in (
                    "verify it with a short-lived code", "to your verified address",
                    "The approved attachment copy uses the same expiry",
                ):
                    self.assertNotIn(removed, notice)
        for route in ("terms/index.html", "beta/terms/index.html"):
            terms = normalized(" ".join(Page((output / route).read_text()).article))
            with self.subTest(route=route):
                self.assertIn("Account-data requests may be made through available account functions", terms)
                self.assertIn("reasonable verification of the request and its recipient", terms)
                self.assertIn("Privacy Notice explains data handling, retention and request arrangements", terms)

    def test_current_privacy_retention_distinguishes_active_and_inactive_records(self):
        output = self.build()
        for route in ("privacy/index.html", "beta/privacy/index.html"):
            notice = normalized(" ".join(Page((output / route).read_text()).article))
            with self.subTest(route=route):
                for statement in (
                    "App activity histories use a rolling 30-day period",
                    "past interactions and outcomes, use a rolling 90-day period",
                    "Expired records on inactive devices are removed when the app next accesses them",
                    "activity summaries for up to 30 days after receipt",
                    "personalisation examples for up to 90 days from the interaction",
                    "received evaluation records for up to 90 days after receipt",
                    "On your device", "On our service",
                    "We retain shared analysis results only while needed for service operation or evaluation",
                    "Requests concerning personal data in shared analysis results or other retained records are handled under section",
                    "The retention period depends on completion of that purpose, applicable legal requirements and unresolved claims",
                ):
                    self.assertIn(statement, notice)
                deletion_heading = "7. Deletion and retention" if route.startswith("beta/") else "6. Deletion and retention"
                deletion_text = notice.split(deletion_heading, 1)[1]
                self.assertNotIn("existing puzzles and progress", deletion_text.lower())
                self.assertNotIn("Withdrawal, where available", notice)
                self.assertNotIn("not automatically erased", notice)
                self.assertNotIn("They are reviewed when", notice)
                self.assertNotIn("Derived insights are retained as needed", notice)
                request_section = 6 if route.startswith("beta/") else 5
                self.assertIn(f"shared analysis results or other retained records are handled under section {request_section}", notice)
                self.assertNotRegex(notice.lower(), r"(?:anonymous|anonymised) (?:shared |analysis )?(?:results|insights)")

    def test_retained_beta_23_and_beta_22_keep_their_published_source_bytes(self):
        expected = {
            "2026-10-14-beta.23": {
                "terms-beta.md": "51293d48a8caea613e66a1f02507a496044e1aa1a9cec57b1f84f57d465db5a7",
                "privacy-beta.md": "75cffa3fbf955d4c950d7dcbd9b8895ba45e67d228b0ba3a980946bdbe3fc618",
            },
            "2026-10-10-beta.22": {
                "terms-beta.md": "311ad4df9b19960564d9a3508ad6ec3c577c98f1c6e43d12a04f249a8ab03394",
                "privacy-beta.md": "edff7b3443fa209c577347d5feca6517c970217bbc48d5c53c88406cfab9b0c4",
            },
        }
        output = self.build()
        for edition, files in expected.items():
            for name, expected_hash in files.items():
                with self.subTest(edition=edition, name=name):
                    raw = (self.root / "legal" / edition / name).read_bytes()
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), expected_hash)
                    self.assertEqual((output / "legal" / edition / name).read_bytes(), raw)

    def test_all_internal_routes_assets_and_section_links_resolve_without_scripts(self):
        output = self.build()
        update_urls = {load_client_release(self.root / source)["ios"]["updateUrl"] for source in ("client-release.json", "internal/client-release.json")}
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
                            if uri.netloc != "puzzle.versava.net":
                                self.assertEqual(path.relative_to(output).as_posix(), "versions/index.html")
                                self.assertIn(target, update_urls)
                        continue
                    self.assertFalse(uri.netloc)
                    if uri.path:
                        resolved = output / uri.path.lstrip("/")
                        if uri.path.endswith("/"):
                            resolved /= "index.html"
                        self.assertTrue(resolved.is_file(), target)
                    if uri.fragment:
                        self.assertIn(uri.fragment, page.ids)

    def version_sections(self, source):
        beta_marker = '<section class="support-section" aria-labelledby="beta-versions">'
        release_marker = '<section class="support-section" aria-labelledby="release-versions">'
        self.assertEqual(source.count(beta_marker), 1)
        self.assertEqual(source.count(release_marker), 1)
        beta, release = source.split(beta_marker, 1)[1].split(release_marker, 1)
        self.assertIn('<h2 id="beta-versions">Beta</h2>', beta)
        self.assertIn('<h2 id="release-versions">Release</h2>', release)
        return beta, release.split('</main>', 1)[0]

    def assert_no_testflight_invitation(self, source):
        self.assertNotIn("Open TestFlight", source)
        self.assertNotIn("testflight.apple.com", source)
        self.assertFalse(any(urlsplit(target).netloc == "testflight.apple.com" for target in Page(source).targets))

    def test_current_versions_groups_matching_beta_policies_and_marks_release_not_released(self):
        policy_bytes = {name: (self.root / name).read_bytes() for name in ("client-support.json", "internal/client-support.json")}
        output = self.build()
        policy = load_client_support(self.root / "client-support.json")
        source = (output / "versions/index.html").read_text()
        beta, release = self.version_sections(source)
        self.assertEqual(beta.count('<h3>Current app policy</h3>'), 1)
        self.assertEqual(source.count('class="contact-card version-card"'), 1)
        self.assertIn("TestFlight Beta", beta)
        self.assertIn("Beta access is by invitation only", beta)
        self.assertIn(f'Latest supported</dt><dd>{policy["ios"]["latestVersion"]} · Build {policy["ios"]["latestBuild"]}', beta)
        self.assertIn(f'Minimum version</dt><dd>{policy["ios"]["minimumVersion"]} · Build {policy["ios"]["minimumBuild"]}', beta)
        self.assertIn(f'Policy revision {policy["revision"]}', beta)
        self.assertIn("No Android version is listed", beta)
        self.assertIn("Not released yet", release)
        self.assertNotIn("Build ", release)
        self.assertNotIn("1.0.0", release)
        self.assert_no_testflight_invitation(source)
        for target in ("/client-support.json", "/internal/client-support.json"):
            self.assertEqual(Page(source).targets.count(target), 1)
        for name, expected in policy_bytes.items():
            self.assertEqual((self.root / name).read_bytes(), expected)
            self.assertEqual((output / name).read_bytes(), expected)
        self.assertIn("/versions/", Page((output / "beta/index.html").read_text()).targets)
        for route in ("index.html", "404.html", "support/index.html", "terms/index.html", "privacy/index.html"):
            targets = Page((output / route).read_text()).targets
            self.assertNotIn("/versions/", targets)
            self.assertNotIn("/legal/", targets)

    def test_current_versions_follows_policy_changes_without_hardcoded_build_numbers(self):
        policy = load_client_support(self.root / "client-support.json")
        policy["revision"] += 1
        policy["ios"].update(latestVersion="0.2.0", latestBuild=50, minimumVersion="0.1.0", minimumBuild=36)
        for source in ("client-support.json", "internal/client-support.json"):
            (self.root / source).write_text(json.dumps(policy))
        output = self.build()
        text = normalized((output / "versions/index.html").read_text())
        self.assertIn("Latest supported</dt><dd>0.2.0 · Build 50", text)
        self.assertIn("Minimum version</dt><dd>0.1.0 · Build 36", text)
        self.assertIn(f'Policy revision {policy["revision"]}', text)

    def test_current_versions_keeps_distinct_app_store_and_testflight_policies_separate(self):
        beta_policy = load_client_support(self.root / "client-support.json")
        release_policy = json.loads(json.dumps(beta_policy))
        release_policy["revision"] += 1
        release_policy["ios"].update(latestVersion="1.0.0", latestBuild=50, minimumVersion="1.0.0", minimumBuild=50,
                             updateUrl="https://apps.apple.com/app/id6817787046")
        for release_path, beta_path in (("client-support.json", "internal/client-support.json"),
                                        ("internal/client-support.json", "client-support.json")):
            with self.subTest(release_policy=release_path):
                (self.root / release_path).write_text(json.dumps(release_policy))
                (self.root / beta_path).write_text(json.dumps(beta_policy))
                source = (self.build() / "versions/index.html").read_text()
                beta, release = self.version_sections(source)
                self.assertEqual(source.count('class="contact-card version-card"'), 2)
                self.assertIn("TestFlight Beta", beta)
                self.assertIn("Beta access is by invitation only", beta)
                self.assertNotIn("1.0.0 · Build 50", beta)
                self.assertIn("App Store update policy", release)
                self.assertIn("1.0.0 · Build 50", release)
                self.assertNotIn("TestFlight Beta", release)
                self.assertNotIn("Not released yet", release)
                self.assertIn(release_policy["ios"]["updateUrl"], Page(release).targets)
                self.assertEqual(Page(beta).targets, ["/" + beta_path])
                self.assertIn("/" + release_path, Page(release).targets)
                self.assert_no_testflight_invitation(source)

    def test_current_versions_groups_matching_app_store_policies_and_keeps_empty_beta_section(self):
        policy = load_client_support(self.root / "client-support.json")
        policy["ios"].update(latestVersion="1.0.0", latestBuild=50, minimumVersion="1.0.0", minimumBuild=50,
                             updateUrl="https://apps.apple.com/app/id6817787046")
        for name in ("client-support.json", "internal/client-support.json"):
            (self.root / name).write_text(json.dumps(policy))
        source = (self.build() / "versions/index.html").read_text()
        beta, release = self.version_sections(source)
        self.assertIn("No Beta version is listed", beta)
        self.assertIn("Beta access is by invitation only", beta)
        self.assertNotIn("Build ", beta)
        self.assertEqual(release.count('<h3>Current app policy</h3>'), 1)
        self.assertEqual(source.count('class="contact-card version-card"'), 1)
        self.assertIn("1.0.0 · Build 50", release)
        self.assertNotIn("Not released yet", release)
        self.assertEqual(Page(release).targets, [policy["ios"]["updateUrl"], "/client-support.json", "/internal/client-support.json"])
        self.assert_no_testflight_invitation(source)

    def test_current_versions_preserves_distinct_policies_within_the_same_channel(self):
        for channel, url in (("beta", "https://testflight.apple.com/join/CCCawA1Q"),
                             ("release", "https://apps.apple.com/app/id6817787046")):
            with self.subTest(channel=channel):
                for name, version, build in (("client-support.json", "0.2.0", 50),
                                             ("internal/client-support.json", "0.3.0", 51)):
                    policy = load_client_support(self.root / name)
                    policy["revision"] = build
                    policy["ios"].update(latestVersion=version, latestBuild=build, updateUrl=url)
                    (self.root / name).write_text(json.dumps(policy))
                source = (self.build() / "versions/index.html").read_text()
                beta, release = self.version_sections(source)
                populated, empty = (beta, release) if channel == "beta" else (release, beta)
                self.assertEqual(populated.count('class="contact-card version-card"'), 2)
                self.assertNotIn('class="contact-card version-card"', empty)
                for label in ("App policy", "Internal app policy"):
                    self.assertEqual(populated.count(f'<h3>{label}</h3>'), 1)
                for version, build in (("0.2.0", 50), ("0.3.0", 51)):
                    self.assertEqual(populated.count(f'Latest supported</dt><dd>{version} · Build {build}'), 1)
                    self.assertIn(f'Policy revision {build}', populated)
                for target in ("/client-support.json", "/internal/client-support.json"):
                    self.assertEqual(Page(populated).targets.count(target), 1)
                self.assert_no_testflight_invitation(source)

    def test_modern_latest_does_not_change_legacy_mandatory_policy(self):
        legacy_before = {name: (self.root / name).read_bytes()
                         for name in ("client-release.json", "internal/client-release.json")}
        policy = load_client_support(self.root / "client-support.json")
        policy["revision"] += 1
        policy["ios"]["latestBuild"] += 1
        for name in ("client-support.json", "internal/client-support.json"):
            (self.root / name).write_text(json.dumps(policy))
        output = self.build()
        source = (output / "versions/index.html").read_text()
        self.assertIn(f'Latest supported</dt><dd>0.1.0 · Build {policy["ios"]["latestBuild"]}', source)
        self.assertIn("latest available update before continuing", source)
        for name, raw in legacy_before.items():
            self.assertEqual((output / name).read_bytes(), raw)

    def test_versions_explains_minimum_blocked_range_and_optional_public_updates(self):
        policy = load_client_support(self.root / "client-support.json")
        policy["ios"].update(latestVersion="1.1.0", latestBuild=55,
                             minimumVersion="1.0.0", minimumBuild=39,
                             updateUrl="https://apps.apple.com/app/id6817787046", updatePolicy="optional",
                             blockedRanges=[{"fromVersion": "1.0.0", "fromBuild": 40,
                                             "throughVersion": "1.0.0", "throughBuild": 42,
                                             "reason": "security"}])
        (self.root / "client-support.json").write_text(json.dumps(policy))
        source = (self.build() / "versions/index.html").read_text()
        beta, release = self.version_sections(source)
        self.assertIn("latest available update before continuing", beta)
        self.assertIn("Compatible updates remain optional, with a reminder after 14 days", release)
        self.assertIn("Minimum version</dt><dd>1.0.0 · Build 39", release)
        self.assertIn("1.0.0 · Build 40 through 1.0.0 · Build 42, inclusive", release)
        self.assertIn("Security issue. Upgrade required.", release)
        self.assertIn("required immediately below the minimum supported version", source)
        self.assert_no_testflight_invitation(source)

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
