# Case: book labels refused - a clash with an existing label, and the branch's own book as the dummy

Covers: set-up-book-labels
Type: failure path

Mechanically covered by `scripts/tests/test_validate_run_output.py` (the `labels skill refuses` cases).

## Given (input state)

As the happy path, except: (1) the target already has a label with `BOOK_B`'s description under another
code; (2) the dummy decision names one of the branch's own books (run 6's mistake); (3) one code in the
list is `NY001`, not `X<CC><nn>`.

## When (action)

The agent runs `scripts/set_up_book_labels.py`.

## Then (expected outcome)

- Exit 1, **no proposal written**, and the report lists `book-label-conflict` (never reusing, renaming or
  re-describing the existing label), `dummy-is-a-book`, and `book-label-code-bad`.
- The agent puts the conflict and the dummy back to the BOX FE team as decision cards and fixes the code in
  the list; it chooses nothing itself.
