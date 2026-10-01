# J-T8 — MBJ Config screen object, Tier 1 and Tier 2

- **Source:** operator, 2026-10-01 — both queries of J-T8 run in Tier 1 and Tier 2; **identical results**
  (Tier 2 screenshots kept by the operator).
- **Result: PASS.**

## Object (`GOM_GLB_SYS.T__OBJ_DEF_S`)

| PK | PK_NAME | Module | BASIC_STORAGE | EXT_STORAGE | PRE_COMMIT_PROC | FK_PRECOMMIT | PSAVDLL | PSAVFUNC |
|---|---|---|---|---|---|---|---|---|
| 35000182.65 | BOX - MBJ Properties | 35000006.65 | T_BOX_MBJ_PROPERTIES_S | null | null | null | null | null |

No pre-commit and no save function: rows inserted by script need nothing replayed on save.

## Declared fields (`T__EXT_DEF_S`, `FK_PARENT = 35000182.65`) — 25

| FK_EXTENSION | Field | FK_KIND | Target table |
|---|---|---|---|
| 35001590.65 | JobName | 5.1 |  |
| 35001591.65 | InternalId | 5.1 |  |
| 35001592.65 | pBranch | 2.1 | T_PGT_BRANCH_S |
| 35001593.65 | pInstrument | 2.1 | T_PGT_SUB_PRODUCT_S |
| 35001594.65 | pGroup | 2.1 | T_PGT_BR_EVE_S |
| 35001595.65 | pLabel | 2.1 | PGT_DOMAINS |
| 35001596.65 | pSubLabel | 2.1 | PGT_DOMAINS |
| 35001597.65 | Concurrence | 5.1 |  |
| 35001598.65 | Concur_Event_Dependencies | 5.1 |  |
| 35001599.65 | Workers | 5.1 |  |
| 35001600.65 | Task_per_worker | 5.1 |  |
| 35001601.65 | Workers_by_events | 5.1 |  |
| 35001602.65 | Monitor_Types | 5.1 |  |
| 35001603.65 | Monitor_File_Pattern | 5.1 |  |
| 35001604.65 | MONITOR_FILE_MAX_DAYS | 5.1 |  |
| 35001605.65 | InputUser | 5.1 |  |
| 35001606.65 | LstMntUser | 5.1 |  |
| 35001607.65 | LstMntDate | 5.1 |  |
| 35001608.65 | Instanze | 5.1 |  |
| 35001609.65 | InputDate | 5.1 |  |
| 35008579.65 | Mic_Eod | 5.1 |  |
| 35008580.65 | Mic_File_Type | 5.1 |  |
| 35008581.65 | Mic_Sender_Type | 5.1 |  |
| 35008585.65 | Return_Data | 5.1 |  |
| 35009533.65 | Mic_Flow_Mode | 5.1 |  |

`FK_KIND` `2.1` = a reference to the target table, `5.1` = a plain value `[inferred from the pattern]`.
`Return_Data` is declared but was not in the screen's query — it is a table column (`RETURN_DATA`, values
`0`/`1`; see `J-R2b-mbj-properties-describe.md`). The table also has 5 columns the screen does not declare.
