"""Validate the one reviewed AdMob seller declaration before static publication.

Syntax validation does not establish provider ownership or app readiness. Copy the
personalized declaration from the owned AdMob console before creating the file.
Absent source means the seller declaration is not published.
"""

from pathlib import Path
import re


PUBLISHER = "pub-8798981282479093"
DECLARATION = re.compile(
    rf"google\.com, {PUBLISHER}, DIRECT(?:, [a-f0-9]{{16}})?\n"
)


def load(path: Path):
    if path.is_symlink():
        raise ValueError("app-ads.txt must be a reviewed regular source file")
    if not path.exists():
        return None
    if not path.is_file() or path.stat().st_size > 4096:
        raise ValueError("Invalid app-ads.txt source")
    try:
        content = path.read_bytes()
        text = content.decode("ascii")
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError("Invalid app-ads.txt text") from error
    if DECLARATION.fullmatch(text) is None:
        raise ValueError("app-ads.txt must contain only the reviewed direct Google publisher row")
    return content
