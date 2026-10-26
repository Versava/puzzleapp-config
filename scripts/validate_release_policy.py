"""Additive, track-specific policies; legacy schema 1/2 files stay unchanged."""

import json
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from validate_client_release import MAX_BYTES, channel as legacy_channel, number, version


TRACKS = ("alpha", "beta", "public")


def exact(value, names):
    if not isinstance(value, dict) or set(value) != set(names):
        raise ValueError("Invalid release policy fields")


def validate(value, expected_track=None):
    exact(value, ("schemaVersion", "revision", "track", "ios", "android"))
    track = value["track"]
    if type(value["schemaVersion"]) is not int or value["schemaVersion"] != 3 or track not in TRACKS:
        raise ValueError("Invalid release policy schema or track")
    if expected_track is not None and track != expected_track:
        raise ValueError("Release policy track mismatch")
    number(value["revision"])
    alpha = track == "alpha"
    for platform in ("ios", "android"):
        channel = value[platform]
        if channel is None:
            continue
        fields = {"latestVersion", "minimumVersion", "updateUrl", "blockedRanges", "updatePolicy"}
        if alpha:
            fields |= {"latestBuild", "minimumBuild"}
        exact(channel, fields)
        latest = (*version(channel["latestVersion"]),)
        minimum = (*version(channel["minimumVersion"]),)
        if alpha:
            latest += (number(channel["latestBuild"]),)
            minimum += (number(channel["minimumBuild"]),)
        if minimum > latest:
            raise ValueError("Release minimum exceeds latest")
        # Reuse the URL allowlist, without introducing build authority for Beta/Public.
        legacy_channel({"latestVersion": channel["latestVersion"],
                        "minimumVersion": channel["minimumVersion"],
                        "latestBuild": channel.get("latestBuild", 1),
                        "minimumBuild": channel.get("minimumBuild", 1),
                        "updateUrl": channel["updateUrl"]})
        host = "apps.apple.com" if track == "public" else "testflight.apple.com"
        if urlsplit(channel["updateUrl"]).hostname != host:
            raise ValueError("Release update destination does not match track")
        if channel["updatePolicy"] != ("optional" if track == "public" else "required"):
            raise ValueError("Invalid release update policy")
        ranges = channel["blockedRanges"]
        if not isinstance(ranges, list) or len(ranges) > 32:
            raise ValueError("Invalid release blocked ranges")
        previous = None
        for item in ranges:
            fields = {"fromVersion", "throughVersion", "reason"}
            if alpha:
                fields |= {"fromBuild", "throughBuild"}
            exact(item, fields)
            start, end = version(item["fromVersion"]), version(item["throughVersion"])
            if alpha:
                start += (number(item["fromBuild"]),)
                end += (number(item["throughBuild"]),)
            if start > end or end >= latest or (previous is not None and start <= previous):
                raise ValueError("Release blocked ranges must be ordered, disjoint and below latest")
            if item["reason"] not in ("security", "compatibility"):
                raise ValueError("Invalid release blocked reason")
            previous = end
    return value


def read_json(path):
    raw = Path(path).read_bytes()
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("Invalid release JSON size")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate release JSON key")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def load(path, expected_track=None):
    return validate(read_json(path), expected_track)


def load_index(root):
    root = Path(root)
    index = read_json(root / "releases/index.json")
    exact(index, ("schemaVersion", "revision", "beta", "public"))
    if type(index["schemaVersion"]) is not int or index["schemaVersion"] != 1:
        raise ValueError("Invalid release index schema")
    number(index["revision"])
    policies = {track: load(root / f"releases/{track}.json", track) for track in TRACKS}
    for track, allowed in (("beta", {"testing", "unavailable"}),
                           ("public", {"inReview", "available", "unavailable"})):
        item = index[track]
        exact(item, ("version", "minimumVersion", "status", "releasedAt"))
        if item["status"] not in allowed:
            raise ValueError("Invalid release availability status")
        if item["status"] in {"testing", "available"}:
            if not isinstance(item["releasedAt"], str) or date.fromisoformat(item["releasedAt"]).isoformat() != item["releasedAt"]:
                raise ValueError("An obtainable release requires its real release date")
        elif item["releasedAt"] is not None:
            raise ValueError("An unreleased version cannot have a release date")
        if item["version"] is not None:
            version(item["version"])
            if version(item["minimumVersion"]) > version(item["version"]):
                raise ValueError("Release index minimum exceeds latest")
        if item["status"] == "unavailable":
            if item["version"] is not None or item["minimumVersion"] is not None:
                raise ValueError("Unavailable release cannot advertise a version")
        elif item["version"] is None:
            raise ValueError("Release status requires a version")
        if item["status"] in {"testing", "available"}:
            channel = policies[track]["ios"]
            if channel is None or channel["latestVersion"] != item["version"] or channel["minimumVersion"] != item["minimumVersion"]:
                raise ValueError("Available release must match its obtainable policy")
    return index, policies
