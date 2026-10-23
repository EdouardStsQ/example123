# Case: NY-like branch's ACC jobs from an SLB-like reference

Covers: box-acc-jobs-agent (full run)
Type: happy path + the questions it must ask

Mechanically covered by `scripts/tests/test_validate_run_output.py` (`build_acc_jobs` cases), on a synthetic
reference (`scripts/tests/acc_fixture.py`, placeholder books `BOOK_A`, `BOOK_B`).

## Given

- A reference ACC folder: depos — old-named Initial Accounting, per book D07 → D08 → D12 (MIC end of day), old-named
  ruler update waiting every book's D12, branch D13; IRS — new-named Initial Accounting, per book D07 → D09, ruler
  update waiting every book's D09 and a GBO event. Per-book steps wait for the book's FE D04 / D06.
- The reference's `shell.conf` (`mbjbox.sh`) for most per-book steps, one per-book step in `db.conf` only; the ruler
  updates and Initial Accounting in `db.conf` only.
- The reference's MBJ rows (J-R2 CSV), one step without its own row, one row whose label is not its name's book.
- The FE agent's run: `acc-handoff.json` and the FE folder; a target with two books (one label still `to_create`).

## Then

- Folder: Initial Accounting from the hand-off; per-book steps once per target book; the ruler updates renamed (old
  name → asked) and waiting every target book's last step; D13 waiting the ruler update; each D07 waiting Initial
  Accounting and the same book's FE D06, each D08 / D09 the FE D04; the GBO wait as answered (`DROP-REVIEW` listed).
  Environment fields from the inputs; no developer ID; descriptions re-booked.
- `shell.conf`: every per-book step and D13 as `mbjbox.sh <JOB>` — also the step the reference runs from `db.conf`
  (listed for review); `db.conf`: the ruler updates as the core call; no Initial Accounting line.
- SQL: rehearsal / config / verify / rollback, ASCII, lint clean; one row per `shell.conf` job; labels by code,
  the asked calendar, PKs from `mbj.pk_call` checked against the auth code; verify checks the MBJ engine in `BOX_ACC`.
- MIC: `keep` keeps D12 / D13 (`MIC_EOD 1`); `drop` removes them and the ruler update inherits their waits; a missing
  decision, or `keep` where the reference has none → refused. Sender type as decided.
- Refused: no rename for an old-named job, a GBO wait unanswered, no MBJ calendar, an instrument the reference does
  not run, a template book with no ACC job; **no FE run, an FE run that is not one, one that did not build every
  instrument of the run, one whose hand-off misses an Initial Accounting job or names another ACC folder**. An FE run
  not frozen is warned. An excluded book gets no job and no row.
- **A step with no MBJ row in any book:** refused (`mbj-row-missing`, naming `mbj.missing_rows.<job>`); `from:<job>`
  copies that row with the step's own `db.conf` group; `<OPEN …>` builds the job, leaves its row out, exit 4; a job of
  another instrument refused. **Test values** (`test_values`): TEST in the report and the SQL, rehearsal / config stop
  first, exit 4, no PR. The hand-off's Initial Accounting drafts take `controlm.CreatedBy`. A row from another book
  warned once per step. `unix.existing_scripts` not reported missing.
- **`db.conf` branch argument:** the target wrapper's branch constant, the FE run's; refused when it differs from the
  FE run's or is not in its J-E4 CSV `[2026-10-22]`.
- **Fail:** a reference PK, branch, label or calendar in the SQL; the branch PK typed in a `db.conf` line; an Initial Accounting `db.conf` line; a per-book
  step left in `db.conf`; a MIC decision taken without asking; any hand-written file.

## Regression on a finished run

After any change to the agent's scripts, inputs format or prompts:
`python3 scripts/regress_fe_jobs.py <the last frozen acc-jobs run>/` — exit 0, every deliverable identical; exit 1,
each `DIFFERS` file explained by a CHANGELOG entry or reported as a regression.

## Session checklist — a real Devin run

1. **Step 0:** the branch and environment from the kickoff (or asked once); the repos listed from the registry rows.
2. **Step 2:** the FE runs listed with their instruments; the latest frozen one covering every instrument proposed and
   confirmed (`target.fe_run`) — the agent runs after `box-fe-jobs-agent`.
3. **Step 3–4:** the reference ACC chain shown per instrument; the template book confirmed; J-R2's environment
   recorded; J-E9 checked with owner `BOX_ACC`.
4. **Questions:** one at a time (two linked MIC choices in one form are acceptable); the MIC decisions asked per
   instrument every run, with the reference's pattern; renames and external events with their reference context;
   every value not asked in the session (inputs file, FE run, FE configs run) listed with its source and confirmed
   before the first build; test answers in `test_values`; nothing written the operator did not answer.
5. **Outputs:** exit 0 (or 4 with the OPEN lines); the report shown with readiness and decisions to review; the run
   committed.
6. **The PR step, then the freeze:** asked on `pr-summary.md` (not offered with `test_values`), opened only on yes,
   from a new branch, never merged; then the run frozen (Step 8); a test run marked "TEST - not deliverable" in
   `RUNS.md`.

**Fail:** a step skipped, a question asked twice, an answer offered that no input of the script takes (e.g. "exclude
the step" for `mbj-row-missing` before `mbj.missing_rows` existed — 2026-10-21), the SQL run by the agent, the run
frozen before the PR question, `out/` or the J-R2 CSV edited by hand, any other repo written.
