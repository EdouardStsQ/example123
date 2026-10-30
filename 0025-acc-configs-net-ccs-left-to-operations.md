# 0025. BOX ACC configs: the CCS end-of-month netting (Net CCS PlanBS) is left to the operations user — a handover for UAT

Date: 2026-10-30
Status: accepted — supersedes, for screen 13, "the reference's rows as they are" (operator, 2026-10-26; charter,
catalogue §13) and the Net CCS part of ADR 0023 point 4

## Context

Screen 13 (*Config. › Net EOM to CCS*, `T_BOX_NETCCS_BSPLAN_S`, [`box-acc-model.md`](../reference/box-acc-model.md)
§8.1) says which accounts BOX nets at the end of the month for CCS. Since 2026-10-26 the agent asked per run whether
the netting applies and, if yes, proposed the reference's rows as they are, accounts by code — and, from NY's DEV run
(`gap_20261029_1`), created the reference's netting accounts missing in the target from the reference's BOX rows
(ADR 0023 point 4). NY's DEV rehearsal of 2026-10-30 carried 11 such rows and 11 accounts copied from SLB.

## Decision

`[BOX ACC expert via operator, 2026-10-30]`

1. **The accounts a branch nets at month end are the operations / accounting user's to define** — never taken from the
   reference branch (its accounts are its own). The agent creates **no** Net CCS PlanBS row and **no** account for
   it from the reference.
2. **Screen 13 is on standby until UAT**, when the operations users are involved. Each run writes a **handover** for
   them, `04-net-ccs-handover.md` (template
   [`net-ccs-handover.md.tmpl`](../../agents/sigom-box-acc-configs-agent/templates/net-ccs-handover.md.tmpl)): what
   the screen does, what they must decide (per row: instrument, instrument type, strategy, the account to net; the
   `EOM_CCS_ACTIVE` switch row), what the target already has for it (events `5210.65` / `5211.65`, the netting
   standard historics and topics, the internal account — A-13c, verify only), the reference's rows **as an example
   only** (by code), the target's CCS accounts on netting topics for information, the open questions, and how the
   rows will be created once decided.
3. **The question "does it apply?" is not asked any more** in a gap run: the matrix's screen 13 says `handover (UAT)`.
   A run whose inputs hold the operations user's rows (`decisions.net_ccs`: the rows, who decided, the date) creates
   them — accounts by code, each one present in BOX or created on screen 10 from the target's GBO, never from the
   reference.

## Consequences

- NY's DEV run `gap_20261029_1` (PR "NY_SCH DGBOUS ACC config"): the 11 Net CCS rows and the accounts taken from SLB
  only for them leave `acc-values.json` (listed under `_not_carried`: "screen 13 — handover for UAT, ADR 0025"); the
  run writes `04-net-ccs-handover.md`; precheck and rehearsal again before the config. The `FFM` question moves to
  the handover.
- Charter (screen 13, inputs, hard rule 23), kickoffs (gap run: A-13 kept as verify only, no question; SQL step),
  catalogue §13 and §10, model §8.1, templates (matrix row 13, values), eval case, NY inputs (`eom_ccs_netting`),
  open item 4zv.
- `scripts/render_acc_sql.py` keeps `T_BOX_NETCCS_BSPLAN_S` among its generic tables — for the run that has the
  operations user's rows.

## Alternatives considered

- Copy the reference's rows and let the user change them (2026-10-26): rejected — a DEV / technical run would create
  another branch's netting accounts for this one, and the user might not notice which to change.
- Ask the operator during the gap run: rejected — the operator is not the operations user; UAT is when they are
  involved.
