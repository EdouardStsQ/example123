# J-E10 — who takes a label (both tiers)

- **Source:** operator, 2026-10-02 — queries (a), (b), (c) of J-E10 in Tier 1 and Tier 2 (screenshots).

## (a) `PKG_GMBATCHPROCESS.F_EXECUTEGROUP*` arguments

| Tier | Owner | `F_EXECUTEGROUP` | `…CONTACAP` | `…CONTASWAP` |
|---|---|---|---|---|
| 1 | `PGT_ES` | 7: group, branch, date, instrument, vstatic, **P_LABEL, P_SUBLABEL** | 7 (same) | 7 (same) |
| 2 | `PGT_BOS` | 5 (no label) | — | — |
| 2 | **`PGT_BRL`** 🆕 | **7 — P_LABEL, P_SUBLABEL** | — | — |
| 2 | `PGT_NY` | **5 (no label)** | 5 | 5 |

No overloads in either tier. `PGT_CO` (seen in J-E1) returns no `F_EXECUTEGROUP` rows — no such function, or not
visible to the account `[open]`.

## (b) Entry points with `P_LABEL` / `P_SUBLABEL`

| Owner.package | Procedures | Tier 1 | Tier 2 |
|---|---|---|---|
| `PGT_PRG.PKG_BATCHPROCESS` (core engine) | `P_EXECUTEGROUP` (label = position 7, sub-label 8), `F_SETMONITOR`, `P_SETMONITOR` | ✅ | ✅ |
| `PGT_PRG.PKG_BATCHPROCESS_MBJ` | `P_EXECUTEEVENT`, `P_EXECUTESELE`, `P_INSERTPROCESSCONTROL` | ✅ | ✅ |
| `BOX_ACC.PKG_BATCHPROCESS_MBJ` | same + `P_INSERTMOVEMENTCOUNT` | ✅ | ✅ |
| `PGT_ES.PKG_GMBATCHPROCESS` | the three `F_EXECUTEGROUP*` | ✅ | — |
| `PGT_BRL.PKG_GMBATCHPROCESS` | `F_EXECUTEGROUP` | — | ✅ |
| `PGT_NY.PKG_GMBATCHPROCESS` | — | — | ❌ |

## (c) Wrapper package dates

| Tier | Owner | Created | Last DDL |
|---|---|---|---|
| 1 | `PGT_ES` | 16-JAN-21 | 14-JUN-25 |
| 2 | `PGT_BOS` | 16-JUL-22 | 16-JUL-22 |
| 2 | `PGT_BRL` | 20-SEP-25 | 11-AUG-26 |
| 2 | `PGT_NY` | 16-JUL-22 | 07-FEB-26 |

## Read

1. **The engine already takes the book in Tier 2** — `PGT_PRG.PKG_BATCHPROCESS.P_EXECUTEGROUP` has `P_LABEL`,
   `P_SUBLABEL` in both tiers. Only NY's **wrapper** does not pass them.
2. **There is a Tier 2 precedent:** `PGT_BRL`'s wrapper has the 7-argument `F_EXECUTEGROUP`. The NY change = the
   same two arguments on `PGT_NY`'s `F_EXECUTEGROUP` (and `…CONTASWAP`, `…CONTACAP`, as `PGT_ES` has), passed through
   to the core — a wrapper change, not an engine change `[inferred: from signatures; the bodies are not readable]`.
3. **To keep GBO's existing 5-argument calls working**, the two new arguments must default to NULL — J-E10 (d) shows
   whether `PGT_ES` / `PGT_BRL` declare them that way.
