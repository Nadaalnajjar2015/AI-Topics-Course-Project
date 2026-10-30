MOCK DATA – fictional, for a student prototype

# Regulatory Reporting product guide

## Overview

camt.053 and custom daily and monthly central-bank reports. Cedar Payment Systems operates this fictional product. New circulars are proposed changes; this guide describes the baseline configuration.

## Message types and key fields

camt.053 statements and custom regulatory reports. Statement elements include `<Stmt>`, `<Ntry>`, `<Amt>`, `<CdtDbtInd>` and `<BookgDt>`.

## Validation rules

1. RPT-R01: Reconcile daily totals and monthly summaries with camt.053 statement entries.
2. RPT-R02: BANK-A daily reconciliation runs at 18:00; BANK-D monthly totals follow its local configuration.
3. RPT-R03: Invalid report files yield FF01; unspecified gateway failures use MS03 and need investigation.

## Rejection handling

- FF01: Invalid file format. The file or message does not conform to its configured format.
- MS03: Reason not specified. The reporting institution or gateway did not provide a specific reason.
- TM01: Cut-off time passed. The instruction arrived after the configured cut-off.

Use the exact reason_codes.md section as evidence. Never turn an unknown reason into an asserted cause.

## Configuration per client

- BANK-A: country=Country X; message_standard=pacs.008.001.08; cutoff_time=14:00; amount_limit=100000; local_rules=['Creditor address mandatory for amounts above 10,000.', 'Daily reconciliation report at 18:00.']
- BANK-D: country=Country Y; message_standard=pacs.008.001.10; amount_limit=200000; cutoff_time=16:00; local_rules=['Validate creditor bank identifiers.', 'Produce monthly regulatory totals.']

Only clients listed above enable this module. Message standard, amount limits, enabled fields and cut-off settings are client configuration, not universal ISO rules.

## Reports

Provide a daily audit of references, statuses, reason codes and processing times. Reconcile accepted and returned entries before preparing monthly summaries. Record rejected instructions separately from settled totals.
