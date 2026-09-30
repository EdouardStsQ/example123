# 0009. Book and dummy labels are a skill of their own, not FE pre-steps

Date: 2026-09-30
Status: accepted — supersedes the P2 part of [0007](0007-pre-steps-pk-and-dummy-label.md) and the P3 pre-step
added earlier the same day

## Context

On 2026-09-30 the FE agent got pre-step P3 (the branch's book labels), built inside `render_sql.py` and
driven by the FE `values.json`, next to P2 (the dummy label). But books are not FE-only: FE step 11, the BOX
batch jobs (named from the label: `XNY02` → `GMBX3NY02D07`), the ACC MBJ properties and the Data-Lake feeds
all key on them. And P2 and P3 wrote the same table under two different PK rules (P2 refused a typed PK;
labels have fixed PKs). `[stated: operator, 2026-09-30]` *"its going to be better to fix issues if its a
skill. and its not only related to sigom box fe configs."*

## Decision

- Skill **`set-up-book-labels`** with its own script `scripts/set_up_book_labels.py` and its own folder
  `runs/<BRANCH>/<env>/books/` (spans runs): book list, decisions, evidence, and the outputs — a
  **book register** every agent reads, and the proposal SQL for the BOX FE team.
- It covers **both** the book labels and the dummy label, under one PK rule decided by the BOX FE team
  (fixed PKs, or an allocation expression).
- The FE renderer keeps **P1** and a **step-11 gate**: it re-evaluates the book folder (so a stale register
  cannot pass), refuses step 11 until every label exists, and requires step 11's books and dummy to be the
  register's. The MIS Book tab rows themselves stay FE configuration.
- `values.json` `prechecks` is retired (`values-moved`).

## Alternatives considered

- **Keep P2/P3 in the renderer.** Every other consumer would re-implement or re-read FE internals, and a
  rule change would be edited in several places.
- **A skill with no script.** The rules are exact-match and collision rules; prose alone would drift.

## Consequences

- One place to fix label issues, with its own tests; the FE agent and the jobs agent call it.
- The book folder is the input of the batch-jobs agent's job matrix.
- Run folders move `00-books.csv` into `books/`.
