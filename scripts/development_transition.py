"""One explicitly reviewed development transition; normal history stays strict."""

from datetime import timedelta
from hashlib import sha256
import json
from pathlib import Path

from validate_manifest import (
    MAX_BYTES, _JsonShapeReader, day, keys, pairs, require, validate,
    validate_extension,
)


def manifest_hash(manifest):
    return sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_transition(path):
    with Path(path).open("rb") as stream:
        payload = stream.read(MAX_BYTES + 1)
    require(len(payload) <= MAX_BYTES, "Development acknowledgement is too large")
    text = payload.decode("utf-8")
    _JsonShapeReader(text).validate()
    value = json.loads(text, object_pairs_hook=pairs)
    keys(value, ("schemaVersion", "authorizedOn", "reason", "from", "through",
                 "previousManifestSha256", "replacementManifestSha256", "replacementManifest"))
    require(type(value["schemaVersion"]) is int and value["schemaVersion"] == 1, "Unknown development acknowledgement schema")
    day(value["authorizedOn"])
    require(day(value["from"]) <= day(value["through"]), "Invalid transition interval")
    require(isinstance(value["reason"], str) and 1 <= len(value["reason"]) <= 1000, "A development transition needs an explicit reason")
    hashes = value["previousManifestSha256"]
    require(isinstance(hashes, list) and 1 <= len(hashes) <= 16, "Expected exact previous manifest hashes")
    require(all(isinstance(item, str) and len(item) == 64 and all(c in "0123456789abcdef" for c in item) for item in hashes), "Invalid previous manifest hash")
    require(len(set(hashes)) == len(hashes), "Duplicate previous manifest hash")
    replacement = validate(value["replacementManifest"])
    require(manifest_hash(replacement) == value["replacementManifestSha256"], "Acknowledged replacement hash differs")
    return value


def _check_scope(previous, replacement, start, through):
    """Check every assignment boundary, including the end of the exception."""
    require(replacement["revision"] > previous["revision"], "Transition must advance revision")
    require(replacement["datePolicy"] == previous["datePolicy"], "Transition changed date policy")
    require(replacement["windows"][0]["from"] <= previous["windows"][0]["from"]
            and replacement["validThrough"] >= previous["validThrough"], "Transition shrank coverage")
    first, last = previous["windows"][0]["from"], previous["validThrough"]
    boundaries = {first, start}
    if through < "9999-12-31":
        boundaries.add((day(through) + timedelta(days=1)).isoformat())
    for manifest in (previous, replacement):
        for field in ("windows", "additions", "selections"):
            for window in manifest.get(field, []):
                boundaries.add(window["from"])
                if window["through"] < "9999-12-31":
                    boundaries.add((day(window["through"]) + timedelta(days=1)).isoformat())
    def identity(manifest, field, when):
        for window in manifest.get(field, []):
            if window["from"] <= when <= window["through"]:
                return window["edition"], window["minBuild"]
        return None
    for when in boundaries:
        if not first <= when <= last or start <= when <= through:
            continue
        for field in ("windows", "additions", "selections"):
            require(identity(previous, field, when) == identity(replacement, field, when),
                    "Development transition changed dates outside its approved interval")


def validate_publication(previous, current, acknowledgement=None):
    try:
        validate_extension(previous, current)
        return
    except ValueError:
        if acknowledgement is None:
            raise
    require(manifest_hash(previous) in acknowledgement["previousManifestSha256"],
            "Rewrite is not an acknowledged development source")
    replacement = acknowledgement["replacementManifest"]
    _check_scope(previous, replacement, acknowledgement["from"], acknowledgement["through"])
    # A later extension must preserve the entire exact acknowledged replacement.
    # The acknowledgement never authorizes a second rewrite or a hidden edit.
    validate_extension(replacement, current)
