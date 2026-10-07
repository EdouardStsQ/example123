# 0011. The BOX ACC configs agent: what a new branch changes, where each value comes from

Date: 2026-10-07
Status: accepted (phase 1 — the gap run); phase 2 (rendered SQL) after the first run's evidence

## Context

`sigom-box-acc-configs-agent` was named and deferred (2026-09-11) until the FE agent had run for real — it has (runs
1-7). `[stated: operator, 2026-10-07]` gave the scope rules, and a Confluence checklist of the eleven **BOX -
Accounting** SIGOM screens with the queries the SIGOM traces showed (tables, owner objects):

- configure **only what depends on the branch**; global objects stay as they are (*"Condition Port Properties do not
  depend on the branch … Config. Local Properties does"*);
- Accounting Topics and Event Grouping / Event Config are **global** — but ask whether to keep the global Event
  Grouping or create a **branch copy** (same configuration, the branch's own PK) so a later branch change does not
  touch the global one;
- Cross Account Config **from GBO**; Global Accounts **from GBO** (the accounts are the same as GBO's);
- Portfolio Properties **not directly from GBO** — GBO's carry GBO topics; a GBO → BOX topics mapping exists
  (not seen yet);
- Net Contract applies **only to MADRID REAL** (copied from GBO by a PL);
- MBJ Config belongs with the jobs, in a BOX ACC equivalent of `box-fe-jobs-agent`.

## Decision

1. **Per screen, a stated action** (charter table): *verify* (global: Condition Port Properties, Accounting Topics,
   Standard Historic, Event Config), *verify + ask* (Event Grouping: global or branch copy), *copy from the reference
   BOX* (Config. Local Properties, to the target's branch **group**), *from the target's GBO, translated* (Cross
   Account Config, Global Accounts), *reference shape + GBO accounts through the topic mapping* (Portfolio Properties),
   *N/A unless Madrid real* (Net Contract), *other agent* (MBJ → planned `box-acc-jobs-agent`; labels →
   `sigom-box-fe-configs-agent`).
2. **Phase 1 = a read-only gap run**: the queries of [`acc-config-mining.md`](../reference/queries/acc-config-mining.md)
   in the reference tier and the target tier, a gap matrix per screen, and the operator's decisions recorded in the
   run's inputs file. **No SQL is rendered in phase 1.**
3. **Phase 2 = rendered SQL**, built like the FE renderer (ADR 0006) once phase 1 shows the real column sets, the PK
   rule of the ACC tables, the link-array extensions and the topic mapping.
4. The FE configs agent, the jobs agents, their prompts and scripts are **not changed**. Two jobs-agent documents
   still say MBJ rows belong to this agent; they change when `box-acc-jobs-agent` is built.

## Alternatives considered

- **Build the renderer now** from the FE pattern. Unknown: the INSERT column sets, the ACC PK rule, the
  `T_BOX_LINK_ARRAY_X` extensions of the local-properties arrays, how GBO topics map to BOX topics. A renderer
  written on guesses is the class of error the FE runs paid for five times.
- **Copy everything from the reference branch.** Wrong for the GBO-sourced screens (accounts are the branch's own) and
  unnecessary for the global ones.
- **Copy Portfolio Properties from GBO.** Brings GBO topics into BOX (operator).

## Consequences

- The first ACC run produces evidence and decisions, not SQL — reviewable by the BOX team before anything is written.
- Portfolio Properties accounts stay **OPEN** until the GBO → BOX topic mapping is found.
- A branch-specific Event Grouping changes the group PK the ACC jobs (MBJ rows) must use — recorded in the decisions
  for `box-acc-jobs-agent`.
