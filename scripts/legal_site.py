"""Render public and testing documents from checksummed, retained Markdown editions."""

import hashlib
import html
import json
from pathlib import Path
import re


EDITION = re.compile(r"[a-z0-9][a-z0-9.-]{0,63}")
CHANNELS = ("alpha", "beta", "public")
FILES = {channel: {kind: f"{kind}-{channel}.md" for kind in ("terms", "privacy")} for channel in CHANNELS}
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
    if set(current) != {"schemaVersion", *(f"{channel}Edition" for channel in CHANNELS)} or type(current["schemaVersion"]) is not int or current["schemaVersion"] != 2:
        raise ValueError("Invalid current legal edition metadata")
    for channel in CHANNELS:
        value = current[f"{channel}Edition"]
        if not isinstance(value, str) or not EDITION.fullmatch(value):
            raise ValueError(f"Invalid {channel} edition identifier")
    editions = {}
    for folder in sorted(legal.iterdir()):
        if not folder.is_dir():
            continue
        if folder.is_symlink() or not EDITION.fullmatch(folder.name):
            raise ValueError("Invalid legal edition directory")
        manifest = read_json(folder / "manifest.json")
        if set(manifest) != {"schemaVersion", "edition", "channel", "documents"} or type(manifest["schemaVersion"]) is not int or manifest["schemaVersion"] != 1 or manifest["edition"] != folder.name or manifest["channel"] not in CHANNELS:
            raise ValueError(f"Invalid legal manifest: {folder.name}")
        channel = manifest["channel"]
        if f"-{channel}." not in folder.name:
            raise ValueError("Legal edition does not match its channel")
        if not isinstance(manifest["documents"], dict) or set(manifest["documents"]) != set(FILES[channel]):
            raise ValueError("Both Terms and Privacy documents are required")
        texts = {}
        for kind, filename in FILES[channel].items():
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
    for channel in CHANNELS:
        edition = current[f"{channel}Edition"]
        if edition not in editions or editions[edition][0]["channel"] != channel:
            raise ValueError(f"Current {channel} edition is missing or uses another channel")
    return current, editions


def render_document(text):
    """Preserve the document's words; escape all source markup as plain text."""
    output, sections, paragraph = [], [], []
    seen = set()
    in_list = False

    def inline(value):
        escaped = html.escape(value)
        return escaped.replace("support@versava.net", '<!--email_off--><a href="mailto:support@versava.net">support@versava.net</a><!--/email_off-->')

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

    def page(title, body, path, active=None, testing=False):
        navigation = header[0]
        if active:
            navigation = navigation.replace(f'href="{active}"', f'href="{active}" aria-current="page"')
        robots = '<meta name="robots" content="noindex, follow">' if testing else ""
        return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} | Daily Pause</title><meta name="description" content="{html.escape(title)} for Daily Pause by Versava Limited.">{robots}
<link rel="canonical" href="{HOST}{path}"><link rel="icon" href="/brand.svg" type="image/svg+xml"><link rel="stylesheet" href="/styles.css"></head>
<body><a class="skip-link" href="#main">Skip to content</a>{navigation}{body}{footer[0]}</body></html>
'''

    def add(path, content):
        pages[path.lstrip("/") + "index.html"] = content

    for edition, (manifest, texts) in editions.items():
        channel = manifest["channel"]
        label = "Public" if channel == "public" else channel.title()
        testing = channel != "public"
        historical = channel == "alpha"
        context = ("Historical Alpha testing documents." if historical else
                   "For invited Beta testing." if testing else "Public app and website documents.")
        for kind, text in texts.items():
            article, sections = render_document(text)
            title = text.splitlines()[0].removeprefix("# ")
            permanent = f"/legal/{edition}/{kind}/"
            nav = _navigation(sections)
            body = f'''<main id="main" class="document-page page-width">
<p class="breadcrumb"><a href="/">Daily Pause</a> / {label} documents</p>
<details class="mobile-contents"><summary>On this page</summary>{nav}</details>
<div class="document-layout"><aside class="contents"><p class="contents-label">On this page</p>{nav}</aside>
<div><p class="document-status">{context} <a href="{permanent}">Permanent link to this edition</a>.</p>
<article class="document" data-policy-document="{kind}" data-policy-channel="{channel}" aria-label="{html.escape(title)}">{article}</article>
<div class="document-end"><a href="/support/">Contact support</a><a href="/legal/{edition}/{FILES[channel][kind]}">Save the original text</a><a href="/legal/">Document editions</a><a href="#main">Back to top</a></div>
</div></div></main>'''
            add(permanent, page(title, body, permanent, testing=testing))
            if edition == current[f"{channel}Edition"]:
                canonical = f"/{kind}/" if channel == "public" else f"/{channel}/{kind}/"
                add(canonical, page(title, body, canonical, active=canonical, testing=testing))
        edition_body = f'''<main id="main" class="support-page page-width"><p class="eyebrow">{label} document edition</p><h1>{html.escape(edition)}</h1>
<p class="support-intro">The retained Terms and Privacy Notice for this edition.</p><ul class="edition-list">
<li><a href="/legal/{edition}/terms/">{html.escape(texts["terms"].splitlines()[0].removeprefix("# "))}</a></li>
<li><a href="/legal/{edition}/privacy/">{html.escape(texts["privacy"].splitlines()[0].removeprefix("# "))}</a></li>
<li><a href="/legal/{edition}/manifest.json">Source checksums</a></li></ul><p><a href="/legal/">All editions</a></p></main>'''
        add(f"/legal/{edition}/", page(f"{label} document edition", edition_body, f"/legal/{edition}/", testing=testing))
    history = "".join(f'<li><a href="/legal/{edition}/">{html.escape(edition)}</a> · {editions[edition][0]["channel"].title()}</li>' for edition in reversed(editions))
    add("/legal/", page("Document editions", f'<main id="main" class="support-page page-width"><p class="eyebrow">Daily Pause</p><h1>Document editions</h1><p class="support-intro">Public and testing editions, retained for reference.</p><ul class="edition-list">{history}</ul></main>', "/legal/", testing=True))
    beta = '''<main id="main" class="support-page page-width"><p class="eyebrow">Invited testing</p><h1>Daily Pause Beta</h1>
<p class="support-intro">Daily Pause is currently tested on iPhone through TestFlight. Read the documents for that testing programme.</p>
<ul class="edition-list"><li><a href="/beta/terms/">Beta Testing Terms</a></li><li><a href="/beta/privacy/">Beta Privacy Notice</a></li></ul>
<p>Production paid purchases, subscriptions and publisher ads remain disabled. Designated TestFlight builds may test monthly Daily Pause Plus subscriptions, supported star and diamond consumables, and the one-time Remove Ads product in Apple's Sandbox without real charges when testing controls permit it. The revised Plus product banks two diamonds per eligible paid UTC day, including missed days that can be claimed after cancellation or expiry. Active verified Plus also covers eligible reward benefits directly: the capped daily star bonus, selected supported Past-day unlocks, and hints two and three. These direct benefits require active coverage; banked paid diamonds remain separate. It does not include all-pack access or automatic-ad removal; verified legacy all-packs rights remain separate. Individual cash-pack checkout is disabled, including its purchase tests. Production Remove Ads checkout remains disabled. Labelled Google sample videos do not grant stars, past-day access or paid hints.</p>
<p>Read and accept the testing Terms and acknowledge the Privacy Notice inside the app before starting. Visiting this site does not accept them or enrol you in testing.</p>
<p><a href="/terms/">Public Terms of Use</a> · <a href="/privacy/">Public Privacy Notice</a> · <a href="/support/">Support</a></p></main>'''
    add("/beta/", page("Beta testing", beta, "/beta/", active="/beta/", testing=True))
    support = '''<main id="main" class="support-page page-width"><p class="eyebrow">Daily Pause help</p><h1>Here to help.</h1>
<p class="support-intro">Questions about a puzzle, your account, or your privacy? Contact Versava.</p>
<section class="contact-card"><h2>Email support</h2><!--email_off--><a class="contact-email" href="mailto:support@versava.net?subject=Daily%20Pause%20support">support@versava.net</a><!--/email_off-->
<p>For an app issue, include the app version, what happened and whether you were playing as a guest or using an Apple-linked account.</p></section>
<section class="support-section"><h2>Reporting a problem</h2><p>Tell us what you expected and what happened. Screenshots can help; remove unrelated personal information. Do not include passwords, access tokens or payment-card details.</p></section>
<section class="support-section"><h2>Account and privacy requests</h2><p>Use the same email for access, correction or deletion requests. We may need information to verify account ownership. Signing out, removing the app or leaving TestFlight does not itself delete server-held account records.</p><p><a href="/privacy/">Public Privacy Notice</a> · <a href="/beta/privacy/">Beta Privacy Notice</a></p></section>
<section class="support-section"><h2>Invited Beta testing</h2><p>Daily Pause is currently tested on iPhone through TestFlight. Production paid purchases, subscriptions and publisher ads remain disabled. Designated TestFlight builds may test monthly Daily Pause Plus subscriptions, supported star and diamond consumables, and the one-time Remove Ads product in Apple's Sandbox without real charges when testing controls permit it. Individual cash-pack checkout is disabled, including its purchase tests. Production Remove Ads checkout remains disabled. Designated Beta builds can show labelled Google sample ads, which do not grant paid hints.</p><p><a href="/beta/terms/">Beta Testing Terms</a> · <a href="/beta/privacy/">Beta Privacy Notice</a></p></section>
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
    for edition, (manifest, _) in editions.items():
        sources.extend(f"legal/{edition}/{name}" for name in (*FILES[manifest["channel"]].values(), "manifest.json"))
    for relative in sources:
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((root / relative).read_bytes())
    return sorted([*generated, *sources])
