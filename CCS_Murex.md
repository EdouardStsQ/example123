# CCS in Murex

> **Scope:** Murex-specific representation of Cross Currency Swaps, including Cross Currency Basis Swaps and Cross Currency Reset Swaps (MTM CCS). Covers the Murex screen layout, generator configuration, flow types, and calculation examples.
> **Layer:** Qaracter — generic Murex behaviour, not Santander-specific configuration. Field names and screen layout apply to any Murex CCS.
> **Source:** Cross Currency Swaps and Cross Currency Reset Swaps product documentation (Santander internal, 2018-2020).

---

## 1. Product Identification in Murex

| Field | Value |
|-------|-------|
| Product type label | `Currency swap` |
| Trade family (`M_TRN_FMLY`) | `CURR` |
| Trade group (`M_TRN_GRP`) | `CCS` |
| Trade type (`M_TRN_TYPE`) | `SWAP` |

---

## 2. Screen Layout

A CCS in Murex is displayed as **Currency swap** under **Financial definition** with two legs side by side. The top section shows:
- `Generator` — the template (e.g. `CCS EUR-USD`, `CCS EUR-GBP`, `CCS MXN-USD`)
- `Maturity` — contractual and adjusted maturity dates
- `Nominal` — notional of Leg 1 (base currency)
- `versus` — notional of Leg 2 (underlying currency), typically the FX-converted equivalent

Each leg panel shows:
- Rate type: `Fixed rate` or `Floating rate`
- `Index` — floating rate index (floating legs only)
- `Currency` — each leg has its own distinct currency
- `Start date` / `Maturity`
- `Schedules definition Details` link — opens the full flow schedule
- `1st fixing` — first observed rate for this leg
- `Convention` — day count convention
- `Rate` (fixed) or `Margin` (floating spread over index)

The **Characteristics** tab (Deal Information) shows `Portfolio`, `Counterpart`, and `Risk section`.

---

## 3. Generator Configuration

CCS generator structure is similar to IRS but with additional multi-currency fields.

### Top-level settings

| Field | Description |
|-------|-------------|
| `Schedules` | `Independent sets across legs` |
| `Stub period` | `Up front` |
| `Market quote` | `Automatic` |
| `Bid/Ask driving leg` | `Automatic` |
| `Settlement delay` | `Inherited from currency` |
| `Amortizing` | `Common definition across legs` or `Independent definition across legs` |
| `Evaluation` | `Default` |
| `Future Cash proceed cut-off` | Date cut-off for future cash proceeds |

### Per-leg settings

All IRS leg settings apply, plus:

| Field | Description |
|-------|-------------|
| `Currency` | Distinct currency per leg (e.g. EUR on Leg 1, USD on Leg 2) |
| `Payment calendar` | May differ per leg (e.g. `EUR/USD` for cross-currency calendars, `TARGET`, `LONDON`, `NEW YORK`) |
| `Fixing calendar` | May differ per leg (e.g. `WARSAW` for PLN, `TARGET` for EUR, `LONDON` for GBP) |
| `Indexed` | Checked on the variable leg of MTM Reset swaps; links to the FX indexation list |
| `Marked to market` | Checked on the variable leg for MTM Reset variant (e.g. `EUR/USD CCS`) |
| `Multi Currency` | Checked when the swap has a multi-currency component |
| `Day count` | `Yes` — enables day count |
| `Initial exchange` | ✓ — principal exchange at trade start |
| `Intermediate payments` | ✓ if amortization or reset flows |
| `Final exchange` | ✓ — principal return at maturity |

---

## 4. Flow Types

CCS legs generate more flow types than IRS due to principal exchanges:

| Code | Description |
|------|-------------|
| `PRI INI` | Initial principal exchange at trade start |
| `PRI AMO` | Intermediate amortization or FX reset of notional |
| `INT` | Periodic interest payment |
| `PRI FIN` | Final principal return at maturity |

Flow schedule columns are the same as IRS, plus:

| Column | Description |
|--------|-------------|
| `Cur` (Outstanding capital indexations) | Reference date, reference rate, and rate for FX indexation — shown on MTM Reset variable legs |

---

## 5. Cash Flow Calculation

### Standard interest flow formula (same as IRS)
```
Flow = Nominal × (Rate / 100) × DayFrac
DayFrac = Days / Base
```

### Example — Fixed leg (EUR, ACT/360, 2.75%)
```
Nominal:    1,531,002.81 EUR
Start date: 12/07/2018
End date:   14/01/2019
Days:       186
Base:       360
DayFrac:    0.516667
Rate:       2.750%
Flow:       1,531,002.81 × (2.75/100) × 0.516667 = 21,753.00 EUR
```

### Example — Floating leg with margin (GBP, ACT/365)
```
Nominal:    150,000,000 GBP
Start date: 24/10/2018
End date:   24/01/2019
Days:       92
Base:       365
DayFrac:    0.252055
Rate:       0.808060% (GBLIBOR3M fixing)
Margin:     0.213750%
Flow:       150,000,000 × ((0.808060 + 0.213750)/100) × 0.252055 = 386,328.16 GBP
```

### Example — Floating leg no margin (MXN, ACT/360, TIIE28D)
```
Nominal:    275,000,000 MXN
Start date: 29/10/2018
End date:   26/11/2018
Days:       28
Base:       360
DayFrac:    0.077778
Rate:       8.1215% (MXNTIIE28D fixing)
Flow:       275,000,000 × (8.1215/100) × 0.077778 = 1,737,098.61 MXN
```

---

## 6. Cross Currency Reset Swap — MTM Flows

### FX Reset flow calculation (variable leg notional adjustment)

At each period start, the variable leg notional is reset. A `PRI AMO` flow is generated representing the notional difference.

**When the variable leg and FX rate are in the same currency (USD/USD):**
```
Constant Nominal (EUR):  7,300,000
Period 1 FX rate:        1.175 EUR/USD → USD Nominal: 8,577,500
Period 2 FX rate:        1.1474 EUR/USD → USD Nominal: 8,376,020
Notional difference:     -201,480 USD
(The PRI AMO flow on the USD leg = -201,480 USD)
(No conversion needed — the difference is already in the variable leg currency)
```

**When variable leg is in a different currency from the FX rate (PLN/EUR example):**
```
Constant Nominal (EUR):  15,000,000
Period 1 FX rate (PLN):  4.2770 → PLN Nominal: 64,155,000
Period 2 FX rate (PLN):  4.3618 → PLN Nominal: 65,427,000
Difference (PLN):        1,272,000
Converted to EUR:        1,272,000 / 4.3618 = 291,622.72 EUR
Adjusted EUR Nominal:    15,000,000 - 291,622.72 = 14,708,377.28 EUR
```

The `Outstanding capital indexations` columns in the flow schedule show the reference date, reference FX rate, and reset rate used for each period.

### Interest flow on variable leg (after reset)
Calculated on the reset notional using the same formula as standard CCS:
```
Nominal:    8,577,500 USD (post-reset)
Start date: 10/07/2018
End date:   10/10/2018
Days:       92
Base:       360
DayFrac:    0.255556
Rate:       2.331440% (USLIBOR3M fixing)
Flow:       8,577,500 × (2.331440/100) × 0.255556 = 51,105.81 USD
```

---

## 7. Murex Generator Examples by CCS Type

| Generator | Type | Legs | Example indices |
|-----------|------|------|-----------------|
| `CCS EUR-PLN` | Float-Float (Reset) | EUR (EURIBOR3M) vs PLN (PLNWIBOR3M) | Variable PLN leg resets to EUR/PLN FX |
| `CCS EUR-USD` | Float-Float | EUR (EURIBOR3M) vs USD (USLIBOR3M) | Standard basis swap |
| `CCS EUR-USD` (MTM) | Float-Float (Indexed) | EUR (EURIBOR3M) vs USD (USLIBOR3M) | USD leg indexed + marked to market |
| `CCS EUR-GBP` | Float-Float | GBP (GBLIBOR3M) vs EUR (EURIBOR3M) | Standard basis swap |
| `CCS EUR-CZK` | Fixed-Float | CZK (fixed) vs EUR (EURIBOR3M) | Fixed-for-floating |
| `CCS MXN-USD` | Float-Float | USD (USLIBOR1M) vs MXN (MXNTIIE28D) | EM basis swap |

---

## 8. Key Differences from IRS in Murex

| Dimension | IRS | CCS |
|-----------|-----|-----|
| Product label | `Interest rate swap` | `Currency swap` |
| Principal exchange fields | Initial/Final exchange unchecked | Initial/Final exchange always checked |
| Flow types | `INT`, `FLW` | `PRI INI`, `PRI AMO`, `INT`, `PRI FIN` |
| `Indexed` field | Not used | Used on variable leg for MTM Reset |
| `Marked to market` | Not used | Used on variable leg for MTM Reset |
| Payment calendars | Often same on both legs | Typically different per leg (per currency) |
| Flow schedule columns | Standard | Includes `Outstanding capital indexations` on reset legs |
| `Characteristics` tab | Standard | May show FLEX warning if entered as FLEX type |

> **Note on FLEX:** In some Santander trades, the `Characteristics` tab is highlighted in red indicating the trade was entered as a FLEX (flexible) structure rather than a standard generator-driven structure. This is a Murex data quality flag and does not affect economic behaviour but may affect downstream processing.

---

*Document maintained by Qaracter — AUKI Programme.*
*Last updated: June 2026*
