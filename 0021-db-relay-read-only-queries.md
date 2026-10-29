# 0021. A read-only DB relay on the operator's machine — agents' queries run without copy-paste

Date: 2026-10-28
Status: **proposed** — built and tested without a database (`scripts/tests/test_db_relay.py`); the operator tests it on
DGBOUS and decides. Until accepted, **no agent uses it** and the rule "no agent touches a database" stands unchanged.

## Context

Every query of the agents is handed to the operator, who runs it in SQL Developer and returns a CSV. The agents run in
the cloud (Devin) and cannot reach the bank's databases (internal hosts, e.g. `dgbous.nngg.corp`); the operator's PC
can. An SSH tunnel from the cloud into the bank network was ruled out.

## Decision (proposed)

`[operator, 2026-10-28]`

0. **The agent stays in the cloud (Devin)** `[operator, 2026-10-28]`: the only place both it and the operator's PC
   reach is the git repo, so git is the channel. An MCP server or a JDBC / SQLcl client on the PC would be faster, but
   only for an agent running on that PC.
1. **`scripts/db_relay.py` runs on the operator's PC**, in a clone of its own: it watches the agent's branches
   (`--branches "devin/*"`; one `git ls-remote` every 10 s, a pull only when a branch moved), pulls the query
   requests (`runs/**/relay/<NNN>-<name>.sql`, header `-- relay: env=… system=… out=…`), runs each new one and
   pushes the CSV (in the run's `01-evidence/`) and a log back. Outbound connections only (git, the database), as
   today; every query and result in the git history. **Nothing to install** — the bank allows no Python package
   `[operator, 2026-10-28]`: Python's standard library, git and the PC's **SQL\*Plus** (21.17; CSV output since 12.2).
2. **Read-only, enforced by the relay:** one statement, `SELECT` / `WITH` only; no DML, DDL, PL/SQL, `FOR UPDATE`,
   `INTO`, database link; no function but SQL built-ins (a package function can write inside a `SELECT`); no
   unsubstituted `&` value; forbidden tables refused (`T_PGT_USAENTPROP_S`); every session `SET TRANSACTION READ ONLY`
   before the query and `ROLLBACK` after, SQL\*Plus exiting on the first error; row cap and time limit. The query runs
   from a temporary script with `TERMOUT OFF` (rows go to the CSV only); numbers exact (`NUMWIDTH 40`, `.` decimal),
   UTF-8 (`NLS_LANG`). The owner accounts the operator uses (`box_acc`, `pgtadmin`, …)
   are acceptable on that basis `[operator, 2026-10-28]`.
3. **Accounts by system, from `docs/reference/db-routes.csv`** (environment, host, port, SID, system → account,
   `relay_allowed`) — never chosen by the agent. Only `tier2-dev` (DGBOUS) allowed at first. GBO → `pgtadmin` (all GBO
   tables), objects owned by DEVENG → `deveng`, BOX schemas → their own account `[operator, 2026-10-28]`.
4. **Passwords** in **Windows Credential Manager** (`--save-passwords ENV`: asked, checked against the database, then
   stored — encrypted with the Windows login, outside the repo, visible / removable in Control Panel; standard library
   only) or, if not saved, asked once per session and kept in memory. Handed to SQL\*Plus on its standard input —
   never on its command line, in the repo, a file, a log, git or the chat. A rejected password (`ORA-01017`) is
   dropped from memory and from the store. User names (shared schema accounts) are in the routes file.
5. `--review` shows each request and asks before running it — the operator's choice while trust is built.
6. **The agent's side: `scripts/relay_ask.py`** — one call per batch: the same guard and route checks before
   anything is pushed (exit 2), one commit and push, then a pull every 10 s until every answer is there (exit 0 / 1),
   or a timeout (exit 3: the relay is not running — manual mode). **Skill `run-db-queries`**: the DB access mode
   (relay / manual, asked at the start of a run, default manual) and how agents use it.

## To accept it

The operator's smoke test on DGBOUS (`runs/NY_SCH/tier2-dev/relay-test/README.md`): `--save-passwords tier2-dev`,
`--once` (001 and 002 `ok`, 003 `refused`), then a round trip with Devin (`--watch --branches "devin/*"`, Devin calling
`relay_ask.py`). Then: the charters' "no database" rule becomes
"read-only, through the relay, in the allowed environments"; the kickoffs point to skill `run-db-queries`.

## Consequences

- Results reach GitHub as today (the operator commits the CSVs now); the privacy rules of each agent still apply to
  what it asks (counts, codes, hashes — never portfolio or counterparty values).
- Queries that call a package function (e.g. `f_getPKByLabel`) are refused by the relay — run by hand.
- InfoSec / the operator's manager to be told: a script on a corporate PC runs read-only queries pulled from a repo.

## Alternatives considered

- An SSH tunnel from the agent's machine into the bank network: rejected — inbound access to the bank network.
- The agent inside the bank network (an enterprise deployment of the agent platform): not in the operator's hands.
- Credentials given to the agent: rejected — the agent cannot reach the database anyway, and secrets would leave the PC.
