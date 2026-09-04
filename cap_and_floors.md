# Cap & Floors

## Purpose of this document

This is a reference document on the Cap & Floor product: what the product is, how its payoff works, how it is priced at a conceptual level, and how its terms are represented in Murex. It is meant to be read on its own — a new joiner or anyone unfamiliar with the product should come away understanding the mechanics, not just recognizing the trade capture screen.

## Overview

Caps and Floors are over-the-counter interest rate derivatives used to hedge exposure to a floating interest rate. Both are built from a strip of individual options (a strip of caplets for a Cap, a strip of floorlets for a Floor) written on a reference index — one option per period over the life of the trade. At the end of each period, the option pays out only if the reference index fixes on the "wrong side" of an agreed strike rate.

They are typically used by borrowers or investors who are exposed to a floating rate and want to limit how far that rate can move against them, without giving up the potential benefit of a favorable move (unlike a swap, which locks in a single fixed rate for the whole life of the trade).

Like any option, a Cap or Floor has a premium, paid by the buyer to the seller for the protection. That premium is not simply the intrinsic value of "how far in the money the strike already is" — it is priced using an option pricing model (typically Black-76 or a shifted log-normal / normal (Bachelier) model) off the volatility of the underlying index. This is why the Murex screens carry fields such as Main Vol and Log-normal Shift alongside the strike: the desk is pricing and risk-managing optionality on every period of the strip, not just checking where the index has already fixed.

## 1. Cap

A **Cap** (or interest rate cap) is a derivative that puts a **maximum limit** on an interest rate. If the market rate goes above that level, the cap pays the buyer the difference.

In other words, it is a derivative in which the buyer receives a payment at the end of each period in which the underlying index **exceeds the strike**. If the index fixes at or below the strike, no payment is made for that period — the buyer's downside is simply the premium already paid.

Typical use case: a borrower paying a floating rate buys a Cap to protect against the rate rising above a level they can afford, while still benefiting if the rate stays low.

### 1.1 Payoff formula

For each period in the strip, the caplet payoff to the buyer is:

**Payoff = Nominal × max(Index − Strike, 0) × Day-count fraction**, paid at the end of the period (in arrears).

The day-count fraction is the number of days in the period divided by the year basis of the convention (e.g. days/360 or days/365 — see §6 on conventions below). Summed across all periods, this is the strip of caplets that makes up the Cap.

### 1.2 A fixing-mechanics distinction worth knowing: term rates vs. compounded/RFR rates

Not every "Index" fixes the same way, and this matters for reading the Murex screens correctly:

- **Term rates** such as WIBOR or EURIBOR are forward-looking: the rate for a given period is set (fixed) shortly before the period starts, so it is already known on day one of that period. This is why, in Example 1 below, "1st fixing" shows a real value (1.640000%) — it is the WIBOR fixing that applied from the start.
- **Compounded risk-free rates (RFRs)** such as SOFR Compound (or, in other currencies, SONIA/€STR compounded) are backward-looking: the rate is built up by compounding daily overnight fixings across the period, so it is only fully known at (or just before) the end of the period. This is why, in Example 2 below, "1st fixing" shows 0.000000% — not an error or an at-the-money starting point, but simply a placeholder because nothing can be known yet at trade date. The actual rate for that period only appears once the period has accrued, as seen in its flow schedule.

This distinction also affects pricing: caplets on compounded RFRs are valued with models adapted for backward-looking, in-arrears rates, rather than the simpler forward-rate approach used for IBOR-style caplets.

### 1.3 Murex representation of a Cap

**Example 1 — PLN WIBOR 1M Cap**

| Field | Value |
|---|---|
| Portfolio | PPO3 (sells to) |
| Counterparty | Z86I |
| Nature | Generic |
| Index | PLN WIBOR 1M |
| Nominal | 3,000,000 |
| Start date | 09 sep 2019 |
| Maturity | 07 sep 2020 |
| Payout | **Cap** |
| Strike | 3.5000% |
| Currency | PLN |
| 1st period | Included |
| 1st fixing | 1.640000% |
| Convention | LIN ACT/365 |
| Margin | 0.0000 |
| Roll date | 30 sep 2019 |

**Direction:** Portfolio PPO3 *sells* the cap to Z86I, so our book is **short** this option — we have received (or will receive) premium and are short vega/gamma on this trade. Z86I is the buyer and the one entitled to a payment when the index exceeds the strike.

The flow schedule confirms the mechanics: the trade resets monthly (calculation periods roughly 30 days), and each period's floating rate is fixed against the 3.50% strike. Across the periods shown, the fixed rate (1.64% at inception, then around 1.63%, later rising through 1.29%–2.01% as the index moved) stayed **below** the 3.50% strike for the whole observed history, so the cap remained out-of-the-money and the buyer was not entitled to a payment in this window. This illustrates the core payoff rule: a Cap only pays when the fixing rate breaches the strike from above.

**Open item to verify:** the flow schedule for several of the later periods (e.g. 30 abr, 31 may, 30 jun, 31 jul, 31 ago 2020) shows small *negative* flow values (such as -167.19 and -363.87 PLN) even though the fixed rate is below the strike, which on a plain-vanilla cap should produce a flow of exactly zero. This is not explained by the payoff formula above and should be checked against the underlying trade in Murex (possible causes include a margin, a change in an applicable strike/vol parameter for those specific periods, or a booking convention this document isn't capturing) before this example is relied on as a clean "zero payoff" illustration.

**Example 2 — USD SOFR COMP Cap**

| Field | Value |
|---|---|
| Portfolio | ESVOL_CAPS_USD (buys from) |
| Counterparty | MIFI |
| Nature | Generic |
| Index | USD SOFR COMP |
| Nominal | 300,000,000 |
| Start date | 20 feb 2026 |
| Maturity | 20 feb 2027 (payment date 22 feb 2027) |
| Payout | **Cap** |
| Strike | 3.4000% |
| Currency | USD |
| 1st period | Included |
| 1st fixing | 0.000000% |
| Convention | LIN ACT/360 |
| Margin | 0.0000 |
| Premium | 0.1711% = 513,300 USD, settled 20 feb 2026 |
| Live remaining capital | 300,000,000 |

**Direction:** Portfolio ESVOL_CAPS_USD *buys* this cap from MIFI, so our book is **long** this option — we paid the premium (513,300 USD) and are long vega/gamma, entitled to a payment whenever the index exceeds the strike.

This trade is quarterly (three-month calculation periods) rather than monthly, and unlike Example 1 it shows a period that actually pays out. In the first period (20 feb 2026 – 20 may 2026), the compounded SOFR rate fixed at **3.66888%**, which is above the 3.40% strike. Because the index exceeded the strike, the cap generated a real payment of **44,813.33 USD**, paid on 22 may 2026. The three remaining periods (may–aug, aug–nov, nov–feb 2027) had not yet fixed at the time of this snapshot, so their rate and flow columns still read 0.00000 — as explained in §1.2, this is expected for a compounded RFR index, since each period's rate is only known once that period has accrued, not at trade date.

The flow schedule also carries a **Delta** of 100.0000 (Delta Csh 1.6667) against the fixed first-period flow — this is the sensitivity of that leg's value to a move in the underlying index. Once a period has fixed, its caplet has effectively become a certain cash flow (delta close to fully "locked in" for that leg), whereas the unfixed future periods still carry live optionality and would show vega as well as delta risk until they fix.

Together, the two examples show both sides of the same payoff logic: Example 1 stayed under the strike throughout and paid nothing; Example 2 fixed above the strike in its first period and triggered a real cash payment to the buyer.

## 2. Floor

A **Floor** (or interest rate floor) is a derivative that puts a **minimum limit** on an interest rate. If the market rate goes below that level, the floor pays the buyer the difference.

It is the mirror image of a Cap: the buyer receives a payment at the end of each period in which the underlying index **is below the strike**. If the index fixes at or above the strike, no payment is made for that period.

Typical use case: an investor or lender receiving a floating rate buys a Floor to protect the minimum yield they earn if rates fall, while still benefiting if rates rise.

The payoff formula mirrors the Cap, with the max() flipped: **Payoff = Nominal × max(Strike − Index, 0) × Day-count fraction**, per period, paid in arrears.

### 2.1 Murex representation of a Floor

**Example — EUR EURIBOR 1M Floor**

| Field | Value |
|---|---|
| Portfolio | ESLD_CAPS_EUR (sells to) |
| Counterparty | XMD9 |
| Nature | Generic |
| Index | EURIBOR 1M |
| Nominal | 500,000 |
| Start date | 19 feb 2026 |
| Maturity | 19 aug 2026 |
| Payout | **Floor** |
| Strike | 0.5500% |
| Currency | EUR |
| 1st period | Included |
| 1st fixing | 1.932000% |
| Convention | LIN ACT/360 |
| Margin | 0.0000 |
| Premium | 0.0000% (no premium recorded) |
| Live remaining capital | 500,000 |

**Direction:** Portfolio ESLD_CAPS_EUR *sells* the floor to XMD9, so our book is **short** this option, symmetric with the short Cap in Example 1 — the counterparty XMD9 is the buyer entitled to a payment if the index fixes below the strike.

At inception, the first fixing of 1.932% sits well above the 0.55% strike, meaning this floor starts out **out-of-the-money**: for that first period the index would need to drop by well over one percentage point before the floor would pay out. EURIBOR is a term rate (see §1.2), so this 1.932% is a genuine known fixing, not a placeholder.

**Gap in this example:** no flow schedule was provided for this trade, so the realized payments across its six-month life aren't shown here — only the trade's static terms. Unlike the Cap section, this document does not currently include a Floor example where the index actually fixes below the strike and a payment is triggered; if a flow schedule showing that scenario becomes available, it should be added here so the Floor section is as complete as the Cap section.

## 3. Cap vs. Floor — quick comparison

| | Cap | Floor |
|---|---|---|
| Protects against | Rate rising too high | Rate falling too low |
| Pays out when | Index **>** Strike | Index **<** Strike |
| Payoff formula | Nominal × max(Index − Strike, 0) × day-count fraction | Nominal × max(Strike − Index, 0) × day-count fraction |
| Typical buyer | Floating-rate borrower | Floating-rate lender / investor |
| Built from | Strip of caplets | Strip of floorlets |
| Murex "Payout" field | Cap | Floor |

## 4. How Caps and Floors relate to swaps: put-call parity

A Cap and a Floor on the same index, strike, nominal, and schedule are not independent products — they are linked by put-call parity:

**Cap(K) − Floor(K) = Payer Interest Rate Swap fixed at K**

Buying a Cap at strike K and simultaneously selling a Floor at the same strike K (same index/schedule/nominal) replicates a payer swap: you pay fixed at K and receive the floating index, with no residual optionality. This identity is useful both for sanity-checking prices (a Cap and Floor struck at the current swap rate should have equal premiums, since the replicated swap is then at-market and worth zero) and for understanding structures like collars below.

## 5. Collars

A **collar** combines a Cap and a Floor on the same underlying exposure — typically buying one and selling the other. The most common structure is a **zero-cost collar**: a floating-rate borrower buys a Cap (to limit how high their rate can go) and simultaneously sells a Floor (giving up the benefit of rates falling below the floor strike), choosing the floor strike so that the premium received offsets the premium paid on the cap. The result is a floating rate that is contained within a band [Floor strike, Cap strike] at little or no upfront cost, at the price of giving up the benefit of very low rates. The same idea works in reverse for an investor hedging the downside on a floating-rate asset: buy a Floor, sell a Cap.

## 6. Day-count conventions

The examples above use two different conventions — LIN ACT/365 for the PLN WIBOR cap, and LIN ACT/360 for the USD SOFR and EUR EURIBOR trades. "ACT" means the actual number of calendar days in the period is used; "360" or "365" is the year basis the day count is divided by. This is not a cosmetic detail: for the same number of calendar days and the same rate, an ACT/360 period produces a slightly larger day-count fraction (and therefore a slightly larger flow) than an ACT/365 period, because the denominator is smaller. Market convention for a given currency and index generally dictates which basis applies (e.g. USD and EUR money-market rates conventionally use ACT/360; PLN WIBOR-linked flows here use ACT/365), so this is normally inherited from the index rather than freely chosen on the trade.

## 7. Glossary of fields seen in the Murex screens

- **Index**: the floating reference rate the option is written on (e.g. PLN WIBOR 1M, USD SOFR COMP, EUR EURIBOR 1M).
- **Nominal**: the notional amount on which each period's payment is calculated.
- **Strike**: the rate level that separates "in-the-money" from "out-of-the-money" for each period.
- **Net Strike / Applicable Strike**: the strike as actually applied to a given period's calculation, after any adjustments (e.g. margin) are taken into account; equal to the base Strike in all periods shown in these examples, since Margin is 0.
- **Rate Factor**: a scaling factor (1.0000 in all examples here) applied to the fixed rate when computing the period's flow — relevant where a trade applies a leverage or participation factor to the index.
- **1st fixing**: the value of the index already known/fixed for the first calculation period at trade date. For a term-rate index (WIBOR, EURIBOR) this is a real known rate; for a compounded RFR index (SOFR Compound) it reads 0.000000% as a placeholder because the rate is only known once the period accrues — see §1.2.
- **Main Vol / Log-normal Shift**: inputs to the option pricing model used to value each caplet/floorlet — the implied volatility and, where used, a shift applied to support a shifted log-normal model (useful when rates are very low or negative, since a plain log-normal model cannot handle a zero or negative underlying).
- **Delta / Delta Csh**: risk sensitivities — Delta is the sensitivity of the caplet/floorlet's value to a move in the underlying index; Delta Csh expresses that sensitivity in cash terms. Once a period has fixed, its flow is effectively certain and delta reflects that; unfixed future periods still carry live delta and vega risk.
- **Convention**: the day-count / rate convention used to compute accrued flows (e.g. LIN ACT/365, LIN ACT/360) — see §6.
- **Margin**: a spread added to or subtracted from the index before comparing it to the strike (0 in all examples here).
- **Roll date**: the date the schedule's periodic reset/roll is anchored to, used to generate the calculation period boundaries going forward.
- **Premium**: the upfront price paid by the buyer to the seller for the optionality, usually quoted as a percentage of nominal and as a cash amount, and priced using an option model rather than intrinsic value alone.
- **Live Remaining Capital**: the nominal still outstanding and subject to the option going forward — relevant for amortizing structures; equal to the full Nominal in these examples since none of them amortize.
- **Flow schedule**: the period-by-period breakdown showing calculation dates, fixing dates, the rate that actually fixed, and the resulting cash flow (if any) for each period.
