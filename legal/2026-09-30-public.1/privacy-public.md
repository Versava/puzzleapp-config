# Daily Pause Privacy Notice

Version: 2026-09-30-public.1 · Updated: 30 September 2026

This notice explains how Versava Limited, a company registered in Hong Kong
(Versava, we, us, or our), handles personal information for the Daily Pause
website and public versions of Daily Pause: Pocket Puzzles and associated
services when they are available. Invited pre-release builds have a separate
Daily Pause Beta Privacy Notice, including their TestFlight and sample-ad
processing. Publishing this notice does not announce a public app launch.

Contact support@versava.net about privacy, access or correction, or other
requests concerning your records. You can also write to Privacy Contact,
Versava Limited, Unit 1319, 13/F, One Midtown, 11 Hoi Shing Road, Tsuen Wan,
Hong Kong.

This notice provides information; acknowledging it is not consent to advertising,
tracking, or unrelated processing. The separate Terms of Use explain the
applicable agreement. We explain optional features before enabling their
additional processing and obtain separate consent where required.

## 1. Visiting the website and contacting us

Our public website contains static information, legal documents, support details,
and app configuration. We do not add website analytics, an advertising SDK, a
sign-up form, or a website acceptance receipt. Visiting a page does not create
a Daily Pause account. Links to email support open your chosen mail application;
your message is sent only if you send it.

Cloudflare hosts and delivers this site and configuration and provides network
security. Requests expose connection information such as IP address, requested
path, request time, browser or client information, and response status. The
provider may process request and security information and use security cookies
where its protections require them. This is distinct from an analytics or
advertising choice made by Daily Pause.

If you contact support, we process your message, contact details, and any app,
device, screenshots, or logs you choose to provide to answer the request and
investigate the relevant problem. Avoid sending usable account credentials,
payment-card details, or unrelated personal information.

## 2. Puzzle play and information on your device

Puzzle generation happens locally using the puzzle date and supported generator
versions. We do not send your identity to a service to generate each puzzle.
The app contacts the configuration service to check available versions and
schedules; those requests expose the connection information described above.

The app saves puzzle questions, your board entries and marks, completion
progress, preferences, cached account and unlock information, and pending
reward claims on your device. An offline claim contains the completed board
and puzzle, date, account, and claim references so it can be validated when
connectivity returns. It is tied to the account for which it was authorised.

On iPhone, account credentials and the account delivery journal use the system
Keychain; puzzle progress is stored separately. This is not a general cloud
backup of every board. Clearing app data, changing devices, or removing the app
can lose local information; credential survival after reinstall is not guaranteed.

## 3. Guest and Apple-linked accounts

When the app first connects to our account service, it can create a guest
account. We create a random account identifier and creation record and issue
private session and guest-recovery credentials. The service keeps credential
hashes, validity, and use records rather than the usable credential values
returned to your device. A guest identifier is pseudonymous; it does not mean
that all associated activity is unidentifiable.

If you choose Sign in with Apple, Apple supplies a signed identity assertion.
We verify it and retain the Apple identifier needed to recognise your Daily
Pause account. The current flow does not request your name or email address
for that purpose, and we do not receive your Apple password. Apple handles
its sign-in interaction under its own privacy practices.

Linking normally associates the guest wallet and server history with that Apple
identifier. An identity already linked to another Daily Pause account does not
silently merge the accounts.

## 4. Completions, stars, and access records

For an eligible reward, the app sends the solved board, puzzle and version
references, reward date, account-bound authorisation, and claim reference to our
service. We validate the board and eligibility. The reward route retains
completion metadata and a hash of the proof, rather than the raw solved board
as a server progress save.

The account service maintains the confirmed star balance, earning and spending
history, reward authorisations, completion records, and supported pack or
past-day unlocks. These records prevent duplicate rewards and repeated charges
and restore confirmed access to the appropriate account. Expired authorisations
or transaction history may remain associated with those records after they
stop allowing a new claim.

A pending local claim is not an additional server balance. Server time and the
original authorisation determine whether a delayed claim remains eligible.
Local claims can remain until submitted, rejected, expired, or cleared through
account handling.

## 5. Payments and advertising status

Real paid purchases, paid subscriptions, publisher advertising, and live
ad-funded rewards are not enabled at the date of this edition. We do not
currently collect payment-card information or run a live purchase flow. This
notice does not give permission to enable those features without their required
information, choices, and store confirmation.

If store purchases are offered, the store will handle payment details under its
own practices. Our intended verification service uses transaction and product
identifiers, signed transaction or receipt information, purchase or subscription
status and dates, and an association with the appropriate Daily Pause account
for access, restoration, fraud prevention, and reconciliation. These records
would not give us your full payment-card details. We will explain the offered
flow before enabling it.

If publisher ads or verified rewarded ads are offered later, the app will explain
the provider and applicable privacy choices. An account-bound reward reference
may be sent to the ad provider and returned through its verification service to
confirm the correct account and reward. Advertising software can process IP
addresses and approximate location, device or app identifiers, software details,
ad views and interactions, performance information, and diagnostics. A
non-personalised ad can still use device storage or identifiers. Separate
consent, where required, must be obtained before the relevant processing;
accepting Terms or acknowledging this notice does not provide it.

Designated Beta builds may show Google sample ads under their Beta notice.
Those samples do not grant spendable stars or past-day access and are separate
from a public live-ad offer.

## 6. Technical records and agreement receipts

Our services and network providers receive connection information, including
IP addresses, request paths and times, and response status. The account service
uses time-limited hashed rate-limit buckets based on IP addresses or account
identifiers to prevent abuse. Application error records contain request paths
and error categories; the application error handler does not intentionally log
request bodies, bearer credentials, Apple identity assertions, or signed
purchase receipts. Providers can also process operational and security records.

The current app agreement mechanism keeps Terms acceptance, Privacy Notice
acknowledgement, document versions, and the time of those actions in local app
preferences. It is not currently uploaded to the account service as a server
receipt. Removing that storage or receiving a revised required edition can
require the actions again. It is not an advertising consent record.

We do not request precise location for puzzle generation or the time-based sun
and moon display. The current app does not request Apple's cross-app tracking
permission. Any future permission or related processing must be explained at
the appropriate time.

## 7. Purposes and applicable grounds

We use the information described here to deliver requested account, puzzle,
reward and unlock services, provide the website and configuration, respond to
support and privacy requests, diagnose relevant faults, prevent misuse, protect
legal rights, and comply with applicable legal duties.

Where GDPR or similar requirements apply, information objectively necessary for
a requested account and reward service is processed to perform that arrangement.
Proportionate website security, fault investigation, support, and protection of
legal rights rely on legitimate interests, subject to your rights and the
applicable balancing requirements. Specific statutory recordkeeping or
disclosure relies on the relevant legal obligation. Optional processing that
requires consent relies on a separate consent, withdrawable without affecting
earlier lawful processing.

Terms acceptance is not a blanket permission for processing. Under applicable
Hong Kong privacy law, an unrelated new purpose requires prescribed consent
unless a lawful exception applies. Using the app or contacting support does
not enrol you in marketing or authorise publication of an identifiable testimonial.

## 8. Recipients and international processing

Authorised Versava personnel handle records for support, security, account
administration, relevant fault investigation, and privacy requests. Cloudflare
supplies the account service, database, configuration, website delivery, and
related operational security. Apple supplies optional sign-in and any enabled
store transaction flow. Communications providers handle support messages.
Google handles sample-ad processing in designated Beta builds; any later public
advertising processing will be separately disclosed. Information necessary for
a legal duty or claim may be provided to the relevant authority or adviser,
subject to applicable restrictions.

We do not sell puzzle history or account records, or provide them to a third
party for targeted advertising. This does not mean that an enabled ad provider
would receive no technical information; section 5 explains the distinction.

Versava is based in Hong Kong and providers operate internationally. Information
may be processed in Hong Kong, the European Economic Area, or other countries
where the relevant providers or authorised personnel operate. We do not promise
that all information remains in your country. Contact our Privacy Contact for
information about destinations and the transfer arrangements applicable to your
records. International processing remains subject to applicable data-protection
requirements.

## 9. Retention and account requests

Local progress remains until app storage handling, a reset, or device controls
remove it. Pending reward claims leave their delivery queue when no longer
eligible or after confirmation; related local puzzle progress can remain.

The service regularly cleans expired session and guest credentials, time-limited
rate-limit buckets, and expired sign-in challenges no longer needed by a session.
This does not delete the account, wallet, completion history, or unlocks.

We retain account and access records for providing and reconciling the account's
services, investigating relevant misuse or disputes, and complying with legal
duties. We have not implemented a fixed automatic account-ledger deletion period.
Support and operational records are kept for their relevant purpose; retention
for a legal duty or claim must be limited to the necessary information and period.
A retention decision takes account of whether the account or request remains
active, an unresolved access or security issue, applicable obligations, and
relevant claim periods rather than assuming every record needs the same duration.

Signing out revokes relevant credentials but does not delete server records.
Uninstalling or losing an unlinked guest credential does not automatically
delete them. Contact our Privacy Contact for access, correction, account closure,
or deletion requests. We assess and respond under applicable law, including any
lawful retention requirement, and may need to verify ownership without asking
you to email usable credentials. Apple and other providers separately control
information retained under their own practices.

## 10. Choices, rights, and security

Apple linking is optional. A guest account does not require an Apple identity;
online verification and an account are necessary to earn or redeem
server-confirmed stars. Free puzzle play can continue offline when the required
local content is available. Optional advertising or other consent choices must
remain separate from the agreement and information acknowledgement.

Hong Kong law provides access and correction rights. Where applicable law
provides them, you can also request erasure, restriction or portability, object
to legitimate-interest processing, withdraw consent, and complain to the relevant
data-protection authority. Contact support@versava.net about your records. We
may need to verify that the request concerns your account and respond within
the applicable statutory period.

We use encrypted connections, credential hashing, iPhone Keychain storage,
authentication, and restricted administrative access to reduce unauthorised
access. No system provides an absolute security guarantee. Protect your device
and contact us if you suspect that it or your account is compromised.

## 11. Changes and contact

Revisions identify their edition and date. We will give additional notice of
material changes where required, and obtain separate consent for new processing
where law requires it. A later paid or advertising feature is not authorised
merely by acknowledging this notice.

Privacy correspondence: support@versava.net, or Privacy Contact, Versava Limited,
Unit 1319, 13/F, One Midtown, 11 Hoi Shing Road, Tsuen Wan, Hong Kong.
