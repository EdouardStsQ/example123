# NY_SCH — branch-level files (every environment)

`[operator, 2026-10-27]` What is the same in every environment of NY_SCH is kept **once**, here — never copied into
an environment folder (`tier2-pre`, `tier2-dev`, `tier2-preparalelo`, …).

| File | What | Read by |
|---|---|---|
| `books/books-excluded.csv` | the four books with no BOX job (XNY07, XNY09, XNY18, XNY19; scope `jobs`) `[operator, 2026-10-09]` | `build_fe_jobs.py`, `build_acc_jobs.py` (by default; `target.books_excluded`) |
| `books/label-aliases.csv` | Equation's alias code per book with jobs (18), source `629.4` **proposed** — to confirm (open item 4zw) `[Equation via operator, 2026-10-27]` | `sigom-box-acc-configs-agent` screen 14 (`label_aliases.file`) |
| `acc-configs/condition-map.csv` | GBO → BOX **condition pairs** and value translations for NY's portfolio properties ([ADR 0020](../../../docs/decisions/0020-portfolio-properties-imported-from-gbo.md)): `instruments, gbo_cond_pk, gbo_func_or_field, gbo_description, box_func_or_field, box_description, value_map, how (same field / same text / confirmed / none), status, evidence, date` — BOX conditions by function / field (their PK read per environment, A-01). Empty until the first gap run under ADR 0020; the expert's hints (2026-10-28, OTC GBO `2496.35` vs Tier 1 BOX `266.21`): Strategy and Delivery(1) / Cash(0) exist in both; Instrument Type, the branch function and Folder only in GBO (dropped unless BOX has them); GBO "call/put indicator" ≈ BOX "Check if Option is Call or Put" — to confirm (values `SWAP` vs `CALL`) | `sigom-box-acc-configs-agent` (`condition_map.file`) |

**Override:** a file of the same name in an environment's `books/` is used for that environment instead (the
scripts warn `excluded-books-env-override` when it differs from this one). Use it only when the environment really
differs.

**Stays per environment** (environment-specific columns): `books/00-books.csv` (`label_pk`, its source and status
per environment), `books/books-register.csv`, `book-labels.json`, `fe-jobs/instrument-plan.csv` (built / done per
environment), every inputs file (PKs, servers, runs).
