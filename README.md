# PuzzleApp public configuration

Public release metadata for PuzzleApp's on-device puzzle generators.

This repository is separate from the private `puzzleapp-deploy` repository,
which contains infrastructure and deployment configuration. Application source,
generator implementations, and development tools remain in the application
monorepo.

## Intended contents

- A static JSON manifest assigning generator editions to explicit date ranges.
- Supported manifest schemas and validation tools.
- Platform-specific app version requirements and public store links.
- Public release notes describing future generator changes.

The app will generate puzzles locally from a date-derived seed. An edition
fixes the seed recipe, per-game generator versions, rules, and difficulty
profiles. Generator code is delivered through normal app updates; the manifest
only identifies the edition to use.

## Schedule rules

- Publish bounded date ranges. Never assume an old edition continues forever.
- Preserve all published date-to-edition assignments and started puzzles.
- Release compatible app builds before activating a new edition.
- Cached, covered dates remain playable offline when the app supports the edition.
- An unsupported scheduled edition requires an app update. A date outside cached
  coverage requires a configuration refresh; it does not by itself mean an app
  update is necessary.

## Publication boundary

Everything in this repository is public. Do not commit credentials, signing
keys, environment files, deployment scripts, internal infrastructure identifiers,
database exports, or private puzzle solutions.

The planned static host can publish the manifest through a CDN. Creating this
repository does not enable hosting or change the current PuzzleApp DNS records.

## Current status

Repository scaffold only. No active generator schedule, production manifest,
or hosted endpoint has been published. Those will be added with the first
implemented and validated on-device generator edition.
