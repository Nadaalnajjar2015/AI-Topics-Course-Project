---
change_id: CHG-P-004
template_id: payments
title: Lower wallet limits for basic-KYC users
issuer: Central Bank of Country X
scope: all
published: 2026-02-14
effective: 2026-04-01
---
MOCK DATA – fictional, for a student prototype

# Lower wallet limits for basic-KYC users

## Requirements

1. From 1 April 2026, all WAL participants must cap basic-KYC wallet balances at 500.
2. WAL must reject transactions forbidden by the updated KYC tier limit with AG01.
3. WAL owners must test both the boundary balance and an amount above the limit.

## Background

Basic-KYC wallets previously used higher client-specific limits.
