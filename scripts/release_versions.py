"""Render an honest availability fallback from the same JSON fetched by browsers."""

import html
import json

from validate_release_policy import load_index


def render(root):
    index, policies = load_index(root)
    snapshot = {"/releases/index.json": index,
                "/releases/beta.json": policies["beta"],
                "/releases/public.json": policies["public"]}
    snapshot_attribute = html.escape(json.dumps(snapshot, separators=(",", ":"), sort_keys=True), quote=True)
    sections = []
    for track, label in (("public", "Release"), ("beta", "Beta")):
        item, channel = index[track], policies[track]["ios"]
        latest = html.escape(channel["latestVersion"] if channel else item["version"] or "Not listed")
        minimum = html.escape(channel["minimumVersion"] if channel else item["minimumVersion"] or "Not listed")
        facts = f'<div><dt>Latest version</dt><dd>{latest}</dd></div><div><dt>Minimum supported version</dt><dd>{minimum}</dd></div>'
        blocked = ""
        if channel and channel["blockedRanges"]:
            blocked = '<h4>Blocked versions</h4><ul>' + ''.join(
                f'<li>{html.escape(item["fromVersion"])} through {html.escape(item["throughVersion"])}, inclusive — {html.escape(item["reason"].title())}</li>'
                for item in channel["blockedRanges"]) + '</ul>'
        section_id = "beta-versions" if track == "beta" else "release-versions"
        sections.append(f'<section class="support-section" aria-labelledby="{section_id}"><h2 id="{section_id}">{label}</h2>'
                        f'<section class="contact-card version-card"><dl class="version-facts">{facts}</dl>{blocked}</section></section>')
    return (f'<div id="release-details" aria-live="polite" data-index-revision="{index["revision"]}" '
            f'data-beta-revision="{policies["beta"]["revision"]}" data-public-revision="{policies["public"]["revision"]}" '
            f'data-release-snapshot="{snapshot_attribute}">'
            + "".join(sections) + '</div>')
