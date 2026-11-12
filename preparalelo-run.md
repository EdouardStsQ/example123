# Devin kickoff — `sigom-box-fe-configs-agent` — NY_SCH, **PRE-PARALELO** (IGBOUSIB), full run

> **How to start — nothing to paste.** Open a Devin session with this repo attached and type:
> **`Run automation/agents/sigom-box-fe-configs-agent/prompts/preparalelo-run.md`**
> Devin reads this file and asks you for anything it needs, one question at a time.

`[operator, 2026-11-12]` NY_SCH's FE configuration ran OK in Tier 2 PRE (run 7). This run configures the **same
branch in another environment**, PRE-PARALELO, with the same agent and the same rules. It is **not** a new kind of
run: you follow [`tier2-full-run.md`](tier2-full-run.md) **in full** — every order, gate, pre-step, hard rule and
rendering step — with only the differences below. Where the two disagree, **this file wins**.

## What changes

| | Tier 2 PRE (`tier2-full-run.md`) | **This run** |
|---|---|---|
| `TARGET_ENV` / `GBO_SOURCE` | Tier 2 PRE, both | **PRE-PARALELO (IGBOUSIB)**, both — same environment |
| `RUN_FOLDER` | `runs/NY_SCH/tier2-pre/` | **`runs/NY_SCH/tier2-preparalelo/`** (its `tests/` folder is another area: leave it alone). Every `runs/NY_SCH/tier2-pre/…` path of the kickoff — the render, validate and metrics commands, `values.json`, `books/` — becomes `runs/NY_SCH/tier2-preparalelo/…`. The reviews of runs 2–6 stay where they are (history) |
| `run.run_no` | 7 | **1** — the first run in this environment; nothing to archive. Never write into `runs/NY_SCH/tier2-pre/` |
| Accounts | one read-only account (`BOX_FE` + `DEVENG` + `GOM_GLB_SYS`); an applying account | **`BOX_ADMIN`** — BOX side: `BOX_FE`, `GOM_GLB_SYS` queries, the P1 precheck and the SQL (rehearsal, config, verify); **`pgtadmin`** — GBO side: `DEVENG`, `PGT_*` queries. Each query says which of the two runs it. The preflight (Q-G4) runs on **both**: `BOX_FE` visible to `BOX_ADMIN`, `DEVENG` to `pgtadmin`. A grant missing (`ORA-00942`, `ORA-01031`, a package not visible) → name the object and ask — never another account's data |
| `TARGET_AUTH_CODE` | 44 (Q-G3c) | **from Q-G3c in PRE-PARALELO** — never assumed to be 44. The P1 expected line and the pre-steps status use this environment's code |
| Tier 1 reads | Tier 1, as before | **unchanged** — every `REFERENCE_*` query still runs in Tier 1 |
| Books | `runs/NY_SCH/tier2-pre/books/` | **`runs/NY_SCH/tier2-preparalelo/books/`**: copy `00-books.csv` from `tier2-pre/books/` (the 22 books `XNY01`…`XNY22` are the branch's — not asked again); skill [`set-up-book-labels`](../../../skills/set-up-book-labels/SKILL.md) runs **on this environment** (Q-10d, Q-10f, Q-10c (c) in PRE-PARALELO): labels and their PKs are this database's |
| `DUMMY_BOOK_LABEL` | decided for Tier 2 PRE | **decided again for PRE-PARALELO** (its own Q-10d): Tier 2 PRE's choice is shown on the dummy card as the precedent, its PK is not reused unless Q-10d proves the same label exists here |
| SME decisions (accrual values, error limits, books, Days Matured — steps 6, 11, 12, 14a) | asked in run 7 | **the run 7 answers are proposed, not re-asked from scratch**: read them from run 7's `values.json` / decisions (in `runs/NY_SCH/tier2-pre/`, or its archive), show them **on one card** with their source and date; `SME_IN_SESSION` confirms or changes each. Unconfirmed → `SME_DECISION_REQUIRED`, as the kickoff says. A value that depends on this environment's rows (a PK, a label) is never carried — it is mined again |
| Q-01 (existing configuration for NY) | — | asked as in the kickoff; an existing NY configuration in PRE-PARALELO → **stop** (adapting it is a human decision) |

## Before you start (operator)

| | |
|---|---|
| **Repos** | this automation repo (read/write) — as `tier2-full-run.md` |
| **Database** | Devin gets no connection. You run every query in PRE-PARALELO with `BOX_ADMIN` or `pgtadmin` (the query says which), and in Tier 1 for the reference reads |
| ✏️ **Devin asks** | `SME_IN_SESSION`; the confirmations on the run 7 decisions card; the dummy label card |

## Done when

As `tier2-full-run.md`, in `runs/NY_SCH/tier2-preparalelo/`: P1 OK with PRE-PARALELO's auth code, labels exit 0,
the SQL rendered and validated, rehearsal `REHEARSAL OK`, config committed, verify passing, `06-run-metrics.md`.
Commit and **push after every commit**; give the operator the hash from GitHub.
