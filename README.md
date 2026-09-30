# Book labels — NY_SCH, Tier 2 PRE

Skill [`set-up-book-labels`](../../../../skills/set-up-book-labels/SKILL.md) · script
`python3 scripts/set_up_book_labels.py runs/NY_SCH/tier2-pre/books/`. **Spans runs — never archived with an
FE run.** Read by the FE run (step 11, `../`) and by the batch-jobs run (`../jobs/`).

**Status 2026-09-30: not run yet.**

| Input | State |
|---|---|
| `00-books.csv` | 22 books, codes `XNY01`…`XNY22` in the order given, descriptions exactly as the data-lake labels `[stated: operator, 2026-09-30]` (`G10NY` with a zero, confirmed). Verify each against the data-lake source |
| `book-labels.json` | branch `20007.4`, country `NY`; **dummy and PK rule not decided** (BOX FE team cards) |
| `01-evidence/` | empty — the operator runs Q-10f (Tier 2, `&&COUNTRY_CODE = NY`, the dummy's code), Q-10c (c) for an existing dummy, Q-10e if labels are missing |

Expected: none of the `XNY` labels exists yet (`NY001`, used by FE runs 4 and 6, is a GBO label), so the
first complete run ends with `book-labels-PROPOSAL.sql` for the BOX FE team.
