# Tier 2 PRE — batch job configuration (reference copies)

Real configuration files of the **Tier 2 PRE environment** (where NY_SCH is onboarded): the jobs every Tier 2 branch
runs there. Same care as `../tier1-prod/`: real values, never pasted into `docs/`; no agent edits them.

## Put here (operator)

| File | What |
|---|---|
| `db.conf` | database jobs: `<JOB>:<type>:<flag>:<PL/SQL call>;` (one logical line per job — an editor may wrap it) |
| `shell.conf` | Unix script jobs |
| `EXTRACTED.md` | one line per file: date copied, server / path, who copied it |

Copy the files **unchanged** (line numbers are cited as evidence). Before pushing, replace any password or connection
string with a placeholder and say so in `EXTRACTED.md`. Then:

```bash
python3 scripts/parse_job_confs.py runs/_reference/tier2-pre/      # -> jobs-inventory.csv (commit it too)
```

## Read by

| Agent / script | For |
|---|---|
| `box-fe-jobs-agent` (`target.env_folder`) | the target's own jobs: a generated name already used here is refused; a reference GBO wait gets NY's look-alike job (INFERRED) |
| `box-batch-jobs-agent` (J-T5) | the target's job inventory — expect **no NY BOX job** yet |
| skill `explain-box-job` | "what does `GMNY…` do?" |

## What the file shows `[read: operator screenshots, 2026-10-07]`

- NY's existing jobs are **`GMNY<nnnn><D|M><ss>`, mostly with a `_PR` suffix** (`GMNY0011D01_PR`) — NY's GBO jobs (the
  role `GMGB…` has in Tier 1). The parser files them as family `OTHER` (only `GMGB` is named GBO); flags `T:F` and `T:P`.
- `PGT_NY.Pkg_GMBatchprocess.f_ExecuteGroup` is called with **5 arguments** (group, branch, date, instrument, mode) —
  the same as J-E10: no label argument. Groups are passed as **named constants** (`CST_CURVAS_FIX_LOC`, `CST_PK_FINAC`),
  not PKs; dates sometimes through `PKG_NY_UTILITY.f_get_MisExecDat(CST_CALEND_PROC, …)`.
- Two NY branch constants: **`CST_PK_BRA_NYSCH`** (NY_SCH) and **`CST_PK_BRA_NYIBF`**.
- The currency-index check is `GMNY0011D01_PR` / `GMNY0012D01_PR` (`f_returnverificurrindex(0 | 1, …)`); NY's GBO
  market data load curves and prices before it (`GMNY0087D01_PR`, `GMNY0013D01_PR` / `D02_PR`).
- One job appears twice (`GMNY0087D01_PR`, lines 22-23) — the parser flags it (`dup_in_file`).
