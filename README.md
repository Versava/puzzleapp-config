# PuzzleApp public configuration

Public release metadata for PuzzleApp's deterministic, on-device puzzle generators.
The application monorepo includes this repository at `public-config/`. The separate
`puzzleapp-deploy` repository stays private and contains legacy infrastructure
configuration; none of it belongs in this public repository.

## Schedule

Prepared `manifest.json` revision 4 covers **0001-01-01 through 2026-12-31**.
It preserves `local-v1` through September 27 and uses `local-v2` from September 28;
both use the frozen `daily-mix-v1` selection of four games from the six-game pool.
In `local-v2`, each date and game independently selects easy, medium or hard from
a deterministic seed. The selected game kinds remain unchanged. Archive days
are generated only when selected; this repository contains no level files.

**0001-01-01 through 2026-09-27** retains its exact recipe and minimum build 3.
**2026-09-28 through 2026-12-31** now requires build 4 under the explicit
development acknowledgement below. Existing attempts retain their exact
snapshots. The account service retains all 285 prior releases for old tickets
beside 95 new selected releases; existing account balances and grants are unchanged.

Build `0.1.0+1` understands the base schedule, `0.1.0+2` the daily mix, and
`0.1.0+4` the new difficulty edition and bundled baseline. Older clients continue
to reject rewritten assignments during refresh; a native app update supplies
the new baseline. PuzzleApp is not released in stores, so both store URLs remain
`null`. Static metadata never installs executable code. Compatible store builds
must precede new editions once public store releases exist.

## Manifest contract

| Field | Meaning |
| --- | --- |
| `schemaVersion` | Manifest format, currently `1`. |
| `revision` | Positive, monotonically increasing publication number. |
| `datePolicy` | `device-local`: a civil date, not an instant or a UTC reset. |
| `validThrough` | Final covered date, equal to the last window's `through`. |
| `windows` | Ordered, contiguous, inclusive date ranges with `edition` and platform `minBuild`. |
| `selections` | Optional ordered, nonoverlapping windows selecting a frozen daily game mix and platform `minBuild`. |
| `additions` | Optional ordered, nonoverlapping windows within base coverage, with separately versioned extra games and platform `minBuild`. |
| `updates` | Optional official App Store / Google Play HTTPS URLs; `null` before release. |

Dates use the proleptic Gregorian calendar, years 0001–9999. Manifests are limited
to 256 KiB and 128 base windows; integer fields use positive signed 32-bit values. Selections and legacy additions each have a 128-window limit; gaps are allowed between these optional windows. Unknown fields, duplicate keys, base
coverage gaps, overlaps, invalid dates, and unsupported schema versions are rejected.
`manifest.schema.json` describes the structure; `scripts/validate_manifest.py`
also checks calendar semantics and immutable publication history.

The manifest contains metadata only. Generator code ships inside normal app
updates. Published date-to-edition and date-to-minimum-build assignments are
immutable, including announced future dates. Never amend a published edition's
algorithm: ship a new edition identifier instead.
Announced selection and legacy addition windows cannot be removed, shortened or
reassigned. The selection edition freezes the candidate pool and shuffle; later
game additions use a new edition. Older clients that do not recognize selections
retain their older base schedule and need an updated app for the daily mix.

## Offline and update behavior

- The app starts from its bundled schedule and last valid cached schedule.
- Covered dates remain playable offline if the installed app supports the edition.
- An unsupported edition or insufficient installed build requires an app update.
- Exhausted calendar coverage requires a schedule refresh; it alone does not mean
  the app needs updating. If refresh fails, the app retains the last valid schedule.
- Started puzzles keep their exact question snapshots and progress.
- Rollbacks and changes to existing assignments are rejected by the client.

## Validate and publish

Python 3.12 or newer and Git are sufficient; no third-party Python packages are
required. Run from this repository:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_release.py --baseline-ref cc8f8ab
python3 scripts/build.py
```

The history check validates the current schedule against previous published
mainline manifests from the explicit revision-2 development checkpoint
`cc8f8ab`. That checkpoint records the approved four-of-six daily settings before
strict overlap immutability was introduced. All commits since it remain checked,
including hidden rewrites followed by unrelated commits. Without `--baseline-ref`,
the gate checks the entire history. The static build copies only `manifest.json`,
`manifest.schema.json`, `index.html`, `404.html`, and `_headers` to `dist/`.
No application source, puzzle answers, server functions, or credentials are built.

For the user-approved active-development difficulty change,
`development-transition.json` records exact canonical SHA-256 hashes of the
revision-2 and revision-3 source manifests, the full revision-4 replacement and
its hash, and the only approved interval: **2026-09-28–2026-12-31**. The publication
gate checks those exact artifacts, keeps all earlier archive dates fixed, and
requires subsequent revisions to preserve the entire replacement. It does not
permit another rewrite, unknown source content or hidden edits. Ordinary
`validate_extension` remains strict; CI's previous-manifest check explicitly
uses this acknowledgement. It is source history, not an app-manifest field,
and is excluded from static hosting output.

For a calendar extension:

1. Increment `revision` and extend coverage by prepending or appending contiguous windows.
2. Preserve all existing date assignments and minimum builds.
   This includes the absence of optional selection/addition rules: adding one
   over previously covered dates also changes their effective recipe and is rejected.
   Introduce new game mixes only on dates outside already announced coverage.
3. If introducing an edition, release and verify compatible app builds first.
4. Run the validation commands and review the manifest diff before pushing.
5. After hosting deploys, verify the response body, revision, CORS, cache headers,
   and conditional request behavior at the public endpoint.

GitHub Actions runs the same checks. Cloudflare Pages must also run the history
check inside its build, so publication cannot race the independent GitHub check.
Use framework **None**, production branch **main**, output directory **dist**, and
this build command:

```sh
python3 -m unittest discover -s tests && python3 scripts/check_release.py --baseline-ref cc8f8ab && python3 scripts/build.py
```

The production URL is [puzzle.versava.net/manifest.json](https://puzzle.versava.net/manifest.json),
with [puzzleapp-config.pages.dev/manifest.json](https://puzzleapp-config.pages.dev/manifest.json)
as the host URL. The prior revision was verified on 2026-09-28: exact manifest bytes, HTTP 200,
public CORS, five-minute freshness, ETag conditional 304, and missing-file 404.
The Cloudflare GitHub integration is limited to **only this public repository**.
A static Pages project needs no EC2, database, or runtime API. Revision 4 is
prepared locally; its publication and matching app/Worker rollout are not claimed here.

The manifest is public and uses a five-minute HTTP cache lifetime, public CORS,
and ETags supplied by the host. Native clients use conditional requests. Browser
clients must work without requiring a custom server for preflight requests.

## Publication boundary

Everything committed here is public. Never add credentials, signing keys,
environment files, infrastructure account identifiers, database exports, private
puzzle solutions, or files from `puzzleapp-deploy`. Its private status is deliberate.
Force-pushing or rewriting release history defeats history-based safeguards;
retain the published mainline history.
