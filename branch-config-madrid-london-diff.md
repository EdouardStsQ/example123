# BOX_ACC — Madrid vs London branch-config diff

Deterministic diff of the two live branches' **BOX_ACC account-resolution config**, mined read-only
from the system of record (2026-08-24) and compared with `branch-config-agent/scripts/diff_branches.py`.
Config is keyed by **branch group** (see [box-branch-config-surface](branch-config-surface.md) §6): Madrid group `269.4`,
London group `21462.4`. Properties matched on `(FK_INSTRUMENT, DESCRIPTION)`; mapping cells on
`(instrument, property, topic) → GL-account CODE`.

## The numbers `[confirmed: DB diff]`

| Dimension | Madrid (269.4) | London (21462.4) | Shared | Reading |
|---|---|---|---|---|
| Instruments with properties | 8 | 7 | **7** (London ⊆ Madrid; Madrid +`20367.4`) | near-identical instrument scope |
| Portfolio properties (instrument + description) | 80 | 101 | **0** | different **naming conventions** |
| Topics used | 679 | 599 | **599** (London ⊆ Madrid) | **standardized topic vocabulary** |
| (instrument, topic) coverage | 977 | 853 | **853** (London ⊆ Madrid) | **shared structure / scope** |
| GL accounts referenced | 318 | 448 | **11** | accounts are **branch-specific** |
| (property, topic) → account cells | 10,853 | 12,937 | **0** | no concrete config transfers |

## Findings

1. **Concrete config does not transfer between branches.** Properties share **0** (naming conventions
   differ) and GL accounts share only **11** of ~300-450 — the two branches post to different charts of
   accounts (Spain `AC&G` vs London `Equation`). This is the data-level proof of the golden rule: a new
   branch's GL accounts are **never** copied/invented — they are SME/GBO-sourced by construction.

2. **The reusable template is structural, not concrete.** What *is* shared:
   - the **topic vocabulary** — London's 599 topics ⊆ Madrid's 679; and
   - the **(instrument, topic) coverage** — London's 853 ⊆ Madrid's 977.
   So an analogue branch tells you **what must be configured** (which instrument+topic combos need an
   account) but **not the account values or the property breakdown**.

3. **Property structure differs by jurisdiction/design.** Madrid names properties by
   **product/strategy** (e.g. *"Deposito Hedging"*, *"CaLL Money Trading STM"*); London breaks them by
   **counterparty sector** (e.g. *"Hedging / Bancos (5)UK"*, *"Hedging / Banco de España"*,
   *"Hedging / 168-SOC NO FINANCIERAS-OS-NR"*) — UK regulatory granularity. Hence London has more
   properties (101) despite fewer instruments.

4. **Madrid is the superset** (instruments, topics, coverage all ⊇ London) → the natural **scope
   template**, though each branch still needs its own property breakdown + GL accounts.

## Implication for onboarding a new branch

- **Scope is templatable** (🟢): the `(instrument, topic)` matrix a branch must cover can be proposed
  from a superset analogue (Madrid).
- **Values are not** (🔴 → open-question): every GL account and the counterparty-sector property
  breakdown are branch/jurisdiction-specific → SME/GBO, never invented.
- Combined with the group-keying result: a new branch **joining an existing group inherits** that
  group's config; a new branch forming a **new group** is seeded from the scope template, with all
  concrete accounts/properties flagged for the SME.

**Sources:** read-only mined config (q1/q2 for groups `269.4` + `21462.4`, 2026-08-24, system-of-record);
diff via `branch-config-agent/scripts/diff_branches.py`; [box-branch-config-surface](branch-config-surface.md).
