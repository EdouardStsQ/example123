# Bond Return Swaps (BRS)

## Purpose of this document

This is a reference document on bond return swaps: what the product is, how the performance and financing legs work, how haircuts and cross-currency conversion are applied, how the flow schedules are constructed, and how the terms are represented in Murex. It is meant to be read on its own — a new joiner or anyone unfamiliar with the product should come away understanding the mechanics, not just recognizing the trade capture screen.

The three worked examples in §11 are a **single-currency USD trade with a large haircut**, and two **cross-currency trades on a BRL government floating-rate note swapped into USD** — the second of which includes both flow schedules. Between them they cover both haircut modes, single-currency and cross-currency structures, with and without principal exchange, and two different financing templates.

**A note on identifiers.** Portfolio, counterparty and security identifiers have been omitted throughout. Each example is described by the characteristics that matter economically — currency, asset type, structure — which is sufficient to follow the mechanics.

## 1. Overview: what a bond return swap is

A bond return swap is a bilateral OTC contract with two legs:

- **The performance leg** pays the **total return of a specified bond** — its price change plus any income it generates over the period.
- **The financing leg** pays a **funding rate**, typically a floating index plus a margin, applied to a notional derived from the bond's value.

The party receiving the performance leg has synthetic **long** exposure to the bond; the party paying it is synthetically **short**. In both cases the exposure is obtained **without buying or borrowing the bond outright** — which is the point of the product.

Three consequences follow:

- **It is a financing product as much as a market-risk product.** Economically a BRS is close to a repo or a financed bond position: one side gets the economics of owning the asset, the other gets a return on the money it has effectively lent. The template field **Trade purpose: Delta one** states this directly — the intent is linear exposure, not optionality.
- **The bond is a reference, not a holding.** Neither party need own it. The contract references its price and income.
- **The two legs have different notionals.** The performance leg runs on the bond's value; the financing leg runs on that value adjusted by a **haircut** (§5.2). Where the haircut is zero the two coincide; where it is not, they diverge substantially.

## 2. Direction

The **Payout** radio buttons on each leg set direction independently, and the performance leg additionally displays a **Short / Long** tag confirming the resulting exposure.

| | Synthetic long | Synthetic short |
|---|---|---|
| Performance leg | **Receive** | **Pay** |
| Tag shown | Long | **Short** |
| Financing leg | **Pay** | **Receive** |
| Economic analogue | Financed purchase of the bond | Short sale, earning on the proceeds |
| Gains when | Bond price rises | Bond price falls |

All three examples are **Pay performance / Receive financing** — synthetic short positions, tagged *Short*.

Note the sign convention in the flow schedules: because the performance leg is *paid*, a **negative** bond return produces a **positive** cash flow to the book. Example 2 demonstrates this (§10.1).

## 3. The bond and its pricing on the capture screen

The **Financial definition** block carries the bond's valuation at inception:

| Field | Meaning |
|---|---|
| **Bond / Market** | The referenced security and the market from which it is priced. |
| **Clean Price** | Price excluding accrued interest. |
| **Accrued Coupon** | Interest accrued since the last coupon, with its day-count fraction alongside. |
| **Dirty Price** | Clean price plus accrued — the price actually used, given *Reference price mode: Dirty*. |
| **Yield** | The yield implied by the clean price. |
| **Effective date / Maturity** | The swap's dates, not the bond's. Maturity shows unadjusted and adjusted values. |
| **Maturity structure** | *Standard* on all three examples. |
| **ValuationShifter** | The lag between the valuation date and the corresponding settlement date (§7). |

**The reconciliation check.** Clean price plus accrued coupon should equal the dirty price. This holds exactly on two of the three examples and fails on one — see §11.4 and §14. It is a cheap and worthwhile check whenever reading one of these screens.

**Day-count bases differ by market.** The USD example accrues on **25/360**; the two BRL examples accrue on a **252** denominator, the Brazilian business-day convention. The accrual basis follows the bond's market, not the swap.

## 4. The performance leg

### 4.1 What it pays

The performance leg pays the change in the bond's value between the first and last valuations, plus income received over the period. The flow schedule (§10.1) makes both components explicit.

### 4.2 Reference price and reference price mode

- **Reference price** — the price against which performance is measured, i.e. the strike of the total-return calculation.
- **Reference price mode** — **Dirty** on all three examples, meaning the comparison uses dirty prices, so accrued interest is inside the performance calculation rather than handled separately.

### 4.3 Nominal, quantity and price

The three are linked:

**Nominal = Quantity × Reference price** (in the swap's currency, with any scaling the security's quotation convention requires)

In the cross-currency examples, 52,569 × 3,804.49970 = 199,998,745, matching the stated nominal to within display rounding. In the USD example, quantity is exactly 100 × nominal, reflecting that instrument's unit denomination. The template field **Performance based on: Shares** indicates the leg is quantity-driven.

### 4.4 Income

- **Income Period** — the window over which coupon income is captured, shown separately from the valuation period (they coincide on all three examples).
- **Income Payment fraction** — the proportion of income passed through, **1.000000** on all three, so 100% of coupon income flows to the performance receiver.
- The template's **Income/Tax credit** configuration governs withholding and tax-credit treatment. It was not captured (§14) and is material wherever the bond's income is subject to withholding — which is common for emerging-market government paper.

### 4.5 Valuation period

**Valuation Period** sets the first and last observation dates for the price. These need not align with the financing leg's calculation period — in Example 2 the performance leg begins two days before the financing leg (§7).

## 5. The financing leg

### 5.1 Index and margin

The financing leg is a floating leg in the ordinary sense: an index, an index factor, and a **margin** added under **Margin mode: Additive**.

| Example | Index | Margin |
|---|---|---|
| 1 | USD SOFR CMP LB -2 | 0.9350% |
| 2 and 3 | USD FIXED RATE | 4.5560% |

The **LB -2** suffix in Example 1 denotes a **two-business-day lookback**: the compounding observation window is shifted back two days relative to the accrual period, so the rate is known slightly before the payment is due. This is a standard mechanism for making a backward-looking compounded rate operationally settleable.

**1st fixing reads 0.000000** on all three, consistent with compounded and estimated indices whose rate is not known at trade date.

### 5.2 The haircut, and its two modes

The financing leg's notional is not simply the bond's value. It is the bond's value adjusted by a **haircut**, and the field carries a **mode indicator** that determines the formula. Both modes appear across the examples:

| Mode indicator | Formula | Example |
|---|---|---|
| **`1 +/- x`** | Start Nominal = Nominal − Haircut Amount, where Haircut Amount = Nominal × haircut % | Example 1 |
| **`x`** | Start Nominal = Nominal × haircut % | Examples 2 and 3 |

Reading the number without the mode indicator inverts the meaning: a haircut of "100" under mode `x` means **no reduction at all**, while a haircut of "96.35" under mode `1 +/- x` means financing on only **3.65%** of the bond's value.

**Worked reconciliation — Example 1** (mode `1 +/- x`, haircut −96.35):

- Nominal 109,188,427.98
- Haircut Amount 105,204,132.42 — which is 96.351% of nominal
- Start Nominal = 109,188,427.98 − 105,204,132.42 = **3,984,295.56**, matching the screen exactly
- Financing therefore accrues on **3.649%** of the bond's value

**Worked reconciliation — Examples 2 and 3** (mode `x`, haircut 100.00):

- Haircut Amount 0.00
- Start Nominal = Nominal = **199,998,744.99** — financing on the full value

The economic effect is significant: in Example 1 the performance leg runs on 109.2m while financing accrues on under 4m, so the financing cost is a small fraction of what a fully-funded position would bear. Why a haircut of that size applies on that trade and none on the others is a question the captures do not answer (§14).

### 5.3 Marked to market: based on initial price

All three templates set **Marked to market: Based on initial price** with **Cash based on: Dirty Price**. The financing notional is therefore fixed off the initial dirty price and **does not reset as the bond marks**.

This is a structural choice with real consequences. In a resetting structure the financing notional tracks the asset's value, so the funded amount stays aligned with the exposure. Here it does not: if the bond rallies, the performance leg grows while the financing leg continues to accrue on the original amount. Anyone reconciling financing accruals against a marked exposure needs to know which convention applies.

### 5.4 Fixing and payment timing

| Example | Fixing | Payment |
|---|---|---|
| 1 | **In arrears** | In arrears |
| 2 and 3 | **Up front** | In arrears |

In-arrears fixing suits a compounded overnight index, whose rate is only known once the period has run. Up-front fixing sets the rate at the start of the period. Payment is in arrears throughout.

### 5.5 Principal exchange

Whether principal is exchanged is set by the **Initial / Intermediate / Final exchange** flags on both template sections:

- **Example 1** — all three unticked. No principal flows; the swap settles on performance and financing alone.
- **Examples 2 and 3** — **Final exchange ticked** on both the Security and Interest sections. The flow schedules accordingly carry `PRI` rows of −199,998,744.99 on the performance leg and +199,998,744.99 on the financing leg, which **offset exactly** (§10.3).

## 6. Cross-currency bond return swaps

Examples 2 and 3 introduce a dimension Example 1 does not have: the **bond is denominated in one currency and the swap settles in another**.

The bond is a BRL government note; both legs pay in USD. The mechanism is visible in the trade capture and explicit in the flow schedule:

- **First valuation** is recorded in **BRL**, alongside a **First fx rate** in USD-BRL.
- Each price observation is converted to USD at the prevailing FX fixing — here a PTAX-based rate.
- Performance is measured on the **converted** prices, so the return the swap pays is the return **in USD terms**.

The consequence is that **a cross-currency BRS embeds an FX position**, and the FX component can dominate. Example 2's flow schedule shows exactly that (§10.1): the bond gained 6.54% in BRL while the BRL weakened 6.93%, leaving the position **down 0.36% in USD**. A trader long the bond's local-currency performance would have made money; the swap, measured in USD, lost.

Related template settings:

- **Multicurrency Indexation: Fixed Indexation** on both legs.
- **First prices and FX rate inherited: from trade (customized)** — the initial price and FX rate are taken from the trade rather than from a market source.
- **MultiCurrency propagation** and **Multi Currency** unticked.
- **Indexed ✔** on the security leg of the BRL template, with an indexations list attached — absent on the USD template.

Note also that the **calendars split by function** on the cross-currency trades: the security leg uses Brazilian calendars (payment BRASIL CDI, fixing SAO PAOLO) while the interest leg uses NEW YORK. The asset lives in one market and the cash settles in another, and the configuration reflects that.

## 7. Dates and the valuation shifter

**ValuationShifter** sets the lag between a valuation date and its corresponding settlement date — `+2 OPEN DAYS` on Example 1, `+2 OD BRAZIL` on Examples 2 and 3, the latter using the Brazilian calendar. It can be inherited from the security (Example 1's template) or set as a specific delay (the BRL template).

Its visible effect is that **the two legs need not start on the same date**:

| Example | Performance leg start | Financing leg start | Effective date |
|---|---|---|---|
| 1 | 09 sept 2026 (Wed) | 11 sept 2026 (Fri) | 11 sept 2026 |
| 2 | 12 ago 2026 | 14 ago 2026 | 14 ago 2026 |
| 3 | **14 ago 2026** | 14 ago 2026 | 14 ago 2026 |

In Examples 1 and 2 the performance leg begins two open days before the financing leg — the price is observed on the valuation date while cash settles two days later. Example 3, on the same template as Example 2, has both legs starting together, so the shift is not applied uniformly across trades using the same template. That difference is worth confirming (§14).

Maturity is shown as an unadjusted and an adjusted date, as elsewhere in the system.

## 8. Templates

The **Template** field supplies the structural configuration of both legs, in the same way a generator does for a swap. Two templates appear:

| Field | USD template | BRL template |
|---|---|---|
| Description | Based on initial price, floating | Based on initial price, floating |
| Evaluation | **Accrual - PV effect** | **Default** |
| Accrual delay | +1 open day | *(not shown)* |
| Flows projection delay | +1 open day | **Redefined, +0 BD** |
| Stub period position | Both ends (forward) | Both ends (forward) |
| Direction | Nominal | Nominal |
| Non-settled cash handling | In future cash (when all but FX rate is fixed) | Same |
| Treat collateral | On pool level | On pool level |
| Early settlement | Yes | Yes |
| Valuation shifter | **Inherited from security** | **Specific delay, +2 OD BRAZIL** |
| Liquidation | Average price | Average price |
| Increase lot fungibility | Always effective date | Always effective date |
| Trade purpose | **Delta one** | **Delta one** |
| *Security leg* | | |
| Evaluation | **Accrual, sens. accrual** | **Inherited** |
| Start delay | +0 BD | +00 BD |
| Payment calendar | NEW YORK | **BRASIL CDI** |
| Fixing calendar | NEW YORK | **SAO PAOLO** |
| Performance based on | Shares | Shares |
| Indexed | Unticked | **Ticked** (indexations list) |
| Final exchange | Unticked | **Ticked** |
| *Interest leg* | | |
| Evaluation | Accrual, sens. accrual | Inherited |
| Marked to market | Based on initial price | Based on initial price |
| Cash based on | Dirty Price | Dirty Price |
| Payment calendar | NEW YORK | NEW YORK |
| Fixing calendar | **US GVT BND** | **NEW YORK** |
| Fixing | **In arrears** | **Up front** |
| Payment | In arrears | In arrears |
| Rate convention | LIN ACT/360 | LIN ACT/360 |
| Margin mode | Additive | Additive |
| Rate factor applied | To main index | To main index |
| Final exchange | Unticked | **Ticked** |
| Interest exposure | **Yes** | **No** |

Two settings deserve particular attention because they change the trade's economics rather than its plumbing: **Final exchange** (§5.5) and **Interest exposure**, which differ between the templates and therefore between otherwise similar trades.

Note also **Early Settlement: Yes** and **Liquidation: Average price** on both — the swap can be unwound early, in whole or in part, with liquidation priced on an average basis. That matters for lifecycle handling, since a BRS is frequently partially unwound rather than run to maturity.

## 9. Payment conditions

All three examples set **Payment Conditions: Cash** — the swap settles in cash rather than by delivery of the underlying bond.

## 10. The flow schedules

Example 2 includes both flow schedules, which is where the product's mechanics become concrete. Each leg produces two flow types: **INT** (the periodic economic flow) and **PRI** (principal, present only where final exchange is enabled).

### 10.1 The performance flow

Headed *Performance payments USD (Initial: Pay/Short)*:

| Element | Value |
|---|---|
| Quantity | 52,569.0000 |
| **First** fixing / bond settlement date | 12 ago 2026 / 12 ago 2026 |
| First price, dirty return | **19,662.79582** (BRL) |
| First fx fixing date / rate | 12 ago 2026 / **5.1683** |
| First converted price | **3,804.49970** (USD) |
| **Last** fixing / bond settlement date | 25 feb 2027 / 25 feb 2027 |
| Last price, dirty return | **20,949.01830** (BRL) |
| Last fx fixing date / rate | 25 feb 2027 / **5.5264** |
| Last converted price | **3,790.73203** (USD) |
| **Price Difference** | **−13.76770** |
| Payment date | 01 mar 2027 |
| **Flow** | **723,752.89 USD** |

The schedule shows the whole calculation in one row, and each step reconciles:

- **Conversion:** 19,662.79582 / 5.1683 = 3,804.4997 — the first converted price, exactly.
- **Price difference:** 3,790.73203 − 3,804.49970 = −13.76767, matching the −13.76770 shown to display precision.
- **Flow:** 52,569 × 13.7677 = 723,754, against 723,752.89 shown — agreeing to within the rounding of the displayed price difference.
- **Sign:** the price difference is negative and the flow is positive, because the book **pays** this leg. A loss on a leg you pay is a receipt (§2).

**The FX effect, made explicit.** In local currency the bond rose from 19,662.80 to 20,949.02, a gain of **6.54%**. Over the same window the BRL weakened from 5.1683 to 5.5264 per USD, **6.93%**. Converted, the price fell from 3,804.50 to 3,790.73 — a loss of **0.36%** in USD. The currency move more than consumed the bond's gain. This single row is the clearest demonstration of why a cross-currency BRS cannot be analysed as a bond position alone.

### 10.2 The financing flow

Headed *Floating flows payments USD (Rec)*:

| Element | Value |
|---|---|
| Calculation period | 14 ago 2026 → 01 mar 2027 |
| Nominal | 199,998,744.99 |
| Fx / converted dirty price | 5.1683 / 3,804.49970 |
| Fixing date | 14 ago 2026 |
| Rate | **0.0000** *(shown italic — estimated)* |
| Margin | **4.5560** |
| Payout spread / Sales margin / Rate factor | 0.0000 / 0.0000 / 1.0000 |
| Payment date | 01 mar 2027 |
| **Flow** | **5,036,879.50 USD** |

**This reconciles exactly.** The period runs 199 days from 14 August 2026 to 1 March 2027, and on ACT/360:

199,998,744.99 × 4.5560% × 199 / 360 = **5,036,879.50**

Note that the projected rate is **zero**, so the entire financing accrual comes from the margin. The capture was taken in pricing mode with forward rates estimated, but a rate of exactly zero on an index named *USD FIXED RATE* is worth confirming (§14).

### 10.3 Principal flows

Both legs carry a `PRI` row dated 01 mar 2027:

- Performance leg: **−199,998,744.99 USD**
- Financing leg: **+199,998,744.99 USD**

These **offset exactly**, which is what the *Final exchange* flags on this template produce (§5.5). They are not a net cash movement; they are the gross representation of principal on each leg. Any downstream process that treats them as independent cash flows will double-count unless the offset is recognised.

### 10.4 Pricing mode

These schedules were produced in **pricing mode**, so future fixings and future prices are **estimates**, not realised values. The last price of 20,949.01830 and the last FX of 5.5264 are projections for February 2027, not observed data. The structure and arithmetic of the schedule are real; the forward-looking values are model output and will be replaced as fixings occur.

## 11. Worked examples

### 11.1 Example 1 — USD single-currency BRS with a 96.35% haircut (pay performance / short)

| Field | Value |
|---|---|
| Template | USD loan-type return swap template |
| Asset | USD-denominated loan-type security |
| Effective date | 11 sept 2026 |
| Maturity | 11 ago 2027 |
| Clean / Accrued / Dirty | 99.5903 / 0.4097 / **100.0000** |
| Accrual basis | 25 / 360 |
| Yield | 2.347717% |
| ValuationShifter | +2 OPEN DAYS |
| Payment conditions | Cash |
| **Performance leg** | **Pay — Short** |
| Start date | 09 sept 2026 |
| Nominal | 109,188,427.98 |
| Quantity | 10,918,842,798.00 |
| Reference price / mode | 100.0000 USD / **Dirty** |
| Valuation and income period | 09 sept 2026 → 11 ago 2027 |
| Income payment fraction | 1.000000 |
| **Financing leg** | **Receive — Floating** |
| Index | **USD SOFR CMP LB -2** |
| Start date | 11 sept 2026 |
| **Haircut** | **−96.35**, mode `1 +/- x` |
| **Haircut amount** | **−105,204,132.42** |
| **Start nominal** | **3,984,295.56** |
| Convention | LIN ACT/360 |
| Margin | **0.9350%** |
| Principal exchange | **None** |

**Position:** synthetic short of a USD asset, financed.

**Pricing:** clean 99.5903 + accrued 0.4097 = **100.0000** exactly, and the reference price is likewise 100 on a dirty basis — the swap is struck at par.

**The haircut is the defining feature.** Financing accrues on 3,984,295.56 — **3.649%** of the 109.2m performance notional (§5.2). The financing cost of this position is therefore a small fraction of the exposure it carries.

**Financing index:** SOFR compounded with a two-day lookback, plus 93.5bp, fixing in arrears with a **US GVT BND** fixing calendar against a NEW YORK payment calendar.

**Dates:** performance starts Wednesday 9 September, financing Friday 11 September — the two open days of the valuation shifter. Term runs 336 days.

### 11.2 Example 2 — BRL/USD cross-currency BRS, with flows (pay performance / short)

| Field | Value |
|---|---|
| Template | BRL bullet floating, compounded accrual |
| Asset | BRL government floating-rate note |
| Effective date | 14 ago 2026 |
| Maturity | 01 mar 2027 |
| Clean / Accrued / Dirty | **1,013.41134** / 18,669.6920 / 19,662.79582 |
| Accrual basis | 252 (Brazilian business-day) |
| Yield | 2.052092% |
| ValuationShifter | +2 OD BRAZIL |
| Payment conditions | Cash |
| **Performance leg** | **Pay — Short** |
| Start date | **12 ago 2026** |
| Nominal | 199,998,744.99 |
| Quantity | 52,569.00 |
| Reference price / mode | **3,804.49970 USD** / Dirty |
| First valuation / First fx | 1,013.41134 BRL / **5.1683 USD-BRL** |
| Valuation and income period | 12 ago 2026 → 25 feb 2027 |
| Income payment fraction | 1.000000 |
| **Financing leg** | **Receive — Floating** |
| Index | USD FIXED RATE |
| Start date | 14 ago 2026 |
| Start nominal | **199,998,744.99** |
| Haircut | **100.00**, mode `x` → haircut amount **0.00** |
| Convention | LIN ACT/360 |
| Margin | **4.5560%** |
| Principal exchange | **Final exchange enabled** |

**Position:** synthetic short of a BRL government note, with the economics delivered in USD.

**Cross-currency structure.** The bond prices in BRL; every observation is converted to USD at a PTAX-based fixing, and performance is measured on the converted series. The trade is therefore simultaneously a bond position and an FX position (§6).

**No haircut.** Financing runs on the full 199,998,744.99, the direct counterpart to Example 1.

**Flows** are set out in §10 and reconcile: financing exactly at 5,036,879.50, performance to within display rounding at 723,752.89, and offsetting principal rows.

**A pricing inconsistency.** Clean 1,013.41134 + accrued 18,669.6920 = 19,683.10334, against a stated dirty price of **19,662.79582** — a gap of **20.30752**. This does not reconcile, and Example 3 shows why it matters (§11.4).

### 11.3 Example 3 — BRL/USD cross-currency BRS, the mirror (pay performance / short)

| Field | Value |
|---|---|
| Template | BRL bullet floating, compounded accrual — **identical to Example 2** |
| Asset | The same BRL government floating-rate note |
| Effective date | 14 ago 2026 |
| Maturity | 01 mar 2027 |
| Clean / Accrued / Dirty | **993.10380** / 18,669.6920 / 19,662.79582 |
| Yield | **2.213873%** |
| **Performance leg** | **Pay — Short** |
| Start date | **14 ago 2026** |
| Nominal | 199,998,744.99 |
| Quantity | 52,569.00 |
| Reference price / mode | 3,804.49970 USD / Dirty |
| First valuation / First fx | **993.10380 BRL** / 5.1683 USD-BRL |
| Valuation and income period | 14 ago 2026 → 25 feb 2027 |
| **Financing leg** | **Receive — Floating** |
| Index / Margin | USD FIXED RATE / 4.5560% |
| Start nominal / Haircut | 199,998,744.99 / 100.00 mode `x`, amount 0.00 |
| Principal exchange | Final exchange enabled |

**This trade is the same shape as Example 2** — same bond, same nominal to the cent, same quantity, same reference price, same first FX rate, same margin, same maturity, same template. It differs in exactly three respects: the performance leg starts on 14 August rather than 12 August, the clean price is 993.10380 rather than 1,013.41134, and the yield is correspondingly higher at 2.213873%.

**And its pricing reconciles exactly:** 993.10380 + 18,669.6920 = **19,662.7958**, matching the dirty price of 19,662.79582.

The two trades taken together therefore isolate the problem in Example 2. Same bond, same dirty price, same accrued coupon — but one clean price ties out and the other is **20.30754 too high**, precisely the gap by which Example 2 fails to reconcile. The lower clean price in Example 3 also implies the higher yield, so Example 3 is internally coherent throughout. The likeliest explanation is that Example 2's clean price and yield are observed as of its 12 August performance start while the accrued and dirty price are as of the 14 August effective date, but that should be confirmed rather than assumed (§14).

**Structurally**, the pairing of Examples 2 and 3 — same asset, same size, same terms, two different books, opposite ends of the same economics — has the shape of a mirror or back-to-back booking. Nothing in the captures confirms it.

### 11.4 The three examples side by side

| | Example 1 | Example 2 | Example 3 |
|---|---|---|---|
| Structure | Single currency (USD) | **Cross-currency BRL→USD** | **Cross-currency BRL→USD** |
| Asset | USD loan-type security | BRL government FRN | Same BRL government FRN |
| Direction | Pay performance — Short | Pay performance — Short | Pay performance — Short |
| Effective date | 11 sept 2026 | 14 ago 2026 | 14 ago 2026 |
| Maturity | 11 ago 2027 | 01 mar 2027 | 01 mar 2027 |
| Clean + accrued = dirty? | **Yes** (99.5903 + 0.4097 = 100.0000) | **No** (off by 20.30752) | **Yes** (993.10380 + 18,669.6920) |
| Accrual basis | 25/360 | 252 | 252 |
| Performance nominal | 109,188,427.98 | 199,998,744.99 | 199,998,744.99 |
| Quantity | 10,918,842,798.00 | 52,569.00 | 52,569.00 |
| Reference price / mode | 100.0000 / Dirty | 3,804.49970 USD / Dirty | 3,804.49970 USD / Dirty |
| **Haircut mode** | **`1 +/- x`** | **`x`** | **`x`** |
| **Haircut** | **−96.35** | **100.00** | **100.00** |
| Haircut amount | −105,204,132.42 | 0.00 | 0.00 |
| **Financing nominal** | **3,984,295.56 (3.65%)** | **199,998,744.99 (100%)** | **199,998,744.99 (100%)** |
| Financing index | USD SOFR CMP **LB -2** | USD FIXED RATE | USD FIXED RATE |
| Margin | 0.9350% | 4.5560% | 4.5560% |
| Fixing | In arrears | **Up front** | **Up front** |
| Fixing calendar (interest) | **US GVT BND** | NEW YORK | NEW YORK |
| Security calendars | NEW YORK | **BRASIL CDI / SAO PAOLO** | **BRASIL CDI / SAO PAOLO** |
| Legs start together? | No (+2 open days) | No (+2 open days) | **Yes** |
| Principal exchange | **None** | **Final exchange** | **Final exchange** |
| Interest exposure | **Yes** | No | No |
| Flows captured | No | **Yes** | No |

## 12. Risk profile

A BRS is a **delta-one** product — linear exposure to the bond, with no optionality — but the exposures are more numerous than that suggests:

- **Price risk on the bond**, for the full performance notional. The performance-leg receiver is long, the payer short.
- **Interest rate and credit spread risk**, inherited from whatever drives the referenced bond's price. A government floater and a corporate loan carry very different sensitivities.
- **FX risk on cross-currency structures.** Example 2 shows the currency move exceeding the bond move (§10.1). This is a first-order exposure, not a residual.
- **Financing risk.** The financing leg reprices with its index, and the margin is fixed for the life of the trade. Where the financing notional is set on the initial price and does not reset (§5.3), the funded amount and the exposure diverge as the bond marks.
- **Haircut and collateral risk.** The haircut determines how much of the position is financed. The template's **Treat collateral: On pool level** indicates collateral is managed at pool rather than trade level, which affects how exposure is measured and margined.
- **Counterparty credit risk**, over the life of the swap — a bilateral OTC exposure, mitigated by collateral rather than eliminated.
- **Income and withholding risk.** Income passes through at the configured fraction (100% here), but the tax and withholding treatment behind the *Income/Tax credit* configuration determines what is actually received — material for emerging-market government paper.
- **Early termination and liquidation.** With early settlement enabled and liquidation priced on an average basis, partial unwinds are expected behaviour rather than exceptions, and each creates a valuation and settlement event.
- **Basis between the swap and the cash bond.** The referenced price comes from a specified market source; a hedge held in the physical asset will not track perfectly.

## 13. Glossary of fields seen in the Murex screens

**Financial definition**

- **Template**: the configuration template supplying both legs' structural settings (§8).
- **Bond / Market**: the referenced security and its pricing source.
- **Archiving Group / Cutoff**: the pricing group and cutoff basis (*FIXING*).
- **ValuationShifter**: lag from valuation date to the corresponding settlement date (§7).
- **Effective date / Maturity / Maturity structure**: the swap's dates and schedule shape.
- **Clean Price / Accrued Coupon / Dirty Price / Yield**: the bond's valuation at inception, with the accrual day-count fraction shown beside the accrued figure (§3).
- **Payment Conditions**: *Cash* — settled in cash rather than by delivery (§9).

**Performance leg**

- **Payout (Pay / Receive)** and the **Short / Long** tag: direction and resulting exposure (§2).
- **Bond × factor / Market**: the referenced asset and its multiplier.
- **Nominal / Quantity**: the performance notional and the unit count (§4.3).
- **Reference price / Reference price mode**: the strike of the total-return calculation and whether it is measured clean or dirty (§4.2).
- **First valuation / First fx rate**: on cross-currency trades, the initial price in the bond's currency and the initial FX rate (§6).
- **Valuation Period / Income Period**: the observation windows for price and for income (§4.5).
- **Income Payment fraction**: the proportion of coupon income passed through (§4.4).

**Financing leg**

- **Payout / Fixed or Floating**: direction and rate type.
- **Index × factor**: the financing index and its multiplier. A `LB -n` suffix denotes an n-day lookback (§5.1).
- **Start Nominal**: the financing notional after the haircut (§5.2).
- **Haircut** and its **mode indicator** (`x` or `1 +/- x`), and **Haircut Amount**: the adjustment from performance nominal to financing nominal (§5.2).
- **Convention**: the financing day count (LIN ACT/360 throughout).
- **1st fixing / Margin**: the opening rate and the spread over the index.
- **Payout spreads (Pay / Receive)**: additional spreads, zero throughout.

**Template**

- **Evaluation / Accrual delay / Flows projection delay**: valuation method and timing offsets.
- **Stub period position / Direction / Non-settled cash handling**: schedule and cash treatment.
- **Treat collateral / Early Settlement / Liquidation / Increase lot fungibility**: collateral and lifecycle handling.
- **Trade purpose**: *Delta one* — the product's intent.
- **Marked to market / Cash based on**: whether the financing notional resets, and the price basis used (§5.3).
- **Performance based on**: the driver of the security leg (*Shares*).
- **Indexed / Multicurrency Indexation / First prices and FX rate inherited**: indexation and cross-currency settings (§6).
- **Fixing / Payment**: rate-setting and settlement timing (§5.4).
- **Initial / Intermediate / Final exchange**: principal exchange flags (§5.5).
- **Interest exposure**: differs between the two templates; its effect should be confirmed (§14).
- **Income/Tax credit / Return / Schedules definition**: sub-configurations reached by Edit links, not captured (§14).

**Flow schedule**

- **Flow Tp**: `INT` for the periodic economic flow, `PRI` for principal (§10.3).
- **First / Last fixing, bond settlement date, price, fx fixing date, fx rate, converted price**: the two ends of the performance calculation (§10.1).
- **Price Difference**: the change in converted price driving the performance flow.
- **Calc start / Calc end / Nominal / Rate / Margin / Rate Factor**: the financing accrual inputs (§10.2).
- **Insertion / Deletion Event ID**: lifecycle event references (*Reset*).

## 14. Open items and gaps in this document

1. **Example 2's clean price does not reconcile** (§11.2, §11.3). Clean plus accrued exceeds the stated dirty price by 20.30752, while Example 3 — the same bond, same dirty price, same accrued — reconciles exactly. The likely cause is a valuation-date mismatch between the 12 August performance start and the 14 August effective date, but this should be confirmed, particularly given the accounting implications of which price is authoritative.
2. **The 96.35% haircut on Example 1 is unexplained** (§5.2). The arithmetic reconciles to the cent, but why financing accrues on 3.65% of the position's value on that trade and 100% on the others is not visible in the captures. This is the single largest economic difference across the set.
3. **`Rate: 0.0000` with a 4.5560% margin on an index named USD FIXED RATE** (§10.2). Pricing mode explains estimated forwards, but a projected rate of exactly zero, with the entire financing accrual coming from the margin, should be confirmed.
4. **The valuation shifter is applied inconsistently** (§7). Examples 1 and 2 start their legs two open days apart; Example 3, on the same template as Example 2, starts both legs together.
5. **The Income/Tax credit, Return and Schedules definition sub-screens were not captured.** These sit behind Edit links on the template and govern coupon pass-through, withholding treatment and the period structure — the configuration that most directly determines the accounting treatment of income on these trades.
6. **The Evaluation conditions and Termination Fees tabs were not captured.** Given that early settlement is enabled and partial unwinds are expected, termination fee configuration is a real economic term.
7. **`Interest exposure` differs between the two templates** (Yes on the USD template, No on the BRL one) and its effect is not documented.
8. **Only one trade's flow schedules were captured**, and in pricing mode (§10.4). A realised-fixings view, and flows for the haircut trade in Example 1, would show how the two structures behave differently over their lives.
9. **No receive-performance (synthetic long) example.** All three are synthetic shorts. The mechanics are symmetric, but a long example would confirm the sign conventions in the flow schedules.
