# 0019. Branch-level run folder: what is the same in every environment is kept once

Date: 2026-10-27
Status: accepted

## Context

A branch's run folders are per environment (`runs/<BRANCH>/<tier>-<env>/`) because their PKs, registers, servers and
build status differ. Two files did not: the books with no BOX job (`books-excluded.csv`) and the GL's alias code per
book (`label-aliases.csv`). Kept in `tier2-pre/books/`, a run in another environment (DEV, PRE Paralelo) would not
find them — the excluded books would silently get jobs.

## Decision

`[operator, 2026-10-27]`

1. **`runs/<BRANCH>/branch/`** holds what is the same in every environment: `branch/books/books-excluded.csv` and
   `branch/books/label-aliases.csv`. Never copied into an environment folder.
2. **The scripts read it by default.** `build_fe_jobs.py` / `build_acc_jobs.py` (`excluded_books_csv`):
   `target.books_excluded` if it exists → a `books-excluded.csv` beside the environment's register (an override for
   that environment, warned `excluded-books-env-override` when it differs from the branch's) → the branch folder's.
   An older run's explicit path that no longer exists finds the branch's file, so an older run rebuilds identically.
3. **Stays per environment:** `books/00-books.csv` (`label_pk`, its source and status), the register,
   `book-labels.json`, `fe-jobs/instrument-plan.csv` (built / done), the inputs files.
4. `new_run.py` prints the branch-level files (read from there, not copied).

## Consequences

- NY_SCH: both files moved to `runs/NY_SCH/branch/books/`; the FE / ACC jobs inputs and the ACC configs inputs
  point there.
- Agents, the labels skill, the catalogue (screen 14) and the templates name the branch folder.
