"""Validate the public client policy before static publication."""

import json
from pathlib import Path
import re
from urllib.parse import urlsplit

MAX_BYTES = 16384
MAX_NUMBER = 2147483647


def version(value):
    if not isinstance(value, str) or not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", value):
        raise ValueError("Invalid client version")
    parts = tuple(int(part) for part in value.split("."))
    if any(part > MAX_NUMBER for part in parts):
        raise ValueError("Invalid client version")
    return parts


def number(value):
    if type(value) is not int or not 1 <= value <= MAX_NUMBER:
        raise ValueError("Invalid client build/revision")
    return value


def channel(value):
    expected = {"latestVersion", "latestBuild", "minimumVersion", "minimumBuild", "updateUrl"}
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError("Invalid client channel")
    latest = (*version(value["latestVersion"]), number(value["latestBuild"]))
    minimum = (*version(value["minimumVersion"]), number(value["minimumBuild"]))
    if minimum > latest:
        raise ValueError("Client minimum exceeds latest")
    if not isinstance(value["updateUrl"], str):
        raise ValueError("Invalid client update URL")
    url = urlsplit(value["updateUrl"])
    safe = (
        url.scheme == "https" and url.netloc in {"testflight.apple.com", "apps.apple.com"}
        and not url.query and not url.fragment
        and ((url.netloc == "testflight.apple.com" and re.fullmatch(r"/join/[A-Za-z0-9]{8}", url.path))
             or (url.netloc == "apps.apple.com" and re.fullmatch(r"/(?:[a-z]{2}/)?app/(?:[a-zA-Z0-9-]+/)?id[0-9]+", url.path)))
    )
    if not safe:
        raise ValueError("Client update URL must be an allowlisted Apple destination")
    return value


def validate(value):
    if not isinstance(value, dict) or set(value) != {"schemaVersion", "revision", "ios", "android"}:
        raise ValueError("Invalid client release policy")
    if type(value["schemaVersion"]) is not int or value["schemaVersion"] != 1:
        raise ValueError("Unknown client release schema")
    number(value["revision"])
    channel(value["ios"])
    if value["android"] is not None:
        channel(value["android"])
    return value


def load(path: Path):
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES:
        raise ValueError("Client release policy exceeds 16 KiB")
    return validate(json.loads(raw))


if __name__ == "__main__":
    import sys
    value = load(Path(sys.argv[1] if len(sys.argv) > 1 else "client-release.json"))
    print(json.dumps({"revision": value["revision"], "iosLatestBuild": value["ios"]["latestBuild"]}))
