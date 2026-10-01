# Daily Pause Beta Privacy Notice

Version: 2026-10-01-beta.2 · Updated: 1 October 2026

This notice explains how Versava Limited, a company registered in Hong Kong
(Versava, we, us, or our), handles personal information during
invited testing of Daily Pause, listed as Daily Pause: Pocket Puzzles.
You and your mean the person participating in this pre-release testing
programme, which we call the Beta.

For privacy questions, access or correction requests, or requests concerning
your account, contact support@versava.net, or write
to Privacy Contact, Versava Limited, Unit 1319, 13/F, One Midtown, 11 Hoi Shing
Road, Tsuen Wan, Hong Kong.

Acknowledging this notice confirms that it has been provided to you. It is not
consent to advertising, tracking, or unrelated processing. The separate Daily
Pause Beta Testing Terms govern participation.

## 1. Puzzle play and information on your device

Puzzle generation happens on your device, using the puzzle date and supported
generator versions. We do not send your identity to a remote service to generate
each puzzle.

The app saves puzzle questions, your board entries and marks, completion
progress, preferences, cached account and unlock information, and pending reward
claims locally. A pending reward claim contains the completed board and its
puzzle, date, account, and claim references so it can be checked when connectivity
returns. The claim is tied to the account for which it was authorised.

On iPhone, account credentials and the account delivery journal use the system
Keychain; puzzle progress is stored separately on the device. Local storage is
not a general cloud backup of every board. Clearing app data, changing devices,
or removing a build may lose local information. Credential survival after a
reinstall is not guaranteed.

The app contacts a static configuration service to check supported generator
versions and schedules. Those network requests also expose normal connection
information to the hosting and network providers.

## 2. Guest and Apple-linked accounts

When you first connect to our account service, it can register a guest account.
We create a random account identifier, record its creation time, and issue
private session and guest-recovery credentials. The service stores hashes of
these credentials, together with their validity and use records, rather than
the usable credential values returned to your device. A guest identifier is
pseudonymous; it does not mean that all activity is unidentifiable.

Each account also has a stable, non-secret support code. You can copy that code
when asking us for help so authorised staff can locate the correct account. A
support code alone cannot sign in, recover a lost guest account, or authorise a
wallet change. You may choose an optional player nickname and change or clear
it in Account. If you choose Sign in with Apple and your account has no player
nickname, we can use the name Apple provides as an editable default. Apple
usually provides this name only during your first authorisation. A name you
have already chosen is retained. Do not use another person's identity or
include sensitive information in your nickname.

The player nickname is stored with your account, cached on your device, and
shown to authorised staff for account support. An Apple-provided default may
be kept with your authenticated session in the device Keychain until the
account service confirms it. A player nickname, including a name provided
by Apple, is not proof of identity or a credential for accessing an account.

We record when the account was first created and its latest activity observed
by our online service. Recent session-use and expiry times help us check access
and investigate problems. These records do not show your last offline play
or identify a particular physical device. The staff account views do not
collect device fingerprints or display raw Apple account identifiers, credential
hashes, session secrets or IP addresses.

For support, authorised staff may add a private label and notes, including the
name or relevant contact context you provide, to associate your support code
with a support request or invited tester. Those notes are not shown to players
or published. Staff are instructed to record relevant support context only,
not passwords, usable credentials or unrelated sensitive information. We record
administrative changes, their reason and staff reference, including corrective
star grants and pausing or restoring new rewards and redemptions. These controls
preserve existing stars and unlocks; a paused account can still use existing
access and contact support.

If you choose Sign in with Apple, Apple supplies a signed identity assertion.
We verify it and retain the Apple account identifier needed to recognise your
Daily Pause account. We also request the optional name described above to
provide a default player nickname. That name is separate from the signed
identity assertion and is not used to verify your identity. We do not request
your email address or receive your Apple password. Apple handles your sign-in
interaction under its own privacy practices.

Linking a guest account normally associates its existing wallet and server
history with that Apple identifier. An Apple identity already linked to another
account is not silently merged with the guest account.

## 3. Rewards, wallet, and unlock records

To validate an eligible daily reward, the app sends the solved board, puzzle
and version references, reward date, account-bound authorisation, and a claim
reference to our service. We check the board and reward eligibility. The reward
route stores completion metadata and a hash of the submitted proof, rather
than retaining the raw solved board as a server progress save.

We maintain your confirmed star balance, the history of earning and spending
stars, reward authorisations and completion records, and supported pack and
past-day unlocks. These records prevent duplicate rewards and repeated charges
and allow confirmed access to be restored to the appropriate account. Some
expired authorisations and historical transaction records remain linked to that
history even after they stop allowing a new claim.

If you explicitly choose to switch from a guest account to an existing Apple
account, those accounts and their balances remain separate. Where the app
supports saving a guest account for a later switch back, its private credential
is stored in the iPhone Keychain. It remains subject to its validity, revocation
and device-storage limits; a support code is not a substitute. Switching
accounts does not combine reward claims or upload every saved puzzle board.

Offline claims may remain on your device until successfully submitted, rejected,
expired, or cleared through account handling. A pending local claim is not an
additional server balance. Server time and the original authorisation determine
whether a delayed claim can still be credited.

Real paid purchases and paid subscriptions are disabled in this Beta
version. There is no current payment-card collection or live purchase flow.
If payment testing or real purchases are offered later, we will explain the
transaction data and applicable terms before enabling them.

## 4. Test ads and technical information

Publisher advertising and real ad-funded rewards are disabled. Designated
Beta builds can display clearly labelled Google sample ads. An optional sample video
does not credit spendable stars or unlock a day, and this sample flow does not
send an account-bound production reward ticket to Google.

When a sample ad is requested, Google's Mobile Ads software may process IP
addresses and approximate location derived from them, app or device identifiers,
software information, ad views and interactions, performance information, and
SDK diagnostics. Sample advertising still involves this technical processing;
it is not a promise that Google receives no information. The app requests
non-personalised ads and does not request Apple's cross-app tracking permission
or precise location permission. Non-personalised ads can still use device
storage or identifiers.

Acknowledging this notice or accepting the Terms is not an advertising consent
choice. Production advertising, its privacy choices, and verified ad rewards
remain separate developing features. Any consent required for optional
advertising or tracking must be obtained separately before that processing.

Our account and configuration services and their network providers receive
connection information, including IP addresses, request paths and times, and
response status. The account service uses time-limited hashed rate-limit
buckets derived from IP addresses or account identifiers to prevent abuse.
Service error records contain request paths and error categories; the application
error handler does not intentionally log request bodies, bearer credentials,
Apple identity assertions, or signed purchase receipts. Cloud and network
providers can also process operational request and security information.

## 5. TestFlight invitations, diagnostics, and your reports

For email invitations, we and Apple use the email address supplied for your
invitation, tester details, group membership, and invitation status. These are
separate from the identifier used for Sign in with Apple inside Daily Pause.
Participation does not enrol you in marketing.

Apple automatically collects and shares TestFlight installation, usage, device
and operating-system information, and crash reports with us; testers cannot
opt out of that TestFlight collection. These records may include your name and
invitation email. Feedback and screenshots you submit are voluntary. We use
TestFlight reports to evaluate and improve the app and related products, and
do not share those reports with third parties.

If you contact us directly, we process your message, contact details, and the
build, device, screenshots, or logs you choose to provide. Avoid including
unrelated personal information or secrets in a report.

## 6. Terms acceptance and notice acknowledgement

The current app stores a local record of your Terms acceptance and Privacy
Notice acknowledgement, the document versions, and the time of your actions.
This record is kept on your device in app preferences. It is not currently
uploaded to our account service or protected by a server receipt.

The record lets the app determine whether the current documents have been
accepted and provided. Clearing its storage or installing a materially revised
edition may require the actions again. Acknowledgement does not establish that
you consent to unrelated processing.

## 7. Purposes and applicable grounds

We use the information described above to provide requested account, puzzle,
reward and unlock functions; administer invited testing; diagnose and improve
the app; respond to support and privacy requests; prevent misuse; and comply
with applicable legal duties.

Where GDPR or similar requirements apply, processing objectively necessary for
your requested account and reward service is based on performance of that
arrangement. Testing administration, proportionate fault investigation,
security, support, and protection of legal rights rely on our legitimate
interests, subject to your rights and the applicable balancing requirements.
Specific statutory recordkeeping or disclosure relies on the relevant legal
obligation. Optional processing that requires consent relies on a separate
consent, which can be withdrawn without affecting earlier lawful processing.

Accepting the Terms is not a blanket consent to all processing. Under applicable
Hong Kong privacy law, an unrelated new use requires prescribed consent unless
a lawful exception applies. We do not use participation as permission to send
marketing or publish an identifiable testimonial.

## 8. Recipients and international processing

Authorised Versava personnel access records for testing, support, security,
account administration, and privacy requests. Cloudflare supplies our account
service, database, configuration delivery, and related operational security.
Apple supplies TestFlight and optional Apple sign-in. Google handles the
sample-ad processing described above. Communications providers handle messages
you send to our support address. Information necessary for a legal obligation
or legal claim may also be disclosed to the appropriate authority or adviser,
subject to applicable restrictions.

We do not sell your puzzle history or account records, or provide them to a
third party for targeted advertising. The Google technical processing described
in section 4 remains relevant even though live ads are disabled.

Versava is based in Hong Kong, and service providers operate internationally.
Information may be processed in Hong Kong, the European Economic Area, and
other countries where the relevant providers or authorised personnel operate.
This is not a promise that all information remains in your country. Contact
our Privacy Contact for information about destinations and the transfer
arrangements applicable to your records. International processing remains
subject to the requirements of applicable data-protection law.

## 9. Retention and leaving the Beta

Local progress remains on your device until it is removed by app storage
handling, a reset, or your device controls. Pending reward claims are removed
from their delivery queue when no longer eligible or after confirmation;
associated local puzzle progress can remain.

Our service regularly cleans up expired session and guest credentials,
time-limited rate-limit buckets, and expired sign-in challenges that are no
longer needed by a session. This cleanup does not delete the account, wallet
history, completion records, or confirmed unlocks.

We retain account and access history while administering the Beta account,
reconciling rewards, investigating relevant problems or misuse, or handling
rights and disputes. We have not set a fixed automatic deletion period for
those beta records. Optional nicknames, support codes, service-activity records, private support
notes and administrative audit history are retained for the account, support,
security and accountability purposes described above. Clearing your nickname
does not erase a relevant earlier audit or support record. Invitation, support,
and diagnostic records are retained
for the relevant testing, support, security, and legal purposes; they do not
all disappear when a build expires. Any continued retention for a legal duty
or claim must be limited to the information and period necessary for that
purpose.

Signing out revokes the relevant credentials but does not delete server records.
Uninstalling Daily Pause, losing a guest credential, or choosing Stop Testing
in TestFlight does not automatically delete them either. There is currently no
automatic account-deletion control in this beta build. You can request access,
correction, account closure, or deletion by contacting our Privacy Contact.
We assess and respond to requests under applicable law, including any lawful
retention requirement. Apple and Google separately control information they
retain under their own practices.

## 10. Choices, rights, and security

Testing and feedback are voluntary. You can stop testing or decline optional
Apple linking. A first server account and online verification are necessary to
earn or redeem server-confirmed stars; a guest account does not require providing
an Apple identity. Free puzzle play can continue offline where the necessary
local content is available.

Hong Kong law provides rights of access and correction. Where applicable law
provides them, you may also request erasure, restriction, portability, object
to legitimate-interest processing, withdraw consent, and complain to the
relevant data-protection authority. Contact
support@versava.net about your records or requests.
We may need to verify that a request concerns your account, and respond within
the applicable statutory period. Do not send your usable account credential
or Apple password by email.

We use encrypted connections, credential hashing, device Keychain storage,
authentication, and restricted administrative access to reduce unauthorised
access. No system provides an absolute security guarantee. Use a device you
control and contact us if you suspect that your account or device has been
compromised.

## 11. Changes to this notice

Revisions will identify their version and date. We will give additional notice
of material changes where required, and obtain separate consent for new
processing where the law requires it. A later paid, advertising, or public-release
feature is not authorised merely by acknowledging this beta notice.

Privacy correspondence: support@versava.net, or
Privacy Contact, Versava Limited, Unit 1319, 13/F, One Midtown, 11 Hoi Shing Road,
Tsuen Wan, Hong Kong.
