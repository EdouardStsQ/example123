# Tier 1 PROD — batch job configuration (reference copies)

Real configuration files of an **environment**, not of a branch run: the jobs every branch in Tier 1
(Madrid, SLB) runs in PROD. Read by [`box-batch-jobs-agent`](../../../agents/box-batch-jobs-agent/AGENT.md)
(reference inventory, explain mode). Same care as any run folder: real values, never pasted into `docs/`.

## Put here (operator)

| File | What | Where it comes from |
|---|---|---|
| `db.conf` | database jobs: `<JOB>:<type>:<flag>:<PL/SQL call>;` | Unix app tree, Tier 1 PROD |
| `shell.conf` | Unix script jobs: `<JOB> : <debug> : <chdir> : <shell script> : <params>` | Unix app tree, Tier 1 PROD (header `/Projectos/GM/Unix/gm/etc/shell.conf`) |
| `mbjbox.sh` | the script most BOX accounting jobs in `shell.conf` run — a launcher for `MBJBOXACC.jar` (chain doc L2) | Unix app tree, `bin/` |
| `conf-BOX-files.txt` *(optional)* | `ls -l` of `/appl/gm/bin/GBOCL_MBJBATCH/conf/BOX` — names only; never copy credentials | Unix app tree |
| `EXTRACTED.md` | one line per file: date copied, server/path, who copied it | operator |

Copy the files **unchanged** (no reformatting, no trimming): line numbers are cited as evidence. Before
pushing, replace any password or connection string with a placeholder and say so in `EXTRACTED.md`.

**Saved on the operator's side 2026-10-01** (`db.conf`, `shell.conf`, `mbjbox.sh`). A repo zip delivered by Claude
does not contain them — unzip it **without deleting this folder's files**.

## Then

```bash
python3 scripts/parse_job_confs.py runs/_reference/tier1-prod/
```

writes `jobs-inventory.csv` here — one row per job line (active or commented out): file, line, banner,
family (BOX / GBO / OTHER, and why), decoded name (`GMBX<n><CC><nn>D<ss>` or old naming), scope (product
chain or generic), and for `db.conf` the entry point and `f_ExecuteGroup` arguments.

**Checked 2026-10-01** (Devin, `jobs-inventory-check.md`): coverage complete (the 44 unmatched lines are
comment headings such as `# SWAP:`), 0 `OTHER` rows, all `f_ExecuteGroup` lines decoded, all `mbjbox.sh` params
`<job> $ODATE 0000`, spot checks match. Findings: 822 job names in **both** files (→ `shell.conf` runs, `db.conf` line legacy —
BOX dev), `GMBX8` = Cap & Floors, 446 `ES` `mbjbox.sh` lines (MBJ row count pending).

**Refresh** when PROD changes (a new branch, book or product): copy the files again, update
`EXTRACTED.md`, re-run the parser. A Tier 2 copy goes in `runs/_reference/tier2-<env>/` the same way.
