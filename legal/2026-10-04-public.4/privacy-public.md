# Daily Pause Privacy Notice

Version: 2026-10-04-public.4 · Updated: 4 October 2026

This notice explains how Versava Limited, Hong Kong, handles personal information
for the Daily Pause website, public app Daily Pause: Pocket Puzzles, and its
associated services when available. Invited TestFlight builds have a separate
Beta Privacy Notice. Publication does not announce an App Store launch.

Privacy contact: support@versava.net, or Privacy Contact, Versava Limited,
Unit 1319, 13/F, One Midtown, 11 Hoi Shing Road, Tsuen Wan, Hong Kong.
Our appointed EU representative is CHOI, Chong Hing, Fasangartenstr 102,
81549 München; privacy@versava.net. You may contact the representative about
the processing of your personal information and applicable GDPR rights.
Acknowledgement means this information was provided. It is not consent to
advertising, tracking or unrelated processing. Optional consent is separate.

## 1. Website, configuration and local play

The public website provides static app information, legal documents, support
details and configuration. We add no website analytics, advertising SDK,
sign-up form or website agreement receipt. A visit does not create an account.
Cloudflare hosts and delivers the site and configuration and provides security.
Requests expose IP address, path, time, browser or client details and response
status. Cloudflare can process request/security information and security cookies
where its protections require them. Email links send a message only if you send
it through your chosen mail app.

Daily and Past puzzles are generated locally from date and supported generator
versions; reviewed packs are bundled with the app. We do not send your identity
to remotely generate every question. Configuration checks expose ordinary
connection information. We do not request precise location for puzzles or the
time-based sun and moon display.

The app saves questions, board entries, marks, progress, preferences, confirmed
access caches and pending deliveries locally. Pending reward proofs contain
the solved board and puzzle, date, release/version, account and retry references
so the service can verify them later. They remain bound to their account.
On iPhone, account credentials and account delivery journals use Keychain;
boards are stored separately. This is not general cloud backup of every board.
Device changes, removal or clearing storage can lose local records; Keychain
survival after reinstall is not guaranteed.

Pack sorting is a local preference not sent to the service. Local hint records
retain the question revision, account or initial device allowance, hint number,
delivery references and the latest cell cue/board hash. They prevent duplicate
delivery through undo or restart. Pending currency delivery can retain signed
Apple evidence, product and transaction identifiers and account token in the
Keychain journal until acknowledged. The product-price cache separately keeps
product metadata and fetch times.

## 2. Guest and Apple-linked accounts

Connecting can create a guest account with a random identifier, creation time,
session and recovery credentials. The service stores credential hashes and
validity/use times rather than usable returned values. A pseudonymous guest is
not necessarily unidentifiable. Each account has a non-secret support code for
staff lookup; that code does not authenticate or recover the account.

You can choose, change or clear a player nickname. If none exists, an optional
name supplied on your first Apple authorisation can be its editable default.
The service stores the nickname, the app caches it, and authorised staff see it
for support. A pending Apple-provided default can remain in the authenticated
Keychain session until saved. A nickname is not an identity credential.

Optional Sign in with Apple supplies a signed identity assertion, which we
verify. We keep the Apple identifier needed to recognise the account. We request
the optional name, not your email or Apple password. Name is separate from the
signed assertion and is not used to verify identity. Apple handles sign-in
under its own practices. A fresh authorisation can supply a short-lived code
for account deletion and Apple token revocation; it is not a request to email
us credentials. Linking normally retains the guest wallet; an identity already
linked elsewhere does not silently merge accounts.

We retain account creation and observed online activity, session use and expiry
times for service and security. They do not identify a physical device or the
last offline play. Staff views do not show raw Apple identifiers, credential
hashes, session secrets or IP addresses. Authorised staff can add relevant
private support labels/notes and corrective actions with a reason and staff
reference. These records must not contain passwords or unrelated sensitive
information. Pausing new rewards/redemptions does not remove existing balances
or confirmed access.

## 3. Rewards, hints, wallet and access

Reward validation sends solved-board proofs, question and version/release
references, date, authentication and claim/retry references. Today rewards also
use account-bound authorisation. The service checks eligibility, dates and
required access. It retains completion metadata and proof hashes, rather than
the raw solved board as a cloud progress save.

Account records include confirmed star/diamond balances and ledgers, reward
authorisations, free daily claims, eligible-from creation UTC date, completed
puzzle dates/releases, lifetime diamond milestones and previously rewarded
coverage, historical exchanges, hints and confirmed pack/Past grants. They
calculate rewards, prevent duplicates and reconcile access. Reading a wallet
does not award a milestone. Historical currency-unit versions and audited
adjustments remain distinguishable.

Where the newcomer offer is enabled, the service records whether this account
qualifies, the gift policy and fixed 30-star/one-current-diamond amounts, the
currency-unit version, eligibility and collection times, and the collection's
retry reference. Its confirmed credits appear in the corresponding ledgers and
credit lots. These records prevent another collection after retry, relaunch or
Apple linking. Reading the status does not credit the wallet; accounts already
created before eligibility begins are not backfilled.

Pack requests include the account, pack, offer revision, required price type,
star/diamond amounts, currency version and retry reference. Combined prices
create both debits together. Grants retain price and offer evidence; rejected
quotes or insufficient funds do not debit a wallet. Shop metadata remains
separate from fixed pack questions.

Hint requests contain question/revision/access references, hint number, payment
method and retry reference, not your board or locally selected cue. Grants
record cost, method and confirmed source, including eligible ad or Apple
subscription evidence. First hints can be local/offline; paid grants need
verification. Account switching does not merge queued proofs or balances.

## 4. Apple purchases and subscriptions

Apple handles payment-card and store-account details under its practices; we
do not receive your full card details or Apple password. Our verification
service processes signed evidence, Apple environment, product, transaction and
original-transaction identifiers, purchase/renewal/expiry and revocation dates,
account association, quantities, delivery status and refund/reversal evidence.
These records provide the supported offer and prevent repeated delivery. A
bonus is part of the transaction's confirmed quantity, not another repeatable
reward. Previously delivered quantities are not silently rewritten.

Subscription coverage and eligible UTC dates determine banked paid daily
diamonds. Active status separately determines direct Plus reward benefits.
Those claims retain the relevant account/date/question and verified coverage
references. They do not create fictitious Google ad events. Remove Ads and
permanent pack/Past grants remain separate. Restore reconciles supported
evidence with the appropriate account and does not replenish spent currency or
move a transaction away from another existing account. The deletion section
explains explicit restoration of supported current Apple rights on a new account.

Provider status notifications can update recorded purchase lifecycle evidence.
The app does not decide whether Apple approves a refund. A purchase displayed
as successful can remain undelivered until server confirmation. Beta Sandbox
data and billing are governed by the separate Beta notice; a testing purchase
does not buy public-release access.

For the approved unspent-only currency-refund handling, the service records
credit lots, their source and currency-unit version, allocations of later
spending, and a verified refund adjustment and outcome. Only units still
attributable to that purchase can be reversed; no automatic debt is created.
Historical deliveries without that attribution are marked for review rather
than inferred from the current wallet. These journals and raw purchase evidence
are removed with the account; the account export includes explicit journal
fields while omitting raw signed evidence and usable credentials.

## 5. Google ads and separate privacy choices

Where enabled, Google provides automatic ads, optional rewarded videos and
privacy messages. The SDK can process IP address/approximate location, device
and app identifiers, software details, ad views/interactions, performance and
diagnostics. Requests are non-personalised, which can still involve identifiers
or device storage. We do not request Apple's cross-app tracking permission or
precise-location permission. Necessary Google consent/refusal choices precede
permitted ad requests; Terms acknowledgement is not that consent. Required
Ad privacy options in Store and beside placements let you change choices, with
permission rechecked before new requests. Free puzzle play remains available.

An optional reward request sends Google an account-bound identifier and random
scoped reward reference. It contains no Apple name, email, nickname or puzzle
answer. Google's signed callback supplies the reference, provider transaction
and ad/reward parameters. The service verifies them and retains the account,
purpose, date/question/hint, operation and creation/expiry/verification times
with any confirmed grant. A repeated callback or local completion message alone
does not credit another reward. Banner views earn nothing. Labelled sample ads
can process technical information but do not grant currency or access.

Verified Remove Ads suppresses automatic placements; optional rewarded videos
remain separate. Active Plus can cover eligible reward benefits without loading
their videos. Neither benefit removes processing already done by a provider.

## 6. Support, technical records and agreement receipts

Support processes your message, contact details and app/device information,
screenshots or logs you voluntarily provide to answer and investigate it. Avoid
usable credentials, payment-card details and unrelated personal information.
Communications providers handle those messages.

Services and network providers receive connection information such as IP
address, path, time and status. Time-limited hashed IP/account rate-limit
buckets prevent abuse. Application errors intentionally record paths and error
categories, not request bodies, bearer credentials, Apple assertions or signed
purchase evidence. Providers can process their own operational/security records.

Terms acceptance and Privacy acknowledgement, document versions and action time
are stored locally, not currently uploaded as a server agreement receipt.
Deleting that storage or a required revised edition can require fresh actions.
This is separate from advertising consent.

## 7. Export, deletion and retention

Export my data in Account retrieves an authenticated, machine-readable copy of
available server account data: profile, balances/ledgers, completion and reward
records, hints, access grants, purchase/delivery lifecycle, structured account
support actions and credential-use timestamps. It excludes usable credentials,
secret token values and raw provider evidence. Free-text staff/security notes
need separate human review because they can contain another person's details or
security-sensitive information; their internal status does not itself remove
access rights. The export identifies records withheld from its automatic copy.
It does not include every device-only board or messages held by support, Apple
or Google. Request a supplemental review in Account or contact our Privacy
Contact for other personal information. This copy is not a limit on your rights.

When the request-preparation service is enabled, an authenticated Account data
request also queues a copy of the available server account export on our private
NAS for authorised request-handling staff. The account database records the
request reference, preparation state, timestamps and integrity reference; the
private prepared-copy manifest records its expiry.
The prepared copy has the same automatic-export limits described above; free-text
staff/security notes and other requested records still need separate review.
A prepared copy is not an automatic complete response to every access request.

Automated notifications go to our internal privacy mailbox,
privacy@versava.net, when the request is recorded and when preparation is
confirmed. They contain the request reference, support code, environment,
request/due timestamps, status and a protected administration link. They contain
no account export, usable credentials, raw Apple evidence or staff notes. Email
and network providers process the notification metadata. A notification or mail
provider's acceptance is not proof that staff read it or that a reply was sent
to you; delivery retries can repeat a notification. Staff review and their
response to you remain separate, and the authenticated account can check the
request's status.

The prepared NAS export is a restricted request-handling copy, never a public
link or an email attachment. It is available for at most 30 days from durable
preparation. Downloads recheck the live request/account and the acknowledged
copy's integrity; expired, deleted-account, corrupt or unacknowledged copies
are not served. The preparation service checks expiry and recorded account
erasures at startup and regularly while running and removes affected files.
A service interruption can delay physical file cleanup even though expiry
prevents access; deletion is not a promise of instant erasure of offline media.
Prepared exports must not be copied into routine backups; any separately
authorised recovery copy must follow the same limited retention and later erasures.
Already delivered notification messages follow the support/privacy mailbox's
purpose-based handling rather than being recalled by account deletion.

Sharing or saving the export is your choice. The app prepares a temporary file
for the native share/save sheet and removes its temporary copy afterwards.
Copies you save or send are controlled by you and the chosen destination.
On supported web builds, a deliberate download saves the file through your
browser. We do not post exports publicly or log their contents.

Delete account in Account offers a deliberate confirmation and removes the live
account profile, support labels/notes and associated administrative entries,
gameplay/reward records, wallets, hints, unlocks, unclaimed banked Plus
allowances and purchase associations. All
its service sessions and recovery credentials stop working. On confirmation,
the app removes related local account/progress records; other devices' local
copies are not remotely erased. The deletion response does not create another
guest account. Export beforehand if you need a copy.

For linked accounts we attempt Apple token revocation using fresh authorisation.
Unavailable authorisation or revocation does not prevent deleting our records;
the app explains if you also need to remove Daily Pause from Apple's Sign in
with Apple settings. Deletion does not cancel store subscriptions or delete
Apple/Google records. It does not transfer the old wallet, unlocks or unclaimed
allowances to a new account.

An explicit Restore Purchases on a new account can verify current Apple evidence
and associate valid Remove Ads or active Plus with that account. The service
records the product, verified transaction/original-purchase reference,
environment, new account association and restoration status to deliver those
rights and prevent conflicting ownership. Where needed, it asks Apple to update
the app-account token for the current purchase and subsequent subscription
renewals; Apple's past transaction records are not rewritten. New Plus diamond
eligibility begins on the next UTC date and earlier dates are not credited.
These new-account records do not revive deleted personal history or replenish
consumable purchases. No separate deleted-account purchase/day ledger is retained
for this restoration.

After deletion, a hashed, non-authorising retry digest and deletion outcome
permit confirmation of a failed network response for 24 hours without restoring
account access. The receipt contains no account profile, Apple
identifier, raw purchase evidence or usable session credential. Confirmation
ends at the end of that window; scheduled cleanup removes expired receipts.
We do not retain a deleted wallet or transaction history merely to keep it
recoverable.

Cloudflare database recovery snapshots can retain earlier information for the
configured recovery window, up to 30 days. They are restricted recovery copies,
not an active account or a routine source of play or marketing data. A separate
restricted erasure marker expires after 31 days and is removed by scheduled
cleanup. It contains the random account identifier and deletion time, without
profile, gameplay, wallet or purchase
content. This permits operators to reapply subsequent deletions before restored
service resumes. It is a technical recovery safeguard, not a claim of legally
required financial retention. Its expiry is separate from the 24-hour retry
outcome. Operator-held recovery copies must follow the same limited recovery
window and deletion replay; deletion does not instantly erase every provider
snapshot.

While an account remains active, account and delivery history supports requested
services, reconciliation, security and rights. Expired credentials, sign-in
challenges and rate-limit buckets are cleaned regularly. Signing out or
uninstalling does not erase the account. Support correspondence, provider logs
and any genuinely necessary legal-claim records follow their relevant purpose
and documented review rather than an invented blanket retention period. A
specific legal obligation or unresolved claim can require limited information;
it does not justify keeping every account field indefinitely. Ask our Privacy
Contact about records outside the account copy or any applicable exception.

## 8. Purposes, recipients and international processing

We process information to provide requested account, puzzle, reward and paid
access services; verify delivery; handle support/rights; diagnose faults and
protect security/legal rights. Where applicable, necessary requested-service
processing relies on the contract; proportionate support, security and rights
protection rely on legitimate interests; identified legal duties rely on their
legal obligation; optional processing requiring consent uses separate consent.
Consent withdrawal does not affect earlier lawful processing. Terms are not
blanket permission. Unrelated new purposes require the appropriate legal basis
and, under applicable Hong Kong rules, prescribed consent where required.

Authorised Versava personnel handle support, administration, security and
rights requests. Cloudflare Workers provides the account/economy API and D1
stores its account records. Our privately operated NAS hosts the restricted
content studio and pack registry and, where enabled, prepares temporary
account-request copies for staff. Website/configuration and legal sources are
maintained in GitHub and delivered as static pages through Cloudflare Pages
and its security services; Apple handles sign-in, transactions and billing;
Google handles enabled ads and privacy messages; communications providers
handle support and internal request-status notifications. Necessary information can be supplied to authorities or advisers for
an applicable duty or claim, subject to restrictions. We do not sell puzzle or
account histories or supply them for third-party targeted advertising; enabled
Google technical processing is still relevant.

Versava is based in Hong Kong and providers operate internationally. Processing
can occur in Hong Kong, the EEA and other countries where providers or authorised
personnel operate. This is not a local-residency guarantee. Our Privacy Contact
can explain destinations and applicable transfer safeguards or provide the
relevant information. International processing must respect applicable law.

## 9. Choices, rights, security and changes

Apple linking is optional. Account verification is needed for confirmed rewards
and redemptions, but local free play can continue with supported cached content.
Hong Kong law provides access and correction rights. Where applicable, rights
also include erasure, restriction, portability, objection to legitimate-interest
processing, consent withdrawal and complaint to the relevant regulator.

Use Account for the available copy/deletion or supplemental review, or
support@versava.net for other requests. We may reasonably verify ownership
without asking you to email usable credentials. Where GDPR applies, we normally
respond within one month; a lawful extension is explained within that month.
Statutory rights are not limited to the self-service export or waived by deletion
confirmation. Review can redact third-party details or protected security
information where justified; we explain the relevant restriction rather than
withholding all internal records merely because they are internal.

Encrypted connections, credential hashing, iPhone Keychain, authentication and
restricted staff access reduce unauthorised access; no system is absolutely
secure. Protect your device and report suspected compromise. Revisions identify
edition and date, with material-change notice and separate new consent where
required. Contact our Privacy Contact at the email/address above.
