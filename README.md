# External repos — read-only copies (workaround)

`[stated: operator, 2026-10-06]` Two repos the agents need live in **another GitHub organisation**, so Devin cannot
attach them. Their files are copied here, **unchanged**, until the repos can be attached (e.g. once
`cib-auki-aukicnfgsrvc` moves under `cib-boxfin`). Then delete this folder and point the inputs at the repos.

Same rules as `runs/_reference/tier1-prod/`: real values, never pasted into `docs/`; no agent edits these files; the
scripts never copy a `CreatedBy` (developer ID) into an output. Before pushing, check there is no password, token or
connection string (replace it with a placeholder and say so below).

## Layout — keep each source repo's own paths

```
runs/_reference/external/
  cib-auki-aukicnfgsrvc/                       per-environment descriptors (DeployDescriptor), <repo>/<env>.json
    cib-boxfin-t1mdesfe/{pre,pro}.json          Madrid FE
    cib-boxfin-t1mdslbfe/{pre,pro}.json         SLB FE
    cib-boxfin-t1mdloadprices/{pre,pro}.json    load prices (Madrid + SLB)
    (recommended next: cib-boxacc-t1mdesac, cib-boxacc-t1mdslbac, cib-boxfin-mdfinancialcheck,
     cib-boxacc-t1mdacccheck, cib-boxfin-t1mdalmfields, cib-boxfin-mdschedulmonitor)
  cib-auki-aukictrlmcntrm/                     Data Lake (AUKI) Control-M jobs: one set of jobs per book
    doc/auki migracion/MIG_ES_LB_diariai.json   Madrid + SLB
    doc/auki ny/control-m_NY.json               NY
```

| Read by | What for |
|---|---|
| `box-fe-jobs-agent` (`reference.descriptor_dir`, `prerequisites[].descriptor_dir`) | waits added only in an environment (e.g. PRO: load prices, GBO, Data Lake) |
| `box-fe-jobs-agent` (`datalake.reference_json`, `datalake.target_json`) | each book's Data Lake job: a target book waits for its own (book label description = `book_vr`) |

## Copied

| File | Source repo / branch / commit | Date | By |
|---|---|---|---|
| *(fill one line per file)* | | | operator |
