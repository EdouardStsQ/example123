# DB relay — test on DGBOUS — NOT used by any agent yet

[`scripts/db_relay.py`](../../../../scripts/db_relay.py) (operator's PC) and
[`scripts/relay_ask.py`](../../../../scripts/relay_ask.py) (Devin), ADR 0021 (**proposed**, 2026-10-28). Nothing to
install: Python, git and SQL\*Plus.

## 0. A clone for the relay (once)

The relay checks out the agent's branches and commits its answers there: give it its own clone, never the one you
work in.

```powershell
mkdir C:\db-relay; cd C:\db-relay
git clone <the cib-box-aukinbranch URL>
cd cib-box-aukinbranch\automation
```

## 1. Passwords (once)

```powershell
python scripts/db_relay.py --save-passwords tier2-dev
```

Asks each account's password (`pgtadmin`, `deveng`, `box_acc`, `box_fe`, `box_sys`, `box_stc`; Enter to skip one),
checks it on DGBOUS (`OK … connected as … (read-only transaction)`) and only then keeps it in Windows Credential
Manager (`box-db-relay:DGBOUS:<account>`). Never in the repo. `--forget tier2-dev` removes them; `--check tier2-dev`
re-checks.

## 2. Three ready-made queries, no git

```powershell
python scripts/db_relay.py --once
```

| Request (`smoke_20261028_1/relay/`) | Account | Expected |
|---|---|---|
| `001-A-G1-branch-GBO.sql` | `pgtadmin` | `ok`, 1 row: NY SCH `20007.4`, group `21447.4` |
| `002-A-G4-group-in-box-BOX_ACC.sql` | `box_acc` | `ok`: rows only if DGBOUS's BOX already holds NY's group (checkpoint 1 of the ACC configs agent) |
| `003-must-be-refused.sql` | — | `refused` (`forbidden word UPDATE`), **never sent to the database** |

Results: `smoke_20261028_1/01-evidence/*.csv` and `relay/*.log.json`. Delete a log to run that request again; leave
these files uncommitted in the relay's clone (or delete them) before step 3.

## 3. Round trip with Devin

On the PC (stays running; Ctrl+C to stop):

```powershell
python scripts/db_relay.py --watch --branches "devin/*" --review
```

(`devin/*` = the branches Devin creates — use the prefix your Devin sessions show.) In Devin, paste:

> *Work on a new branch `devin/relay-test`. Write `SELECT b.PK AS branch_pk, b.DESCRIPTION AS branch, b.FK_LOCALGROUP
> AS group_pk FROM PGT_STC.T_PGT_BRANCH_S b WHERE b.PK = 20007.4` to `/tmp/q/a-g1.sql`, create the folder
> `runs/NY_SCH/tier2-dev/relay-test/smoke_20261028_2/`, then run
> `python3 scripts/relay_ask.py runs/NY_SCH/tier2-dev/relay-test/smoke_20261028_2 --env tier2-dev GBO:A-G1-branch-TGT=/tmp/q/a-g1.sql`
> and show me its output and the CSV.*

Expected: the relay shows the query and asks `Run it read-only? [y/N]`; after `y`, Devin prints
`ok 001-A-G1-branch-TGT: 1 rows -> …` within ~10–30 s.
