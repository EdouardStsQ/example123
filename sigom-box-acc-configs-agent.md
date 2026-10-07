# Case: the BOX ACC gap run — only branch-dependent rows proposed, each from a stated source

Covers: sigom-box-acc-configs-agent (phase 1, gap run)
Type: happy path + guard rails

**Pending** — first run (NY_SCH, Tier 2 PRE, reference SLB Tier 1).

## Given

The target branch and its group (A-G1); the reference branch's BOX ACC rows for the approved instruments (local
properties with their four arrays, portfolio properties with their generated lists, cross account config, ACC event
groups from its MBJ rows); the target's GBO rows (cross account config, portfolio properties and their accounts); the
global catalogues in both tiers (topics, conditions, standard historic, event groups and events, accounts).

## When

`Run automation/agents/sigom-box-acc-configs-agent/prompts/tier2-gap-run.md`, the operator returning each CSV.

## Then

- **Global screens** (topics, conditions, standard historic, event config): `present`, or `ask` when missing in the
  target — never `create`.
- **Event grouping:** one question per reference ACC group, `global` or `branch-copy`; the answer is in the inputs file.
- **Local properties:** `create` per instrument from the reference's rows, arrays listed by `FK_EXTENSION`; nothing if
  the target's group already has them.
- **Cross account config:** `create` from the target's GBO rows; account by code; the GBO topic **not** used as a BOX
  value — translated per A-03b or `OPEN`.
- **Portfolio properties:** `create` per instrument with the reference's shape; accounts `OPEN` until the topic mapping
  is given; no GBO topic in the matrix.
- **Global accounts:** the target's GBO accounts missing in BOX → `create` (copied from GBO); none from the reference.
- **Net contract:** `N/A` (not Madrid real). **MBJ:** not in the matrix (other agent).
- An instrument the reference has no ACC rows for (e.g. CDS) → `N/A — no reference`.
- **Fail:** any SQL written, any GBO topic as a BOX value, any account taken from the reference branch, a global
  object marked `create`, a query run in the wrong tier.
