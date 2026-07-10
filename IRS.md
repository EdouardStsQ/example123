# Interest Rate Swap (IRS)

> **Scope:** Generic product definition — system-agnostic. No Murex, Calypso, or BOX specifics.
> **Layer:** Qaracter — reusable across all programmes and client environments.
> **Purpose:** Reference for any team (accounting, development, AI agents) needing to understand what an IRS is and how it works economically.

---

## 1. What is an Interest Rate Swap?

An Interest Rate Swap (IRS) is an OTC derivative contract in which two counterparties exchange interest payments on a notional principal amount for a defined period. The notional is never exchanged — it is only used as a calculation base (hence also called "notional" rather than "nominal").

IRS are mono-currency products: both legs are in the same currency, so no principal exchange takes place at inception or maturity.

Three main types:

| Type | Description |
|------|-------------|
| **Vanilla IRS** | One party pays a fixed rate; the other pays a floating rate referenced to a published index (e.g. EURIBOR, SOFR, LIBOR, TIIE) |
| **Basis Swap** | Both parties pay floating rates, each referenced to a different index or tenor |
| **Compounding Swap** | At least one leg pays a compounded flow — interest is reinvested and paid at the end of the compounding period rather than at each calculation period end |

IRS are among the most liquid and widely used interest rate products in any market. They are primarily used to hedge fixed or floating rate exposures on assets and liabilities.

---

## 2. Structure: Two Legs

### Fixed Leg
- Pays a predetermined fixed interest rate on the notional
- Payment frequency and day count convention agreed at trade inception
- Cash flow formula: `Flow = Notional × (Rate / 100) × DayFrac`
- Where `DayFrac = Days / Base` (e.g. 181 / 365 for ACT/365)

### Floating Leg
- Pays a floating rate referenced to a published index (e.g. EURIBOR3M, GBPLIBOR6M, MXNTIIE28D)
- Rate fixed periodically according to the index tenor (fixing date precedes the payment date)
- Same flow formula applies, using the fixed index rate for each period
- Payment frequency typically matches the index tenor (e.g. 3M index → quarterly payments)
- Fixed and floating legs may have different payment frequencies

---

## 3. Types of IRS

### 3.1 Vanilla IRS (Fixed vs Floating)
The most common structure. One party pays a fixed rate, the other pays a floating rate linked to a market index.

**Example:** Bank pays fixed 8.20% (GBP, ACT/365, 6m frequency) against receiving GBPLIBOR6M flat.

**Cash flow calculation:**
```
Notional:   93,750,000 GBP
Start date: 31/12/2014
End date:   30/06/2015
Days:       181
Base:       365
DayFrac:    0.495890
Rate:       3.6200% (customized for this period)
Flow:       93,750,000 × (3.62/100) × 0.495890 = 1,682,928.08 GBP
```

### 3.2 Basis Swap (Floating vs Floating)
Both legs pay floating rates referenced to different indices or tenors. Used to limit interest rate risk arising from different rate tenors on the same currency, or to access liquidity in other currencies.

Basis swaps are quoted as a spread over one index, with the other index paid flat. By convention, the spread is added to the leg with the **shorter tenor**.

**Example:** Bank receives EUR EONIA COMP + 0.15% against paying EURIBOR6M flat.

**Cash flow calculation (basis swap leg with margin):**
```
Notional:   4,400,000 EUR
Start date: 06/11/2018
End date:   06/05/2019
Days:       181
Base:       360
DayFrac:    0.502778
Rate:       -0.3646% (index fixing)
Margin:     +0.15%
Flow:       4,400,000 × ((-0.3646 + 0.15) / 100) × 0.502778 = -4,746.64 EUR
```

#### Why does the basis spread exist?

In theory, if markets were frictionless, the spread should be zero — compounding a 3M rate twice should equal a 6M rate. In practice it does not, for two reasons:

**Credit and liquidity risk embedded in IBOR rates.** IBOR rates reflect the cost of unsecured interbank lending for a specific term. A 6M rate embeds more credit and liquidity risk than a 3M rate: you are committed for longer, with no option to withdraw if counterparty conditions deteriorate. Rolling two 3M loans gives you that optionality; one 6M loan does not. The 6M rate therefore carries a premium over compounded 3M, and the spread in the basis swap compensates for this difference.

**This spread was negligible before the 2008 financial crisis.** It widened sharply in August 2007 and peaked in October 2008 with the Lehman crash, when short-term credit and liquidity risk became priced explicitly. Post-crisis, separate yield curves are required for different tenors — the "multi-curve" framework — precisely because these spreads can no longer be assumed to be zero.

Other contributing factors include regulatory capital requirements, money market issuance patterns, investor tenor preferences, and banks hedging their own balance sheet tenor mismatches.

> **Note on cross-currency basis swaps (CCS):** the spread in a CCS has different drivers — primarily USD funding demand, structural FX hedging flows, and deviations from Covered Interest Parity. This is documented in `CCS.md`.

### 3.3 Compounding Swap
A compounding swap is a variation of the plain IRS in which at least one leg pays a **compounded** flow: interest calculated at each calculation period is reinvested and paid at the end of the compounding period rather than at the end of each period individually.

**Key distinction from OIS compounded swaps:** In an OIS swap, the *underlying rate* is compounded (e.g. SOFR compounded in arrears). In a compounding swap, the *interest flows themselves* are compounded — the rate per period can be an IBOR rate or a fixed rate.

**Zero coupon swaps** are a special case of compounding swaps where there is a single payment at maturity.

**Common use case:** Aligning payment frequencies between two legs with different tenors. For example, paying USLIBOR3M (quarterly calculation) compounded to match the semi-annual payment schedule of the USLIBOR6M leg.

---

## 4. Compounding: Economic Mechanics

### What compounding means economically
Instead of paying interest at the end of each calculation period, the interest amount is reinvested at the same (or a different) rate for the next period. The accumulated amount is paid at the end of the compounding window.

### Compounding conventions

Eight compounding rules are available, differing in how the margin is treated in the reinvestment and whether broken (stub) periods are included or excluded from compounding:

| Rule | Description |
|------|-------------|
| `(I+M) at (I+M)` | Flow including margin is compounded at rate including margin |
| `(I+M) at I` | Flow including margin is compounded at rate excluding margin |
| `(I at I) + M` | Flow excluding margin is compounded; margin paid separately |
| `I at (I+M)` | Flow excluding margin is compounded at rate including margin |
| `I at (I+M) + M` | Flow excluding margin compounded at rate including margin; margin paid separately |
| `No compounding` | Flows simply summed — no compounding |
| `(I+M1) at (I+M2)` | Two separate margins: M1 applied to the flow, M2 to the compounding |
| `(I+M) at C` | Flow including margin compounded using an option value (non-linear swaps) |

### Compounding formulas

For a compounding window of **n** periods:

**Notations:**
- τᵢ = day count fraction of period i
- rᵢ = floating rate of period i
- lᵢ = interest rate factor of period i
- mᵢ = rate margin of period i
- N = swap notional
- Cᵢ = floating coupon of period i excluding margin = N × (βᵢ − 1)
- Mᵢ = margin flow of period i = N × (λᵢ − 1)
- Flowᵢ = full flow of period i including margin = N × (αᵢ − 1)

**Interest rate factors per convention:**

| Convention | αᵢ (rate + margin) | βᵢ (rate only) | λᵢ (margin only) |
|------------|---------------------|-----------------|-------------------|
| Linear | 1 + (rᵢ × lᵢ + mᵢ) × τᵢ | 1 + rᵢ × lᵢ × τᵢ | 1 + mᵢ × τᵢ |
| Exponential | e^((rᵢ×lᵢ+mᵢ)×τᵢ) | e^(rᵢ×lᵢ×τᵢ) | e^(1+mᵢ×τᵢ) |
| Yield | (1 + rᵢ × lᵢ + mᵢ)^τᵢ | (1 + rᵢ × lᵢ)^τᵢ | (1 + mᵢ)^τᵢ |

**Payment formula for `(I+M) at (I+M)` over n periods:**
```
Payment = Σᵢ₌₀ⁿ⁻¹ [ Flowᵢ × (Πⱼ₌ᵢ₊₁ʲ⁼ⁿ αⱼ − 1) ] + Σᵢ₌₀ⁿ Flowᵢ
```

For `No compounding`: `Payment = Σᵢ₌₀ⁿ Flowᵢ`

### Compounding period direction and stub handling
When the payment frequency ratio is greater than 1 (i.e. one payment covers multiple calculation periods), four modes determine how stub/broken periods are handled:

| Mode | Direction | Stub period treatment |
|------|-----------|-----------------------|
| Backward (broken periods included) | From maturity backward | Stub included in compounding |
| Backward (broken periods excluded) | From maturity backward | Stub excluded — paid separately |
| Forward (broken periods included) | From start date forward | Stub included in compounding |
| Forward (broken periods excluded) | From start date forward | Stub excluded — paid separately |

---

## 5. Cash Flow Types

| Code | Description |
|------|-------------|
| `INT` | Interest flow that will be paid at the payment date |
| `INC` | Incremental interest flow — not paid immediately; compounded with the next period and paid with all other `INC` flows at the end of the compounding window |
| `FLW` | Additional flow generated by certain indices with settlement lags |
| `PRI` | Capital flow exchanged |
| `INI` | Initial capital flow (not exchanged — notional record only) |
| `FIN` | Final capital flow (not exchanged — notional record only) |
| `AMO` | Amortized capital flow |

---

## 6. Key Economic Concepts

### Day Count Fraction
`DayFrac = Days / Base`
- Days = number of calendar days between calculation start and end dates
- Base = day count convention denominator (e.g. 360 for ACT/360, 365 for ACT/365)

### Payment Frequency
The frequency at which interest payments are made. For vanilla IRS:
- Fixed leg: often annual or semi-annual
- Floating leg: typically matches the index tenor (e.g. 3M, 6M, 28D)

The two legs may have different payment frequencies. In compounding swaps, the payment frequency ratio defines how many calculation periods are grouped into one payment.

### Fixing (Reset)
On each reset date, the floating rate is observed from the index and locked in for that calculation period. The fixing date typically precedes the payment date.

### NPV Computation
The Net Present Value of an IRS is the sum of all discounted future cash flows across both legs. Required inputs:
1. Discounting rate curve (per currency)
2. Estimation rate curve (for floating leg projection)
3. Rate convention and interpolation formula
4. Day count and payment configuration

P&L components: Past Cash Proceeds (PCP), Financing (Fin.), Market Value (MV), Future Cash Proceeds (FCP), Present Value Effect (PVeff).

---

## 7. Risk Profile

| Risk | Description |
|------|-------------|
| **Interest rate risk** | P&L sensitivity to changes in the interest rate curve (Rate Curves Delta) |
| **Basis risk** | P&L sensitivity to changes in the spread between two rate curves (Basis Curves Delta). Relevant for basis and compounding swaps. |
| **Counterparty credit risk** | No principal exchange, but mark-to-market exposure can be significant for long-dated swaps |

---

## 8. Common Use Cases

- **Fixed rate payer:** Hedges against rising interest rates on a floating rate liability
- **Fixed rate receiver:** Hedges against falling interest rates on a fixed rate asset
- **Basis swap user:** Converts floating rate exposure from one index to another (e.g. LIBOR 3M to LIBOR 6M)
- **Compounding swap user:** Aligns payment schedules between legs with different calculation frequencies; zero coupon variant defers all cash flows to maturity

---

*Document maintained by Qaracter — AUKI Programme.*
*Last updated: June 2026*
