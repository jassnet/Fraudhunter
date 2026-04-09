# Detection Logic Explained

## What this detector is for

The console does not treat every finding as proof that one affiliate is guilty.

The current detector creates review cases for suspicious environments. A case represents a cluster of conversions that share the same:

- date
- IP address
- user agent

This means the detector is environment-centric.

## Stable case identity

- `case_key = hash("conversion_case|date|ipaddress|useragent")`
- `finding_key` is still stored for lineage and recompute history

Operators should triage by `case_key`, not by recompute timestamp and not by a single affiliate projection.

## Why a case can include multiple affiliates or programs

One suspicious environment can touch more than one affiliate or more than one program.

Because of that, the console shows:

- `affected_affiliate_count`
- `affected_affiliates`
- `affected_program_count`
- `affected_programs`

The UI should not flatten an environment case into one affiliate owner.

## Risk meaning

Risk score reflects how unusual the environment pattern is. It does not mean one affiliate is conclusively fraudulent by itself.

The correct operator flow is:

1. open the case
2. inspect environment evidence
3. inspect review history
4. apply a review decision with a reason

## Detail evidence contract

The primary detail table is `evidence_transactions`.

Those rows always match the suspicious environment itself:

- same date
- same IP address
- same user agent

`affiliate_recent_transactions` is secondary context only.

## Review implications

Because settings and recompute generations can change, review state is attached to the stable `case_key`.

This keeps review history attached to the same environment case even when `finding_key` changes across recomputes.
