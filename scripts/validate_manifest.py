"""Validate public schedules and append-only publication; standard library only."""

import argparse
from datetime import date, timedelta
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

MAX_BYTES = 262144
MAX_NUMBER = 2147483647
MAX_DEPTH = 16


def require(condition, message):
    if not condition:
        raise ValueError(message)


def keys(value, expected):
    require(isinstance(value, dict) and set(value) == set(expected), "Unexpected object fields")


def positive(value):
    require(type(value) is int and 1 <= value <= MAX_NUMBER, "Expected a positive 32-bit integer")


def day(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value), "Expected YYYY-MM-DD")
    parsed = date.fromisoformat(value)
    require(date(1, 1, 1) <= parsed <= date(9999, 12, 31), "Date outside supported range")
    return parsed


def validate(value):
    keys(value, ("schemaVersion", "revision", "datePolicy", "validThrough", "windows", "updates", *(("additions",) if "additions" in value else ()), *(("selections",) if "selections" in value else ())))
    require(type(value["schemaVersion"]) is int and value["schemaVersion"] == 1, "Unsupported schema")
    positive(value["revision"])
    require(value["datePolicy"] == "device-local", "Unsupported date policy")
    end = day(value["validThrough"])
    windows = value["windows"]
    require(isinstance(windows, list) and 1 <= len(windows) <= 128, "Expected 1..128 date windows")
    previous = None
    for window in windows:
        keys(window, ("from", "through", "edition", "minBuild"))
        start, through = day(window["from"]), day(window["through"])
        require(start <= through, "Reversed date window")
        require(previous is None or start == previous + timedelta(days=1), "Windows must be ordered and contiguous")
        require(isinstance(window["edition"], str) and re.fullmatch(r"[a-z][a-z0-9-]{0,63}", window["edition"]), "Invalid edition")
        keys(window["minBuild"], ("ios", "android"))
        for build in window["minBuild"].values():
            positive(build)
        previous = through
    require(previous == end, "validThrough must match the final window")
    for field in ("additions", "selections"):
        optional = value.get(field, [])
        require(isinstance(optional, list) and (field not in value or 1 <= len(optional) <= 128), "Expected 1..128 optional windows")
        previous = None
        for window in optional:
            keys(window, ("from", "through", "edition", "minBuild"))
            start, through = day(window["from"]), day(window["through"])
            require(day(windows[0]["from"]) <= start <= through <= end, "Optional window outside base coverage")
            require(previous is None or start > previous, "Optional windows must be ordered and nonoverlapping")
            require(isinstance(window["edition"], str) and re.fullmatch(r"[a-z][a-z0-9-]{0,63}", window["edition"]), "Invalid optional edition")
            keys(window["minBuild"], ("ios", "android"))
            for build in window["minBuild"].values():
                positive(build)
            previous = through
    for addition in value.get("additions", []):
        for selection in value.get("selections", []):
            require(max(addition["from"], selection["from"]) > min(addition["through"], selection["through"]), "Selection and additions windows overlap")
    keys(value["updates"], ("ios", "android"))
    for platform, host in (("ios", "apps.apple.com"), ("android", "play.google.com")):
        update = value["updates"][platform]
        keys(update, ("url",))
        if update["url"] is not None:
            require(isinstance(update["url"], str) and len(update["url"]) <= 2048, "Invalid store URL")
            url = urlsplit(update["url"])
            require(url.scheme == "https" and url.hostname == host and url.username is None and url.password is None and url.port in (None, 443), "Expected official HTTPS store URL")
    return value


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, "Duplicate JSON key")
        result[key] = value
    return result


class _JsonShapeReader:
    """Bound recursion before decoding, using the same depth rule as Dart."""

    def __init__(self, source):
        self.source = source
        self.index = 0

    def whitespace(self):
        while self.index < len(self.source) and self.source[self.index] in " \r\n\t":
            self.index += 1

    def take(self, character):
        if self.index < len(self.source) and self.source[self.index] == character:
            self.index += 1
            return True
        return False

    def string(self):
        start = self.index
        require(self.take('"'), "Expected a JSON string")
        while self.index < len(self.source):
            character = self.source[self.index]
            self.index += 1
            if character == "\\":
                require(self.index < len(self.source), "Incomplete JSON escape")
                self.index += 1
            elif character == '"':
                return json.loads(self.source[start:self.index])
        raise ValueError("Unterminated JSON string")

    def value(self, depth=0):
        require(depth <= MAX_DEPTH, "Manifest nesting is too deep")
        self.whitespace()
        require(self.index < len(self.source), "Incomplete JSON value")
        if self.take("{"):
            self.whitespace()
            if self.take("}"):
                return
            names = set()
            while True:
                self.whitespace()
                name = self.string()
                require(name not in names, "Duplicate JSON key")
                names.add(name)
                self.whitespace()
                require(self.take(":"), "Expected a JSON colon")
                self.value(depth + 1)
                self.whitespace()
                if self.take("}"):
                    return
                require(self.take(","), "Expected a JSON comma")
        if self.take("["):
            self.whitespace()
            if self.take("]"):
                return
            while True:
                self.value(depth + 1)
                self.whitespace()
                if self.take("]"):
                    return
                require(self.take(","), "Expected a JSON comma")
        if self.source[self.index] == '"':
            self.string()
            return
        start = self.index
        while self.index < len(self.source) and self.source[self.index] not in ",}] \r\n\t":
            self.index += 1
        token = self.source[start:self.index]
        require(token, "Expected a JSON value")
        if token not in ("true", "false", "null"):
            require(re.fullmatch(r"-?(0|[1-9][0-9]*)", token), "Manifest numbers must use integer notation")
        json.loads(token)

    def validate(self):
        self.value()
        self.whitespace()
        require(self.index == len(self.source), "Unexpected data after manifest")


def load_bytes(payload):
    """Validate file or historical Git blob bytes through one strict boundary."""
    require(len(payload) <= MAX_BYTES, "Manifest exceeds size limit")
    source = payload.decode("utf-8")
    _JsonShapeReader(source).validate()
    return validate(json.loads(source, object_pairs_hook=pairs))


def load(path):
    # Read at most one byte beyond the limit, including for symlinked files.
    with Path(path).open("rb") as stream:
        return load_bytes(stream.read(MAX_BYTES + 1))


def validate_extension(previous, current):
    validate(previous)
    validate(current)
    require(current["revision"] >= previous["revision"], "Manifest revision moved backwards")
    if current["revision"] == previous["revision"]:
        require(current == previous, "A published revision changed")
        return
    first, last = previous["windows"][0]["from"], previous["validThrough"]
    require(current["windows"][0]["from"] <= first and current["validThrough"] >= last, "Published coverage shrank")
    boundaries = {first}
    for manifest in (previous, current):
        for field in ("windows", "additions", "selections"):
            for window in manifest.get(field, []):
                if first <= window["from"] <= last:
                    boundaries.add(window["from"])
                if first <= window["through"] < last:
                    boundaries.add((day(window["through"]) + timedelta(days=1)).isoformat())
    def identity(manifest, field, when):
        for window in manifest.get(field, []):
            if window["from"] <= when <= window["through"]:
                return window["edition"], window["minBuild"]
        return None
    for when in boundaries:
        for field in ("windows", "additions", "selections"):
            require(identity(previous, field, when) == identity(current, field, when), "Published date assignment changed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", default="manifest.json")
    parser.add_argument("--previous")
    args = parser.parse_args()
    current = load(args.manifest)
    if args.previous:
        validate_extension(load(args.previous), current)
    print("Manifest valid: revision", current["revision"], "through", current["validThrough"])


if __name__ == "__main__":
    main()
