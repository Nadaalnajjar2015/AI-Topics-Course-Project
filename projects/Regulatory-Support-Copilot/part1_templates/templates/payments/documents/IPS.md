MOCK DATA – fictional, for a student prototype

# Instant Payment System product guide

## Overview

pacs.008 and pacs.002; 24/7 processing, timeouts and real-time account checks. Cedar Payment Systems operates this fictional product. New circulars are proposed changes; this guide describes the baseline configuration.

## Message types and key fields

pacs.008 customer credit transfers and pacs.002 statuses. Key elements include `<IntrBkSttlmAmt>`, `<Dbtr>`, `<DbtrAcct>`, `<Cdtr>`, `<CdtrAcct>`, `<PstlAdr>`, `<TwnNm>`, `<Ctry>` and `<EndToEndId>`.

## Validation rules

1. IPS-R01: Accept instructions 24/7 with real-time account and duplicate checks.
2. IPS-R02: Require Dbtr/Id for BANK-E; missing identification yields RR01.
3. IPS-R03: Apply configured creditor-address validation; missing mandatory address yields BE04.

## Rejection handling

- AC01: Incorrect account number. The creditor account number is malformed or does not identify an account.
- AC04: Closed account. The creditor account was closed before processing.
- AC06: Blocked account. An account exists but is blocked from the requested operation.
- AG01: Transaction forbidden. The transaction is forbidden for this account or wallet tier.
- AM04: Insufficient funds. The debtor account does not have enough available funds.
- AM05: Duplicate payment. The instruction duplicates a previously processed reference.
- BE04: Missing creditor address. Required creditor address elements are absent.
- FF01: Invalid file format. The file or message does not conform to its configured format.
- RC01: Bank identifier incorrect. The instructed bank identifier is incorrect.
- RR01: Missing debtor identification. Debtor identification required by the configured rule is absent.
- MS03: Reason not specified. The reporting institution or gateway did not provide a specific reason.

Use the exact reason_codes.md section as evidence. Never turn an unknown reason into an asserted cause.

## Configuration per client

- BANK-A: country=Country X; message_standard=pacs.008.001.08; cutoff_time=14:00; amount_limit=100000; local_rules=['Creditor address mandatory for amounts above 10,000.', 'Daily reconciliation report at 18:00.']
- BANK-B: country=Country X; message_standard=pacs.008.001.08; amount_limit=50000; cutoff_time=14:30; wallet_limit_basic_kyc=1500; local_rules=['Creditor address mandatory for amounts above 10,000.', 'Block debits to frozen accounts.']
- BANK-D: country=Country Y; message_standard=pacs.008.001.10; amount_limit=200000; cutoff_time=16:00; local_rules=['Validate creditor bank identifiers.', 'Produce monthly regulatory totals.']
- BANK-E: country=Country X; wallet_limit_basic_kyc=1000; message_standard=pacs.008.001.08; cutoff_time=24/7; amount_limit=10000; local_rules=['Basic-KYC wallet balance must not exceed 1,000.', 'Debtor identification is required.']

Only clients listed above enable this module. Message standard, amount limits, enabled fields and cut-off settings are client configuration, not universal ISO rules.

## Reports

Provide a daily audit of references, statuses, reason codes and processing times. Reconcile accepted and returned entries before preparing monthly summaries. Record rejected instructions separately from settled totals.
