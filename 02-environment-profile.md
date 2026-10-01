# Environment profile — reference (Tier 1) and target (Tier 2 PRE)

**Seeded 2026-09-29** from query results the operator ran while the agent was being designed. They were
shared as **screenshots**, so each is tagged `screenshot`: the agent asks for the CSV export before phase
2, and re-runs anything marked 🆕. Queries by ID: [`box-jobs-queries.md`](../../../../docs/reference/queries/box-jobs-queries.md).

## Owners and code

| Fact | Tier 1 (reference) | Tier 2 PRE (target) | Query | Evidence |
|---|---|---|---|---|
| Wrapper `PKG_GMBATCHPROCESS` owner(s) | `PGT_ES` (the one Madrid's `db.conf` calls); full list 🆕 | `PGT_NY`, `PGT_BOS` (Boston), `PGT_CO` (Colombia) | J-E1 | Tier 2 screenshot; Tier 1 from the `db.conf` line |
| Wrapper NY BOX jobs would call | — | `PGT_NY` — **to confirm** with the BOX team | — | `[inferred]` |
| Engine core `PKG_BATCHPROCESS` owner(s) | 🆕 | `PGT_PRG`, `PGT_STL` | J-E1 | Tier 2 screenshot |
| Catalog owner | `PGT_PRC` | `PGT_PRC` | J-E2 | screenshots |
| Wrapper body readable | no (`PACKAGE` 1605 rows only) | 🆕 (spec read; body presumably not) | J-E3 | Tier 1 screenshot |
| `f_executegroup` arguments | **7**: group, branch, date, instrument, vstatic, **label, sub-label** (spec l. 1535-1542) | **5**: group, branch, date, instrument, vstatic (spec l. 620-626); **no `P_LABEL` anywhere in the spec** | J-E4 | screenshots |
| Other entry points | `f_ExecuteGroupContaSwap`, `f_ExecuteGroupContaCap` (7 args) | `f_executegroupcontaswap`, `f_executegroupcontacap` (5 args), `pgeneraeventosautomatic`, `p_borrarlog`, `ptratapoolcolaterales`, `pglobalizaentity`, `p_ejecutarpositioncontrol`, `f_positioncontrol`, `f_executepositioncontrol`, `f_checkprices` | J-E4 | screenshots |
| Label lookup `PKG_BOXUTILITY` | `BOX_SYS`, `BOX_FE` — VALID | `BOX_SYS`, `BOX_FE` — VALID | J-E5 | operator: same in both |
| MBJ properties table / readers | `BOX_ACC.T_BOX_MBJ_PROPERTIES_S`; reader = `MBJBOXACC.jar` via `mbjbox.sh` | 🆕 (is the jar installed in Tier 2?) | J-E6, J-X4 | reader stated by a BOX dev, 2026-10-01 |
| MBJ Config screen object | `35000182.65` *BOX - MBJ Properties*, module `35000006.65`, no pre-commit, 25 fields | **identical** (table empty — expected) | J-T8 ✅ | [evidence](01-evidence/J-T8-mbj-screen-object-BOTH.md) |
| MBJ engine package `PKG_BATCHPROCESS_MBJ` (what the jar calls) | 🆕 owner / status | 🆕 | J-E9 | called by the jar `[stated: BOX dev, 2026-10-01]` |
| MBJ rows | Madrid `22.21`: **50** (e.g. CCS / FRA / OTC Option, `D07` + `D09` per book); SLB 🆕 | US: **0** (seen, operator) | J-R2 / J-T4 | [evidence](01-evidence/J-R2-mbj-properties-madrid-REF.md) |
| Auth code | (`.21` Madrid rows) | **44** | J-E7 / FE Q-G3c | FE run |
| Engine core versions | 🆕 | 🆕 | J-E8 | — |

## Branch constants in the wrapper

| | Tier 1 `PGT_ES` | Tier 2 `PGT_NY` |
|---|---|---|
| Reference SLB London | `CST_PK_BRANC_LND = 20087.4` (l. 1144, with its own block of group constants) | not in the lines seen |
| Target NY_SCH | **none seen** | **`cst_pk_bra_nysch = 20007.4`** (l. 38) |
| Others | `MAD 22.21`, `LON 42.21`, `SAN 20061.4`, `SCF 96.21`, `BEN 20059.4`, `HK 20063.4`, `AUD 20075.4`, `TOK 20082.4`, `SH 20081.4` | `mad`, `lon`, `san`, `scf`, `ben`, `hk`, `bru 20079.4`, `nyibf 20006.4`, `miami 20104.4`, `scusa 20108.4` |

Product constants (`.4` instrument PKs, e.g. `CST_PK_SWAP = 20092.4`) are the same in both. Group
constants are not (Tier 2's are `.35` = old NY server, `.44` = Tier 2 `[stated: GBO expert via
operator]`). Tier 2's NY constants (`cst_eod_ny_*`, `cst_mtm_ny_*`, ETD NY, NY balance, …) belong to
**GBO** flows: NY is not in BOX yet `[stated: operator, 2026-09-29]`.

## Catalog

| Fact | Tier 1 | Tier 2 | Query | Evidence |
|---|---|---|---|---|
| BOX groups (`GROUPDESCRIP LIKE 'BOX%'`) | 🆕 | **51**, `.65` PKs (e.g. `2407.65` Money Market by book, `2735.65` SWAP by Book, `2996.65` Daily Closing of Settlements SLB) | J-C1 | Tier 2 screenshot (first 21 rows seen) |
| Group `2735.65` events | 7, orders 0-6, update rows 2/20/119/38/38/114/13 | **identical** | J-C2 | screenshots |
| Fingerprint of all BOX groups | 🆕 | 🆕 | J-C5 | — |

## Not yet collected

Tier 1 PROD `db.conf` + `shell.conf` → `jobs-inventory.csv` (J-R1; folder `runs/_reference/tier1-prod/`), the
Tier 2 copies (J-T5), `MBJBOXACC.jar` source / `conf/BOX` / a log (J-X4; `mbjbox.sh` read 2026-10-01), SLB's MBJ properties (J-R2), the Tier 1
Control-M jobs of SLB (J-R4), the Tier 2 Control-M folder repos, NY books resolving to labels (J-T3).
