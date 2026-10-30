---
change_id: CHG-P-002
template_id: payments
title: Mandatory structured creditor address in credit transfers
issuer: Central Bank of Country X
scope: country=Country X
published: 2026-02-10
effective: 2026-06-01
---
MOCK DATA – fictional, for a student prototype

# Mandatory structured creditor address in credit transfers

## Requirements

1. From 1 June 2026, all ACH and IPS credit transfers by participants in Country X must carry a structured creditor address in <Cdtr>/<PstlAdr>, including <TwnNm> and <Ctry>.
2. ACH and IPS payments without the mandatory structured creditor address must be rejected with reason code BE04.
3. Participants must test both complete-address acceptance and missing-address rejection before the effective date.

## Background

Earlier local profiles required an address only above configured thresholds.
