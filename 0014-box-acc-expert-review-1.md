# 0014. BOX ACC configs: the BOX ACC expert's first review of the onboarding plan

Date: 2026-10-22
Status: accepted — screens 2 and 4 are built from GBO since [ADR 0020](0020-portfolio-properties-imported-from-gbo.md) (2026-10-28); points 3, 6 and 7 stand

## Context

The operator reviewed the plan of `sigom-box-acc-configs-agent` ("BOX ACC — onboarding a new branch: what to build
from BOX, what from GBO", draft of 2026-10-16) with the BOX ACC expert. The expert found it good overall and corrected
eight points. Several of them remove questions the agent asked every run, and one changes a GBO source table.

## Decision

`[BOX ACC expert via operator, 2026-10-22]`

1. **Condition Port Properties** — not branch-dependent: BOX is used as it is. The agent verifies that the conditions
   it needs exist and **never asks** about a new condition.
2. **Event Grouping** — the branch's ACC jobs run the **global** event groups. No branch copy, and no question.
   (Supersedes the per-group `global` / `branch-copy` question of ADR 0011 and ADR 0013.)
3. **Config. Local Properties** — the start date `INIVALPCDATE` is always **01/01/1900**, a fixed value, not asked.
4. **Cross Account Config** — the GBO source is **`<GBO schema>.T_MAD_REVAL_ACCOUNTS`**, not
   `PGT_SYS.T_PGT_CROSS_ACCTCONF_S`. The schema is the branch's GBO wrapper owner: `PGT_ES` in Tier 1 (Madrid and SLB),
   `PGT_NY` for NY in Tier 2. Its columns seen so far: `PK`, `FK_BRANCH` (→ `T_PGT_BRANCH_S`), `FK_INSTRUMENT`
   (→ `T_PGT_SUB_PRODUCT_S`), `FK_GLTA` (→ `PGT_ACT.T_PGT_ACCT_GLTA_S`), `TIPO`. How it maps to BOX's columns
   (currency, entity, topic, `ACC_TYPE`) is learnt from the reference (A-03b), never assumed.
5. **Conf Instru Type** — not read from GBO: the **reference branch's BOX rows**, per instrument, are applied as they
   are to the new branch (a new screen of the agent, A-12).
6. **Portfolio Properties** — only GBO portfolio properties with status **Valid** are read; `InValid` ones are
   ignored.
7. **Internal-list topics** — they take the **internal account**, as the reference's do (`INTERNAL`); never left
   without an account.
8. **A Portfolio Properties report** (GBO vs BOX) is produced for the users to review: per BOX portfolio property, its
   topics, the account chosen and the GBO properties it came from.
9. **GBO and BOX tables are similar, not identical**: a column may be added, removed or renamed. Every GBO → BOX copy
   compares both tables' columns first (A-P7) and maps them explicitly; a column with no counterpart is reported.

## Alternatives considered

- Keep asking the event-group and start-date questions with the expert's answer as the default: rejected — the
  expert says they are not branch decisions, and a question asked every run invites a different answer.
- Keep `T_PGT_CROSS_ACCTCONF_S` as a second source of Cross Account Config: rejected as a source; its NY rows
  (settlement accounts by currency) stay in the usage evidence and their BOX route is asked.

## Consequences

- Fewer questions per run: no condition, event-group or local-property date question.
- `box-acc-jobs-agent`'s `mbj.group_map` stays empty (no branch copy of a group).
- Screen 3's evidence must be read again for NY from `PGT_NY.T_MAD_REVAL_ACCOUNTS` (open item 4zr). Its `TIPO` may be
  BOX's `ACC_TYPE` — to confirm on the reference (A-03b).
- A new deliverable, `03-portfolio-properties-report.md`.
- Still open: the portfolio properties' own start date (≥ 01/01/1900), the BOX route of GBO's
  `T_PGT_CROSS_ACCTCONF_S` rows, `ACC_TYPE` if `TIPO` is not it.
