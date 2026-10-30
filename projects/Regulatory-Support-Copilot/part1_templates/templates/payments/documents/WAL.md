MOCK DATA – fictional, for a student prototype

# Mobile Wallet product guide

## Overview

Internal API and pacs.008; wallet limits and KYC levels. Cedar Payment Systems operates this fictional product. New circulars are proposed changes; this guide describes the baseline configuration.

## Message types and key fields

Internal wallet API; external transfers map to pacs.008 and pacs.002. Key elements include `<IntrBkSttlmAmt>`, `<Dbtr>`, `<DbtrAcct>`, `<Cdtr>`, `<CdtrAcct>`, `<PstlAdr>`, `<TwnNm>`, `<Ctry>` and `<EndToEndId>`.

## Validation rules

1. WAL-R01: Basic-KYC balance limit is 1,000 for BANK-E and 1,500 for BANK-B before CHG-P-004 takes effect.
2. WAL-R02: A transaction forbidden for the KYC tier yields AG01.
3. WAL-R03: Validate internal API fields before mapping an external transfer to pacs.008.

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

- BANK-B: country=Country X; message_standard=pacs.008.001.08; amount_limit=50000; cutoff_time=14:30; wallet_limit_basic_kyc=1500; local_rules=['Creditor address mandatory for amounts above 10,000.', 'Block debits to frozen accounts.']
- BANK-E: country=Country X; wallet_limit_basic_kyc=1000; message_standard=pacs.008.001.08; cutoff_time=24/7; amount_limit=10000; local_rules=['Basic-KYC wallet balance must not exceed 1,000.', 'Debtor identification is required.']

Only clients listed above enable this module. Message standard, amount limits, enabled fields and cut-off settings are client configuration, not universal ISO rules.

## Reports

Provide a daily audit of references, statuses, reason codes and processing times. Reconcile accepted and returned entries before preparing monthly summaries. Record rejected instructions separately from settled totals.
