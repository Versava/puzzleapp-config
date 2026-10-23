from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from legal_site import render_document


class LinkContent(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.links = []
        self.text = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.append(dict(attrs)["href"])

    def handle_data(self, value):
        self.text.append(value)


class LegalHelpLinkTests(unittest.TestCase):
    def test_exact_account_help_link_uses_label_and_public_support_route(self):
        rendered, _ = render_document(
            "See [account help](https://puzzle.versava.net/support/) for instructions."
        )
        page = LinkContent(rendered)
        self.assertEqual(page.links, ["/support/"])
        self.assertEqual("".join(page.text), "See account help for instructions.")

    def test_other_markdown_and_source_html_stay_inert_text(self):
        source = (
            '[account help](javascript:alert(1)) '
            '[account help](https://example.com/support/) '
            '<a href="javascript:alert(1)">unsafe</a>'
        )
        rendered, _ = render_document(source)
        page = LinkContent(rendered)
        self.assertEqual(page.links, [])
        self.assertEqual("".join(page.text), source)
        self.assertIn('&lt;a href=&quot;javascript:alert(1)&quot;&gt;', rendered)

    def test_existing_contact_links_still_render_without_nested_anchors(self):
        rendered, _ = render_document(
            "support@versava.net privacy@versava.net "
            "https://puzzle.versava.net/support/ "
            "[account help](https://puzzle.versava.net/support/)"
        )
        page = LinkContent(rendered)
        self.assertEqual(page.links, [
            "mailto:support@versava.net", "mailto:privacy@versava.net",
            "/support/", "/support/",
        ])
        self.assertNotIn('<a href="/support/"><a', rendered)


if __name__ == "__main__":
    unittest.main()
