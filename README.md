# PuzzleApp public configuration

Public release metadata for PuzzleApp's deterministic, on-device puzzle generators.
The application monorepo includes this repository at `public-config/`. The separate
`puzzleapp-deploy` repository stays private and contains legacy infrastructure
configuration; none of it belongs in this public repository.

## Initial schedule

`manifest.json` revision 1 assigns **2026-09-28 through 2026-12-31**, inclusive,
to generator edition `local-v1`. The edition produces Picture Logic, Mini Sudoku,
Colour Links, and Train Tracks from the device's local calendar date. Everyone
using the same edition and date gets the same daily questions.

The first compatible development build is `0.1.0+1`. The app has not yet been
released in the stores, so both store URLs are `null`. Do not announce a public
app release or activate a new edition until compatible store builds are available.

## Manifest contract

| Field | Meaning |
| --- | --- |
| `schemaVersion` | Manifest format, currently `1`. |
| `revision` | Positive, monotonically increasing publication number. |
| `datePolicy` | `device-local`: a civil date, not an instant or a UTC reset. |
| `validThrough` | Final covered date, equal to the last window's `through`. |
| `windows` | Ordered, contiguous, inclusive date ranges with `edition` and platform `minBuild`. |
| `updates` | Optional official App Store / Google Play HTTPS URLs; `null` before release. |

Dates are limited to 2000–2100, manifests to 256 KiB and 128 windows, and integer
fields to positive signed 32-bit values. Unknown fields, duplicate keys, gaps,
overlaps, invalid dates, and unsupported schema versions are rejected.
`manifest.schema.json` describes the structure; `scripts/validate_manifest.py`
also checks calendar semantics and immutable publication history.

The manifest contains metadata only. Generator code ships inside normal app
updates. Published date-to-edition and date-to-minimum-build assignments are
immutable, including announced future dates. Never amend a published edition's
algorithm: ship a new edition identifier instead.

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
python3 scripts/check_release.py
python3 scripts/build.py
```

The history check validates the current schedule against previous published
mainline manifests. The static build copies only `manifest.json`,
`manifest.schema.json`, `index.html`, `404.html`, and `_headers` to `dist/`.
No application source, puzzle answers, server functions, or credentials are built.

For a calendar extension:

1. Increment `revision` and extend the final window, or append a contiguous window.
2. Preserve all existing date assignments and minimum builds.
3. If introducing an edition, release and verify compatible app builds first.
4. Run the validation commands and review the manifest diff before pushing.
5. After hosting deploys, verify the response body, revision, CORS, cache headers,
   and conditional request behavior at the public endpoint.

GitHub Actions runs the same checks. Cloudflare Pages must also run the history
check inside its build, so publication cannot race the independent GitHub check.
Use framework **None**, production branch **main**, output directory **dist**, and
this build command:

```sh
python3 -m unittest discover -s tests && python3 scripts/check_release.py && python3 scripts/build.py
```

The production URL is [puzzle.versava.net/manifest.json](https://puzzle.versava.net/manifest.json),
with [puzzleapp-config.pages.dev/manifest.json](https://puzzleapp-config.pages.dev/manifest.json)
as the host URL. Both were verified on 2026-09-28: exact manifest bytes, HTTP 200,
public CORS, five-minute freshness, ETag conditional 304, and missing-file 404.
The Cloudflare GitHub integration is limited to **only this public repository**.
A static Pages project needs no EC2, database, or runtime API.

The manifest is public and uses a five-minute HTTP cache lifetime, public CORS,
and ETags supplied by the host. Native clients use conditional requests. Browser
clients must work without requiring a custom server for preflight requests.

## Publication boundary

Everything committed here is public. Never add credentials, signing keys,
environment files, infrastructure account identifiers, database exports, private
puzzle solutions, or files from `puzzleapp-deploy`. Its private status is deliberate.
Force-pushing or rewriting release history defeats history-based safeguards;
retain the published mainline history.
