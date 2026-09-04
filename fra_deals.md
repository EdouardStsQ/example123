# Forward Rate Agreements (FRA)

## Purpose of this document

This is a reference document on forward rate agreements: what the product is, how the four dates relate to one another, why settlement happens at the *start* of the interest period on a discounted basis, and how the terms are represented in Murex. It is meant to be read on its own — a new joiner or anyone unfamiliar with the product should come away understanding the mechanics, not just recognizing the trade capture screen.

The three worked examples in §11 are a **bought EUR FRA on IMM dates**, a **bought PLN FRA booked through a generator on end-of-month dates**, and a **sold EUR FRA**. Between them they cover both directions, two currencies with different day-count conventions, both booking methods, three period-date conventions, and both kinds of ancillary flow.

**A note on identifiers.** Portfolio and counterparty identifiers are omitted throughout. Indices, rates, dates and amounts are retained, since those are the economics of the trade.

## 1. Overview: what a FRA is

A forward rate agreement is an OTC contract that **fixes an interest rate today for a defined period starting in the future**. At the start of that period the two parties settle the difference between the agreed rate and the market rate that actually fixes, on an agreed notional.

Four features define it:

- **The notional is never exchanged.** It exists only as the base for calculating the settlement. `Initial exchange`, `Intermediate payments` and `Final exchange` are unticked on both legs of the generator (§9).
- **It has two legs** — a fixed leg at the contract rate and a floating leg on a reference index — but only the **net difference** changes hands.
- **Settlement happens at the start of the interest period, not the end.** This is the defining mechanic and the one that most distinguishes a FRA from anything else (§7).
- **Because it settles early, the amount is discounted.** Paying at the start an amount that economically belongs at the end requires discounting it back (§7.2).

A FRA is, in effect, a **single-period interest rate swap settled in advance**. It is the OTC equivalent of a short-term interest rate future, with the differences noted in §12.

## 2. Direction: buying and selling a FRA

The convention is unambiguous, and the examples confirm it three times over:

| | **Buy** a FRA | **Sell** a FRA |
|---|---|---|
| Fixed leg | **Pay** fixed | **Receive** fixed |
| Floating leg | **Receive** floating | **Pay** floating |
| Gains when | The fixing comes in **above** the FRA rate | The fixing comes in **below** the FRA rate |
| Economic purpose | Protects against rates **rising** | Protects against rates **falling** |
| Analogue | Borrower locking a future funding cost | Depositor locking a future return |

The generator in Example 2 states this outright: **`Buy Sign: Pay Fixed`**.

### 2.1 The sign convention on the fixed leg flow

The direction is directly readable from the sign of the fixed leg's flow, and all three examples agree:

| Example | Direction | Fixed leg flow |
|---|---|---|
| 1 | Buys from | **−2,321,875.11** (negative — paid) |
| 2 | Buys from | **−7,681,696.44** (negative — paid) |
| 3 | **Sells to** | **+250,361.64** (positive — received) |

A negative fixed-leg flow means the book pays fixed and has bought the FRA. A positive one means it receives fixed and has sold.

## 3. The four dates

A FRA has four dates, and confusing them is the commonest source of error:

| Date | What it is |
|---|---|
| **Trade date** | When the contract is agreed. Appears on the flow schedule as the *Mkt.Op date*. |
| **Fixing date** | When the reference index is observed — **two business days before the start**. |
| **Start date** | The beginning of the interest period, and **the date settlement is paid** (§7). |
| **End date** | The end of the interest period. **No cash moves on this date.** |

The end date matters only because it determines the length of the period and therefore the size of the settlement. Nothing settles on it.

### 3.1 The fixing lag is T+2, on the relevant calendar

All three examples fix two business days before the start:

| Example | Fixing | Start | Business days |
|---|---|---|---|
| 1 | Mon 14 sept 2026 | Wed 16 sept 2026 | Tue, Wed = **2** ✓ |
| 3 | Mon 15 mar 2027 | Wed 17 mar 2027 | Tue, Wed = **2** ✓ |
| 2 | Fri 26 mar 2027 | Wed 31 mar 2027 | **see below** |

Example 2 looks like three weekdays apart, but reconciles exactly once the right calendar is applied: **Easter Monday falls on 29 March 2027**, a Warsaw holiday, and this trade's generator specifies a WARSAW calendar. Friday 26th → skip Monday → Tuesday 30th (1) → Wednesday 31st (2). Two *open* days, as configured.

The lesson generalises: **a fixing lag that looks wrong is usually a calendar you have not applied**, and the calendar comes from the generator, not from the trade.

### 3.2 FRA notation

The market names a FRA by the months from spot to the start and to the end of the period: a **1×4** starts in one month and ends in four; a **3×6** starts in three and ends in six. The difference between the two numbers is the length of the interest period.

Example 1, traded 19 August with a 16 September start and 16 December end, is approximately a **1×4** on a three-month index.

## 4. Period date conventions

The start and end dates are not arbitrary, and three distinct conventions appear across just three examples:

| Example | Start | End | Convention |
|---|---|---|---|
| 1 | 16 sept 2026 | 16 dic 2026 | **IMM to IMM** — both are third Wednesdays |
| 3 | 17 mar 2027 | 17 jun 2027 | **IMM start, calendar-month end** — the start is a third Wednesday; the end is the same day-of-month three months later, *not* the next IMM date (which would be 16 June) |
| 2 | 31 mar 2027 | 30 jun 2027 | **End-of-month** — last day of March to last day of June, preserving the month-end rule |

**IMM FRAs** align with the futures strip, which makes them convenient to hedge with short-term interest rate futures and to trade as spreads against them. **End-of-month and broken-date FRAs** are struck to match a specific underlying exposure — a funding rollover on a particular date — rather than to align with the futures calendar.

The practical point: **do not assume the end date is the next IMM date**. Example 3 shows an IMM start with an end date three calendar months later, one day after the June IMM date. The period length follows from the actual dates, and the *Nb of Days* column on the flow schedule is the figure that drives the calculation.

## 5. The two legs

A FRA is booked as two legs, visible in the flow schedule as `Lg 1` and `Lg 2`:

- **Leg 1 — the fixed leg.** Carries the contract rate. Its flow is fully determined at trade date.
- **Leg 2 — the floating leg.** Carries the reference index, with a fixing date. Its flow is zero until the index fixes.

Both legs share the same period, the same notional and the same payment date. In every example the floating leg shows a **rate of 0.00000 and a flow of 0.00**, because none of the three has reached its fixing date yet. That is expected behaviour, not a gap — the flow schedule cannot show a rate that has not yet been published.

### 5.1 Two ways of booking: Index or Generator driven

The **Nature** field on the trade distinguishes them:

| | Nature: **Index** | Nature: **Generator driven** |
|---|---|---|
| Examples | 1 and 3 | 2 |
| What is specified | The index directly | A **generator** template, which supplies the index and the conventions |
| Generator field | Absent | Present |

A generator-driven FRA inherits its calendars, start delays, day counts, fixing and payment conventions from a named template (§9). An index-driven one takes the index directly, with conventions inherited from the currency and index defaults.

Both produce the same product. The generator route is the one that makes the conventions explicit and inspectable.

## 6. Rate, sales margin and net rate

Three rate fields appear on the trade:

| Field | Meaning | Value across all three |
|---|---|---|
| **Rate** | The contract rate agreed with the counterparty | 2.609500 / 3.920000 / 2.881400 |
| **Sales margin** | A commercial spread applied to the rate | **0.0000** on all three |
| **Net rate** | Rate after the sales margin — the rate actually used | Equal to Rate on all three |

With a zero sales margin the net rate equals the rate throughout, so how a margin flows into the calculation is documented from the field alone (§14).

**Premium** reads **None** on all three: a FRA is struck at market and costs nothing at inception.

## 7. Settlement: paid in advance, discounted

This is the defining mechanic of the product.

### 7.1 Payment at the start of the period

The interest period runs from the start date to the end date, but **the settlement is paid on the start date**. In every example the `INT` flows on both legs carry a payment date equal to the period start:

| Example | Period | Payment date |
|---|---|---|
| 1 | 16 sept 2026 → 16 dic 2026 | **16 sept 2026** |
| 2 | 31 mar 2027 → 30 jun 2027 | **31 mar 2027** |
| 3 | 17 mar 2027 → 17 jun 2027 | **17 mar 2027** |

This is what makes a FRA a FRA. An equivalent single-period swap would pay at the *end* of the period; a FRA pays at the beginning.

### 7.2 And therefore discounted

An interest differential earned over a period economically belongs at the *end* of that period. Paying it at the start means paying it early, so the amount is **discounted back** over the period — conventionally at the settlement rate itself.

The generator in Example 2 configures this explicitly on **both** legs:

- **`Payment: Up front disc.`** — paid up front, discounted
- **`Discounting rate: Floating rate`** — discounted at the floating rate, i.e. the rate that fixes

The standard market formula:

> **Settlement = Notional × (R_fix − R_FRA) × d/B ÷ (1 + R_fix × d/B)**

where *R_fix* is the rate that fixes, *R_FRA* the contract rate, *d* the days in the period and *B* the day-count basis. The numerator is the interest differential; the denominator discounts it from the period end back to the start.

**An illustration** using Example 1's terms — notional 352,000,000, FRA rate 2.6095%, 91 days, ACT/360 — for a **buyer** who pays fixed:

| If EURIBOR 3M fixes at | Undiscounted difference | Discount factor | **Settlement** |
|---|---|---|---|
| **2.8095%** (20bp above) | +177,955.56 | 0.9929483 | **+176,700.66 received** |
| **2.4095%** (20bp below) | −177,955.56 | 0.9939462 | **−176,878.25 paid** |

Note the asymmetry: the same 20bp move produces slightly different absolute settlements, because the discount factor itself depends on the fixing.

### 7.3 What the flow schedule shows before fixing

The flow schedule displays the **gross, undiscounted** interest amount on the fixed leg. All three reconcile on:

> **Flow = Notional × Net rate × Days ÷ Basis**

| Example | Calculation | Flow |
|---|---|---|
| 1 | 352,000,000 × 2.6095% × 91/360 | **−2,321,875.11** ✓ |
| 2 | 786,000,000 × 3.9200% × 91/365 | **−7,681,696.44** ✓ |
| 3 | 34,000,000 × 2.8814% × 92/360 | **+250,361.64** ✓ |

**These are gross leg amounts, not the settlement.** The settlement is the *net* of the two legs, discounted per §7.2 — and it cannot be computed until the floating leg fixes, which is why the floating leg reads 0.00000 on all three. Whether the displayed figures are restated after fixing is an item to confirm (§14).

Anyone reconciling a FRA settlement against these numbers will not tie out: they must net the two legs and apply the discount factor.

## 8. Day count conventions

The basis follows the currency and its index, and the two currencies here differ:

| Example | Currency / Index | Basis | Days | Effect |
|---|---|---|---|---|
| 1, 3 | EUR / EURIBOR 3M | **ACT/360** | 91, 92 | Standard EUR money-market basis |
| 2 | PLN / WIBOR 3M | **ACT/365** | 91 | Standard PLN basis |

The difference is not cosmetic. On Example 2's notional, the same rate and period computed on ACT/360 would give 7,788,386.67 instead of 7,681,696.44 — a difference of over 106,000 PLN. The generator states the basis as `LIN ACT/365`, and it is the basis, not an assumption, that must be applied.

## 9. Generators

Where the trade is generator driven, the generator supplies the structural configuration of both legs. From Example 2:

**Trade level**

| Field | Value |
|---|---|
| Phases / Legs per phase | 1 / **2** |
| Schedules | Independent sets across legs |
| Stub period | Up front |
| **Buy Sign** | **Pay Fixed** (§2) |
| Maturity adjustment | Inherited |
| Market quote / Bid-Ask driving leg | Automatic |
| Settlement delay | Inherited from currency |
| Amortizing | Common definition across legs |
| Evaluation | Default |

**Leg level**

| Field | Leg 1 (fixed) | Leg 2 (floating) |
|---|---|---|
| Rate type | **Fixed** | **Floating** |
| Index | — | PLN WIBOR 3M |
| Formula | — | FIXING |
| Currency | PLN | PLN |
| Start delay | +2 OPEN DAYS | +2 OPEN DAYS |
| Payment calendar | **WARSAW** | **WARSAW** |
| Fixing calendar | — | **WARSAW** |
| **Fixing** | — | **In advance** |
| **Payment** | **Up front disc.** | **Up front disc.** |
| **Discounting rate** | **Floating rate** | **Floating rate** |
| Rate convention / Basis | LIN ACT/365 | LIN ACT/365 |
| Computing mode | Linear | Linear |
| Rate expression | Standard | Standard |
| Margin mode | — | Additive |
| Rate formula | — | Standard |
| Day count | Yes | Yes |
| Roundings | None | None |
| Initial / Intermediate / Final exchange | **All unticked** | **All unticked** |

Three settings carry the product's defining behaviour: **`Fixing: In advance`**, **`Payment: Up front disc.`** and **`Discounting rate: Floating rate`**. Together they encode "observe the rate before the period starts, settle at the start, and discount the amount back at the rate that fixed" — which is the whole of a FRA in three fields.

## 10. Ancillary flows

Besides the two interest legs, the flow schedules carry small additional entries, and **two different types appear**:

| Example | Type | Amount | Payment date | Trade date |
|---|---|---|---|---|
| 1 | **FEE** | −53.40 EUR | 19 ago 2026 | 19 ago 2026 |
| 2 | **FLW** | −14,000.00 PLN | 10 ago 2026 | 06 ago 2026 |
| 3 | **FEE** | −8.69 EUR | 27 ago 2026 | 27 ago 2026 |

- **FEE** entries are charges — brokerage or clearing — paid on the trade date itself. At 53.40 EUR on a 352 million notional and 8.69 EUR on 34 million, they are plainly transaction costs rather than economics.
- **FLW** is a different animal. Example 2 is the one trade with **`Additional Flows` ticked**, and its 14,000 PLN entry paid four days after trade date is an agreed supplementary payment, not a charge.

Note also that the fee can sit on **either leg** — Example 1 carries it on Leg 1, Example 3 on Leg 2 — so a leg-filtered view may not show it.

## 11. Worked examples

### 11.1 Example 1 — EUR FRA on IMM dates, bought

| Field | Value |
|---|---|
| Direction | **Buys from** — pays fixed |
| Nature | **Index** |
| Index | EURIBOR 3M |
| Notional | **352,000,000** |
| **Fixing date** | 14 sept 2026 |
| **Start** | **16 sept 2026** |
| **End** | 16 dic 2026 |
| Days / Basis | **91** / ACT/360 |
| Rate / Sales margin / Net rate | **2.609500%** / 0.0000 / 2.6095% |
| Premium | None |
| **Fixed leg flow** | **−2,321,875.11 EUR**, paid **16 sept 2026** |
| Floating leg | Unfixed — rate 0.00000, flow 0.00 |
| Ancillary | FEE −53.40 EUR on 19 ago 2026 |

**Position:** bought, so the book pays 2.6095% and receives EURIBOR 3M for the September–December 2026 period. It gains if the rate fixes above 2.6095%.

**Flow:** 352,000,000 × 2.6095% × 91/360 = **2,321,875.11** ✓, negative because fixed is paid.

**Both period dates are IMM.** 16 September and 16 December 2026 are each the **third Wednesday** of their month — the standard futures dates. Against a 19 August trade date this is approximately a **1×4**.

**Fixing is T+2**: Monday 14 September to Wednesday 16 September.

**Settlement falls on 16 September**, the period *start* — three months before the interest period it relates to ends (§7).

### 11.2 Example 2 — PLN FRA, generator driven, end-of-month dates, bought

| Field | Value |
|---|---|
| Direction | **Buys from** — pays fixed |
| **Nature** | **Generator driven** |
| Generator / Index | PLN FRA 3M / PLN WIBOR 3M |
| Notional | **786,000,000** |
| **Fixing date** | 26 mar 2027 |
| **Start** | **31 mar 2027** |
| **End** | 30 jun 2027 |
| Days / Basis | **91** / **ACT/365** |
| Rate / Net rate | **3.920000%** / 3.9200% |
| Premium | None |
| **Fixed leg flow** | **−7,681,696.44 PLN**, paid **31 mar 2027** |
| Floating leg | Unfixed — rate 0.00000, flow 0.00 |
| Ancillary | **FLW −14,000.00 PLN** on 10 ago 2026 |
| Calendars | WARSAW (payment and fixing) |

**Flow:** 786,000,000 × 3.92% × 91/**365** = **7,681,696.44** ✓ — note the 365 basis. On ACT/360 the same terms would give 7,788,386.67, over 106,000 PLN more (§8).

**End-of-month period dates.** 31 March to 30 June — last day of one month to last day of another, preserving the month-end rule. Neither is an IMM date, so this FRA is struck to a specific exposure rather than to the futures calendar (§4).

**The fixing lag resolves through the Warsaw calendar.** Friday 26 March to Wednesday 31 March is three weekdays, but **Easter Monday on 29 March 2027** is a Warsaw holiday, making it exactly the configured +2 open days (§3.1).

**This is the example that documents the settlement mechanic.** Its generator sets `Payment: Up front disc.` and `Discounting rate: Floating rate` on both legs — the FRA convention stated in configuration rather than inferred (§7.2). And `Buy Sign: Pay Fixed` confirms the direction convention outright.

**Additional Flows is ticked**, and the −14,000 PLN `FLW` entry four days after trade date is the corresponding agreed payment — distinct from the small `FEE` charges on the other two (§10).

### 11.3 Example 3 — EUR FRA, sold

| Field | Value |
|---|---|
| **Direction** | **Sells to** — **receives fixed** |
| Nature | Index |
| Index | EURIBOR 3M |
| Notional | **34,000,000** |
| **Fixing date** | 15 mar 2027 |
| **Start** | **17 mar 2027** |
| **End** | 17 jun 2027 |
| Days / Basis | **92** / ACT/360 |
| Rate / Net rate | **2.881400%** / 2.8814% |
| Premium | None |
| **Fixed leg flow** | **+250,361.64 EUR**, paid **17 mar 2027** |
| Floating leg | Unfixed — rate 0.00000, flow −0.00 |
| Ancillary | FEE −8.69 EUR on 27 ago 2026, **on Leg 2** |

**Position:** the only **sold** FRA in the set. The book receives 2.8814% and pays EURIBOR 3M, so it gains if the rate fixes **below** 2.8814% — the mirror of Examples 1 and 2.

**Flow:** 34,000,000 × 2.8814% × 92/360 = **250,361.64** ✓, and **positive**, confirming the sign convention: fixed received rather than paid (§2.1).

**An IMM start with a calendar-month end.** 17 March 2027 is the third Wednesday of March, but 17 June 2027 is a **Thursday** — the June IMM date is the 16th. So the period runs from an IMM start to the same day-of-month three months later, not to the next IMM date. Hence 92 days rather than 91 (§4).

**Fixing is a clean T+2**: Monday 15 March to Wednesday 17 March, no holiday complication.

**The fee sits on Leg 2** here, where Example 1 carries it on Leg 1 (§10).

### 11.4 The three examples side by side

| | Example 1 | Example 2 | Example 3 |
|---|---|---|---|
| **Direction** | Buy — pay fixed | Buy — pay fixed | **Sell — receive fixed** |
| **Nature** | Index | **Generator driven** | Index |
| Currency / Index | EUR / EURIBOR 3M | **PLN / WIBOR 3M** | EUR / EURIBOR 3M |
| Notional | 352,000,000 | **786,000,000** | 34,000,000 |
| Trade date | 19 ago 2026 | 06 ago 2026 | 27 ago 2026 |
| Fixing date | 14 sept 2026 | 26 mar 2027 | 15 mar 2027 |
| **Start (= settlement)** | **16 sept 2026** | **31 mar 2027** | **17 mar 2027** |
| End | 16 dic 2026 | 30 jun 2027 | 17 jun 2027 |
| **Period convention** | **IMM to IMM** | **End-of-month** | **IMM start, +3 months** |
| Fixing lag | T+2 clean | T+2 **via Warsaw holiday** | T+2 clean |
| **Days** | 91 | 91 | **92** |
| **Basis** | **ACT/360** | **ACT/365** | **ACT/360** |
| Rate | 2.609500% | 3.920000% | 2.881400% |
| Sales margin | 0 | 0 | 0 |
| Premium | None | None | None |
| **Fixed leg flow** | **−2,321,875.11** | **−7,681,696.44** | **+250,361.64** |
| Floating leg | Unfixed (0.00000) | Unfixed (0.00000) | Unfixed (0.00000) |
| Ancillary flow | **FEE** −53.40 (Leg 1) | **FLW** −14,000.00 | **FEE** −8.69 (Leg 2) |
| Additional Flows flag | Unticked | **Ticked** | Unticked |
| Calendars | — | WARSAW | — |

## 12. FRAs compared with adjacent products

A FRA sits between two other instruments, and knowing where it differs is useful.

**Against a short-term interest rate future.** Both fix a rate for a future period on a three-month index, and IMM-dated FRAs use the same dates as the futures strip. The differences:

| | FRA | STIR future |
|---|---|---|
| Venue | **OTC, bilateral** | Exchange traded |
| Terms | Negotiated — any notional, any dates | Standardized contract size and IMM dates |
| Credit | Bilateral counterparty exposure | Cleared, novated to a CCP |
| Cash flows | Single settlement at period start | **Daily variation margin** |
| Convexity | None — a single discounted settlement | **Convexity adjustment** required, because daily margining correlates with rates |

That last row is the substantive one: a FRA rate and a futures-implied rate for the same period are **not the same number**, and the difference grows with maturity.

**Against a single-period interest rate swap.** Economically almost identical, with one difference: the swap pays at the **end** of the period, undiscounted; the FRA pays at the **start**, discounted. The discounting exists precisely to make the two equivalent in present-value terms.

## 13. Risk profile

- **Interest rate risk**, concentrated at a single point on the curve. A FRA is exposure to one forward rate for one period, which makes it a precise hedging instrument and a precise speculative one.
- **Curve risk in a book of FRAs.** Individual FRAs across different periods combine into a curve position; offsetting notionals do not mean offsetting risk unless the periods match.
- **Basis risk.** A FRA hedges exposure to its specific index and tenor. Hedging a funding cost linked to a different index, or a different reset frequency, leaves basis.
- **Fixing risk**, concentrated in a single observation. The entire settlement turns on one published rate on one date — unlike a swap, where a bad fixing on one reset is diluted across many.
- **Counterparty credit risk**, bilateral and uncollateralized unless a separate agreement applies. Exposure runs from trade date to the settlement date and is largest just before fixing, when the rate differential is nearly known but unpaid.
- **Settlement timing risk.** Cash moves at the period start, months before the economic exposure it relates to ends — which matters for funding and cash forecasting.
- **Convention risk.** Three period conventions and two day-count bases appear in three examples (§4, §8). Applying the wrong basis to Example 2 misstates the flow by over 100,000 PLN.
- **Calendar risk.** Example 2's fixing date only reconciles once the Warsaw holiday calendar is applied (§3.1). A fixing computed on the wrong calendar produces the wrong date and potentially the wrong rate.

## 14. Glossary of fields seen in the Murex screens

**Trade capture**

- **buys from / sells to**: direction — buy means pay fixed (§2).
- **Nature**: **Index** or **Generator driven** — how the trade is booked (§5.1).
- **Generator**: the convention template, on generator-driven trades (§9).
- **Index**: the reference rate the floating leg fixes against.
- **Start / End**: the interest period, each shown as an entered and a resolved date. Settlement falls on the **start** (§7.1).
- **Fixing date**: when the index is observed — T+2 before the start (§3.1).
- **Nominal amount**: the calculation base. Never exchanged (§1).
- **Premium**: **None** on a FRA — struck at market, no cost at inception.
- **Rate / Sales margin / Net rate**: the contract rate, any commercial spread, and the rate actually applied (§6).
- **Indexations leg 1 / leg 2, Flex**: unused on all three.
- **Additional Flows**: whether supplementary flows are attached — ticked on Example 2 (§10).
- **Flows / Risk / Pricing**: links to the flow schedule and analytics.

**Generator (deal details)**

- **Phases / Legs per phase**: 1 and 2 — one period, two legs.
- **Buy Sign**: **Pay Fixed** — defines what "buy" means (§2).
- **Schedules / Stub period / Amortizing / Maturity adjust.**: schedule construction.
- **Start delay**: lag from trade to effective date (+2 OPEN DAYS).
- **Payment calendar / Fixing calendar**: the holiday calendars — the reason Example 2's fixing reconciles (§3.1).
- **Fixing**: **In advance** — the rate is set before the period starts.
- **Payment**: **Up front disc.** — settlement paid at the start, discounted (§7.2).
- **Discounting rate**: **Floating rate** — the rate used to discount.
- **Rate convention / Basis**: the day count (§8).
- **Computing mode / Rate expression / Rate formula / Margin mode**: Linear, Standard, Standard, Additive.
- **Initial / Intermediate / Final exchange**: all unticked — no principal moves (§1).
- **Day count / Roundings**: Yes, and None throughout.

**Flow schedule**

- **Lg**: the leg — 1 fixed, 2 floating (§5).
- **Flow Tp**: `INT` interest, `FEE` a charge, `FLW` an additional flow (§10).
- **Start / End Date**: the interest period.
- **Remaining Capital**: the notional the flow is computed on.
- **Fixing Date**: when the floating leg observes its index.
- **Rate / Convert Rate / Margin / Rate Factor**: the rate build-up; the floating leg reads 0.00000 until it fixes.
- **Payment Date**: when the flow settles — the period **start** on the interest legs (§7.1).
- **Flow**: the gross, undiscounted leg amount (§7.3). Negative means paid.
- **Nb of Days**: days in the period, driving the calculation.
- **Mkt.Op Date**: the market operation date — effectively the trade date.

## 15. Open items and gaps in this document

1. **No fixed example has reached its fixing date.** All three floating legs read 0.00000 with zero flow, so the **discounted net settlement has not been observed**. The generator states the convention (§7.2), and the formula is standard, but a fixed and settled FRA would show it actually applied — and would confirm whether the displayed gross leg amounts are restated post-fixing. This is the most valuable gap to close.
2. **Whether the displayed leg flows are gross or eventually netted** is not determinable from these captures (§7.3). Anyone reconciling a settlement must net the legs and discount; whether the system restates the leg rows or holds them gross should be confirmed.
3. **Sales margin is zero on all three** (§6), so how a commercial spread adjusts the net rate and flows through to the settlement is undocumented.
4. **The `FLW` additional flow on Example 2 is unexplained** (§10). A 14,000 PLN payment four days after trade date is clearly not a brokerage charge, but what it represents is not visible.
5. **Only one generator captured.** The two index-driven trades inherit their conventions from currency and index defaults that were not shown, so their calendars and day counts are inferred from the reconciliation rather than read from configuration.
6. **No valuation captured.** The flow schedule shows contractual amounts; the FRA's mark-to-market and its sensitivity to the forward curve are not visible.
7. **No non-EUR/PLN example**, and no index other than a three-month IBOR. A FRA on a compounded risk-free rate would behave differently — the fixing would be in arrears rather than in advance, which conflicts with the up-front settlement convention and would need its own treatment.
