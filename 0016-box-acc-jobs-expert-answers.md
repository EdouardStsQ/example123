# 0016. BOX ACC jobs: the BOX team's answers on MBJ (calendar, PKs, db.conf steps, server, CreatedBy, FE run)

Date: 2026-10-26
Status: accepted

## Context

The first ACC jobs run for a Tier 2 branch (`acc-jobs/all_20261021_1`) was a test: its MBJ calendar and PK call were
test values, one reference step had no MBJ row anywhere, and the run waited on a sign-off of the FE jobs. The
operator took the eight blocking questions (B1–B8) to the BOX expert, the BOX dev and the BOX team.

## Decision

`[BOX expert / BOX dev / BOX team via operator, 2026-10-26]`

1. **B1 — per-book steps through MBJ.** Every per-book ACC step runs through `shell.conf` (`mbjbox.sh`) + one MBJ row
   — confirmed as the pattern for a new branch.
2. **B4 — except what the reference never runs through MBJ.** A per-book step with **no MBJ row in any book** of the
   reference, which the reference runs from `db.conf`, is built as `db.conf` per book (core call, the book's label),
   exactly as the reference (e.g. SLB's CCS D08, group `3555.65`). Not asked; `mbj.missing_rows` only overrides it.
3. **B2 — `FK_CALENDAR` is not used by MBJ**: the engine takes the branch's calendar. The column copies the
   reference row's value; `mbj.calendar` is retired.
4. **B3 — PKs from the table's sequence** (`BOX_ACC.SPK_T_BOX_MBJ_PROPERTIES_S`, J-E11), checked first as the FE
   configs agent's pre-step P1: a read-only **precheck** SQL compares the sequence with the table's highest PK of the
   installation's fraction and prints a proposal for the BOX team when it is behind; each PK =
   `NEXTVAL` + the fraction, checked unused. `mbj.pk_call` is retired (`mbj.sequence`).
5. **B5 — same Control-M server** for the FE and ACC folders (for now): the ACC folder takes the FE run's folder server
   unless given.
6. **B6 — the MBJ engine in Tier 2** is being deployed by the BOX team: not a blocker (a warning, as before).
7. **B7 — `CreatedBy`** is the user ID of the person running the agent, asked every run (FE and ACC jobs agents);
   never carried over from an earlier run, never the reference's developer ID.
8. **B8 — no sign-off before the ACC jobs.** The ACC agent asks which FE run to treat as OK (frozen or not); no
   sign-off of the FE run and no PR on the target's FE repos is needed to build and test the ACC jobs. PRs on the
   target's repos stay the operator's yes per repo (ADR 0012).

## Consequences

- `build_acc_jobs.py`: `mbj.sequence` (required), `mbj.calendar` / `mbj.pk_call` gone; a fifth SQL file
  (`precheck`); per-book `db.conf` lines for steps never run through MBJ (`step-in-dbconf-as-reference`);
  `controlm.ControlmServer` from the FE run (`controlm-server-from-fe-run`).
- A branch's earlier test run (calendar / PK call as test values) is rebuilt as a new run without `test_values`.
- Still open for the target: the Control-M server per environment (PRE / PRO), the precheck's result in the target.
