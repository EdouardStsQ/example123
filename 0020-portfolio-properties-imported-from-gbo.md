# 0020. BOX ACC configs: portfolio properties imported from GBO one by one; local properties from GBO; clashes reported

Date: 2026-10-28
Status: accepted — replaces, for screens 2 and 4, the charter's "the shape is the reference's BOX property" (applied
with ADR 0014) and "GBO's portfolio properties are consolidated into fewer BOX ones"

## Context

The BOX expert reviewed `03-portfolio-properties-report.md` of NY's gap run `gap_20261023_1`. The run proposed BOX
portfolio properties with the **reference's shape** (its number of properties, its conditions) and took only the
accounts from GBO: Swap had 3 `Valid` in-scope GBO properties but 5 BOX properties to create, and thousands of topic
rows OPEN (several GBO accounts for one topic of one BOX property). The expert: the portfolio properties are built by
**inserting the GBO ones in BOX**. GBO's conditions are not BOX's: some exist only in GBO (Instrument Type, the branch
function, Folder), some exist in both (Strategy, Delivery(1) / Cash(0)), some are the same thing under another name
(GBO "Function to return call/put indicator" vs BOX "Check if Option is Call or Put").

In BOX a portfolio property's lists are **generated** from its instrument's local property (`f_GenTopicCond`, which
also removes what the local property does not hold — `p_ClearList`): a property can only carry the conditions and
topics of the local property. In NY's GBO every property of an instrument has the same topic list (rows ÷ properties
is a whole number for every instrument and list, `box-acc-model.md` §9.5) — only the accounts and the condition values
differ.

## Decision

`[BOX expert via operator, 2026-10-28]`

1. **One BOX portfolio property per `Valid`, in-scope GBO portfolio property** — every one is imported; no
   consolidation. Its `DESCRIPTION` is the GBO property's, as it is (run folder only). Its topic → account rows are its
   own GBO property's (topics by `CODE`, ADR 0018; internal-list topics → the internal account, ADR 0014).
2. **Conditions: the GBO property's, only those that exist in BOX.** Each GBO condition is paired with a BOX condition
   of the target's catalogue (screen 1, verify only): automatically when the agent is sure (the same field domain —
   Strategy, Instrument Type —, the same description text), otherwise the agent reads both functions' source,
   **proposes the pair and the value translation** (e.g. `SW` → `Swaption`, `PUR` → `1`) and **asks the operator once
   per condition pair**. A GBO condition with no BOX twin is **dropped** (listed); a BOX condition is never created
   and never added when the GBO property does not have it. The confirmed pairs are the branch's **condition map**,
   the same in every environment: `runs/<BRANCH>/branch/acc-configs/condition-map.csv`.
3. **Local properties (screen 2) are built from GBO, not copied from the reference:** per instrument, the topics of the
   in-scope GBO properties (by `CODE`, in the same global / local / internal list as in GBO) and their conditions that
   exist in BOX; start date 01/01/1900 (ADR 0014). The reference's local property is shown for comparison only. A GBO
   property whose topics or conditions are not the instrument's common set is a **finding**: BOX would generate the
   missing rows empty and mark it `InValid` (`p_StatusPortFolio`).
4. **Clashes.** BOX refuses two `Valid` portfolio properties of one group, instrument and start date with identical
   condition values (`p_StatusPortFolio`). Dropping GBO-only conditions can make GBO properties identical in BOX: a
   **clash group**. The agent **asks once per run** what to do, default **(a)**:
   - **(a)** create the properties that do not clash; hold each clash group until the operator (the accounting user)
     names the property to keep — the next run (`--from`) creates it; the others are listed as not carried;
   - **(b)** create them all; BOX marks the clashing ones `InValid`; they are listed for the user to fix in SIGOM.

   Either way the report has a **clashes** section per group: the BOX condition values they share, each GBO property's
   full GBO conditions and values, the dropped conditions that told them apart (**why** they clash) and how their
   topic → account rows differ (what choosing one leaves out). The agent recommends none.
5. Values that name a portfolio, a counterparty or an entity are never extracted (hard rule 7): A-04f gives a hash, so
   a clash can be detected without the value.

## Consequences

- Screen 2: `create` from GBO (A-04d / A-04e / A-04f + the condition map), not from A-02a / A-02b; A-02 is a
  comparison. Screen 4: one row per GBO property; most OPEN accounts disappear (each BOX property takes its own GBO
  property's accounts); a topic with several accounts in one GBO property stays OPEN (BOX: one row per topic and list).
- New catalogue queries A-04f (each in-scope GBO property's conditions and values, masked), A-04g (the GBO
  conditions' catalogue), A-04h (a condition function's source, either system).
- The report template has a condition-map section, per-property conditions (kept / dropped) and a clashes section;
  the inputs file has `decisions.pp_clash_mode` (asked every run) and `decisions.pp_clash_choices`.
- Without a branch condition in BOX, a property of NY SCH serves its whole group in BOX — open item 4zb (BOX dev).
- NY's gap run `gap_20261023_1` (screens 2 and 4) is superseded: a new gap run.

## Alternatives considered

- Keep the reference's shape and fill the accounts from GBO (ADR 0014): rejected by the expert — the properties are
  the target's own configuration.
- Create every GBO condition missing in BOX: rejected — conditions are global (ADR 0014); only what exists is used.
- Merge clashing properties automatically when their topic → account rows are identical: rejected — every `Valid`
  GBO property is imported; the user decides.
