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
  is `<JOB>:T:P:PGT_PRG.Pkg_BatchProcess.p_ExecuteGroup(group, <branch PK>, to_date('$ODATE','YYYYMMDD'),
  <instrument | NULL>, to_char(sysdate,'RRRR-mm-DD HH24:MI:SS'), 0, <label | NULL>, NULL)` — the branch PK on per-book
  lines too — exit 0. **Fail:** a core line with `NULL` as branch or the date as `P_TIME`.
- **Fail:** a job of another instrument in the output, an SLB event name left anywhere (also `-NOK`), the PRE host
  in the folder file, any hand-written JSON, a guessed folder name, a reference host in the output, or an order taken from
  step numbers instead of events.
