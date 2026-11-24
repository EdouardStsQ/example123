# GBUX — NY UME Extendida, rebuilt in BOX (every environment)

`[operator, 2026-11-18]` The BOX lead's ask: the GBUX file GBO US produces today for Equation, produced from BOX data.
Agent: [`box-report-migration-agent`](../../../../../agents/box-report-migration-agent/AGENT.md); kickoff
[`kickoff-gbux.md`](../../../../../agents/box-report-migration-agent/prompts/kickoff-gbux.md); why this shape:
[ADR 0028](../../../../../docs/decisions/0028-report-migration-gbo-to-box.md). The report's own files are the same in
every environment, so they live here once; runs live in `runs/NY_SCH/<tier>-<env>/reports/gbux_<date>_<n>/`.

| File | What | Changed by |
|---|---|---|
| `gbo-spec/` | The GBO US team's specification, as received — read-only ([README](gbo-spec/README.md)) | the operator (adding files) |
| `layout.csv` | The 22 fields: positions, widths, allowed values (right-trimmed), sensitive fields (trade id, GL account), source section | a PR, citing the spec |
| `decodes.csv` | Every GBO value the logic tests (instruments, deposit subtypes, payouts, directions, extensions, constants, GBO identities) → output, and its BOX value (`<gap run>` until R-B4 / R-T1 shows it) | the gap run (`box_value`, with its evidence) |
| `field-matrix.seed.csv` | The proposed BOX source of every field and population / leg / topic rule, from the repo's model docs — each run copies it to `02-field-matrix.csv` and confirms it | a PR |
| `decisions.csv` | D1–D8: the decisions this report needs from its owners, each with the **default** the runs apply meanwhile; `decided` only with the owner's answer and date | the operator, with the owner's answer |
| `deviations.csv` | DV1–DV13: the GBO behaviours (unreachable branches, legacy defects, operational defects) — `copy` the file's content or `fix` | the operator, with the BOX lead's answer |
| `topics-rr.csv` | *(written by the first gap run, R-G1)* the copy of `PGT_NY.T_PGT_TOPICS_RR` by topic `CODE` — decision D3's default | the gap run |
| `local/` | **git-ignored, never committed**: GBO files received before a run exists — `GBUX261120` (20-Nov-2026, from the BOX lead, 750k+ records). A run reads them from here; their check and comparison reports go into the run | the operator |

The first slice (D2's default): NY SCH deposits and IRS. Trade-level files (GBO / BOX files, spools, id crosswalks,
detail differences) never enter the repository — a run keeps them in its git-ignored `local/` folder, and the
scripts that read them run on the operator's PC.

**Same content, efficient build** `[BOX lead, 2026-11-24]`: the BOX SELECT reproduces the file, not GBO's row-by-row
procedure — see the charter's hard rule 11 and the kickoff's *Efficiency* row.
