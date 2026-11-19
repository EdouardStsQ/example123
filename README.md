# GBUX — the GBO specification (read-only)

The GBO side's own analysis of the NY UME Extendida file (`GBUX<YYMMDD>`, sent to Equation), produced by the GBO US
team and passed on by the BOX lead `[operator, 2026-11-18]`. It describes the **current GBO** report and stops at the
GBO output contract: mapping it to BOX is `box-report-migration-agent`'s work ([ADR 0028](../../../../../../docs/decisions/0028-report-migration-gbo-to-box.md)).

**No agent edits these files.** The layout, decodes and field matrix next to this folder cite them by number and
section (`1-process-spec §3`, `2-field-dictionary §Field 22`, `5-lineage-matrix §Field 21`).

## The files (names as received)

| File | Cited as | What |
|---|---|---|
| `UME Extendida NY.md` | `UME Extendida NY.md` | High-level overview: wiring, flow, products, eligibility, layout, operational observations |
| `GBUX - 1 Current GBO process specification.md` | `1-process-spec` | End to end: batch wiring, file contract, population, products, record generation, NEAR/FAR, lifecycle, failure behaviour |
| `GBUX - 2 Field data dictionary.md` | `2-field-dictionary` | The 22 fields: position, width, output expression, sources, decodes, current-code details |
| `GBUX - 5 GBO source lineage matrix.md` | `5-lineage-matrix` | Every field's GBO tables, columns, packages and constants; shared sources; constants; suggested stages |

Referenced by them but not received: `GBUX - 3 PRE evidence and examples` (baseline records and distributions) and
`GBUX - 4 Legacy behaviours and open clarifications`. If they come: file 4 as it is; file 3 **only** if it holds no
file records (trade ids, accounts) — distributions and counts only; otherwise its records stay outside the repo.

## The one edit made when they were added

The source paths pointed to a local Windows folder holding a personal user id. Before committing, every
`C:\Users\<user>\TASKS\` prefix was **removed**, so the paths start at the repository (`cib-tiichl-gbot2amdatabase\…`).
Nothing else was changed.
