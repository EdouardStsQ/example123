# J-R2b — `BOX_ACC.T_BOX_MBJ_PROPERTIES_S` structure

- **Source:** operator, 2026-10-01 — `DESCRIBE BOX_ACC.T_BOX_MBJ_PROPERTIES_S` (environment not stated; the
  screen object is identical in both tiers, J-T8) and `SELECT DISTINCT RETURN_DATA …` → `0`, `1`.
- **32 columns**, `NOT NULL`: `PK`, `MIC_EOD` only.

| Column | Null? | Type | On the screen (J-T8) |
|---|---|---|---|
| PK | NOT NULL | NUMBER | identity |
| FK_OWNER_OBJ |  | NUMBER | identity |
| FK_PARENT |  | NUMBER | identity |
| FK_EXTENSION |  | NUMBER | **not declared** |
| JOB_NAME |  | VARCHAR2(20) | declared |
| INSTANZE |  | VARCHAR2(20) | declared |
| FK_BRANCH |  | NUMBER | declared |
| FK_INSTRUMENT |  | NUMBER | declared |
| FK_GROUP |  | NUMBER | declared |
| CONCURRENT_EVENTS |  | VARCHAR2(1) | declared |
| CONCURRENT_EVENTS_DEPENDENCY |  | VARCHAR2(500) | declared |
| WORKERS |  | NUMBER | declared |
| TASKS_PER_WORKER |  | VARCHAR2(3) | declared |
| RETURN_DATA |  | VARCHAR2(1) | declared |
| RECOVER_MANUAL_MOVS |  | VARCHAR2(1) | **not declared** |
| RECOVER_RECLASSIFICATION_MOVS |  | VARCHAR2(1) | **not declared** |
| RECOVER_REGULARIZATION_MOVS |  | VARCHAR2(1) | **not declared** |
| FK_LABEL |  | NUMBER | declared |
| FK_SUBLABEL |  | NUMBER | declared |
| FK_CALENDAR |  | NUMBER | **not declared** |
| MONITOR_TYPES |  | VARCHAR2(12) | declared |
| MONITOR_FILE_PATTERN |  | VARCHAR2(200) | declared |
| MONITOR_FILE_MAX_DAYS |  | NUMBER | declared |
| MIC_SENDER_TYPE |  | VARCHAR2(10) | declared |
| WORKERS_BY_EVENTS |  | VARCHAR2(500) | declared |
| INPUTDATE |  | DATE | declared |
| INPUTUSER |  | VARCHAR2(30) | declared |
| LSTMNTDATE |  | DATE | declared |
| LSTMNTUSER |  | VARCHAR2(30) | declared |
| MIC_FILE_TYPE |  | VARCHAR2(30) | declared |
| MIC_EOD | NOT NULL | VARCHAR2(1) | declared |
| MIC_FLOW_MODE |  | VARCHAR2(30) | declared |

## What a new row needs

- Binding: `JOB_NAME`, `FK_BRANCH`, `FK_INSTRUMENT`, `FK_GROUP`, `FK_LABEL`, `FK_SUBLABEL`; identity: `PK`,
  `FK_OWNER_OBJ = 35000182.65`, `FK_PARENT` NULL, `FK_EXTENSION` NULL (to confirm on the reference rows).
- **`MIC_EOD` must be set** (`NOT NULL`).
- Flags and settings (`RETURN_DATA`, `RECOVER_*`, parallelism, MIC, monitoring): copy from the reference row of
  the same job step (J-R2 profile query).
- **`FK_CALENDAR`: not copied** — likely branch-specific; decided per target (open item 4e).
