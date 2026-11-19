# Kickoff — gap run: where does each field of the report come from in BOX?

Agent: [`box-report-migration-agent`](../AGENT.md). Parameters come from the branch's kickoff (e.g.
[`kickoff-gbux.md`](kickoff-gbux.md)): `<BRANCH>`, `<report>`, `<tier>-<env>`, the two accounts, the GBO wrapper
schema, the slice of products.

## Step 1 — read, before asking anything

1. [`AGENT.md`](../AGENT.md) (hard rules) and [ADR 0028](../../../docs/decisions/0028-report-migration-gbo-to-box.md).
2. The report folder `runs/<BRANCH>/branch/reports/<report>/`: `README.md`, `gbo-spec/` (the GBO side's
   specification — all of it), `layout.csv`, `decodes.csv`, `field-matrix.seed.csv`, `decisions.csv`,
   `deviations.csv`. If `gbo-spec/` holds no specification file yet, say so and work from the seed's citations.
3. The BOX model: [`box-data-model.md`](../../../docs/reference/box-data-model.md),
   [`fe-raw-data-stage.md`](../../../docs/reference/fe-raw-data-stage.md),
   [`box-fe-test-lookups.md`](../../../docs/reference/box-fe-test-lookups.md),
   [`gbo-box-product-tables.csv`](../../../docs/reference/gbo-box-product-tables.csv),
   [`accounting-resolution-chain.md`](../../../docs/reference/branch-config/accounting-resolution-chain.md),
   [`box-acc-model.md`](../../../docs/reference/box-acc-model.md).
4. The catalogue: [`report-migration-mining.md`](../../../docs/reference/queries/report-migration-mining.md).

## Step 2 — the run folder

`python3 scripts/new_run.py --branch <BRANCH> --tier <tier> --env <env> --area reports --name <report>` (or
continue an open run: read its `RUN.md`, inputs and `01-evidence/`, ask only what is missing — ADR 0023's rule).
Write `report-inputs.json` from [`templates/report-inputs.example.json`](../templates/report-inputs.example.json),
every value with its source; ask what the kickoff does not give. Create `local/` (git-ignored) for trade-level files.

## Step 3 — the queries, in this order

R-P1, R-P2 → R-B1 → R-G0 → R-G1 (+ R-G1b) → R-T1 → R-B3 (+ R-B3b), R-B5 → R-B2 and R-B4 (written from R-B1, saved
before they are run) → R-G2 (local) + R-G2c. Ask them in batches; **save each result the moment it arrives**
(`01-evidence/<ID>-<short name>.csv`) and name the file in your reply. A failed query: its error and account in the
report — never a rewritten query presented as the catalogue's.

## Step 4 — the outputs

1. `02-field-matrix.csv` — start from the seed (copy it), then row by row: the BOX source **named from the evidence**
   (`01-evidence/<file>.csv` in `evidence`), class (`same` / `equivalent` / `constant` / `derived` / `n/a` /
   `OPEN`), confidence, status `confirmed` when the evidence shows it, `OPEN` with its decision id when nothing does.
   Keep every seed row.
2. `topics-rr.csv` in the report folder (D3's default) from R-G1, and the `box_value` column of `decodes.csv` from
   R-B4 / R-T1 — each with its evidence file in `source`.
3. Proposals only for `decisions.csv` / `deviations.csv`: a new decision or deviation the evidence shows (a new id,
   status `default`, its default); never an answer, a date or `decided`.
4. `03-gap-report.md` from [`templates/gap-report.md.tmpl`](../templates/gap-report.md.tmpl): the counts per class
   (they add up to the matrix), what changed against the seed, every OPEN with the queries tried, the questions for
   each decision's owner ready to send.

## Step 5 — before you say it is finished

`python3 scripts/check_report_run.py <run>` must print `REPORT RUN OK`; fix every `FAIL`. Then stop: the operator
reviews the matrix (and sends the questions) before the build ([`build.md`](build.md)).
