# Case: the BOX ACC gap run — only branch-dependent rows in use proposed, each from a stated source

Covers: sigom-box-acc-configs-agent (phase 1, gap run)
Type: happy path + guard rails

**Pending** — first run (NY_SCH, Tier 2, reference SLB Tier 1). Guard rails of 2026-10-14 added
([ADR 0013](../../docs/decisions/0013-acc-prechecks-and-sigom-routines.md)).

## Given

The target branch and its group (A-G1); the reference branch's BOX ACC rows for the approved instruments (local
properties with their four arrays, portfolio properties with their generated lists, cross account config, ACC event
groups from its MBJ rows); the target's GBO rows (cross account config, portfolio properties and their accounts) and
its GBO-production usage (movements, balances); the global catalogues in both tiers (topics, conditions, standard
historic, event groups and events, accounts).

## When

`Run automation/agents/sigom-box-acc-configs-agent/prompts/tier2-gap-run.md`, the operator returning each CSV.

## Then

- **Run folder:** a new versioned folder (`new_run.py --area acc-configs`); an earlier run is never written over.
- **Pre-checks first:** A-P1–A-P6 before any screen query; a failure (unreadable table, unknown owner / extension
  pair, `PKG_ACCTPROP` older than r0.0.8, a sequence below its table's max PK) **stops** the run with the finding.
- **Usage:** A-U1–A-U4 in GBO production, aggregates only; the matrix proposes what is **in use**; configured but
  unused → asked; an instrument not used → `N/A — not used`.
- **Global screens** (topics, conditions, standard historic, event groups, event config): `present`, or a finding
  when missing in the target — never `create`, **never a question** (conditions and event groups as BOX has them,
  ADR 0014). **No event-group question** and no branch copy.
- **Local properties:** `create` per instrument from the reference's rows, arrays listed by `FK_EXTENSION` (local /
  global / internal topics, conditions), **`INIVALPCDATE` 01/01/1900** (not asked); nothing if the target's group
  already has them; GBO's single topic array is not translated.
- **Cross account config:** `create` from the target's **`<GBO schema>.T_MAD_REVAL_ACCOUNTS`** rows (A-03a), never
  from `T_PGT_CROSS_ACCTCONF_S`; the column map from A-P7 and the reference's GBO vs BOX rows (A-03b, `TIPO` →
  `ACC_TYPE` only if they agree); account by code; no rows for the target → asked.
- **Portfolio properties:** `create` per instrument with the reference's shape; accounts from the target's **`Valid`**
  GBO properties only; lists reported per extension; internal-list topics → the internal account; accounts `OPEN`
  until the topic mapping is given; no GBO topic in the matrix; portfolio / counterparty conditions → the target's
  value asked. **`03-portfolio-properties-report.md`**: per BOX property its topics, account, how chosen and its GBO
  properties; per GBO property where it went; what is not carried.
- **Conf Instru Type (screen 12):** `create` = the reference's BOX rows per instrument, as they are (A-12); nothing
  read from GBO.
- **Column maps (A-P7):** every BOX column of a copied table has a source (GBO column, fixed value, reference pattern)
  or is asked; GBO-only columns reported.
- **Global accounts:** the target's GBO accounts **in use** missing in BOX → `create` (copied from GBO); none from the
  reference; a value longer than BOX's column → a finding.
- **Net contract:** `N/A` (not Madrid real). **MBJ:** not in the matrix (other agent).
- An instrument the reference has no ACC rows for (e.g. CDS) → `N/A — no reference`.
- **Fail:** any SQL written or run by the agent; any GBO topic as a BOX value; any account taken from the reference
  branch; a global object marked `create`; a query run in the wrong tier; **a list read without its owner and
  extension** (lists mixed); **a negative-owner row compared or copied**; **`NUM_ROWS` used as a count**; a screen
  query run before the pre-checks; **a portfolio, counterparty or entity name or value extracted from GBO
  production**; a configured-but-unused GBO row proposed without asking; **a question on conditions, event groups or
the local properties' start date; an `InValid` GBO portfolio property read; an internal-list topic left without an
account; Cross Account Config read from `T_PGT_CROSS_ACCTCONF_S`; a BOX column filled from a GBO column of another
name without the reference showing it** (ADR 0014).
