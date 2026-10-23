# 0015. BOX ACC configs: the scope comes from configuration — no usage window, one GBO source per run

Date: 2026-10-22
Status: accepted — supersedes the GBO-production usage step of [ADR 0013](0013-acc-prechecks-and-sigom-routines.md)

## Context

ADR 0013 added a usage step: the target's movements over a window (default the last full quarter) decided what was
"in use", and every "configured but unused" row became a question. The first NY run then showed that a window misses
topics that are used rarely (cancellations, year-end results, cash FX, memorandum topics), so the rule became
"copy full lists, scope by the branch condition" (2026-10-15). After the BOX ACC expert's review (ADR 0014) every
part of the build has a configuration source. The window no longer decides anything, but the agent still asked for it
`[operator, 2026-10-22: "we know exactly what to build in BOX"]`.

The GBO reads also used an environment of their own (`GBO-PROD`, then PRE PARALELO for NY), separate from the
environment the run started in, without saying so at the start.

## Decision

`[operator, 2026-10-22]`

1. **No usage window.** What is built comes from configuration only: the target's `Valid` GBO portfolio properties
   whose branch condition is the target's, with their **full** lists (A-U1, A-U7), the reference's BOX rows, and the
   target's `T_MAD_REVAL_ACCOUNTS` rows. No "configured but unused" question. `&&ACCOUNT_CODES` = the in-scope lists'
   real accounts (A-U7b) + A-03a's.
2. The windowed queries (A-U0, A-U2, A-U2b, A-U3, A-U4, A-U4b, A-U5, A-U6) stay in the catalogue as **optional
   diagnostics**, run only when the BOX team asks (e.g. postings outside the configuration).
3. **One GBO source per run**, asked once at the start (`gbo_source.env`; default the target environment, or a
   fresher copy of production such as PRE PARALELO). Env tag `GBO` for every query on the target's GBO tables; `TGT`
   for the target's BOX; `REF` for the reference tier.

## Alternatives considered

- Keep the window as a cross-check: rejected — it cannot change the build, and a question asked every run invites a
  scope by usage again.
- Always read GBO in the target environment: rejected for now — on 2026-10-15 Tier 2 PRE's GBO was older than PRE
  PARALELO (Cross Account Config 17 vs 24 rows); the operator chooses per run.

## Consequences

- Fewer queries and no window question; the run states its GBO source at the start.
- A rarely used topic is never lost (full lists).
- Postings that no configuration explains (NY: no-topic postings, `GENTRANSITCASH` / `FXNETLOSS`) are found only when
  the diagnostics are run — NY's July results are already recorded (open item 4zc).
