# Daily Pause Beta Privacy Notice

Version: 2026-10-03-beta.10 · Updated: 3 October 2026

This notice explains how Versava Limited, a company registered in Hong Kong
(Versava, we, us, or our), handles personal information during
invited testing of Daily Pause, listed as Daily Pause: Pocket Puzzles.
You and your mean the person participating in this pre-release testing
programme, which we call the Beta.

This edition covers the revised diamond-unit, daily-claim, hint and Plus
subscription configuration prepared for an upcoming Beta build. Processing for
a new feature begins only when the corresponding app and service controls are
ready; this notice alone does not enable a purchase or change a wallet.

For privacy questions, access or correction requests, or requests concerning
your account, contact support@versava.net, or write
to Privacy Contact, Versava Limited, Unit 1319, 13/F, One Midtown, 11 Hoi Shing
Road, Tsuen Wan, Hong Kong.

Acknowledging this notice confirms that it has been provided to you. It is not
consent to advertising, tracking, or unrelated processing. The separate Daily
Pause Beta Testing Terms govern participation.

## 1. Puzzle play and information on your device

Daily and Past puzzle generation happens on your device, using the puzzle date
and supported generator versions. Reviewed pack questions are supplied in the
app's released content bundle. We do not send your identity to a remote service
to generate each puzzle.

The app saves puzzle questions, your board entries and marks, completion
progress, preferences, cached account and unlock information, and pending reward
claims locally. A pending star or diamond claim contains the completed board
and its puzzle, date, release or version, account, and retry references so it can
be checked when connectivity returns. The claim is tied to its account; changing
accounts does not transfer it to a different wallet.

On iPhone, account credentials and the account delivery journal use the system
Keychain; puzzle progress is stored separately on the device. Local storage is
not a general cloud backup of every board. Clearing app data, changing devices,
or removing a build may lose local information. Credential survival after a
reinstall is not guaranteed.

The app contacts a static configuration service to check supported generator
versions and schedules. Those network requests also expose normal connection
information to the hosting and network providers.

The selected pack sort order is saved in device preferences. This presentation
setting is not sent to our account service. The app uses confirmed permanent
pack grants to show owned packs first; temporary subscription access remains
separate from permanent ownership.

The first free hint can be used offline. The app saves the number of delivered
hints with the puzzle identifier, immutable question revision, and account
identifier, or a device-local allowance before an account exists. This record
is separate from the board entries, so undoing or restarting a board does not
reset it. When a first guest account is registered, the device-local allowance
can carry over instead of providing another free hint. Confirmed account hint
grants are also reconciled with the service when online. Local delivery and
retry references prevent a confirmed grant from being delivered twice.
For a pending delivery and the latest delivered cue, local puzzle storage also
keeps the highlighted cell index, whether it identifies a mistake, and a hash
of the board state so the same cue can be restored on the matching board.
These cue records stay in the device's puzzle storage, separate from the
account Keychain cache on iPhone. The account delivery journal also keeps pending
diamond proofs, references for already acknowledged proofs, and exchange retry
references. Pending currency-delivery records can include Apple's signed
transaction evidence, transaction and product identifiers, and the associated
Daily Pause account token. On iPhone these account-bound records use the Keychain;
the separate product-price cache contains product metadata and fetch times.

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
preserve existing wallet balances and unlocks; a paused account can still use
existing access and contact support.

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

To validate an eligible star or diamond reward, the app sends the solved board,
puzzle and version or release references, puzzle date, account authentication,
and a claim or retry reference to our service. Today star claims also use their
account-bound reward authorisation. We check the board, date and reward
eligibility, including existing access when a Past proof is submitted. The
reward routes store completion metadata and a hash of the submitted proof,
rather than retaining the raw solved board as a server progress save.

We maintain your confirmed star and diamond balances, separate histories of
earning and spending them, lifetime diamond milestone awards, the eligible-from
UTC date derived from your account's original server creation time, verified
completed puzzle dates and their releases, exchange amounts and retry references,
reward authorisations, and supported pack and past-day unlocks. These records
calculate the seven-consecutive-completed-date diamond milestones and prevent
duplicate rewards or repeated charges. Past proofs can count towards eligible
diamond chains but do not award daily stars; pack and practice completion do not
count towards the chains. They also help reconcile confirmed access with the
appropriate account; they do not guarantee recovery of lost credentials. Some
expired authorisations and historical transaction records remain linked to that
history even after they stop allowing a new claim.

The diamond-unit transition retains historical ledger rows and records their
currency version. A one-time audited adjustment adds nine times the existing
confirmed balance so each old diamond becomes ten new diamonds without rewriting
earlier entries. Lifetime milestone counters and previously rewarded date
coverage are retained in the applicable unit to prevent another award for those
dates. New milestone grants record ten new diamonds per eligible seven-date
group within verified completed-date chains, accounting for dates already used
by earlier awards. Reading a wallet or applying
the unit transition does not itself award a completion milestone.

For the separate free Today claim, the service records the account, current
server UTC date, claim reference, grant time and one-star ledger credit. It
checks that the date has not already been claimed. This online claim does not
submit a puzzle board or require a completion; it remains separate from the
first-puzzle and full-set completion records. An unclaimed free allowance cannot
be carried to a later UTC day using the device clock.

A pack-unlock request sends the account, pack identifier, configured offer
revision, required price type, expected star and diamond amounts, applicable
currency version and a retry reference. A price type identifies a star-only,
diamond-only or mandatory combined price. The service records the permanent pack
grant, confirmed offer revision, required amounts, operation reference and time.
A combined grant creates both wallet debits in the same transaction. These
records preserve permanent ownership and prevent duplicate grants or charges;
an insufficient balance or rejected changed offer creates no new grant or debit. The local account delivery journal keeps
account-bound retry details for incomplete unlock requests. Shop order and
prices are separate metadata from the immutable puzzle questions.

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

Hint requests send the account, puzzle and question-revision references, the
requested hint number, payment method, and a retry reference. For daily or
pack questions, references also identify the date, release, recipe or pack
needed to validate the question and existing access. The service records the
account, puzzle, revision and question key, hint number, grant method, star
or diamond cost, currency version where applicable, operation reference and
time, plus a verified ad transaction reference where applicable. Star-funded
and diamond-funded hints create the corresponding wallet debit and source
reference. Plus-funded second or third hints retain the verified Apple
environment, transaction and original-transaction references used to authorise
that grant. These records enforce ordered hint usage and prevent repeated
charges; hints from the fourth onwards require a diamond-funded grant. The hint request does not submit your board entries, the suggested
cell or an answer; the app decides which cell to highlight locally.

Production paid purchases and subscriptions remain disabled. Designated
TestFlight builds may offer controlled monthly Daily Pause Plus subscription
tests through Apple's Sandbox when our testing controls permit it. Sandbox
transactions do not charge real money. Supported star and diamond consumables
may also be tested in designated Sandbox builds when separate controls permit
them; production currency checkout remains disabled. The one-time Remove Ads
product may also be tested in designated Sandbox builds when its separate
controls permit it, without real-money charges. Production Remove Ads checkout
and individual cash-pack checkout, including cash-pack purchase tests, remain
disabled. Remove Ads test transactions use the same signed verification,
account association, delivery, restore and revocation records described below;
this does not enable publisher ads or turn sample videos into verified rewards.
Direct diamond pack unlocking uses confirmed wallet diamonds rather than a
cash purchase. A future production offer will need its own clear offer and
applicable privacy choices before it is enabled.

A supported currency bundle can include a displayed promotional bonus. Its
configured total, including that bonus, is recorded as the one fulfilled quantity
for the verified transaction. New designated offers may total 50, 200 or 500
stars, or 10, 40 or 100 diamonds. Previously fulfilled transaction quantities
remain recorded as originally delivered; a changed offer does not rewrite them
or deliver its bonus again during retry or restore.

When supported purchase testing is enabled, Apple processes the store
confirmation and supplies signed transaction information. The app sends it to
our service to verify the product, environment, transaction and association
with the correct Daily Pause account before confirming access or currency
delivery. Apple receives a Daily Pause account token with the purchase request
and returns it with the transaction information. This token is the app account's
identifier, not an Apple password or a requirement to link that app account to
Sign in with Apple. Apple does not give us your payment-card details or Apple
password. We retain account, product, transaction and original-transaction
identifiers, Sandbox or Production environment, signed time, and relevant expiry,
upgrade, refund or revocation status. Verified notification identifiers and times
help process Apple status updates without repeating them.

For the revised Plus product, these records associate verified subscription
coverage with the correct Daily Pause account. We retain the supported product,
environment, transaction and original-transaction references, coverage start and
end, and refund or revocation status. Eligible UTC calendar dates determine the
banked two-diamond allowance; the service records which dates were credited,
their transaction references, amounts and ledger source references so overlapping
periods or repeated claims cannot duplicate the grant. A manual claim can collect
unclaimed covered dates through the server's current date after ordinary
cancellation or expiry; it is not proof that you visited or solved a puzzle on
each of those dates. Refund or revocation can change valid coverage. These
subscription diamonds are separate from completed-puzzle milestone awards.

For active, server-verified Plus, the service can authorise the eligible daily
one-star bonus, a permanent unlock for a selected supported Past date, or the
second and third hints without loading an ad. The service retains the account,
claim purpose, date, release or question references, operation reference and
grant time, together with the verified Apple environment, transaction and
original-transaction references. These records share the existing daily bonus
and hint limits and prevent duplicate grants. A Plus claim does not create a
fictitious Google ad event or send a reward ticket to Google. A confirmed
selected-date Past grant remains separate from the currently active subscription;
no blanket local archive grant is created.

The new Plus subscription does not establish all-pack or automatic-ad-free access,
and banked paid diamonds do not establish an active Plus period. Verified
historical rights under the earlier all-packs subscription remain separate. Renewal, expiry, refund and refund-reversal evidence can update the
appropriate product's status. A notification without the account token can be
matched only to an already recorded subscription with the same verified
environment, original transaction identifier and supported product. Restore
requests check eligible signed evidence for the associated account; they do not
move coverage to another account or repeat credited daily allowances.
Subscription status, coverage and claimable amounts are cached with the account
on your device; cached prices are separate and never establish access or a
spendable balance. Test status updates can be delayed, and current testing does
not guarantee recovery of every missed provider notification. Sandbox records
remain identified as test records and do not represent paid ownership in a
future public release.

For consumable currency delivery, the service additionally retains the signed
Apple transaction evidence and its hash, purchase and verification times, the
fixed currency and quantity, the fulfilled transaction identifier, related
wallet credits, and refund or revocation evidence. A transaction can be credited
only once for its verified environment and identifier. Delivery records support
safe retries; an ordinary restore does not replace spent consumables. Refund
status continues to be recorded while new checkout is disabled. Handling refunds
after currency has been spent or exchanged remains unresolved and is a release
gate, not an enabled automatic negative-balance adjustment.

The verified wallet and ad-free entitlement are cached on the device, using
the Keychain on iPhone. For currency delivery, the app reads unfinished
transactions from StoreKit and keeps account-bound signed evidence and retry
records in that Keychain delivery journal. It acknowledges the exact StoreKit
transaction only after the service confirms its durable credit and the wallet
response is saved locally. A failed upload or acknowledgement can leave a
record pending for another check; device-storage or credential loss can limit
recovery. Other supported purchase or restore requests derive retry references
from signed StoreKit evidence. Remove Ads has no ordinary subscription expiry;
refund or revocation status can still affect its access. Sandbox records remain
identified as testing records and do not represent a paid purchase in a future
public release.

## 4. Test ads and technical information

Publisher advertising and real ad-funded rewards are disabled. Designated
Beta builds can display clearly labelled Google sample ads. An optional sample
video does not credit spendable stars, unlock a day or grant a paid hint, and
this sample flow does not send an account-bound production reward ticket to
Google.

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

If verified rewarded-hint testing is separately enabled, its ad request sends
Google an account-bound user identifier and a random, scoped reward reference
that lets our service match the signed completion callback to the requested
question and hint number. The service stores the reward reference and its
hash, account, question and hint references, operation reference, creation and
expiry times, and whether it has been consumed. For an accepted callback, it
records Google's unique transaction reference and the verification time.
Provider callbacks also contain ad and reward parameters used for verification.
The hint grant links that verified event to the account and question; it does
not store the hint content or your board. A sample video or local SDK callback
alone does not grant a paid hint. This account-bound live flow is disabled
while publisher ads and live ad-funded rewards are disabled.

Remove Ads suppresses automatic ad placements while valid; it does not turn an
optional rewarded video into an ad-free grant. Choosing a rewarded video can
still involve the Google processing described in this section.

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
reward, exchange, unlock and hint functions; verify supported Sandbox purchase
access and reconcile incomplete currency delivery; administer invited testing;
diagnose and improve
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
Apple supplies TestFlight, optional Apple sign-in, and Sandbox purchase
processing and transaction status information. Google handles the
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
handling, a reset, or your device controls. Pending star and diamond claims are
removed from their delivery queue when no longer eligible or after confirmation;
associated local puzzle progress can remain. The local hint allowance survives
an ordinary board reset and remains subject to device-storage limits. Confirmed
delivery retry records can be removed from their queue after
reconciliation without removing the account's grant or transaction history.
Pending signed currency evidence can remain in the account delivery journal
until the service confirms delivery and StoreKit acknowledgement succeeds,
or device/account storage handling removes it. Already acknowledged proof and
operation references may remain to prevent a repeated delivery. StoreKit
separately maintains its transaction state under Apple's practices.

Our service regularly cleans up expired session and guest credentials,
time-limited rate-limit buckets, and expired sign-in challenges that are no
longer needed by a session. This cleanup does not delete the account, wallet
history, completion records, confirmed unlocks, hint grants, or purchase history.

We retain account and access history while administering the Beta account,
reconciling rewards, diamond chains, exchanges, hints and transactions,
investigating relevant problems or misuse, or handling
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
earn or redeem server-confirmed stars or diamonds; a guest account does not
require providing an Apple identity. Free puzzle play can continue offline where
the necessary local content is available.

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
