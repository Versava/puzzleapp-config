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

    def test_unreviewed_source_files_are_not_published(self):
        (self.root / "unreviewed-internal.txt").write_text("Not website content.")
        (self.root / "legal" / self.edition / "unreviewed-internal.txt").write_text("Not a policy.")
        output = self.build()
        actual = {str(path.relative_to(output)) for path in output.rglob("*") if path.is_file()}
        expected = {
            "manifest.json", "manifest.schema.json", "client-release.json", "index.html", "404.html",
            "_headers", "styles.css", "brand.svg", "legal/current.json",
            "internal/manifest.json", "internal/client-release.json",
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
