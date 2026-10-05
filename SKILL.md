---
name: find-box-jobs
description: Finds a branch's BOX batch jobs in an environment - which ones run (FE from db.conf, ACC from shell.conf via MBJ), filtered by side, product and branch - and their order from the branch's Control-M folder JSON. Use whenever an agent needs "the jobs of branch X for product Y", to explain them or to copy them for a new branch.
---

# Find a branch's BOX jobs

`[2026-10-02]` One way to answer *"which BOX jobs does branch X run for product Y, and in what order"*, shared by
[`box-batch-jobs-agent`](../../agents/box-batch-jobs-agent/AGENT.md) (EXPLAIN list questions, GAP) and
[`box-fe-jobs-agent`](../../agents/box-fe-jobs-agent/AGENT.md) (the reference chain it copies). Why a skill:
[ADR 0010](../../docs/decisions/0010-box-fe-jobs-agent.md). The mechanism is
[`box-batch-chain.md`](../../docs/reference/job-chains/box-batch-chain.md) L1-L2.

**Scripts:** `scripts/parse_job_confs.py` (the inventory) and `scripts/find_jobs.py` (the filter and the order).

## The rules

| Rule | Source |
|---|---|
| Only **executed** bindings count: a `db.conf` line of a job also in `shell.conf` is legacy (`executed = N-legacy`) | BOX dev via operator, 2026-10-01 |
| **FE** = `db.conf` (`f_ExecuteGroup` through the branch wrapper); **ACC** = `shell.conf` running `mbjbox.sh` (MBJ row) | same |
| Product = `GMBX<n>` **or** the `db.conf` instrument constant (`CST_PK_DEP`…) — so old-named jobs are found | parser summary, 2026-10-01 |
| Branch = the name token **or** the `db.conf` branch constant, both from [`branch-registry.csv`](../../docs/reference/branch-registry.csv) — a new branch is a new row there | jobs inventory |
| Order = Control-M events: a job runs after every job whose `-OK` event it waits for. Never by name or step number | chain doc L1 |
| **The branch's own folder repo**: the registry's `fe_controlm_repo` / `acc_controlm_repo` (+ the shared check / ALM repos) | operator, 2026-10-02 |

## How to run

```bash
python3 scripts/parse_job_confs.py runs/_reference/<env>/                 # once per copy of the job confs
python3 scripts/find_jobs.py runs/_reference/<env>/ --side FE --product <product> --branch <branch> \
    --controlm <the branch's FE folder repo> --out <run folder>/01-evidence/<name>
```

A branch not in the registry: add its row (or pass `--token XX --branch-const CST_PK_…`). Without `--controlm`: the list, no order.

## Steps

1. The job confs of the environment are in `runs/_reference/<env>/` and `jobs-inventory.csv` is current (has
   `executed`); otherwise run the parser.
2. Run `find_jobs.py` with the side, product and branch asked. For an order, attach the branch's folder repo.
3. Answer with its table, **and what it says it cannot see**: old-named / token-less `shell.conf` jobs (their
   branch and product are in their MBJ row, J-R2), and jobs "not found in the Control-M repos given" — ask for
   that repo; never invent an order.

## Output

The count and table (job, side, product, branch, book, step, group, conf file:line; with `--controlm`: order,
folder, waits inside / outside the list), as markdown, and `.csv` + `.md` with `--out`.

**Success** = the script exits 0 and every listed job has an order (or a stated reason it has none).

## Failure modes

| Failure | Detection (script code) | Handling |
|---|---|---|
| No inventory for the environment | `inventory-missing` | copy the job confs into `runs/_reference/<env>/`, run the parser |
| Inventory from before 2026-10-01 | `inventory-old` | run the parser again |
| Product not known | `product-unknown` | one of: generic, depos, commodities, irs, ccs, cfm, fra, otc, cap |
| Branch not known | `branch-unknown` | give `--token` and `--branch-const` |

## Never

- Count an `N-legacy` line, or order jobs by name.
- Copy a `CreatedBy` (developer ID) or a book description into `docs/`.

## Eval cases

[`evals/cases/find-box-jobs.md`](../../evals/cases/find-box-jobs.md).
