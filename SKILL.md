---
name: set-up-book-labels
description: Sets up a branch's BOX book labels, and its dummy book label, in a target environment - asks for the book list, checks which labels exist, and generates the inserts for the missing ones for the BOX FE team to run - ending in a book register the agents read. Use before FE step 11, and before any BOX batch job or MBJ properties row for the branch is designed.
---

# Set up a branch's BOX book labels (books and the dummy)

`[stated: operator, 2026-09-30]` Books are set up once per branch and environment, and every consumer
reads the same result: **FE step 11** (one row per branch × approved instrument × book, plus the dummy
row per instrument), the **BOX batch jobs** (they run by label: `GMBX3NY02D07` is book `XNY02`), the **ACC
MBJ properties** (a label per job), and the Data-Lake feed jobs (per book). Why a skill and not an FE
pre-step: [ADR 0009](../../docs/decisions/0009-book-labels-skill.md).

**Script:** `scripts/set_up_book_labels.py` — all the rules below are enforced there, with tests.
**Called by:** [`sigom-box-fe-configs-agent`](../../agents/sigom-box-fe-configs-agent/AGENT.md) (before
step 11; its renderer re-checks the book folder) and
[`box-batch-jobs-agent`](../../agents/box-batch-jobs-agent/AGENT.md) (reads the register).

## The rules

| Field | Rule | Source |
|---|---|---|
| Table | `PGT_SYS.PGT_DOMAINS`, `FK_OWNER_OBJ = 17910.4` (SIGOM `GBO > SYS > Process > Batch > Label Config`) | `[stated: operator, 2026-09-30]` |
| `CODE` | **`X` + country code + two digits from `01`**: `XES01`…, `XNY01`…; continue after any code already taken | same |
| `DESCRIPTION` | **exactly** the book label the data lake sends — case, spaces, punctuation | same |
| `PK` | **fixed**, as the BOX FE team decides: they give each PK, or name the allocation expression | same |
| Dummy | one label other branches already use as their dummy, or a new one; **never** one of the branch's books | FE charter; run 4, run 6 |
| Job name token | the label code without its `X` (`XNY02` → `GMBX3NY02D07`) | `[stated: operator, 2026-09-30]` |

## The book folder — `runs/<BRANCH>/<env>/books/` (spans runs; never archived with a run)

| File | Written by | Content |
|---|---|---|
| `00-books.csv` | agent, from the operator's list | `seq, label_code_proposed, label_description, description_source, label_pk, label_pk_source, instruments, status` |
| `book-labels.json` | agent | branch PK, country code, the dummy decision; when labels are missing, `pk_rule` and `model_columns` (shape: [`book-labels.example.json`](book-labels.example.json)) |
| `00-decisions.md` | agent | the BOX FE team's answers (decision · value · name · role · date · evidence) |
| `01-evidence/Q-10f-book-labels-target.csv` | operator | which labels exist in the target (`PK, CODE, DESCRIPTION`) |
| `01-evidence/Q-10c-dummy-book-target.csv` | operator | branches already using an existing dummy (`FK_BRANCH, COUNT(*)`) |
| `01-evidence/Q-10e-domains-columns.csv` | operator | the label table's columns — only when labels are missing |
| `books-register.csv` | **script** | every book and the dummy: `kind, seq, code, description, pk, status, origin, evidence` |
| `book-labels-PROPOSAL.sql` | **script** | only when labels are missing: the inserts, for the BOX FE team |
| `book-labels-report.md` | **script** | found / to create / blocking |

Queries: [`fe-config-mining.md`](../../docs/reference/queries/fe-config-mining.md) Q-10c (c), Q-10d, Q-10e,
Q-10f.

## How to run

```bash
python3 scripts/set_up_book_labels.py runs/<BRANCH>/<env>/books/
```

Exit `0` every label exists (register complete) · `1` refused (reasons printed) · `4` labels to create
(proposal written).

## Steps

1. **Ask for the books** if `00-books.csv` is missing: the book labels exactly as the data lake sends
   them. Ask the operator to confirm any character a screenshot makes ambiguous (`0` / `O`, spaces).
2. **Write the codes** `X<CC>01`, `02`… in the order given, after any `X<CC>` code already in the target;
   `book-labels.json`: branch PK (Q-G1), country code.
3. **Dummy card** to the BOX FE team, after Q-10d: an existing shared label (`"mode": "existing"`, its
   code) or a new one (`"mode": "create"`, code and description). Record the answer as a decision.
4. The operator runs **Q-10f** in the target (with the dummy's code), and **Q-10c (c)** with an existing
   dummy's PK; save both in `01-evidence/`. Run the script.
5. **Exit 1:** fix what it names. A **conflict** (a code with another description, or a description under
   another code) is a person's decision — never reuse, rename or re-describe a label to make it fit.
6. **Exit 4 with `book-labels-rule-missing`:** the **PK-rule card** to the BOX FE team — `fixed` (they give
   each PK: `label_pk` in `00-books.csv`, `dummy.pk` for a new dummy) or `expression` (they name it) — and
   the model row (`FK_OWNER_OBJ = 17910.4` plus every NOT NULL column Q-10e lists). The operator runs Q-10e.
   Write `pk_rule` and `model_columns`; run again.
7. **Exit 4 with a proposal:** hand `book-labels-PROPOSAL.sql` to the BOX FE team. It inserts only the
   missing labels, stops inserting nothing if any code, description or PK already exists, and does not
   commit. Meanwhile FE step 11 stays `EXTERNAL_CHECK_REQUIRED`.
8. After they run it: Q-10f again, the script again → **exit 0**. The register is complete: FE step 11
   carries exactly its book PKs and its dummy PK; the jobs agent takes its codes.

## Decision cards (one at a time; record each in `00-decisions.md`)

```text
DECISION - Dummy book label in <env>
Why it matters : every instrument needs a (dummy book x instrument) row in FE step 11
Evidence       : Q-10d - reference dummy '<CODE> - <DESCRIPTION>'; target candidates with branch counts
Options        : A) existing label <CODE> (used by <n> branches)   B) another: ____   C) create one: code, description
Recommendation : the candidate matching the reference CODE that the most target branches use
If wrong       : that (book, instrument) is never scheduled by the FE batch - silently
Authority      : BOX FE team
```

```text
DECISION - PK rule for the labels to create in <env>
Why it matters : <n> book label(s) (and the dummy, if new) do not exist; their PK is fixed
Evidence       : books-register.csv (to_create), Q-10e (NOT NULL columns)
Options        : A) fixed PKs - give one per label   B) allocation expression: ____
Model row      : FK_OWNER_OBJ = 17910.4, plus <NOT NULL columns>
If wrong       : a duplicate or wrong label, and everything keyed on it
Authority      : BOX FE team
```

## Output

`books-register.csv` complete (every row `exists`, a dummy row), `book-labels-report.md`, the decisions —
or, while labels are missing, `book-labels-PROPOSAL.sql` handed to the BOX FE team.

**Success** = the script exits 0.

## Failure modes

| Failure | Detection (script code) | Handling |
|---|---|---|
| No book list | `book-list-missing` | ask the operator (step 1) |
| No configuration | `book-config-missing` | write `book-labels.json` (step 2) |
| Q-10f / Q-10c (c) / Q-10e missing | `evidence-missing` | run the query named in the message |
| A code breaks `X<CC><nn>`, or has another country code | `book-label-code-bad` | fix `00-books.csv` |
| A code exists with another description, or a description under another code | `book-label-conflict` | stop; a person decides |
| Labels to create, no PK rule | `book-labels-rule-missing` | PK-rule card (step 6) |
| PK rule neither `fixed` nor a valid expression | `book-label-pk-rule` | PK-rule card again |
| `fixed` rule, a label without its PK | `book-label-pk-missing` | ask the BOX FE team for it |
| `FK_OWNER_OBJ` not `17910.4` | `book-label-owner` | fix the model row |
| A model column not in the table, or a NOT NULL column unset | `target-column-missing`, `target-not-null-not-written`, `target-null-in-not-null` | fix the model row from Q-10e |
| No dummy decided | `dummy-missing` | dummy card (step 3) |
| The dummy is one of the books | `dummy-is-a-book` | dummy card again |
| An existing dummy absent from the target | `dummy-label-not-in-target` | dummy card again |
| No other branch uses the existing dummy | `dummy-not-in-use` | dummy card again: a shared label, or create one |
| A decision cited without name, role or date | `decision-missing` | record the answer with name, role and date |

## Never

- Run the proposal. The BOX FE team reviews it and runs it.
- Choose a PK, or change a description, a code or a dummy to make a row fit.
- Create a label the book list does not name.

## Eval cases

[`evals/cases/set-up-book-labels-happy-path.md`](../../evals/cases/set-up-book-labels-happy-path.md),
[`evals/cases/set-up-book-labels-failure-paths.md`](../../evals/cases/set-up-book-labels-failure-paths.md).
