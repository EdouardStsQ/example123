# Case: NY_SCH routing already partially configured

Covers: box-datalake-expert
Type: happy path

**Pending** — blocked on Tier 2 DB access. Real `source_system`/country-code values for NY_SCH aren't known yet; fixture will use those once queried, not placeholders standing in for real config.

## Given (input state)

NY_SCH's Murex source_system/country-code identifiers, and current state of the Control-M/`diaria.json` config (present, partial, or absent).

## When (action)

Agent checks for an existing routing entry and proposes an addition if missing.

## Then (expected outcome)

A sample day's NY_SCH data appears in the expected RAW tables after the entry is applied.
