MOCK DATA – fictional, for a student prototype

# Fictional payment rejection reference

These public ISO 20022 codes are used in invented local processing scenarios.

## AC01

Meaning: Incorrect account number.

Typical cause: The creditor account number is malformed or does not identify an account.

What the bank should do: Confirm the account number with the beneficiary before resubmission.

Modules that produce it: CHQ, ACH, IPS, WAL.

## AC04

Meaning: Closed account.

Typical cause: The creditor account was closed before processing.

What the bank should do: Ask the beneficiary for an active account; do not retry the closed account.

Modules that produce it: CHQ, ACH, IPS, WAL.

## AC06

Meaning: Blocked account.

Typical cause: An account exists but is blocked from the requested operation.

What the bank should do: Contact the account-servicing team to resolve the block before retrying.

Modules that produce it: CHQ, ACH, IPS, WAL.

## AG01

Meaning: Transaction forbidden.

Typical cause: The transaction is forbidden for this account or wallet tier.

What the bank should do: Check account permissions and the KYC tier with the servicing team.

Modules that produce it: ACH, IPS, WAL.

## AM04

Meaning: Insufficient funds.

Typical cause: The debtor account does not have enough available funds.

What the bank should do: Arrange sufficient funds and submit a new authorized instruction.

Modules that produce it: CHQ, ACH, IPS, WAL.

## AM05

Meaning: Duplicate payment.

Typical cause: The instruction duplicates a previously processed reference.

What the bank should do: Check the original result and EndToEndId; avoid paying twice.

Modules that produce it: ACH, IPS, WAL.

## BE04

Meaning: Missing creditor address.

Typical cause: Required creditor address elements are absent.

What the bank should do: Supply Cdtr/PstlAdr with TwnNm and Ctry when the configured rule requires them.

Modules that produce it: ACH, IPS, WAL.

## FF01

Meaning: Invalid file format.

Typical cause: The file or message does not conform to its configured format.

What the bank should do: Validate the message structure against the configured schema version.

Modules that produce it: CHQ, ACH, IPS, WAL, RPT.

## RC01

Meaning: Bank identifier incorrect.

Typical cause: The instructed bank identifier is incorrect.

What the bank should do: Confirm the beneficiary bank identifier before resubmission.

Modules that produce it: ACH, IPS, WAL.

## RR01

Meaning: Missing debtor identification.

Typical cause: Debtor identification required by the configured rule is absent.

What the bank should do: Provide the required Dbtr/Id fields using verified source information.

Modules that produce it: ACH, IPS, WAL.

## MS03

Meaning: Reason not specified.

Typical cause: The reporting institution or gateway did not provide a specific reason.

What the bank should do: Escalate with the reference and timestamp; do not invent a root cause.

Modules that produce it: ACH, IPS, WAL, RPT.

## TM01

Meaning: Cut-off time passed.

Typical cause: The instruction arrived after the configured cut-off.

What the bank should do: Check the local processing window and the next eligible submission time.

Modules that produce it: CHQ, ACH, RPT.
