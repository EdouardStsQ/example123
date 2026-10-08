# 0012. One exception to read-only: a PR of the target branch's own Control-M folder JSONs

Date: 2026-10-09
Status: accepted

## Context

Every BOX, Control-M and `cib-auki` repo is read-only for every agent: no commit, branch, push, PR, draft PR,
suggested diff or edit (hard rule since the first runs). `[BOX job expert via operator, 2026-10-09]` created the
repos NY's jobs will be deployed from — `cib-boxfin-t2usnyfe` (FE, as SLB's `cib-boxfin-t1mdslbfe`),
`cib-boxfin-t2nyloadprices` (load prices), `cib-boxacc-t2usnyac` (ACC, later) — each holding one file
`projects/<repo>.json`. `[stated: operator, 2026-10-09]` `box-fe-jobs-agent` should open the PR of its JSONs there,
**after asking for confirmation**, and keep writing them in the run's `out/` folder as before.

## Decision

1. **The only write outside this automation repo:** the target branch's own Control-M repos listed in
   `docs/reference/branch-registry.csv` (`fe_controlm_repo`, `prereq_controlm_repos`, later `acc_controlm_repo`), and
   in them only `projects/<repo>.json`.
2. **A PR from a new branch** (`box-fe-jobs/<BRANCH>-<date>`): never a push to the default branch, never a merge.
3. **Only after the operator's yes**, per repo, on a summary (`scripts/stage_target_pr.py` → `out/pr/pr-summary.md`:
   repo, file, Control-M folder, job count, changes against the repo's current file). No → nothing is pushed.
4. The file content is the run's `out/<FOLDER>.json`, unchanged — only the file name is the repo's.
5. Unchanged: the reference repos, the database repos and `cib-auki-aukicnfgsrvc` stay read-only (descriptor PRs are
   manual while that repo is in another organisation); `db.conf.proposal` and the Unix package go to the BOX / Unix
   team.

## Consequences

The agents' charters say so (`box-fe-jobs-agent` hard rule 1; `box-acc-jobs-agent` will reuse it for
`acc_controlm_repo`). A new branch needs its target repos in the registry before its PR step.
