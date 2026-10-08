"""Render public and testing documents from checksummed, retained Markdown editions."""

import hashlib
import html
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from validate_client_release import load as load_client_release


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
        for address in ("support@versava.net", "privacy@versava.net"):
            escaped = escaped.replace(address, f'<!--email_off--><a href="mailto:{address}">{address}</a><!--/email_off-->')
        return escaped

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
<ul class="edition-list"><li><a href="/beta/terms/">Beta Testing Terms</a></li><li><a href="/beta/privacy/">Beta Privacy Notice</a></li><li><a href="/versions/">Current app versions</a></li></ul>
<p>Production paid purchases and subscriptions remain disabled. Designated TestFlight builds may display publisher banners and offer optional rewarded videos when separate advertising controls and privacy choices permit it. Publisher ad requests are non-personalised and use Google’s applicable consent and refusal flow; Ad privacy options is available where required. Verified ad-funded grants need an account-bound ticket and Google’s signed completion callback. Designated TestFlight builds may test monthly Daily Pause Plus subscriptions, supported star and diamond consumables, and the one-time Remove Ads product in Apple's Sandbox without real charges when testing controls permit it. The revised Plus product banks two diamonds per eligible paid UTC day, including missed days that can be claimed after cancellation or expiry. Active verified Plus also covers eligible reward benefits directly: the capped daily star bonus, selected supported Past-day unlocks, and hints two and three. These direct benefits require active coverage; banked paid diamonds remain separate. It does not include all-pack access or automatic-ad removal; verified legacy all-packs rights remain separate. Individual cash-pack checkout is disabled, including its purchase tests. Production Remove Ads checkout remains disabled. Labelled Google sample videos do not grant stars, past-day access or paid hints.</p>
<p>Read and accept the testing Terms and acknowledge the Privacy Notice inside the app before starting. Visiting this site does not accept them or enrol you in testing.</p>
<p><a href="/terms/">Public Terms of Use</a> · <a href="/privacy/">Public Privacy Notice</a> · <a href="/support/">Support</a></p></main>'''
    add("/beta/", page("Beta testing", beta, "/beta/", active="/beta/", testing=True))
    support = '''<main id="main" class="support-page page-width"><p class="eyebrow">Daily Pause help</p><h1>Here to help.</h1>
<p class="support-intro">Questions about a puzzle, your account, or your privacy? Contact Versava.</p>
<section class="contact-card"><h2>Email support</h2><!--email_off--><a class="contact-email" href="mailto:support@versava.net?subject=Daily%20Pause%20support">support@versava.net</a><!--/email_off-->
<p>For an app issue, include the app version, what happened and whether you were playing as a guest or using an Apple-linked account. <a href="/versions/">Check the current supported versions</a>.</p></section>
<section class="support-section"><h2>Reporting a problem</h2><p>Tell us what you expected and what happened. Screenshots can help; remove unrelated personal information. Do not include passwords, access tokens or payment-card details.</p></section>
<section class="support-section"><!--email_off--><h2>Account and privacy requests</h2><p>Supported app versions provide Export my data and Request my data in Account. To delete an account, choose Account → Contact support → Delete account. That path leads directly to an in-app confirmation. When enabled, Request my data queues an available server account copy for authorised staff on our private NAS, with minimal received and prepared notifications to our internal privacy mailbox. Preparation remains separate from human review and the reply to you. The automatic account copy identifies any records requiring human review; internal notes are not excluded from applicable access rights merely because they are internal. Contact support@versava.net for other access, correction, erasure or portability requests, or if those controls are unavailable in your installed build. Our appointed EU representative is CHOI, Chong Hing, Fasangartenstr 102, 81549 München; <a href="mailto:privacy@versava.net">privacy@versava.net</a>. You may contact the representative about personal information processing and applicable GDPR rights. We may reasonably verify ownership; do not email usable account credentials.</p><p>After confirmation, deletion is scheduled for the exact time 14 calendar days later. The account remains usable during this grace period, and Account shows the scheduled date and a direct Stop deletion action while cancellation is still possible. Stopping deletion keeps the account. When deletion becomes final it removes the account's balances, unlocks and unclaimed rewards. Account deletion does not cancel Apple subscription billing; manage the subscription separately. When available in the supported build, Restore Purchases can recover verified Remove Ads and active Plus on a new account without recovering the old wallet or unclaimed allowances. New Plus diamond eligibility starts on the next UTC date. Signing out, removing the app or leaving TestFlight does not itself delete server-held records. Where GDPR applies, the normal response period is one month, with timely explanation of any lawful extension.</p><p><a href="/privacy/">Public Privacy Notice</a> · <a href="/beta/privacy/">Beta Privacy Notice</a></p><!--/email_off--></section>
<section class="support-section"><h2>Invited Beta testing</h2><p>Daily Pause is currently tested on iPhone through TestFlight. Production paid purchases and subscriptions remain disabled. Designated TestFlight builds may display publisher banners and offer optional rewarded videos when separate advertising controls and privacy choices permit it. Publisher ad requests are non-personalised and use Google’s applicable consent and refusal flow; Ad privacy options is available where required. Verified ad-funded grants need an account-bound ticket and Google’s signed completion callback. Designated TestFlight builds may test monthly Daily Pause Plus subscriptions, supported star and diamond consumables, and the one-time Remove Ads product in Apple's Sandbox without real charges when testing controls permit it. Individual cash-pack checkout is disabled, including its purchase tests. Production Remove Ads checkout remains disabled. Other designated Beta builds can show labelled Google sample ads; sample videos do not grant stars, Past-day access or paid hints.</p><p><a href="/beta/terms/">Beta Testing Terms</a> · <a href="/beta/privacy/">Beta Privacy Notice</a></p></section>
<section class="support-section"><h2>Operator</h2><address>Versava Limited<br>Unit 1319, 13/F, One Midtown<br>11 Hoi Shing Road, Tsuen Wan<br>Hong Kong</address></section></main>'''
    add("/support/", page("Support", support, "/support/", active="/support/"))
    policies = [("App policy", "/client-release.json", load_client_release(root / "client-release.json")),
                ("Internal app policy", "/internal/client-release.json", load_client_release(root / "internal/client-release.json"))]
    shared = policies[0][2] == policies[1][2]
    cards = []
    for label, source, policy in policies[:1] if shared else policies:
        ios = policy["ios"]
        testing = urlsplit(ios["updateUrl"]).netloc == "testflight.apple.com"
        label = "Current app policy" if shared else label
        channel = "TestFlight Beta" if testing else "App Store update policy"
        action = "Open TestFlight" if testing else "Open App Store"
        facts = "".join(f'<div><dt>{name}</dt><dd>{html.escape(ios[field])} · Build {ios[build]}</dd></div>'
                        for name, field, build in (("Latest supported", "latestVersion", "latestBuild"),
                                                   ("Minimum supported", "minimumVersion", "minimumBuild")))
        sources = '<a href="/client-release.json">App policy JSON</a> · <a href="/internal/client-release.json">Internal policy JSON</a>' if shared else f'<a href="{source}">Policy JSON</a>'
        android = "No Android version is listed." if policy["android"] is None else f'Android: latest {html.escape(policy["android"]["latestVersion"])} (build {policy["android"]["latestBuild"]}), minimum {html.escape(policy["android"]["minimumVersion"])} (build {policy["android"]["minimumBuild"]}).'
        cards.append(f'''<section class="contact-card version-card"><h2>{label}</h2><span class="badge">{channel}</span>
<dl class="version-facts">{facts}</dl><p><a href="{html.escape(ios["updateUrl"], quote=True)}">{action}</a></p>
<p>Policy revision {policy["revision"]} · {sources}</p><p>{android}</p></section>''')
    beta_only = all(urlsplit(policy["ios"]["updateUrl"]).netloc == "testflight.apple.com" for _, _, policy in policies)
    status = '<p class="home-note">These are invited TestFlight Beta versions. A public App Store release is not listed here.</p>' if beta_only else '<p class="home-note">For installation and current store availability, use the Apple update link above.</p>'
    versions = f'''<main id="main" class="support-page page-width"><p class="eyebrow">Daily Pause updates</p><h1>Current versions</h1>
<p class="support-intro">Find the latest supported iPhone version and where to update.</p>{"".join(cards)}{status}</main>'''
    add("/versions/", page("Current versions", versions, "/versions/", active="/versions/"))
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
