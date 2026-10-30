MOCK DATA – fictional, for a student prototype

# Automated Clearing House product guide

## Overview

pacs.008, pacs.002 and pacs.004; batch windows, limits and field validation. Cedar Payment Systems operates this fictional product. New circulars are proposed changes; this guide describes the baseline configuration.

## Message types and key fields

pacs.008 customer credit transfers, pacs.002 statuses, pacs.004 returns. Key elements include `<IntrBkSttlmAmt>`, `<Dbtr>`, `<DbtrAcct>`, `<Cdtr>`, `<CdtrAcct>`, `<PstlAdr>`, `<TwnNm>`, `<Ctry>` and `<EndToEndId>`.

## Validation rules

1. ACH-R01: Validate pacs.008 against the client message_standard; use pacs.002 for status and pacs.004 for returns.
2. ACH-R02: Enforce BANK-B amount_limit 50,000 and each client's configured batch window.
3. ACH-R07: Creditor address is mandatory above 10,000 for BANK-A and BANK-B; absence yields BE04.
4. ACH-R08: A closed creditor account yields AC04; insufficient funds yield AM04.

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
- TM01: Cut-off time passed. The instruction arrived after the configured cut-off.

Use the exact reason_codes.md section as evidence. Never turn an unknown reason into an asserted cause.

## Configuration per client

- BANK-A: country=Country X; message_standard=pacs.008.001.08; cutoff_time=14:00; amount_limit=100000; local_rules=['Creditor address mandatory for amounts above 10,000.', 'Daily reconciliation report at 18:00.']
- BANK-B: country=Country X; message_standard=pacs.008.001.08; amount_limit=50000; cutoff_time=14:30; wallet_limit_basic_kyc=1500; local_rules=['Creditor address mandatory for amounts above 10,000.', 'Block debits to frozen accounts.']
- BANK-C: country=Country Y; message_standard=pacs.008.001.08; cutoff_time=15:00; amount_limit=75000; local_rules=['Reject closed creditor accounts with AC04.', 'Cheques after 15:00 return TM01.']
- BANK-D: country=Country Y; message_standard=pacs.008.001.10; amount_limit=200000; cutoff_time=16:00; local_rules=['Validate creditor bank identifiers.', 'Produce monthly regulatory totals.']

Only clients listed above enable this module. Message standard, amount limits, enabled fields and cut-off settings are client configuration, not universal ISO rules.

## Reports

Provide a daily audit of references, statuses, reason codes and processing times. Reconcile accepted and returned entries before preparing monthly summaries. Record rejected instructions separately from settled totals.
