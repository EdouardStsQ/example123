# Cross Currency Swap (CCS)

> **Scope:** Generic product definition — system-agnostic. No Murex, Calypso, or BOX specifics.
> **Layer:** Qaracter — reusable across all programmes and client environments.
> **Purpose:** Reference for any team (accounting, development, AI agents) needing to understand what a CCS is and how it works economically. Includes Cross Currency Reset Swaps (MTM CCS) as a subtype.

---

## 1. What is a Cross Currency Swap?

A Cross Currency Swap (CCS) is a contract to exchange, at an agreed future date, principal amounts in two different currencies at a conversion rate agreed at the outset. During the term of the contract, the parties exchange interest — calculated on the principal amounts — according to agreed rates and frequencies.

The underlying concept is to match the difference between the spot and the forward rate of any currency over a specified period.

**Three types of cash flows are generated:**
1. **Capital flows** — initial and final exchange of principal in the two currencies
2. **Interest flows** — periodic interest payments on each leg
3. **Premium flows** — if applicable

Unlike IRS, CCS are multi-currency products. The P&L is natively expressed in the base currency; FX risk is natively expressed in the underlying currency.

**Cash flows cannot be netted** — all flows, including principal, must be exchanged gross.

---

## 2. Structure: Two Legs

Each leg has its own currency, interest rate type (fixed or floating), notional, payment frequency, and day count convention.

**Capital exchanges:**
- **Initial exchange (PRI INI):** At trade start, each party pays the other the agreed principal in their respective currency. Typically at spot FX rate.
- **Intermediate exchanges (PRI AMO):** Amortization payments during the life of the swap, if applicable.
- **Final exchange (PRI FIN):** At maturity, each party returns the original principal they received. The same FX rate as inception applies — regardless of market movements at maturity.

**Interest flows:**
- Calculated per leg using the same formula as IRS: `Flow = Nominal × (Rate / 100) × DayFrac`

---

## 3. Types of CCS

### 3.1 Fixed-for-Fixed CCS
Both legs pay fixed rates in different currencies. Used to access cheaper borrowing in foreign currency markets.

**Classic example:** An American firm needs JPY; a Japanese firm needs USD. The US firm borrows USD at 7% and lends to the Japanese firm; the Japanese firm borrows JPY at 9% and lends to the American firm. Both pay their cheaper domestic rate to the other.

**Cash flow calculation (fixed leg):**
```
Nominal:    1,531,002.81 USD
Start date: 12/07/2018
End date:   14/01/2019
Days:       186
Base:       360
DayFrac:    0.516667
Rate:       2.750%
Flow:       1,531,002.81 × (2.75/100) × 0.516667 = 21,753.00 USD
```

### 3.2 Fixed-for-Floating CCS
One leg pays a fixed rate; the other pays a floating rate referenced to a market index.

**Example:** Receive fixed CZK (0.9939%) vs pay floating EUR (EURIBOR3M, margin -0.0320%).

### 3.3 Floating-for-Floating CCS (Cross Currency Basis Swap)
Both legs pay floating rates in different currencies. Used primarily for swapping liquidity — a firm borrows in a liquid currency and swaps into a less liquid domestic currency.

The basis swap market is liquid for maturities beyond one year (where FX forward markets become illiquid). Cross currency basis quotes encapsulate liquidity spreads between currencies and are used in discount curves.

**Basis swaps are quoted as a spread over one index** (the other index is paid flat).

**Example:** Pay USLIB0R1M + 0.291% vs receive MXNTIIE28D flat (USD/MXN).

**Cash flow calculation:**
```
Nominal:    35,000,000 USD (or 649,425,000 MXN)
Start date: 27/03/2018
Days:       28 (for TIIE28D)
Base:       360
DayFrac:    0.077778
Rate:       8.1215% (index fixing)
Flow:       275,000,000 × (8.1215/100) × 0.077778 = 1,737,098.61 MXN
```

---

## 4. Cross Currency Reset Swap (MTM CCS)

Also known as: FX Reset Currency Swap, Marked-to-Market Currency Swap.

A Cross Currency Reset Swap is a specific case of CCS where the **notional of one leg (the Variable Currency Leg) is periodically adjusted** to reflect changes in the FX rate, while the other leg (the Constant Currency Leg) keeps its notional fixed throughout.

### Purpose
To periodically eliminate the FX exposure arising from movements in the relevant currency exchange rate — specifically the exposure that accumulates from the beginning of one interest period to the beginning of the next.

### Mechanics

**Constant Currency Leg:** Notional fixed throughout. Standard periodic interest payments.

**Variable Currency Leg:** At the start of each period, the notional is reset to: `Variable Notional = Constant Notional × New FX Rate`. An **additional AMO (amortization) flow** is generated at each reset date representing the difference in notional value between periods.

**Reset flow calculation:**
```
Constant Nominal (EUR):   15,000,000
Period 1 FX rate:         4.2770 EUR/PLN → PLN Nominal: 64,155,000
Period 2 FX rate:         4.3618 EUR/PLN → PLN Nominal: 65,427,000
Difference:               1,272,000 PLN = 291,622.72 EUR
Adjusted EUR Nominal:     15,000,000 - 291,622.72 = 14,708,377.28
```

For USD-denominated resets (where both the FX rate and the variable leg are in USD):
```
Constant Nominal (EUR):  7,300,000
Period 1 FX rate (EUR/USD): 1.175 → USD Nominal: 8,577,500
Period 2 FX rate (EUR/USD): 1.1474 → USD Nominal: 8,376,020
Difference:              -201,480 USD
(No conversion back to EUR needed — the difference is directly in the variable leg currency)
```

### Indexed variant (Marked-to-Market + Indexed)
A further variant where one leg is marked to market AND indexed to the FX rate. In the generator this appears as: `Indexed = checked` on the variable leg, `Marked to market = EUR/USD CCS`. The USD notional resets at each period based on the prevailing EUR/USD spot rate.

### Flow Types Generated (Variable Leg)

| Flow Type | Description |
|-----------|-------------|
| `PRI INI` | Initial principal exchange at trade start |
| `PRI AMO` | Reset flow at each period start — difference in variable notional due to FX rate change |
| `INT` | Periodic interest payment on the (reset) variable notional |
| `PRI FIN` | Final principal return at maturity |

---

## 5. Cash Flow Summary by CCS Type

| Flow | Fixed-Fixed | Fixed-Float | Float-Float (Basis) | MTM Reset |
|------|-------------|-------------|---------------------|-----------|
| Initial principal exchange | ✓ | ✓ | ✓ | ✓ |
| Periodic interest (fixed) | ✓ | One leg | — | One leg (if fixed) |
| Periodic interest (floating) | — | One leg | ✓ both legs | One leg (typically) |
| Intermediate amortization | Optional | Optional | Optional | Optional |
| FX reset AMO flow | — | — | — | ✓ at each reset |
| Final principal exchange | ✓ | ✓ | ✓ | ✓ |

---

## 6. Key Differences from IRS

| Dimension | IRS | CCS |
|-----------|-----|-----|
| Currencies | Single currency | Two different currencies |
| Principal exchange | Never | Always (initial + final, and intermediate if reset) |
| FX risk | None | Yes — on the principal and on foreign currency interest |
| Day count | Per convention (same CCY) | May differ per leg |
| NPV currency | Trade currency | Base currency (P&L); underlying currency (FX risk) |

---

## 7. Risk Profile

| Risk | Description |
|------|-------------|
| **Interest rate risk** | Sensitivity to rate curve movements in each currency |
| **FX risk** | Arising from principal exchange and foreign currency interest flows; amplified in MTM Reset swaps |
| **Cross-currency basis risk** | Spread between discount curves in two currencies |
| **Counterparty credit risk** | Amplified vs IRS due to principal exchange |

---

*Document maintained by Qaracter — AUKI Programme.*
*Last updated: June 2026*
