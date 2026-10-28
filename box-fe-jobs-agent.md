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
- `[2026-10-06]` With the reference's load-prices folder and its `pro.json`: a load-prices folder for the target with
  only the reference branch's jobs (`GMBX0<TT>00D01`, `D02`), their `db.conf` lines first, the FE folder file without
  the PRO-only wait, and `descriptors/<FE folder>/pro.json` re-pointed (load-price event renamed, GBO event as answered,
  host replace and one-book entries for review). A queue-job rename on `GMBX0<TT>00D01` → name conflict, next free
  name suggested.
- `[2026-10-06]` Instruments come from the registry (never asked again); per instrument the reference is the branch that
  runs it (`--references`). With the Data Lake JSONs: each target book's first step waits for its own Data Lake job of the
  same type (label description = `book_vr`); a book with none is asked with the closest `book_vr`. A GBO wait shows what
  the GBO job runs and, with the target's job confs, its look-alike (INFERRED).
- `[2026-10-06]` An instrument `skip` in the jobs plan (no onboarded branch runs it in BOX) is shown with its reason and
  never built or asked; one no branch runs and not yet in the plan → `skip` proposed; a forced `reference` is used.
  Building it anyway → `nothing-to-copy`, naming the skip.
- `[2026-10-07]` BOX expert review: the folder file carries the **DEV** host; PRE / PRO hosts come from
  `controlm.env` into `descriptors/<folder>/{pre,pro}.json` (both folders), other per-environment values copied from
  the reference are listed **to confirm**, an activation date not given is **review**. No job of another instrument is
  copied (`GMBX6/7…D11`): a wait on it becomes that job's own waits (D03 → D02, OR-groups merged), or stays (renamed)
  when that instrument is `built` in the plan. `-NOK` events of `If` blocks are renamed. The old queue job is suggested
  from its siblings (`GMBX1NY00D01`); `KEEP` of an SLB job's event is refused. With `dbconf_format: pgt_prg` every line
  is `<JOB>:T:P:PGT_PRG.Pkg_BatchProcess.p_ExecuteGroup(group, <wrapper>.PKG_GMBATCHPROCESS.<branch constant>, to_date('$ODATE','YYYYMMDD'),
  <instrument | NULL>, to_char(sysdate,'RRRR-mm-DD HH24'||CHR(58)||'MI'||CHR(58)||'SS'), 0, <label | NULL>, NULL)` — the branch constant on per-book
  lines too — exit 0. **Fail:** a core line with `NULL` or the PK typed in as branch, the date as `P_TIME`, a `:` inside
  the call `[2026-10-22]`.
- `[2026-10-08]` With every instrument in one run: one FE folder (shared jobs once), the run's instruments' waits on
  each other kept; one Initial Accounting job per instrument (`GMBX<n><TT>00D02`, group `2409.65`) with its `db.conf`
  line, the books' `D02` waiting for them, `acc-handoff.json` for `box-acc-jobs-agent`; `OrderMethod` PRE `ON DEMAND`,
  PRO `JAC1400` from the inputs (never SLB's); `unix/job_unix.sh` with `add_new_jobs.ksh` and one `cp db_job` +
  `chmod 755` per `db.conf` line. **Fail:** an Initial Accounting job missing or in the FE folder, SLB's `JAC0500`.
- `[2026-10-09]` Books in `books-excluded.csv` (the branch folder's, `runs/<BRANCH>/branch/books/`, since 2026-10-27; an environment's own overrides it) get no job and no `db.conf` line; an old-named job of another reference
  book (label `XLB03`) is that step of each target book (no rename asked); a GBO look-alike is proposed only on the
  same group (constants resolved) / same script / same function + argument, else "no confident match";
  `out/unix/` = `job_unix.sh` (delete + add, then `cp` / `chmod`), `db_nuevo.conf`, `db_delete.txt`, NY's
  `delete_jobsBX.ksh`; the PR is opened only after the operator's yes on `pr-summary.md`, from a new branch, never
  merged. **Fail:** a PR without the yes, a push to the default branch, any other repo written.
- `[2026-10-15]` IRS run review: the shared per-book jobs `GMBX0<TT><bk>D01-D03` come from **one** reference book
  (`reference.generic_book`, or the majority form of the complete, new-named books without a cross-book wait —
  `generic-book-chosen`); a wait on another reference book's shared job (also old-named `GMBOX00nn`, by label and
  group) is read as that book's; a reference job waiting on another book's job → `reference-cross-book-wait`, that
  book not used. Template book not given → the book with the most active jobs of the instrument (counts shown), never
  book 01 because it is first. An instrument `built` in the plan but not in the run → refused
  (`shared-jobs-other-run`) unless `separate_run` gives the reason. An external event answered `{desk}` / `<OPEN …>` →
  OPEN, exit 4. Each pending question is asked with its SLB job's context (`explain-box-job`). **Fail:** shared jobs
  of two reference books mixed, a D01 taken from the next book's job, two runs delivering the same shared job, a
  placeholder event in `out/`.
- **Fail:** a job of another instrument in the output, an SLB event name left anywhere (also `-NOK`), the PRE host
  in the folder file, any hand-written JSON, a guessed folder name, a reference host in the output, or an order taken from
  step numbers instead of events.
- `[2026-10-20]` A job or label of an excluded book anywhere in `out/` (except `report.md`) → refused
  `excluded-book-built` after the build.

## Regression on a finished run `[2026-10-20]`

After any change to the agent's scripts, inputs format or prompts, on the branch's last frozen run:
`python3 scripts/regress_fe_jobs.py <run folder>/` (`--map <old repo path>=<new>` for another session's clones).
**Pass:** exit 0, every deliverable of `out/` identical. Exit 1: each `DIFFERS` file is explained by a CHANGELOG entry
since that run, or it is a regression. Mechanically covered on synthetic runs (one and several instruments) by
`scripts/tests/test_validate_run_output.py` (`regress_fe_jobs.py` cases).

## Session checklist — a real Devin run `[2026-10-20]`

What the tests cannot see (how the prompts are followed). Tick each on the transcript of a run started with a branch
kickoff or with `prompts/build.md`:

1. **Step 0:** the branch and environment taken from the kickoff (or asked once when none); the repos to attach listed
   from the registry rows, the missing ones named; the copies under `runs/_reference/external/` checked.
2. **Step 1:** `AGENT.md`, the inputs file, the branch's `fe-jobs/README.md` and open items read; the skills, the
   batch chain doc, the reference's facts read at Step 3, the script header at Step 5 — not all at the start.
3. **Questions:** the environment confirmed, then what to build; the instruments from the registry and the jobs plan
   (`skip` ones shown with their reason, never built); one question at a time, each with its reference context and a
   suggestion; nothing written the operator did not answer.
4. **Answers already in the inputs are not asked again** (external events, servers, folder names, OrderMethod…);
   an `<ask …>` / `<confirm …>` is asked; every value not asked in the session listed with its source and confirmed
   before the first build `[2026-10-21]`.
5. **Outputs:** exit 0, or 4 with the OPEN lines listed; no `excluded-book-built`; the report shown with the GBO events
   checked / not checked; the plan row updated; the run committed.
6. **The PR step, then the freeze:** asked per repo on `pr-summary.md`, opened only on yes, from a new branch, never
   merged; **then** the run frozen (Step 8) `[2026-10-21]`.

**Fail:** a step skipped, a question asked twice or several at once, a value written without an answer, an answer
offered that no input of the script takes, the run frozen before the PR question, `out/` edited by hand, any other
repo written.

