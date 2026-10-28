# NY_SCH — branch-level files (every environment)

`[operator, 2026-10-27]` What is the same in every environment of NY_SCH is kept **once**, here — never copied into
an environment folder (`tier2-pre`, `tier2-dev`, `tier2-preparalelo`, …).

| File | What | Read by |
|---|---|---|
| `books/books-excluded.csv` | the four books with no BOX job (XNY07, XNY09, XNY18, XNY19; scope `jobs`) `[operator, 2026-10-09]` | `build_fe_jobs.py`, `build_acc_jobs.py` (by default; `target.books_excluded`) |
| `books/label-aliases.csv` | Equation's alias code per book with jobs (18), source `629.4` **proposed** — to confirm (open item 4zw) `[Equation via operator, 2026-10-27]` | `sigom-box-acc-configs-agent` screen 14 (`label_aliases.file`) |

**Override:** a file of the same name in an environment's `books/` is used for that environment instead (the
scripts warn `excluded-books-env-override` when it differs from this one). Use it only when the environment really
differs.

**Stays per environment** (environment-specific columns): `books/00-books.csv` (`label_pk`, its source and status
per environment), `books/books-register.csv`, `book-labels.json`, `fe-jobs/instrument-plan.csv` (built / done per
environment), every inputs file (PKs, servers, runs).
