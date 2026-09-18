# Run log — NY_SCH rehearsal: mine GBO Tier 2 → write BOX Tier 1 PRE

Agent: `sigom-box-fe-configs-agent` · Kickoff: `agents/sigom-box-fe-configs-agent/prompts/kickoff-ny-sch.md`
(see its *Active mode, revised 2026-09-18* section)

**Status: ⛔ SUPERSEDED 2026-09-18.** Work moved to [`../tier2-pre/`](../tier2-pre/README.md) — a
**deferred-verification run against the real target** rather than a substituted one.

> **Why this approach was withdrawn.** Substituting Tier 1 PRE as the destination turned every mined FK
> into a cross-environment portability question, blocked step 4 on quote references that are local to
> Tier 2 by design, and produced SQL that would never have been executable anywhere. Running against
> Tier 2 and deferring only the BOX-side reads is strictly better: every FK is native, gate 0f
> disappears, step 4 comes back into scope, nothing is written into a shared pre-production environment,
> and the output is the real deliverable.
>
> **Kept, not deleted** — the findings it produced are real and are cited from the Tier 2 run: the
> `PGT_MRK` environment-specificity finding, the `6401.4` collision, the Tier 1 `BOX_FE` structural
> reference (15 walk tables present), and four query defects.

**Original purpose:** produce NY_SCH's real BOX FE configuration and prove the SQL is correct, ordered
and well-formed, against a stand-in target environment.

> ⚠️ **Split-tier rehearsal.** Values are mined from **GBO Tier 2**, where NY_SCH is actually live, and
> written to **BOX Tier 1 PRE**, the only environment with `BOX_FE` access. The *values* are real; the
> *destination* is a substitution. FK resolution is verified for Tier 1 only (gate 0f) — when Tier 2
> `BOX_FE` access lands, re-run gate 0f against Tier 2 and regenerate.

> ⚠️ **This writes into a shared pre-production environment.** NY_SCH does not exist in Tier 1 PRE and
> this run creates it there. Get an owner's OK before applying anything, keep the rollback `DELETE`s,
> and label the configuration so nobody mistakes it for a real Tier 1 onboarding.

## Why this shape

Access is asymmetric:

| Environment | Access | NY_SCH there |
|---|---|---|
| **Tier 2 PRE** | GBO only (`DEVENG`, `PGT_*`) — **no `BOX_FE`** | **Live and configured.** The real source |
| **Tier 1 PRE** | Full, including `BOX_FE` | Not configured |

`GBO_SOURCE` and `TARGET_ENV` are separate inputs in the charter precisely so they can differ. Mining
the tier where the branch is real and substituting only the target is strictly better than the earlier
plan of mining Tier 1 — a Tier 1 GBO read would have returned either nothing for NY_SCH or another
branch's configuration, and no amount of well-formed SQL rescues a findings table built on that.

**Consequence worth stating:** the findings table this run produces is the one that goes to the SME for
the real run. It is not a throwaway.

## Gate state for this run

| Gate | State |
|---|---|
| 0a | Satisfied — `BRANCH_PK = 20007.4` in GBO Tier 2 |
| 0b | Satisfied — level 1 only; `bc.PK = 141.35` → `FK_MISCONFIG = 64408.35` → "Configuracion -NY" |
| 0c | **Blocked on the SME, but concrete.** A branch's instrument set is its Accrual tab (`T_BOX_ENGACCRCONF_S`). SLB in Tier 1 shows **nine** on screen, of which seven resolve to a Sub-Product row — run Q-05c's `LEFT JOIN` form plus the unjoined `COUNT(*)`, then put the list to the SME |
| 0d | ✅ **RESOLVED 2026-09-17** — `F___SEQUENCE(<table>,'X')` |
| 0e | Evaluated against **Tier 1 PRE**, where `BOX_FE` access exists — can pass here normally |
| 0f | ✅ **Answered, not blocking.** `PGT_STC`/`PGT_SYS` are shared. `PGT_MRK` is **not** — 35 of NY's 38 quote references are `.35`, locally allocated in Tier 2, so they are absent here by design. **Step 4 is `EVIDENCE_REQUIRED — not rehearsable cross-environment`; the other 13 steps continue.** See below |

## Gate 0f — much smaller than it looked

`[stated: Edouard, 2026-09-18]` **`PGT_STC` and `PGT_SYS` hold identical rows in every environment.**
Calendars, currencies, the branch master, Sub-Product instruments and `PGT_DOMAINS` values are therefore
the same in Tier 1 and Tier 2 by design — which is why Q-14's first run matched exactly. Those need **no
cross-environment check**, and a run must never be blocked on one; an apparent divergence there is a
platform escalation, not a walk finding.

**`PGT_MRK` — answered 2026-09-18, and it is the exception.** `[confirmed: DB via Edouard]` NY's curve
references **38 quote references**; only **2** exist in BOX Tier 1 PRE. **35 carry `.35`** — allocated in
NY's own Tier 2 environment. They are NY's own market-data objects, not shared reference data, and Tier
1 has never had reason to hold Santander NY spot closing prices. One PK even collides: `6401.4` is
SANTANDER NY SPOT CLOSING PRICES in GBO Tier 2 and EUROPEAN CENTRAL BANK FIXING here — so `.4` does not
guarantee identity inside `PGT_MRK` the way it does in `PGT_STC`/`PGT_SYS`.

**This does not block the run, and it will not occur in the real one.** `PGT_MRK` is shared between BOX
and GBO *within* an environment, and all 38 were read from GBO Tier 2's `PGT_MRK` — so BOX Tier 2 sees
the same 38 rows. Step 4 resolves natively in the real target.

**So: step 4 is `EVIDENCE_REQUIRED`, annotated "not rehearsable cross-environment — resolves natively in
the real target". No SQL for it. The other thirteen steps proceed.** Two things must not happen: loading
NY's market data into Tier 1 PRE to unblock a test, and substituting Tier 1 quote references — the second
would point NY's curve at ECB fixings instead of Santander NY closes, which is hard rule 6 and the kind
of error nothing downstream catches until the numbers are wrong.

Also out of scope, from the earlier correction: **source-object PKs** — the GBO curve's own `PK = 1.35`
is the identity of the row being read, never an FK the `INSERT` carries. Its absence in the target is
expected and is why the walk exists.

## ✅ PK mechanism — resolved, no longer a diagnostic

`[confirmed: source via BOX FE Developer, 2026-09-17]` PKs come from `F___SEQUENCE(TABLE_NAME,
seq_range)`: `NEXTVAL` from **`SQ_BOX_FINANENG1`** for every walk table, plus — with
`seq_range = 'X'` — `auth_code / 10^length(auth_code)`, read from the single global row in
`gom_glb_sys.t__CORE_INFO_S`.

Emit `v_pk := F___SEQUENCE('T_BOX_ENGCONF_S','X');` assigned to a declared variable, children
referencing the variable. A literal PK, or a bare `SQ_BOX_FINANENG1.NEXTVAL` without the fraction, are
both failures. **A useful property for this run:** the auth code is read from the *target* at execution
time, so the same script self-corrects its PK suffixes when it is later run against Tier 2.

Worth one query here: confirm `F___SEQUENCE` exists and is `VALID` in Tier 1 PRE, and note its owning
schema so the script references it correctly.

## Working assumptions — both stated, neither confirmed

1. `BOX_FE` table structures are identical across tiers and differ only in content. Untested until
   someone with Tier 2 grants runs the Q-G4 diff.
2. ~~`.4` reference data is genuinely replicated across tiers rather than coincidentally numbered.~~
   **Answered 2026-09-18** — `PGT_STC` and `PGT_SYS` are shared schemas with identical rows everywhere.
   `PGT_MRK` is **not**, and `6401.4` proves `.4` alone guarantees nothing there.

## Preflight

Every query batch opens with the visibility preflight (`USER`, `DB_NAME`, visible `BOX_FE` and
`DEVENG` object counts). In a split-tier run it does double duty: it also proves each CSV came from the
environment it claims. A CSV whose preflight was not run is not evidence — hard rule 8.

## Outstanding queries

None requested yet.
