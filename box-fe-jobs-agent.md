# Case: NY-like branch's deposits FE jobs from an SLB-like reference

Covers: box-fe-jobs-agent (full run)
Type: happy path + the questions it must ask

Mechanically covered by `scripts/tests/test_validate_run_output.py` (`build_fe_jobs:` cases), on a synthetic
reference (placeholder books `BOOK_A`, `BOOK_B`).

## Given

- A reference folder: per book `GMBX0<RF><bb>D01-D03` (generic) → `GMBX1<RF><bb>D04-D06` (deposits), `D06` waiting
  for an old-named branch queue job (`FromTime`, no waits); a branch-level deposits job waiting for every book's
  `D03` and for a GBO job's event; `G010014-` hand-off events on `D04` / `D06`.
- Their `db.conf` lines through the reference wrapper, passing the book label.
- A target with two books (one label still `to_create`) and a 5-argument wrapper.

## When

The agent runs `build_fe_jobs.py`, answering each refusal by asking the operator.

## Then

- It asks, one at a time, for: the Control-M folder values, the new name of the old queue job, the mapping of the
  GBO event (`KEEP`), the target wrapper's constants. It never copies host, server, application, calendar or a
  developer ID from the reference.
- Output: 12 per-book jobs (6 × 2 books) + 2 branch jobs; `D06` of book 2 waits for the renamed queue job and book 2's
  `D05`; the branch job waits for both target books' `D03` and the kept GBO event; `G010014-` events renamed.
- `db.conf.proposal`: target job names, wrapper owner, branch constant and labels; the 12 label lines `# OPEN
  checkpoint 3`; exit 4. A warning that one label is not created yet.
- `[2026-10-06]` A rename or external event missing → `pending-questions.md` with, per row, the emitter, folder,
  side · product · level and a suggestion (ACC → `DROP` for now; an approved instrument → its target name; not approved
  or ended → `DROP`; not found → ask the BOX team). The agent asks them one at a time and writes only the operator's
  answer. Asked "what does job X do?" mid-run, it answers with skill `explain-box-job` and repeats the pending question.
- **Fail:** any hand-written JSON, a guessed folder name, a reference host in the output, or an order taken from
  step numbers instead of events.
