# Tier 1 PROD — batch job configuration (reference copies)

Real configuration files of an **environment**, not of a branch run: the jobs every branch in Tier 1
(Madrid, SLB) runs in PROD. Read by [`box-batch-jobs-agent`](../../../agents/box-batch-jobs-agent/AGENT.md)
(reference inventory, explain mode). Same care as any run folder: real values, never pasted into `docs/`.

## Put here (operator)

| File | What | Where it comes from |
|---|---|---|
| `db.conf` | database jobs: `<JOB>:<type>:<flag>:<PL/SQL call>;` | Unix app tree, Tier 1 PROD |
| `shell.conf` | Unix script jobs: `<JOB> : <debug> : <chdir> : <shell script> : <params>` | Unix app tree, Tier 1 PROD (header `/Projectos/GM/Unix/gm/etc/shell.conf`) |
| `mbjbox.sh` *(if you can)* | the script most BOX accounting jobs in `shell.conf` run (`bin/mbjbox.sh <JOB> $ODATE 0000`) — it decides where those jobs get their branch, product, book and group | Unix app tree, `bin/` |
| `EXTRACTED.md` | one line per file: date copied, server/path, who copied it | operator |

Copy the files **unchanged** (no reformatting, no trimming): line numbers are cited as evidence.

## Then

```bash
python3 scripts/parse_job_confs.py runs/_reference/tier1-prod/
```

writes `jobs-inventory.csv` here — one row per job line (active or commented out): file, line, banner,
family (BOX / GBO / OTHER, and why), decoded name (`GMBX<n><CC><nn>D<ss>` or old naming), scope (product
chain or generic), and for `db.conf` the entry point and `f_ExecuteGroup` arguments.

**Refresh** when PROD changes (a new branch, book or product): copy the files again, update
`EXTRACTED.md`, re-run the parser. A Tier 2 copy goes in `runs/_reference/tier2-<env>/` the same way.
