"""Reject rewrites against every prior first-parent mainline manifest."""

from pathlib import Path
import subprocess

from validate_manifest import MAX_BYTES, load, load_bytes, require, validate_extension

ROOT = Path(__file__).resolve().parent.parent


def check_release(root=ROOT):
    root = Path(root)
    current = load(root / "manifest.json")

    def git(*args):
        return subprocess.run(
            ["git", *args], cwd=root, capture_output=True, check=True
        ).stdout

    if git("rev-parse", "--is-shallow-repository").strip() == b"true":
        # Public origin only. Never silently accept a truncated history.
        subprocess.run(["git", "fetch", "--unshallow", "origin"], cwd=root, check=True)
    require(
        git("rev-parse", "--is-shallow-repository").strip() == b"false",
        "A complete mainline history is required for publication",
    )
    commits = git("rev-list", "--first-parent", "HEAD").decode("ascii").splitlines()
    checked = 0
    seen = set()
    # Include HEAD as well: a local dirty build must preserve its committed
    # manifest. Every older mainline commit closes multi-commit push bypasses.
    for commit in commits:
        entry = git("ls-tree", commit, "--", "manifest.json").decode("ascii").strip()
        if not entry:
            continue
        metadata, name = entry.split("\t", 1)
        mode, kind, object_id = metadata.split()
        require(name == "manifest.json" and kind == "blob" and mode == "100644", "Expected a regular manifest file in history")
        if object_id in seen:
            continue
        seen.add(object_id)
        require(int(git("cat-file", "-s", object_id)) <= MAX_BYTES, "Historical manifest exceeds size limit")
        previous = load_bytes(git("cat-file", "blob", object_id))
        validate_extension(previous, current)
        checked += 1
    return checked


if __name__ == "__main__":
    checked = check_release()
    print("Release preserves", checked, "previous mainline manifest versions")
