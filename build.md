# `box-acc-jobs-agent` — build a branch's BOX ACC jobs (the procedure, any branch, any tier)

> **How to start — nothing to paste.** Open a Devin session with this repo attached and type:
> **`Run automation/agents/box-acc-jobs-agent/prompts/build.md`** — Devin asks the branch and the environment, then
> everything else one question at a time. A branch may also have a short kickoff that names them for you (e.g.
> [`build-ny-sch-tier2.md`](build-ny-sch-tier2.md)); it adds no step.

The procedure is the same for every branch and tier; **a branch is data**: its row in
`docs/reference/branch-registry.csv`, its inputs file
`runs/<BRANCH>/<tier>-<env>/acc-jobs/acc-jobs-inputs.<BRANCH>.json`, its `runs/<BRANCH>/<tier>-<env>/acc-jobs/README.md`
and its open items. Run **after `box-fe-jobs-agent`** for the same branch and environment: its `acc-handoff.json` names
the Initial Accounting jobs.

**What a run produces** (`<run folder>/out/`, a proposal for the BOX team — nothing deployed, nothing run): the
target's ACC Control-M folder JSON, `shell.conf` lines (`mbjbox.sh`) for every per-book step, `db.conf` core-call
lines for the branch-level steps, the MBJ rows as four SQL files, the Unix package, the report.

| | |
|---|---|
| ⛔ **Write protection** | No commit, branch, push, PR, draft PR or edit on any repo except this automation repo — **one exception** ([ADR 0012](../../../docs/decisions/0012-target-repo-pr-exception.md)): a PR of `projects/<repo>.json` on the target's own ACC Control-M repo (registry `acc_controlm_repo`), from a new branch, never merged, **only after the operator's yes** (Step 7) |
| **Database** | Devin gets no connection and never runs the SQL. The operator runs the queries of Step 4 and returns the CSVs; the BOX team runs the SQL files |
| 💬 **The operator can ask** | at any time *"what does job `<JOB>` do?"* — skill `explain-box-job` (read its `SKILL.md` the first time), then repeat the pending question |

---

You are running as the `box-acc-jobs-agent`.

**Step 0 — repo root, branch, repos.**
1. The repo root: the folder containing `agents/` (`cib-box-aukinbranch`, folder `automation/`); every path below is
   relative to it. Not found → ask the operator for the path.
2. **The branch** `<BRANCH>` and **its environment folder** `<tier>-<env>` — from the kickoff if one named them, else
   **ask** (show the registry codes and the folders under `runs/<BRANCH>/`). Not in the registry → stop.
3. **Its inputs file** `runs/<BRANCH>/<tier>-<env>/acc-jobs/acc-jobs-inputs.<BRANCH>.json`. None → copy
   `agents/box-acc-jobs-agent/templates/acc-jobs-inputs.example.json` there, fill what the registry gives and say every
   `<ask …>` left.
4. **The repos to attach**, from the registry rows: read-only — the reference's `acc_controlm_repo` and
   `fe_controlm_repo`, optionally `cib-boxacc-dbboxacc`; the PR step only — the target's `acc_controlm_repo`. Say which
   are missing.

**Step 1 — read now:** `agents/box-acc-jobs-agent/AGENT.md`, the inputs file, the branch's `acc-jobs/README.md` and
its open items. The rest when its step comes.

**Step 2 — the environment, the run folder, the FE run.**
1. Confirm the environment (Step 0's) and the instruments: the registry's `instruments` minus the `skip` ones of
   `runs/<BRANCH>/<tier>-<env>/fe-jobs/instrument-plan.csv` — every instrument in one run.
2. `python3 scripts/new_run.py --branch <BRANCH> --tier <tier> --env <env> --area acc-jobs --name <all or instrument>`;
   create `acc-jobs-inputs.json` from the branch's inputs file (answers carried over only from a run the operator
   names, one by one).
3. **The FE run**: `target.fe_run` = the branch's latest finished `fe-jobs/` run of this environment
   (`python3 scripts/new_run.py --list runs/<BRANCH>/<tier>-<env>/fe-jobs`) — confirm with the operator. None → say
   so: Initial Accounting jobs are named by rule and FE waits are not checked.

**Step 3 — the reference chain.** **Read now:** `skills/find-box-jobs/SKILL.md`, `docs/reference/job-chains/box-batch-chain.md`
(L2, *The ACC chain*) and `docs/reference/job-chains/reference-<reference>-acc.md` when it exists. Per instrument:

```bash
python3 scripts/find_jobs.py runs/_reference/tier1-prod/ --side ACC --product <instrument> --branch <reference> \
    --controlm <its ACC folder repo> <its FE folder repo> --out <run folder>/01-evidence/reference-acc-chain-<instrument>
```

`--side ACC` lists the `mbjbox.sh` jobs only: the ACC folder also holds `db.conf` jobs (Initial Accounting, ruler
updates, steps a reference still runs from `db.conf`) — `build_acc_jobs.py` reads the folder itself. Show the chain. Propose the **template book** per instrument (the reference doc's, else the script's choice at Step 5)
and write the operator's answer with its date.

**Step 4 — the queries** (one at a time, values filled in, no `&&`; catalogue `docs/reference/queries/box-jobs-queries.md`):
- **J-R2** in the reference tier (the reference's MBJ rows, `&&REFERENCE_BRANCH_PK` = its branch PK) →
  `01-evidence/J-R2-mbj-properties-REF.csv`; `reference.mbj_csv` = that file; ask **in which environment** it ran and
  write it in `reference.mbj_source_env`. Skip if the branch's evidence already holds it (say so).
- **J-E9** in the target tier, owner `BOX_ACC` → `readiness.mbj_engine` (`deployed` / `not deployed`).
- `mbj.auth_code`: the target installation's auth code (Q-G3c — the FE configs run has it).
- `mbj.calendar` not answered → the calendar query of J-R2's notes (the processing calendars) and ask the BOX expert.

**Step 5 — run, ask, run again.** **Read now:** the header of `scripts/build_acc_jobs.py` and
`skills/explain-box-job/SKILL.md`.

```bash
python3 scripts/build_acc_jobs.py <run folder>/
```

Each `REFUSED` line names one input: ask **that one question**, write the answer, run again. Never edit `out/`.
- **MIC decisions** (`mic-decision-missing`) — every run, per instrument: show the reference's pattern the message
  gives (its MIC end-of-day steps, its sender types) and ask `keep` / `drop` (or `none`) and `reference` / `lastly` /
  `none`. The BOX expert decides; never answer from the reference.
- **Renames** and **external events** — `pending-questions.md`, one row at a time, each with its reference job's
  context (skill `explain-box-job`: what it runs, who waits for it) and the suggestion. `<OPEN - what, who confirms>`
  for an answer owed by another team.
- `mbj.pk_call`, `mbj.calendar` — the BOX dev / BOX expert's answer, with its source.

**Step 6 — finish.** Show `out/report.md` and say: per instrument the template book, the steps and how each runs (the
steps the reference ran from `db.conf` now in `shell.conf`), the MIC decisions, the MBJ rows and where their values
came from (`mbj-row-from-other-book`), the decisions to review (reference defects), the readiness of the MBJ engine,
that the environment descriptors are not generated, and that the files are a proposal. Commit the run folder to the
automation repo only.

**Step 6b — freeze:** once committed (and the PR step done or declined): `python3 scripts/new_run.py --freeze <run folder>`.

**Step 7 — the PR on the target's own ACC repo** (ADR 0012), only once Step 6 is done with no refusal:

```bash
python3 scripts/stage_target_pr.py <run folder>/ --checkout <target ACC repo>=<its clone>
```

Show `out/pr/pr-summary.md` and ask: *"Open a PR on `<repo>` from a new branch `box-acc-jobs/<BRANCH>-<date>` adding /
replacing `projects/<repo>.json` (folder `<FOLDER>`, N jobs)? yes / no"*. Only on **yes**: create the branch, copy the
file, commit, push **the new branch**, open the PR. Never push to the default branch, never merge.

**Regression check — when the agent's scripts, inputs format or prompts changed since the branch's last finished run:**

```bash
python3 scripts/regress_fe_jobs.py <the last frozen acc-jobs run>/ [--map <its old repo path>=<this session's>]
```

Exit 0 = identical deliverables; exit 1 = each `DIFFERS` file explained by a CHANGELOG entry, or a regression to report.
