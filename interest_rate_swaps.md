# Interest Rate Swaps (IRS)

## Purpose of this document

This is a reference document on interest rate swaps: what the product is, how the two legs are defined, how market conventions are applied through generators, how fixing mechanics differ between IBOR and risk-free-rate indices, and how the terms are represented in Murex. It is meant to be read on its own — a new joiner or anyone unfamiliar with the product should come away understanding the mechanics, not just recognizing the trade capture screen.

The three worked examples in §9 are a **EUR EURIBOR 6M swap**, a **GBP overnight-index swap** and a **USD SOFR swap that is both forward-starting and carries a mutual break clause**. They span two fixing conventions, three currencies with three different convention sets, and one structural variation beyond the vanilla shape.

## 1. Overview: what an interest rate swap is

An interest rate swap is a bilateral OTC contract in which two parties **exchange two streams of interest payments** on an agreed notional amount, over an agreed period. In the standard form documented here, one stream is calculated at a **fixed rate** and the other at a **floating rate** linked to a reference index.

Four features define the product:

- **The notional is never exchanged.** It exists only as the base for calculating interest on each leg. All three examples have *Initial exchange*, *Intermediate payments* and *Final exchange* unticked on both legs. This is precisely what separates an interest rate swap from a cross-currency swap, where notionals do change hands.
- **Payments are netted.** Where both legs pay on the same date in the same currency, only the difference is settled.
- **It starts at par.** A vanilla swap is struck so that the present values of the two legs are equal at inception, which is why the fixed rate is what it is and why *Premium* reads **None** on all three examples. The fixed rate is not a forecast — it is the rate that makes the trade worth zero on day one.
- **Value accrues from rate moves.** Once struck, the swap develops a positive or negative mark-to-market as the curve moves away from the level implied at inception.

Unlike an exchange-traded future, a swap is negotiated bilaterally: tenor, notional, start date and structural features are chosen rather than selected from a standardized list. What *is* standardized — day counts, calendars, fixing timing, payment frequency — comes from market convention, applied in the system through a **generator** (§4).

## 2. The two legs

### 2.1 Fixed leg

Pays or receives a rate agreed at inception and unchanged for the life of the trade. Defined by its rate, its day count convention, its payment frequency and its calendar.

### 2.2 Floating leg

Pays or receives a rate that resets periodically against a reference index. Defined by the index, an index factor (×1.0000 on all three examples, meaning the index is taken at face), a margin or spread added to it (zero on all three), the day count, the payment frequency, and — critically — the **fixing convention** (§6).

### 2.3 Direction: payer and receiver

Market convention names a swap from the perspective of the **fixed** leg:

- **Payer swap** — pay fixed, receive floating. **Short duration**: gains when rates rise.
- **Receiver swap** — receive fixed, pay floating. **Long duration**: gains when rates fall.

All three examples are **receiver** swaps: receive fixed, pay floating, long duration.

### 2.4 What the trade screen shows

The capture screen presents the two legs side by side, each with its currency, start and maturity dates, day count convention and rate or index. The left panel is the leg the book receives; the right is the leg it pays. Everything below that surface — calendars, delays, fixing and payment timing, rounding, stub treatment — sits in the generator behind it.

## 3. Nominal, and what it does not tell you

The nominal is the calculation base for both legs. It is **not** an exposure figure and not comparable across trades of different tenors: EUR 31,500,000 over eight years and USD 250,000,000 over ten carry very different risk. The meaningful measure is the swap's sensitivity to a parallel shift in the curve — its BPV or DV01 — which is a function of notional *and* tenor *and* the discount curve, and which does not appear on the capture screen (§10).

## 4. Generators: how market convention is applied

### 4.1 What a generator is

A **generator** is a convention template attached to the trade. Selecting one — *EUR-IBOR*, *GBP CALL MONEY*, *USD-SOFR* — populates the structural configuration of both legs from the market standard for that currency and index, rather than requiring each field to be keyed by hand.

This is the single most important concept for reading these screens correctly, because **most of what defines the trade economically is inherited, not entered**. The trade capture screen shows the negotiated terms — notional, dates, fixed rate, index, margin. The generator supplies everything else: calendars, start delay, day count bases, fixing and payment timing, stub rules, rounding, compounding mechanics. Two swaps that look similar on the capture screen can behave quite differently if their generators differ.

### 4.2 What the generator drives

At trade level:

- **Phases and legs per phase** — the structural shape (1 phase, 2 legs on all three examples; multi-phase structures allow a swap whose character changes partway through its life).
- **Schedules** — whether the two legs' schedules are built independently or in common (*Independent sets across legs* on all three).
- **Stub period** — where an odd period goes when the tenor does not divide evenly into whole periods (*Up front* on all three, meaning the short period sits at the beginning).
- **Amortizing** — whether an amortization profile is defined per leg or shared. Note this differs across the examples: *Independent definition across legs* on the EUR and GBP generators, *Common definition across legs* on the USD one.
- **Settlement delay** — inherited from the currency.

At leg level:

- **Start delay** — the lag from trade date to effective date.
- **Calculation, payment and fixing calendars** — which holiday calendars govern each function. These need not be the same (§6.4).
- **Rate convention and basis** — the day count (§5).
- **Computing mode** — *Linear* on all legs here: simple interest within a period, not compounded.
- **Fixing and payment timing** — in advance or in arrears (§6).
- **Margin mode** — *Additive* on all floating legs here: the spread is added to the index rather than applied multiplicatively.
- **Rate formula / Formula** — *Standard* / *FIXING* on all three: the floating rate is the index fixing itself, without an overlay formula.
- **Rounding rules** — set to *None* throughout.

### 4.3 The three generators compared

| Field | EUR-IBOR | GBP CALL MONEY | USD-SOFR |
|---|---|---|---|
| Floating index | EURIBOR6M | GBP CALL M COMP | USD SOFR COMP |
| Underlying index field | *(not present)* | GBP CALL MONEY | USD SOFR |
| Fixed leg day count | LIN 30/360 | LIN ACT/365 | LIN 30/360 |
| Floating leg day count | LIN ACT/360 | LIN ACT/365 | LIN ACT/360 |
| Start delay | +2 OPEN DAYS | 0 DAY | +02 BD |
| Calculation calendar | TARGET | LONDON | NEW YORK |
| Payment calendar | TARGET | LONDON | NEW YORK |
| Fixing calendar | TARGET | LONDON | **US GVT BND** |
| Fixing | **In advance** | **In arrears** | **In arrears** |
| Payment | In arrears | In arrears | In arrears |
| Margin mode | Additive | Additive | Additive |
| Amortizing | Independent across legs | Independent across legs | Common across legs |
| Stub period | Up front | Up front | Up front |
| Rate factor applied | *(not present)* | To main index | To main index |
| Absolute rate | *(not present)* | No | No |
| Estimation bound dates | *(not present)* | Based on adjusted dates | Based on adjusted dates |
| Underlying dates/rates | *(not present)* | Intrinsic | Intrinsic |

The pattern is clear: the fields in the lower block exist **only on the compounded-index legs**. They are the mechanics of building a rate by compounding daily fixings, and an IBOR leg has no use for them (§6.3).

## 5. Day count conventions

The day count determines how a rate is converted into an interest amount for a period:

**Interest = Notional × Rate × Day-count fraction**

Three bases appear across the examples:

| Convention | Numerator | Denominator | Where it appears |
|---|---|---|---|
| **30/360** | Each month counted as 30 days | 360 | Fixed leg, EUR and USD examples |
| **ACT/360** | Actual calendar days | 360 | Floating leg, EUR and USD examples |
| **ACT/365** | Actual calendar days | 365 | Both legs, GBP example |

Two consequences worth stating plainly:

- **The two legs of a swap frequently use different bases**, and where they do, the fixed and floating rates are **not directly comparable**. In the EUR example, 3.227% on 30/360 is not the same economic rate as 3.227% would be on ACT/360; comparing the headline numbers without adjusting for basis is a mistake. The GBP example, by contrast, runs ACT/365 on both legs, so its two rates *are* directly comparable.
- **The basis is a currency and index convention, not a choice.** It comes from the generator, which is why it differs so consistently across the three examples.

## 6. Fixing conventions: term rates and compounded overnight rates

This is the deepest structural distinction in the set, and it separates Example 1 from Examples 2 and 3.

### 6.1 Forward-looking term rates — fixing in advance

EURIBOR 6M is a **term rate**: it is published as a rate for a six-month period and is known at the *start* of that period. The floating leg therefore fixes **in advance** and pays **in arrears** — the rate is set on day one of the period and the resulting cash flow settles at the end.

The visible consequence is that **1st fixing carries a real rate**: 2.762% in Example 1. That rate is already known at trade date and the first floating payment can be calculated immediately.

### 6.2 Backward-looking compounded rates — fixing in arrears

A compounded overnight index — the GBP and USD examples — has no term rate. The rate for a period is constructed by compounding daily overnight fixings across the period, so it does not exist until the period has run. The leg therefore fixes **in arrears**: both the fixing and the payment happen at the end.

The visible consequence is that **1st fixing reads 0.000000** on both Examples 2 and 3. This is not an error, a missing rate, or an at-market placeholder: nothing can be known at trade date, and the field is populated only once the period accrues.

### 6.3 The index pair, and the compounding mechanics fields

Compounded legs carry **two index fields** where an IBOR leg carries one:

- **Index** — the compounded index actually applied to the leg (*GBP CALL M COMP*, *USD SOFR COMP*).
- **Underlying index** — the overnight rate being compounded (*GBP CALL MONEY*, *USD SOFR*).

They also carry a cluster of configuration fields that exist because compounding requires the observation window to be defined precisely:

- **Estimation bound dates** — how the start and end of the compounding window are determined (*Based on adjusted dates* on both).
- **Underlying dates/rates** — how the dates of the individual overnight fixings inside the window are derived (*Intrinsic* on both).
- **Absolute rate** — whether the resulting rate is treated as absolute (*No* on both).
- **Rate factor applied** — where the index factor is applied (*To main index* on both).

None of these appear on the EURIBOR generator, because a single published term fixing needs no window definition.

### 6.4 The fixing calendar can differ from the payment calendar

The USD example makes a point the other two do not: its calculation and payment calendars are **NEW YORK**, but its **fixing calendar is US GVT BND**. The overnight rate is published on US government securities business days, which are not the same set as New York banking days. Using the banking calendar to determine which days have fixings would produce a wrong compounded rate.

The general lesson: **calculation, payment and fixing calendars are three separate fields and should be read separately.** Assuming they match is safe on the EUR and GBP examples and wrong on the USD one.

## 7. Dates: unadjusted, adjusted, and how the schedule is anchored

### 7.1 The paired date fields

Start date and maturity each display **two dates**: the unadjusted date implied by the tenor, and the adjusted date after applying the business day convention and the relevant calendar. Where the unadjusted date is already a good business day the two are identical.

The examples demonstrate both cases:

- **Example 1** — maturity shows *27 ago 2034* and *28 ago 2034*. The 27th is a **Sunday**, so it rolls forward to Monday the 28th. Its start date, Thursday 27 August 2026, needs no adjustment and shows the same date twice.
- **Examples 2 and 3** — all four dates fall on business days (Friday/Thursday and Friday/Thursday respectively), so unadjusted and adjusted match throughout.

When reconciling schedules or cash flows, it matters which of the two a downstream process uses. Note that the compounded legs' *Estimation bound dates* is set to *Based on adjusted dates* (§6.3), so the compounding window follows the adjusted dates.

### 7.2 Start delay: spot conventions differ by currency

- EUR: **+2 OPEN DAYS**
- GBP: **0 DAY** — the swap starts on trade date
- USD: **+02 BD**

Note also that the notation itself differs between generators (*OPEN DAYS* against *BD*), which is worth being aware of when reading configurations side by side.

### 7.3 Tenor codes and forward starts

Maturity may be expressed as a **tenor code** that resolves to a date. In Example 3 the field reads *10y*, resolving to 31 dic 2037 — and importantly, the ten years is measured from the swap's **start date** (31 dic 2027), not from the trade date. Since that trade is valued as at 9 September 2026, it is a ten-year swap beginning roughly fifteen months forward. See §8.1.

## 8. Structural variations beyond the vanilla shape

### 8.1 Forward-starting swaps

A **spot-starting** swap begins at the currency's standard settlement lag after trade date — Examples 1 and 2. A **forward-starting** swap begins at an agreed later date: Example 3 starts on 31 December 2027, some 478 days after its 9 September 2026 valuation date.

The economics are unchanged in form but the exposure profile is different: no interest accrues on either leg until the start date, while the trade carries mark-to-market and counterparty exposure from trade date onward. The fixed rate on a forward-starting swap reflects **forward** rates for the future period, not spot rates, so it should not be compared directly with a spot-starting swap of the same tenor.

### 8.2 Mutual break clauses

Example 3 carries a **mutual break** — flagged on the *Characteristics* tab and configured in the *Exotic details* panel as **European**, **breakable by Both sides**.

A mutual break (also called an optional early termination) gives **both** counterparties the right to terminate the swap at one or more specified dates, at the trade's prevailing mark-to-market. It is primarily a **credit mitigation device**: a ten-year swap with a break at year five has, in credit terms, much of the profile of a five-year trade, because either party can walk away at fair value at that point. That shortens the effective exposure horizon and reduces the associated capital and valuation-adjustment charges.

Points worth being precise about:

- **European** means exercise at a single specified date. A Bermudan-style clause would allow several. The specific dates sit behind the *dates* link and were not captured (§12).
- **Breakable by Both sides** is what makes it *mutual*. A right held by only one party is an asymmetric break or a cancellable swap — note the separate *Cancellable* checkbox in the same panel, which is unticked here.
- Because the break is symmetric and executed at prevailing mark-to-market rather than at a pre-agreed strike, it is not equivalent to an embedded swaption, and it is conventionally treated as credit mitigation rather than as optionality to be valued. Whether and how it is reflected in valuation should be confirmed rather than assumed from this document.
- **Operationally it creates a scheduled lifecycle event.** On the break date the trade either continues or terminates against a settlement payment. That is a different downstream path from a swap that simply runs to maturity, and it needs to be handled in settlement and accounting rather than discovered when the date arrives.

### 8.3 The Exotic and Flex flags

A trade stops being treated as plain vanilla when the *Characteristics* tab flags it. In Example 3 both **Exotic** and **Flex** are ticked, which is what exposes the *Exotic details* panel containing the break configuration. The remaining exotic features in that panel — barriers, range, ratchet, TARN, PRDC, multi-currency, embedded option — are all set to *No*, confirming the trade is vanilla apart from the break.

The *Flex details* screen was not captured, so what the Flex flag configures on this trade is not documented here (§12).

### 8.4 Variations not present in these examples

The generator screens expose several structural options none of the three examples uses: **amortizing** notionals, **multi-phase** structures (all three are single-phase), **marked to market** and **multi-currency** legs, **forward start capital**, **non-deliverable** legs and **total return** legs. They are noted here so that a reader encountering one recognizes it as a configured variation rather than an anomaly.

## 9. Worked examples

### 9.1 Example 1 — EUR EURIBOR 6M swap, 8 years (receive fixed)

| Field | Value |
|---|---|
| Generator | EUR-IBOR |
| Nominal | 31,500,000 EUR |
| Start date | 27 ago 2026 (unadjusted = adjusted) |
| Maturity | 27 ago 2034 unadjusted → **28 ago 2034 adjusted** |
| Tenor | 8 years |
| Premium | None |
| **Receive** | **Fixed 3.227000%**, LIN 30/360 |
| **Pay** | **Floating EURIBOR6M × 1.0000**, LIN ACT/360, margin 0.000000 |
| 1st fixing | **2.762000%** |
| Fixing / Payment | In advance / In arrears |
| Calendars | TARGET (calculation, payment, fixing) |
| Start delay | +2 OPEN DAYS |
| Notional exchange | None (initial, intermediate and final all unticked) |

**Direction:** receiver — receive fixed, pay floating. Long duration: the position gains if EUR rates fall.

**Dates:** the unadjusted maturity of 27 August 2034 falls on a Sunday and rolls to Monday 28 August under the TARGET calendar. With a +2 open day start delay and a 27 August 2026 effective date, the implied trade date is Tuesday 25 August 2026.

**Mismatched bases:** fixed on 30/360 against floating on ACT/360 — the standard EUR arrangement, and a case where the two headline rates cannot be compared without adjusting for basis (§5).

**What the first fixing tells you.** The floating leg's opening rate is 2.762% against a fixed rate of 3.227% — a gap of 46.5 basis points. Since the par fixed rate is, in effect, an average of the forward rates expected across the swap's life, a fixed rate this far above the current six-month fixing indicates the curve is upward-sloping and the market expects EUR rates to rise. The immediate consequence is that the first net cash flow favours the receiver of fixed; that advantage narrows and reverses if the curve realises as priced.

### 9.2 Example 2 — GBP overnight-index swap, 10 years (receive fixed)

| Field | Value |
|---|---|
| Generator | GBP CALL MONEY |
| Nominal | 25,000,000 GBP |
| Start date | 21 ago 2026 (unadjusted = adjusted) |
| Maturity | 21 ago 2036 (unadjusted = adjusted) |
| Tenor | 10 years |
| Premium | None |
| **Receive** | **Fixed 4.646000%**, LIN ACT/365 |
| **Pay** | **Floating GBP CALL M COMP × 1.0000**, LIN ACT/365, margin 0.000000 |
| Underlying index | GBP CALL MONEY |
| 1st fixing | **0.000000** |
| Fixing / Payment | **In arrears** / In arrears |
| Calendars | LONDON (calculation, payment, fixing) |
| Start delay | **0 DAY** |
| Notional exchange | None |

**Direction:** receiver — long duration in GBP rates.

**An OIS, not an IBOR swap.** The floating leg references a compounded overnight rate rather than a term rate, which drives three visible differences from Example 1: fixing in arrears rather than in advance, a first fixing of 0.000000 rather than a known rate, and the presence of the *Underlying index* field naming the overnight rate being compounded.

**Matched bases.** Both legs run ACT/365, so unlike the EUR example the fixed and floating rates here are directly comparable without adjustment.

**Same-day start.** The 0-day start delay means the swap begins on trade date — Friday 21 August 2026 — rather than at a spot lag. Both start and maturity fall on business days, so no date adjustment applies anywhere on this trade.

### 9.3 Example 3 — USD SOFR swap, 10 years forward-starting, with mutual break (receive fixed)

| Field | Value |
|---|---|
| Generator | USD-SOFR |
| Nominal | 250,000,000 USD |
| Maturity (tenor code) | **10y** → 31 dic 2037 |
| Start date | **31 dic 2027** (unadjusted = adjusted) |
| Maturity | 31 dic 2037 (unadjusted = adjusted) |
| Premium | None |
| **Receive** | **Fixed 4.481000%**, LIN 30/360 |
| **Pay** | **Floating USD SOFR COMP × 1.0000**, LIN ACT/360, margin 0.000000 |
| Underlying index | USD SOFR |
| 1st fixing | **0.000000** |
| Fixing / Payment | **In arrears** / In arrears |
| Calculation / Payment calendar | NEW YORK |
| **Fixing calendar** | **US GVT BND** |
| Start delay | +02 BD |
| Characteristics | **Exotic ✔, Flex ✔** |
| Exotic detail | **Mutual break — European, breakable by Both sides** |
| Notional exchange | None |

**Direction:** receiver — long duration in USD rates, on the largest notional of the three.

**Forward-starting.** The swap begins 31 December 2027 against a valuation date of 9 September 2026 — 478 days, roughly fifteen months, forward. The ten-year tenor runs from the *start* date, not the trade date, so this is a ten-year swap that has not yet begun accruing. Its 4.481% fixed rate reflects forward rates for the 2027–2037 period and is not comparable with a spot-starting ten-year rate.

**Mutual break.** Both parties may terminate at the specified European exercise date at prevailing mark-to-market. The economic tenor is ten years; the *credit* tenor is effectively bounded by the break date. See §8.2 — and note that the actual break dates sit behind a link that was not captured.

**Fixing calendar differs.** Calculation and payment follow NEW YORK; fixings follow US GVT BND, the calendar on which the overnight rate is published. This is the only example where the three calendars are not identical (§6.4).

**Mismatched bases**, as in Example 1: 30/360 fixed against ACT/360 floating.

**On the NPV panel.** The captured panel shows Leg NPVs of 0, a total NPV of 0 and a BPV of 0 as at 9 September 2026. An NPV of zero is consistent with a par trade, but a BPV of zero is not economically meaningful — a ten-year swap on a USD 250,000,000 notional would carry a BPV in the order of two hundred thousand USD per basis point. The panel appears not to have been computed rather than to be reporting a genuine zero, and should not be read as a risk figure.

### 9.4 The three examples side by side

| | EUR IBOR | GBP OIS | USD SOFR |
|---|---|---|---|
| Generator | EUR-IBOR | GBP CALL MONEY | USD-SOFR |
| Currency | EUR | GBP | USD |
| Nominal | 31,500,000 | 25,000,000 | 250,000,000 |
| Direction | Receive fixed | Receive fixed | Receive fixed |
| Fixed rate | 3.227% | 4.646% | 4.481% |
| Fixed basis | 30/360 | ACT/365 | 30/360 |
| Floating index | EURIBOR6M | GBP CALL M COMP | USD SOFR COMP |
| Index type | Forward-looking term rate | Compounded overnight | Compounded overnight |
| Floating basis | ACT/360 | ACT/365 | ACT/360 |
| Bases matched? | **No** | **Yes** | **No** |
| Margin | 0 | 0 | 0 |
| 1st fixing | **2.762%** | **0.000000** | **0.000000** |
| Fixing timing | **In advance** | In arrears | In arrears |
| Start delay | +2 OPEN DAYS | 0 DAY | +02 BD |
| Calendars (calc/pay/fix) | TARGET / TARGET / TARGET | LONDON / LONDON / LONDON | NEW YORK / NEW YORK / **US GVT BND** |
| Start | 27 ago 2026 (spot) | 21 ago 2026 (same day) | **31 dic 2027 (forward)** |
| Maturity | 28 ago 2034 (**rolled from Sunday**) | 21 ago 2036 | 31 dic 2037 |
| Tenor | 8y | 10y | 10y from start |
| Structure | Vanilla | Vanilla | **Mutual break, European, both sides** |
| Notional exchange | None | None | None |
| Premium | None | None | None |

## 10. Valuation and risk

### 10.1 Valuation

A swap's mark-to-market is the difference between the present values of its two legs:

**NPV = PV(leg received) − PV(leg paid)**

At inception a vanilla swap is struck at par so this is zero, which is why none of the three examples carries a premium. Thereafter the value moves as the curve moves: for a receiver swap, a fall in rates raises the value of the fixed leg received relative to the floating leg paid, producing a gain.

Valuing the floating leg requires projecting future fixings from the relevant forward curve, and discounting both legs on the appropriate discount curve. For a compounded overnight leg, projection also requires the compounding window mechanics described in §6.3.

### 10.2 Risk

- **Directional rate risk**, measured by BPV/DV01 — the change in value for a one basis point parallel shift. This is the primary exposure and it does not appear on the capture screen; it must be computed.
- **Curve risk.** A swap is exposed to the shape of the curve, not just its level. Positions across tenors can be BPV-neutral overall while carrying substantial curve exposure.
- **Basis risk.** Exposure to the spread between index families — a EURIBOR-linked leg and a compounded-overnight leg do not move identically, and a book holding both carries the basis between them.
- **Fixing risk.** Each reset converts a projected rate into a realised cash flow. For in-advance legs the next fixing is already known; for in-arrears compounded legs it is still accumulating.
- **Counterparty credit risk.** Unlike an exchange-traded contract, a swap is a bilateral obligation running for its full life. This is what break clauses (§8.2), collateral agreements and clearing are designed to mitigate.
- **Forward-start exposure.** A forward-starting swap carries market and counterparty exposure from trade date even though no interest accrues until the start date.
- **Lifecycle and operational risk.** Fixings, resets, netting of same-date payments, break dates and stub periods are all scheduled events that must be processed correctly.

## 11. Glossary of fields seen in the Murex screens

**Trade level**

- **Generator**: the convention template applied to the trade, populating both legs' structural configuration from the market standard for that currency and index (§4).
- **Maturity**: the end of the swap, shown as an unadjusted and an adjusted date, and optionally driven by a tenor code such as *10y* which resolves from the start date (§7).
- **Nominal**: the calculation base for both legs. Not exchanged, and not a risk measure (§3).
- **Premium**: any upfront payment. *None* on a par swap.
- **Risk section**: analytical grouping; unpopulated on all three examples.

**Leg level (trade capture)**

- **Receive / Pay**: which leg the book receives and which it pays. The fixed leg's direction names the swap (§2.3).
- **Index** and the **× factor**: the floating reference and the multiplier applied to it (1.0000 throughout, meaning the index is taken at face).
- **1st fixing**: the floating rate for the first period. A real rate for a term index; 0.000000 for a compounded index, which cannot be known at trade date (§6.2).
- **Convention**: the leg's day count basis (§5).
- **Margin**: the spread over the index (zero throughout).
- **Rate**: the fixed leg's rate.
- **Schedules definition**: link to the period and frequency configuration — not captured (§12).

**Generator level**

- **Phases / Legs per phase**: the structural shape of the trade.
- **Schedules**: whether leg schedules are built independently or in common.
- **Stub period**: where an odd period is placed (*Up front* throughout).
- **Amortizing**: whether an amortization profile is defined per leg or shared.
- **Start delay**: lag from trade date to effective date (§7.2).
- **Calculation / Payment / Fixing calendar**: the holiday calendars governing period ends, settlement and fixing dates respectively. These are three separate fields and need not agree (§6.4).
- **Fixing**: whether the floating rate is set at the start (*In advance*) or end (*In arrears*) of the period (§6).
- **Payment**: when the cash flow settles (*In arrears* throughout).
- **Rate convention / Basis**: the day count.
- **Computing mode**: *Linear* — simple interest within a period.
- **Margin mode**: how the spread combines with the index (*Additive* throughout).
- **Formula / Rate formula**: the floating rate construction (*FIXING* / *Standard* — the index fixing itself, no overlay).
- **Underlying index**: on compounded legs, the overnight rate being compounded (§6.3).
- **Estimation bound dates / Underlying dates/rates / Absolute rate / Rate factor applied**: compounding window mechanics, present only on compounded legs (§6.3).
- **Initial / Intermediate / Final exchange**: whether notional is exchanged. Unticked throughout — the defining feature of an interest rate swap (§1).
- **Day count**: whether day count applies to the leg (*Yes* throughout).
- **Rounding fields**: rounding applied to rates, flows and capital (*None* throughout).

**Characteristics and exotic configuration**

- **Amortized / Exotic / Flex / Additional flows / Compute / Unlink pay-receive**: flags routing the trade beyond vanilla treatment (§8.3).
- **Mutual break**: both parties' right to terminate at a specified date at prevailing mark-to-market, with an exercise style (*European*) and the party or parties holding the right (*Both sides*) (§8.2).
- **Cancellable**: a termination right, distinct from a mutual break; unticked here.
- **Range / Ratchet / TARN / PRDC / Embedded option / Multi Currency**: exotic payoff features, all *No* on these examples.
- **Sales margin**: commercial margin on a leg; zero here.
- **Leg NPV / Total NPV / BPV**: valuation output — see the caution in §9.3.

## 12. Open items and gaps in this document

1. **Payment frequency is not documented for any of the three swaps.** It sits behind the *Schedules definition → Details* link on each leg, which was not captured. Frequency is a defining economic term — it determines how many payments occur, the length of each accrual period and, on a compounded leg, the compounding window. This is the most significant gap in this document and should be closed for at least one example per generator.
2. **Mutual break dates were not captured** (§8.2). The clause is configured as European and exercisable by both sides, but the actual break date or dates sit behind the *dates* link. Without them, the effective credit tenor of that trade cannot be stated.
3. **The Flex flag is ticked on the USD example but its detail screen was not captured** (§8.3). What Flex configures on that trade is therefore undocumented.
4. **The USD-SOFR generator applies 30/360 to the fixed leg.** Market convention for USD SOFR overnight-index swaps is ACT/360 on both legs. This may be a deliberate configuration choice, but given the GBP OIS generator uses matched bases on both legs, the difference is worth confirming rather than assuming.
5. **Valuation output on the USD example is not meaningful** (§9.3). A BPV of zero on a ten-year swap of that size indicates the panel was not computed. Any reconciliation against system valuation should use a computed figure.
6. **Break clause valuation and lifecycle treatment are not documented.** Whether the mutual break is reflected in valuation, how it affects credit exposure measurement, and how the break event is processed operationally are all questions this document raises but cannot answer from the captured screens.
7. **No payer-direction example.** All three swaps are receivers. The mechanics are symmetric, but a payer example would confirm how direction is represented on the capture screen.
8. **No structural variations beyond the break** (§8.4). Amortizing, multi-phase, multi-currency and non-deliverable legs are all configurable but unused here, and would need their own documentation if they are traded.
