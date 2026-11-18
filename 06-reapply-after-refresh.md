# Re-applying a branch's configuration after an environment refresh

`[operator, 2026-11-17]` PRE-PARALELO (IGBOUSIB) was refreshed after NY_SCH's FE, ACC and MBJ work: GBO (`PGT_*`, the
book labels in `PGT_SYS.PGT_DOMAINS`) and `BOX_FE` came back as a copy, `BOX_ACC` was left as it was. Everything a run
did is in its run folder (values, rendered SQL, outputs), so a refresh means **re-applying, not redoing** — but only
the parts the refresh actually removed, in dependency order. This page is the order and the checks.

## 1. What did the refresh touch? (read-only, ~5 minutes)

Ask the team that refreshed it: which schemas, from which source (PROD?), as of which date, and whether it will
happen again. Then check, in the environment:

| Check | Account | Query (substitute the branch's values from its run folders) | Gone means |
|---|---|---|---|
| auth code | BOX_ACC | `SELECT AUTH_CODE FROM GOM_GLB_SYS.T__CORE_INFO_S;` | a different code: stop — every rendered file is built for one auth code |
| ACC config | BOX_ACC | counts of the group's `T_BOX_ACCT_PORT_PROP_S` / `T_BOX_CONF_LO_PROP_S` rows (`FK_BRANCH = <group>`), the run's global topics by PK or `CODE` | re-apply ACC (§2, steps 2–3) |
| MBJ rows | BOX_ACC | `SELECT COUNT(*) FROM BOX_ACC.T_BOX_MBJ_PROPERTIES_S WHERE FK_BRANCH = <branch>;` | re-apply MBJ (step 4) |
| sequences | BOX_ACC | `ALL_SEQUENCES` for `BOX_ACC.SPK_T_BOX_%` | moved back = a refreshed `BOX_ACC`; compare with the run's last precheck |
| book labels | an account that reads `PGT_SYS` (e.g. BOX_ADMIN) | `SELECT PK, CODE FROM PGT_SYS.PGT_DOMAINS WHERE CODE IN (<the branch's labels>);` | re-create them — the FE run's label step (step 1) |
| FE config | BOX_ADMIN | the FE run's configuration and curve PKs in `BOX_FE.T_BOX_ENGCONF_S` / `T_BOX_ENGFCURVE_S` | re-run FE (step 1) |

A part still there is **not** re-applied: its rows are in place and its sequences have moved past them.

## 2. Re-apply, in this order (each with its usual precheck → rehearsal → config → verify)

1. **FE configuration and book labels** — a new run of the environment's FE kickoff (e.g.
   `agents/sigom-box-fe-configs-agent/prompts/preparalelo-run.md`): archive the previous run (`runs/README.md`), ask
   every query again (the database changed; Q-01 must find no configuration), the label skill creates the labels
   again, the previous run's SME decisions are offered on one card. New PKs are normal (NY 2026-11-17: config
   `335932867.44` instead of `300966176.44`; the labels came back with the same PKs — the refresh reset their
   sequence). Runtime queue rows (`T_BOX_BRPROCCAL_S`) are batch data, never configuration: not re-created.
2. **ACC global data** — only if the imported global topics are gone: run the target's `--import` again from the
   global installation's export output (DGBOBOX, ADR 0027). The export stays valid as long as DGBOBOX was not
   refreshed.
3. **ACC configuration** — only if gone. If GBO was refreshed too, first compare a few counts with the gap run's
   evidence (A-U1 f, A-03a per TIPO, A-U7b / A-10a): unchanged → the same values, re-rendered precheck → rehearsal
   → config → verify in a new run folder that records the refresh; changed → continue the gap run (ADR 0023).
4. **MBJ rows** — the same files of the MBJ run (they are environment-portable: PKs from the sequence, labels by code
   at run time); after step 1, because they look the labels up.

## 3. What a refresh tends to break

- **Sequences behind their tables** (a PROD copy whose rows were inserted with static PKs): the precheck reports
  them; advance the sequence with the BOX ACC expert's NEXTVAL loop (`tier2-sql.md`), as `BOX_ACC`.
- **Grants**: an account may lose or lack a grant it had before (IGBOUSIB: `BOX_ACC` cannot read
  `PGT_STC.T_PGT_CALENDAR_S`, hence `mbj.calendar_check = "separate"`). A compile error (ORA-00942 / PLS-00201)
  means nothing ran — fix the account or the grant, never edit rendered SQL.
- **GBO data drift**: a newer copy of PROD can add or change the branch's GBO configuration — step 2.3's check.

Record the refresh, what was found and what was re-applied in each run's `RUN.md` and in the branch's open items.
