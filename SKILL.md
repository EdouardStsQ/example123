---
name: explain-box-job
description: Explains one BOX batch job from files only - its Control-M folder, schedule and events, the db.conf / shell.conf line that runs it, its group and the group's events by name from the repo DML. Use when an agent or operator asks "what does job X do?", or needs to know who emits an event, mid-task included.
---

# Explain a BOX job

`[2026-10-06]` One way to answer *"what does job X do?"* at **overview** depth, with **0 database queries**, shared by
[`box-fe-jobs-agent`](../../agents/box-fe-jobs-agent/AGENT.md) (questions asked mid-run, and the cards of
`pending-questions.md`) and [`box-batch-jobs-agent`](../../agents/box-batch-jobs-agent/AGENT.md) (an optional
shortcut for EXPLAIN `overview`). The **EXPLAIN procedure of `box-batch-jobs-agent` stays the authority**: its depths,
budgets and answer shape. This skill is its `overview` level in one script. The mechanism is
[`box-batch-chain.md`](../../docs/reference/job-chains/box-batch-chain.md) L1-L3.

**Script:** `scripts/explain_job.py` (it reads the inventory written by `scripts/parse_job_confs.py`).

## The rules

| Rule | Source |
|---|---|
| L1 = the job in the Control-M folder repos given: folder, file:line, `Description`, `When`, waits / emits | chain doc L1 |
| L2 = its **executed** binding: FE = `db.conf` `f_ExecuteGroup`; ACC = `shell.conf` `mbjbox.sh` → the MBJ row (J-R2). A `db.conf` line of a `shell.conf` job is legacy | BOX dev via operator, 2026-10-01 |
| L3 = the group header and its events in order, from `dml/03-PGT_PRC/<rX.Y.Z>/05_Static-Data/` of `cib-boxfin-dbboxfe` (FE) or `cib-boxacc-dbboxacc` (ACC); **the newest release wins** | operator via Devin, 2026-10-02 |
| An event's meaning from its name only is `INFERRED`; its entries (debit / credit) are depth `event` (box-batch-jobs-agent EXPLAIN) | operator, 2026-10-01 |
| Who emits an event = the job whose `eventsToAdd` has it, in **any** folder repo attached (FE and ACC) | operator, 2026-10-06 |

## How to run

```bash
python3 scripts/explain_job.py runs/_reference/<env>/ <JOB> [<JOB> ...] \
    --controlm <FE folder repo> <ACC folder repo> --dml <cib-boxfin-dbboxfe> <cib-boxacc-dbboxacc> [--mbj <J-R2 export .csv>]
```

The folder repos of a branch are in [`branch-registry.csv`](../../docs/reference/branch-registry.csv)
(`fe_controlm_repo`, `acc_controlm_repo`). Without `--mbj`, an ACC job's group is "ask J-R2".

## Steps

1. The environment's job confs are in `runs/_reference/<env>/` with a current `jobs-inventory.csv`; attach the
   branch's FE **and** ACC folder repos and the two DB repos (read-only).
2. Run the script for the job(s) asked.
3. Answer with its card: one paragraph (what it is, when it runs, what it waits for / emits, which group it runs),
   then the lines it printed with their tags. Offer depth `event <PK>` (box-batch-jobs-agent) — never go deeper unasked.
4. **Asked mid-task** (e.g. while `box-fe-jobs-agent` waits for an answer): answer, then **repeat the pending
   question** — the question is not answered by the explanation.

## Output

Markdown per job: **What** (family · side · product · level, `Description`), **L1 Control-M** (folder, repo
file:line, `When`, waits, emits — CONFIRMED), **L2 binding** (conf file:line, branch, instrument — CONFIRMED),
**L3 group** (PK, name, events in order — names CONFIRMED, meaning INFERRED), and what it could not read.

**Success** = exit 0, and every level is either shown with its file:line or says which repo / query would show it.

## Failure modes

| Failure | Detection (script code) | Handling |
|---|---|---|
| No inventory for the environment | `inventory-missing` | copy the job confs into `runs/_reference/<env>/`, run the parser |
| A repo or file passed does not exist | `path-missing` | attach that repo (read-only) or fix the path |
| Job in no file given | card says "not in the inventory nor in the Control-M repos given" | ask which repo holds it |

## Never

- Query the database at this depth, or describe entries from an event name.
- Edit, branch or comment on a BOX or Control-M repo — they are read-only.
- Copy a `CreatedBy` (developer ID) or a book description into `docs/`.

## Eval cases

[`evals/cases/explain-box-job.md`](../../evals/cases/explain-box-job.md).
