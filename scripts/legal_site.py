"""Render public Alpha documents from checksummed, retained Markdown editions."""

import hashlib
import html
import json
from pathlib import Path
import re


EDITION = re.compile(r"[a-z0-9][a-z0-9.-]{0,63}")
FILES = {"terms": "terms-alpha.md", "privacy": "privacy-alpha.md"}
HOST = "https://puzzle.versava.net"


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_object)


def load_editions(root):
    legal = root / "legal"
    current = read_json(legal / "current.json")
    if set(current) != {"schemaVersion", "alphaEdition"} or type(current["schemaVersion"]) is not int or current["schemaVersion"] != 1:
        raise ValueError("Invalid current legal edition metadata")
    if not isinstance(current["alphaEdition"], str) or not EDITION.fullmatch(current["alphaEdition"]):
        raise ValueError("Invalid Alpha edition identifier")
    editions = {}
    for folder in sorted(legal.iterdir()):
        if not folder.is_dir():
            continue
        if folder.is_symlink() or not EDITION.fullmatch(folder.name):
            raise ValueError("Invalid legal edition directory")
        manifest = read_json(folder / "manifest.json")
        if set(manifest) != {"schemaVersion", "edition", "channel", "documents"} or type(manifest["schemaVersion"]) is not int or manifest["schemaVersion"] != 1 or manifest["edition"] != folder.name or manifest["channel"] != "alpha":
            raise ValueError(f"Invalid legal manifest: {folder.name}")
        if not isinstance(manifest["documents"], dict) or set(manifest["documents"]) != set(FILES):
            raise ValueError("Both Alpha documents are required")
        texts = {}
        for kind, filename in FILES.items():
            entry = manifest["documents"][kind]
            if not isinstance(entry, dict) or set(entry) != {"file", "sha256"} or entry["file"] != filename or not isinstance(entry["sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", entry["sha256"]):
                raise ValueError(f"Invalid legal source entry: {kind}")
            source = folder / filename
            if source.is_symlink():
                raise ValueError("Legal sources must not be symlinks")
            data = source.read_bytes()
            if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise ValueError(f"Frozen legal source changed: {folder.name}/{filename}")
            text = data.decode("utf-8")
            if not re.search(rf"^Version: {re.escape(folder.name)} · Updated: .+$", text, re.M):
                raise ValueError("Legal source edition does not match its manifest")
            texts[kind] = text
        editions[folder.name] = (manifest, texts)
    if current["alphaEdition"] not in editions:
        raise ValueError("Current Alpha edition is missing")
    return current["alphaEdition"], editions


def render_document(text):
    """Preserve the document's words; escape all source markup as plain text."""
    output, sections, paragraph = [], [], []
    seen = set()
    in_list = False

    def inline(value):
        escaped = html.escape(value)
        return escaped.replace("support@versava.net", '<a href="mailto:support@versava.net">support@versava.net</a>')

    def flush():
        if paragraph:
            value = " ".join(paragraph)
            css = ' class="version"' if value.startswith("Version:") else ""
            output.append(f"<p{css}>{inline(value)}</p>")
            paragraph.clear()

    for line in text.splitlines():
        if not line.strip():
            flush()
            if in_list:
                output.append("</ul>")
                in_list = False
            continue
        heading = re.fullmatch(r"(#{1,3}) (.+)", line)
        if heading:
            flush()
            if in_list:
                output.append("</ul>")
                in_list = False
            level, title = len(heading[1]), heading[2]
            anchor = "section-" + re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            while anchor in seen:
                anchor += "-next"
            seen.add(anchor)
            output.append(f'<h{level} id="{anchor}">{inline(title)}</h{level}>')
            if level == 2:
                sections.append((anchor, title))
        elif line.startswith("- "):
            flush()
            if not in_list:
                output.append("<ul>")
                in_list = True
            output.append(f"<li>{inline(line[2:])}</li>")
        else:
            if in_list:
                output.append("</ul>")
                in_list = False
            paragraph.append(line.strip())
    flush()
    if in_list:
        output.append("</ul>")
    return "\n".join(output), sections


def _navigation(sections):
    return '<nav aria-label="Document sections">' + "".join(f'<a href="#{anchor}">{html.escape(title)}</a>' for anchor, title in sections) + "</nav>"


def render_pages(root, current, editions):
    home = (root / "index.html").read_text(encoding="utf-8")
    header = re.search(r'<header class="site-header">.*?</header>', home, re.S)
    footer = re.search(r'<footer class="site-footer">.*?</footer>', home, re.S)
    if not header or not footer:
        raise ValueError("Homepage shared navigation is missing")
    pages = {}

    def page(title, body, path, active=None, alpha=False):
        navigation = header[0]
        if active:
            navigation = navigation.replace(f'href="{active}"', f'href="{active}" aria-current="page"')
        robots = '<meta name="robots" content="noindex, follow">' if alpha else ""
        return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} | Daily Pause</title><meta name="description" content="{html.escape(title)} for Daily Pause by Versava Limited.">{robots}
<link rel="canonical" href="{HOST}{path}"><link rel="icon" href="/brand.svg" type="image/svg+xml"><link rel="stylesheet" href="/styles.css"></head>
<body><a class="skip-link" href="#main">Skip to content</a>{navigation}{body}{footer[0]}</body></html>
'''

    def add(path, content):
        pages[path.lstrip("/") + "index.html"] = content

    for edition, (manifest, texts) in editions.items():
        for kind, text in texts.items():
            article, sections = render_document(text)
            title = text.splitlines()[0].removeprefix("# ")
            permanent = f"/legal/{edition}/{kind}/"
            nav = _navigation(sections)
            body = f'''<main id="main" class="document-page page-width">
<p class="breadcrumb"><a href="/">Daily Pause</a> / Alpha documents</p>
<details class="mobile-contents"><summary>On this page</summary>{nav}</details>
<div class="document-layout"><aside class="contents"><p class="contents-label">On this page</p>{nav}</aside>
<div><p class="document-status">For invited alpha testing. <a href="{permanent}">Permanent link to this edition</a>.</p>
<article class="document" data-policy-document="{kind}" aria-label="{html.escape(title)}">{article}</article>
<div class="document-end"><a href="/support/">Contact support</a><a href="/legal/{edition}/{FILES[kind]}">Save the original text</a><a href="/legal/">Document editions</a><a href="#main">Back to top</a></div>
</div></div></main>'''
            add(permanent, page(title, body, permanent, alpha=True))
            if edition == current:
                canonical = f"/alpha/{kind}/"
                for path in (canonical, f"/{kind}/"):
                    add(path, page(title, body, canonical, active=canonical, alpha=True))
        edition_body = f'''<main id="main" class="support-page page-width"><p class="eyebrow">Alpha document edition</p><h1>{html.escape(edition)}</h1>
<p class="support-intro">The retained Terms and Privacy Notice for this edition.</p><ul class="edition-list">
<li><a href="/legal/{edition}/terms/">Alpha Testing Terms</a></li><li><a href="/legal/{edition}/privacy/">Alpha Privacy Notice</a></li>
<li><a href="/legal/{edition}/manifest.json">Source checksums</a></li></ul><p><a href="/legal/">All editions</a></p></main>'''
        add(f"/legal/{edition}/", page("Alpha document edition", edition_body, f"/legal/{edition}/", alpha=True))
    history = "".join(f'<li><a href="/legal/{edition}/">{html.escape(edition)}</a></li>' for edition in reversed(editions))
    add("/legal/", page("Document editions", f'<main id="main" class="support-page page-width"><p class="eyebrow">Daily Pause</p><h1>Document editions</h1><p class="support-intro">Published alpha editions, retained for reference.</p><ul class="edition-list">{history}</ul></main>', "/legal/", alpha=True))
    support = '''<main id="main" class="support-page page-width"><p class="eyebrow">Daily Pause help</p><h1>Here to help.</h1>
<p class="support-intro">Questions about a puzzle, your account, or your privacy? Contact Versava.</p>
<section class="contact-card"><h2>Email support</h2><a class="contact-email" href="mailto:support@versava.net?subject=Daily%20Pause%20support">support@versava.net</a>
<p>For an alpha-build issue, include the app version, what happened and whether you were playing as a guest or using an Apple-linked account.</p></section>
<section class="support-section"><h2>Reporting a problem</h2><p>Tell us what you expected and what happened. Screenshots can help; remove unrelated personal information. Do not include passwords, access tokens or payment-card details.</p></section>
<section class="support-section"><h2>Account and privacy requests</h2><p>Use the same email for access, correction or deletion requests. We may need information to verify account ownership. Signing out, removing the app or leaving TestFlight does not itself delete server-held account records.</p><p><a href="/alpha/privacy/">Read the Alpha Privacy Notice</a></p></section>
<section class="support-section"><h2>Invited alpha testing</h2><p>Daily Pause is currently tested on iPhone through TestFlight. Real purchases and publisher ads are disabled in the current build.</p><p><a href="/alpha/terms/">Alpha Testing Terms</a> · <a href="/alpha/privacy/">Alpha Privacy Notice</a></p></section>
<section class="support-section"><h2>Operator</h2><address>Versava Limited<br>Unit 1319, 13/F, One Midtown<br>11 Hoi Shing Road, Tsuen Wan<br>Hong Kong</address></section></main>'''
    add("/support/", page("Support", support, "/support/", active="/support/"))
    return pages


def build_legal_site(root, output):
    current, editions = load_editions(root)
    generated = render_pages(root, current, editions)
    for relative, content in generated.items():
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
    sources = ["legal/current.json"]
    for edition in editions:
        sources.extend(f"legal/{edition}/{name}" for name in (*FILES.values(), "manifest.json"))
    for relative in sources:
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((root / relative).read_bytes())
    return sorted([*generated, *sources])
