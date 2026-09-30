"""Reject rewrites against every prior first-parent mainline manifest."""

from pathlib import Path
import subprocess
import argparse
import re

from validate_manifest import MAX_BYTES, load, load_bytes, require
from development_transition import load_transition, validate_publication

ROOT = Path(__file__).resolve().parent.parent
FROZEN_LEGAL = re.compile(r"legal/[a-z0-9][a-z0-9.-]{0,63}/(?:manifest\.json|(?:terms|privacy)-(?:alpha|beta|public)\.md)")


def check_legal_history(root, git, commits):
    """Retain every committed edition, including its source-hash manifest."""
    seen = set()
    for commit in commits:
        for entry in git("ls-tree", "-r", commit, "--", "legal").decode("utf-8").splitlines():
            metadata, name = entry.split("\t", 1)
            if not FROZEN_LEGAL.fullmatch(name):
                continue
            mode, kind, object_id = metadata.split()
            require(mode == "100644" and kind == "blob", "Expected a regular frozen legal source")
            if (name, object_id) in seen:
                continue
            seen.add((name, object_id))
            current = root / name
            require(current.is_file() and not current.is_symlink(), f"Retain published legal source: {name}")
            require(current.read_bytes() == git("cat-file", "blob", object_id), f"Frozen legal edition was rewritten: {name}")


def check_release(root=ROOT, baseline_ref=None):
    root = Path(root)
    current = load(root / "manifest.json")
    transition_path = root / "development-transition.json"
    acknowledgement = load_transition(transition_path) if transition_path.is_file() else None

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
    # Generator-development exceptions never exempt legal edition history.
    check_legal_history(root, git, commits)
    if baseline_ref:
        baseline = git('rev-parse', '--verify', f'{baseline_ref}^{{commit}}').decode('ascii').strip()
        require(baseline in commits, 'Publication baseline must be in first-parent history')
        commits = commits[:commits.index(baseline) + 1]
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
        validate_publication(previous, current, acknowledgement)
        checked += 1
    return checked


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-ref', help='Explicit first immutable release checkpoint; defaults to complete history')
    args = parser.parse_args()
    checked = check_release(baseline_ref=args.baseline_ref)
    print("Release validated against", checked, "previous mainline manifest versions")
