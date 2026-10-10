"""Validate modern optional-update and mandatory-support policies.

Legacy client-release.json stays separate: older apps treated latest as a
mandatory upgrade, so advertising an optional update there would block them.
"""

import json
from pathlib import Path

from validate_client_release import MAX_BYTES, channel as legacy_channel, number, version


def channel(value):
    fields = {"latestVersion", "latestBuild", "minimumVersion", "minimumBuild", "updateUrl", "blockedRanges", "updatePolicy"}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("Invalid client support channel")
    legacy_channel({key: item for key, item in value.items() if key not in {"blockedRanges", "updatePolicy"}})
    if value["updatePolicy"] not in ("required", "optional"):
        raise ValueError("Invalid ordinary update policy")
    latest = (*version(value["latestVersion"]), number(value["latestBuild"]))
    ranges = value["blockedRanges"]
    if not isinstance(ranges, list) or len(ranges) > 32:
        raise ValueError("Invalid blocked version ranges")
    previous_end = None
    for item in ranges:
        expected = {"fromVersion", "fromBuild", "throughVersion", "throughBuild", "reason"}
        if not isinstance(item, dict) or set(item) != expected:
            raise ValueError("Invalid blocked version range")
        start = (*version(item["fromVersion"]), number(item["fromBuild"]))
        end = (*version(item["throughVersion"]), number(item["throughBuild"]))
        if start > end or end >= latest or (previous_end is not None and start <= previous_end):
            raise ValueError("Blocked ranges must be ordered, disjoint and below the available update")
        if item["reason"] not in ("security", "compatibility"):
            raise ValueError("Invalid blocked version reason")
        previous_end = end
    return value


def validate(value):
    if not isinstance(value, dict) or set(value) != {"schemaVersion", "revision", "ios", "android"}:
        raise ValueError("Invalid client support policy")
    if type(value["schemaVersion"]) is not int or value["schemaVersion"] != 2:
        raise ValueError("Unknown client support schema")
    number(value["revision"])
    channel(value["ios"])
    if value["android"] is not None:
        channel(value["android"])
    return value


def load(path: Path):
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES:
        raise ValueError("Client support policy exceeds 16 KiB")
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate client support key")
            result[key] = value
        return result
    return validate(json.loads(raw, object_pairs_hook=unique_object))


if __name__ == "__main__":
    import sys
    value = load(Path(sys.argv[1] if len(sys.argv) > 1 else "client-support.json"))
    print(json.dumps({"revision": value["revision"], "iosLatestBuild": value["ios"]["latestBuild"],
                      "blockedRangeCount": len(value["ios"]["blockedRanges"])}))
