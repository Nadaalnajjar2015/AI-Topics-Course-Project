MOCK DATA – fictional, for a student prototype

# Cheque Clearing product guide

## Overview

Cheque images and MICR data; image quality, returns and cut-off times. Cedar Payment Systems operates this fictional product. New circulars are proposed changes; this guide describes the baseline configuration.

## Message types and key fields

Cheque images and MICR; downstream status is local, not a pacs.008 cheque message. Cheque images and MICR identify the cheque. ISO elements in related transfer integrations include `<Dbtr>`, `<Cdtr>` and `<IntrBkSttlmAmt>`.

## Validation rules

1. CHQ-R01: Require readable cheque images and complete MICR data.
2. CHQ-R02: Process BANK-C cheques only up to 15:00; later submissions return TM01.
3. CHQ-R03: Reject an incorrect account with AC01; a closed account with AC04.

## Rejection handling

- AC01: Incorrect account number. The creditor account number is malformed or does not identify an account.
- AC04: Closed account. The creditor account was closed before processing.
- AC06: Blocked account. An account exists but is blocked from the requested operation.
- AM04: Insufficient funds. The debtor account does not have enough available funds.
- FF01: Invalid file format. The file or message does not conform to its configured format.
- TM01: Cut-off time passed. The instruction arrived after the configured cut-off.

Use the exact reason_codes.md section as evidence. Never turn an unknown reason into an asserted cause.

## Configuration per client

- BANK-A: country=Country X; message_standard=pacs.008.001.08; cutoff_time=14:00; amount_limit=100000; local_rules=['Creditor address mandatory for amounts above 10,000.', 'Daily reconciliation report at 18:00.']
- BANK-C: country=Country Y; message_standard=pacs.008.001.08; cutoff_time=15:00; amount_limit=75000; local_rules=['Reject closed creditor accounts with AC04.', 'Cheques after 15:00 return TM01.']

Only clients listed above enable this module. Message standard, amount limits, enabled fields and cut-off settings are client configuration, not universal ISO rules.

## Reports

Provide a daily audit of references, statuses, reason codes and processing times. Reconcile accepted and returned entries before preparing monthly summaries. Record rejected instructions separately from settled totals.
