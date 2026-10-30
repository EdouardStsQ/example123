# 0024. BOX ACC configs: the BOX ACC expert's review of NY's DEV run — clashes created InValid, untranslatable condition values dropped, a readable config

Date: 2026-10-30
Status: accepted — supersedes the clash mode (a) / (b) question of ADR 0020 point 4 (now always (b)), ADR 0023
point 3's first OPEN case (a condition value with no BOX value) and ADR 0023 point 5 (the SQL step in mode (a))

## Context

The operator reviewed NY's DEV run `gap_20261029_1` with the BOX ACC expert (`02-acc-gap-matrix.md`,
`03-portfolio-properties-report.md`, then the config SQL of PR "NY_SCH DGBOUS ACC config"). The expert found the
files very good — and noted the condition map's value translations (e.g. GBO direction `SAL` → BOX `0` on
`11.65`) as particularly good work. Three changes were asked.

## Decision

`[BOX ACC expert via operator, 2026-10-30]`

1. **Clashing portfolio properties are all created, all `InValid`.** When two or more properties clash in BOX (the same
   instrument, start date and kept condition values), every one is created and left `InValid`, for the
   **accounting / operations user** (not a technical user) to choose the one to make `Valid` in SIGOM — the run's
   report has the GBO → BOX properties and a section with the clash groups. The clash mode is **no longer asked**
   (ADR 0020's mode (a), hold, is gone). In a **technical test** (not UAT) one property per group may be made `Valid`
   temporarily, to check it is picked up — the operator's choice, per run; not offered in UAT / PROD; not built in
   the renderer (the operator does it in SIGOM). NY's DEV run `[operator, 2026-10-30]`: not used — all `InValid`.
   **How it is done**: the config creates every property of a group (`expect_invalid`), then, once all exist, runs
   `p_StatusPortFolio` again on each — BOX's own check then sees the identical twins; `InValid` is expected for every
   one, anything else is a problem the rehearsal shows. (Created one by one, the first of a group would otherwise be
   `Valid` — no twin existed yet.)
2. **A condition whose GBO value BOX does not accept is dropped for that property.** When a kept condition pair
   (the condition map) meets a GBO value the BOX condition does not hold — NY: `1.35` "call/put indicator" →
   BOX `13.65` holds `CALL` / `PUT`, but NY's properties `2490`–`2497.35` and `133194` / `133195.44` hold `Touch2`,
   `Accrual`, `SWAP` — the condition is **dropped for that property** only; a property whose value BOX accepts
   (`CAL` → `CALL`) keeps it. **How** `[operator, 2026-10-30]`: BOX builds every property's condition rows from its
   instrument's local property (`f_GenTopicCond`), which keeps the condition for the others; the config deletes that
   property's generated row (`drop_conditions`) before `p_StatusPortFolio` (an empty row would make it `InValid`).
   ⚠ Open, for the BOX expert: re-saving such a property in SIGOM may regenerate the empty row (and make it
   `InValid`). Dropping a condition can make the property clash with another → point 1. **Seen in NY's rehearsal
   (2026-10-30)**: a dropped condition **widens** the property — `2490.35` / `2491.35` (`Touch2`, 13.65 dropped) came
   out `InValid` ("the value of the conditions exists in other portfolio properties"): BOX finds them covering the
   trades of an OTC property created before them whose other conditions are the same (a `CALL` / `PUT` one), which
   stays `Valid`. `[operator, 2026-10-30]`: expected `InValid` in the DEV test (the renderer accepts `expect_invalid`
   without an identical twin on a property with a dropped condition); ⚠ open for the BOX expert: is that what the
   drop rule should give, or should such properties stay out?
3. **A readable config.** The config (23,000+ lines for NY) has a **banner per section** (`===== <n>. <title>
   (<count>) =====`, searchable) and prints a `SECTION|<n>|…` line in its output; each account is numbered
   (`account i/N`). The renderer also writes **`<base>-summary.md`**: what the config inserts, section by section,
   **without SQL** (topics, accounts with their date rules, local properties' arrays, portfolio properties with
   their conditions, dropped conditions and expected status, the clash groups, the other rows) — for the reviewer.

## Consequences

- `scripts/render_acc_sql.py`: `drop_conditions` per portfolio property (refusals `pp-drop-not-in-local`,
  `pp-drop-and-value`); clash groups' second status pass (`STATUS-CLASH|`, `InValid` expected; refusal
  `expect-invalid-no-clash`); section banners; `<base>-summary.md`. Tests.
- The clash mode question disappears from the kickoffs, the charter and the inputs (`decisions.pp_clash_mode` = `b`,
  fixed; `decisions.pp_clash_choices` only records, later, what the accounting user chose — and, in a technical test,
  the property made `Valid` temporarily).
- The condition map records the values BOX does not hold as **"drop on that property"**; the report shows them per
  property (dropped — value not accepted) and the matrix counts them as dropped, not OPEN.
- NY's DEV run: the 10 OTC properties OPEN on `13.65` are carried with `13.65` dropped (they may join clash groups);
  every clash group carried `InValid`; the matrix, the report and the values re-derived from the run's evidence (no
  query asked again — ADR 0023 point 8); then precheck, rehearsal, config.
- Open item 4zz (a) answered; the SIGOM re-save question added.

## Alternatives considered

- Keep holding clash groups (mode a): rejected — the accounting user chooses in SIGOM, on properties that exist.
- Leave an untranslatable condition row empty: rejected — BOX marks the property `InValid` for a reason that is not a
  choice for the user.
- Map `Touch2` / `Accrual` / `SWAP` to a BOX value: rejected — BOX does not hold them; no value is invented.
