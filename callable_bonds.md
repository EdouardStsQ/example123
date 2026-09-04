# Callable Bonds

## Purpose of this document

This is a reference document on callable bond trades: what the embedded call option is, how the call schedule is defined and read, how yield to call replaces yield to maturity as the quoting convention, and how the terms are represented in Murex. It is meant to be read on its own — a new joiner or anyone unfamiliar with the product should come away understanding the mechanics, not just recognizing the trade capture screen.

The three worked examples in §11 are a **USD corporate perpetual with 87 semi-annual calls**, a **EUR corporate bullet with a single three-month par call**, and a **USD sovereign bullet with the same three-month par call structure**. That spread is deliberate: the first is an instrument whose whole character is defined by its call schedule, while the other two carry a call that is almost incidental. Both extremes appear in the same screens and must be read the same way.

**A note on identifiers.** Portfolio, counterparty and security identifiers are omitted throughout. Each example is described by the characteristics that matter economically — currency, issuer type, coupon, maturity and call structure.

## 1. Overview: what a callable bond is

A callable bond is an ordinary bond with an **embedded option held by the issuer** to redeem it early, on specified dates and at specified prices.

The consequences for the holder are asymmetric and worth stating plainly:

- **The issuer calls when it suits the issuer.** In practice that means when refinancing is cheaper — typically after yields have fallen or the issuer's credit has improved. The holder loses the bond precisely when it has become most valuable.
- **Upside is capped.** As the bond's price approaches the call price, further rallies are limited because the market prices in the likelihood of redemption at that level. Downside is not similarly protected.
- **The holder is compensated up front**, through a higher coupon or a lower price than an equivalent non-callable bond would carry.

This is why a callable bond exhibits **negative convexity** near the call price, and why it is quoted on **yield to call** rather than yield to maturity (§7).

### 1.1 Relationship to a straight bond trade

The trade capture screen, the pricing arithmetic and the consideration calculation are **identical** to a straight bond. What is added:

| | Straight bond | Callable bond |
|---|---|---|
| Bond definition screen | Bond definition | **Callable bond definition** |
| Trigger clauses | — | **Calls / Puts / Makewholes** schedule (§5) |
| Yield field | Yield (to maturity) | **YTC** — yield to call, alongside a Yield or Margin field carrying the same value (§7) |
| Redemption | Certain, at maturity | **Uncertain** — at a call date or at maturity |

Note that the **Phase** count is *not* one of the differences. Phases describe the bond's coupon structure and are independent of callability — a straight bond can have more than one phase, and a callable can have just one (§4.2).

Everything in §6 (accrued) and §8 (consideration) works exactly as it does for a non-callable bond. The optionality changes what the bond is worth and when it redeems, not how the ticket is calculated.

## 2. Direction

| | Buy | Sell |
|---|---|---|
| Bond | Received | Delivered |
| Cash | **Paid** — the Total amount | **Received** |
| Accrued interest | **Paid** to the seller | **Received** from the buyer |
| Exposure to the call | **Holds** the short option — the issuer may call the bond away | Transfers that exposure to the buyer |

Examples 2 and 3 are **Buy**; Example 1 is **Sell**.

The buyer of a callable bond is implicitly **short an option to the issuer**. That is the substance of the product: the holder has sold the issuer the right to redeem.

## 3. What the trade screen shows

The capture screen is the same as for a straight bond, with the yield block extended:

| Field | Notes |
|---|---|
| **Bond / Market / ISIN** | The security, its market and identifier. |
| **Quantity / Nominal amount / LotSize** | Position size; the nominal drives every calculation. |
| **Clearing / Settlement** | The venue and the settlement basis — **T+1** on two examples, **T+2** on the third. |
| **Pay. conditions** | *Delivery versus payment* on all three. |
| **Payment / Accrued coupon date** | Settlement date, with the accrual fraction alongside (§6). |
| **Indexed to / Assumed** | Present on one example only, and zero there. Not exercised by any of these trades (§14). |
| **Clean price / Accrued coupon / Dirty price / Accrued amount** | Standard bond pricing (§6). |
| **Yield** *or* **Margin** | The quoted yield measure — see §7 for why the label varies. |
| **YTC** | **Yield to call** — the distinguishing field on a callable. |
| **Sales margin / Sales price / yield** | Commercial spread; zero on all three. |
| **Total amount** | The cash consideration (§8). |

## 4. The callable bond definition

| Field | Meaning |
|---|---|
| **Reference capital** | The issue size — 100,000,000 on all three. Not the trade size. |
| **Bond generator** | The convention template: coupon frequency, day count, and for reset structures the benchmark. |
| **First accrual date** | When interest begins to accrue. |
| **Roll date** | Anchors the coupon schedule. |
| **Maturity** | Final redemption date, if the bond is never called. |
| **Coupon %** | The annual coupon rate. |
| **More… / Special accrual convention** | Additional characteristics; *Yes* and *No* respectively across all three. |
| **Trigger clauses** | The button opening the call, put and makewhole schedules (§5). |
| **Phase / Leg** | The number of distinct coupon regimes over the bond's life — independent of callability. See §4.2. |

### 4.1 Generators and day counts

Three generators appear, and each implies a different accrual basis:

| Generator | Frequency | Day count | Example |
|---|---|---|---|
| **FIX USD 6M H15T5Y** | Semi-annual | ACT/360 basis on the accrual shown | 1 |
| **FIX EUR 1Y LIN ACT/ACTISMA** | Annual | ACT/ACT (ISMA) | 2 |
| **FIX USD 6M 30E/360** | Semi-annual | **30E/360** | 3 |

The third is worth noting because **30E/360 is a computed day count, not a calendar one**: each month counts as 30 days and each year as 360, with day-of-month capped at 30. Example 3's accrual fraction of 98/360 is exactly 30×(8−5) + (21−13) = 98 — a figure that does not match the actual number of calendar days between those dates.

### 4.2 Phases: the coupon structure

The **Phase** indicator shows how many distinct **coupon regimes** the bond has over its life. A bond with one phase pays on a single basis throughout; a bond with two or more changes basis at defined points — a step-up coupon, a fixed period followed by a floating one, or a fixed period followed by a periodic reset.

Across these examples: **1 / 1** on Examples 2 and 3, **1 / 2** on Example 1.

**Phases are independent of callability.** A multi-phase bond is not necessarily callable, and a callable bond is not necessarily multi-phase — Examples 2 and 3 are both callable with a single phase. Straight bonds can and do carry more than one phase. The phase count tells you about the **coupon**, and nothing about the call schedule; that lives entirely in the trigger clauses (§5).

**What identifies a fix-to-reset structure** is therefore the combination of things, not the phase count alone. In Example 1 the second phase, the generator's reference to a five-year Treasury benchmark, the perpetual maturity and the dense call schedule together point to a fix-to-reset perpetual: a fixed coupon until the first call date, after which the coupon resets periodically off the benchmark. That is the standard shape for subordinated bank capital, and it is why such instruments are generally expected — though not contractually required — to be called at the first opportunity. Read those features together rather than inferring the structure from any one of them.

## 5. Trigger clauses: the call schedule

The **Trigger clauses** screen holds the optionality, under three tabs:

- **Calls** — the issuer's right to redeem early. Populated on all three examples.
- **Puts** — the holder's right to require redemption. **Zero on all three** (§14).
- **Makewholes** — redemption at a price computed from a discounted value of remaining cash flows rather than a fixed price. **Zero on all three** (§14).

Two controls sit above the grid: **Date Mode** (*Business* on all three) and **Automatic trigger clauses generation**, which is how a schedule of 87 rows is produced rather than keyed individually.

### 5.1 Reading the columns

| Column | Meaning | Value across all three examples |
|---|---|---|
| **Effective start date** | When the call opportunity opens. | Varies |
| **Effective end date** | When it closes. **Equal to the start date for a single-date call**; later for a window (§5.2). | Varies |
| **Notice Period** | Days of notice the issuer must give before redeeming. | **0** |
| **Repayment Type** | How the redemption amount is determined. | **Price** |
| **Repayment** | The redemption price, as a percentage of nominal. | **100.0000** — par |
| **Maturity** | Which date the bond redeems on if called. | **End date** |
| **Accruals Paid** | Whether accrued interest is paid on redemption. | **Yes** |
| **Coupon Forfeit** | Whether the current coupon is forfeited on call. | **No** |
| **Penalty fee / Rental fee** | Additional amounts on early redemption. | **0.00** |
| **Capital mode** | The capital base the repayment applies to. | **Initial** |

Every call across all three examples is therefore a **clean par call**: redeem at 100, pay the accrued, no forfeit, no fees, no notice recorded.

**`Maturity: End date`** is the field linking a call to its settlement: if exercised, the bond redeems on the **end date** of that clause. For a single-date call the start and end are the same day; for a window, redemption falls at the window's close.

### 5.2 Single-date calls and call windows

The examples show both shapes, and the difference is visible in the first two columns:

- **Single-date call** — start date equals end date. One discrete opportunity. Examples 2 and 3.
- **Call window** — start date precedes end date, with consecutive rows covering the period continuously. Example 1's rows run in six-month windows from the first call date onward, each beginning where the previous ended.

A schedule of contiguous windows describes a bond that is callable throughout the remainder of its life, with redemption falling on the relevant window's end date.

## 6. Accrued interest

Accrued is computed exactly as on a non-callable bond:

**Accrued = (Annual coupon ÷ Frequency) × Days accrued ÷ Days in period**

| Example | Fraction | Calculation | Accrued |
|---|---|---|---|
| 1 | **4 / 360** | 7.125 × 4/360 | **0.079167** |
| 2 | **172 / 365** | 3.125 × 172/365 | **1.472603** |
| 3 | **98 / 360** | (6.875 ÷ 2) × 98/180 | **1.871528** |

All three tie to the screen exactly, and the dirty price follows as clean plus accrued in every case.

Note that the denominator identifies the convention: **360 with a semi-annual or ACT/360 basis**, **365 for the annual ACT/ACT bond**. Example 3's 98 is a computed 30E/360 count rather than actual days (§4.1).

## 7. Yield to call, and the Yield / Margin field

### 7.1 Why YTC rather than YTM

A callable bond's redemption date is uncertain. Quoting a yield to maturity assumes the bond survives to maturity, which for a bond trading above its call price is usually the *less* likely outcome. The market therefore quotes **yield to call** — the return assuming redemption at the call date and price.

Where multiple calls exist, the relevant convention is **yield to worst**: the lowest yield across maturity and every call date, since the issuer will act in its own interest.

### 7.2 The Yield / Margin field carries the same value as YTC

The field beside YTC is labelled differently across the examples, but the value is the same in every case:

| Example | Field label | Field value | YTC |
|---|---|---|---|
| 1 | **Margin** | 7.099069 | **7.0991** |
| 2 | **Yield** | 3.431523 | **3.4315** |
| 3 | **Yield** | 6.447332 | **6.4473** |

The YTC field is simply the same number displayed to four decimals. On Example 1 the label reads *Margin* rather than *Yield* — most likely because that bond's two-phase reset structure (§4.2) makes a margin the natural quoting convention — but the value is not a reset spread; it is the same yield measure. In all three cases the **Sales price / yield** pair carries the identical figure.

The practical point: **the quoted yield on a callable bond is a yield to call, whatever the field is labelled.** It is not comparable with a yield to maturity on a non-callable bond of the same final maturity.

### 7.3 Price relative to par, and what it implies

| Example | Coupon | YTC | Clean price | Position vs par |
|---|---|---|---|---|
| 1 | 7.125% | 7.0991% | 100.1100 | **Above** |
| 2 | 3.125% | 3.4315% | 99.0590 | **Below** |
| 3 | 6.875% | 6.4473% | 103.2100 | **Above** |

The relationship is the standard one — a coupon above the yield puts the bond at a premium, below it at a discount — but it carries extra weight on a callable. A bond trading meaningfully **above its call price** is a bond the market expects to be called, and its price behaviour is dominated by the call rather than by the final maturity.

## 8. The consideration

Built exactly as for a straight coupon bond, in two separately computed components:

**Total = (Nominal × Clean price ÷ 100) + Accrued amount**

| | Example 1 | Example 2 | Example 3 |
|---|---|---|---|
| Clean consideration | 1,000,000 × 100.1100% = **1,001,100.00** | 900,000 × 99.0590% = **891,531.00** | 5,000,000 × 103.2100% = **5,160,500.00** |
| Accrued amount | **791.67** | **13,253.42** | **93,576.39** |
| **Total** | **1,001,891.67** ✓ | **904,784.42** ✓ | **5,254,076.39** ✓ |

All three reconcile to the cent.

As with straight bonds, **do not rebuild the consideration from the dirty price** — the two components are computed and rounded independently, and the displayed dirty price is a rounded presentation of their sum rather than an input.

## 9. Settlement

- **`Pay. conditions: Delivery versus payment`** on all three.
- Settlement basis is **T+1** on Examples 1 and 3 and **T+2** on Example 2 — the convention follows the market and the clearing venue rather than the callable feature.
- **Clearing venue** differs across all three and is populated in each case.

## 10. Call structures seen in practice

The three examples span the range, and recognising which type you are looking at matters more than any individual field.

### 10.1 The three-month par call (Examples 2 and 3)

A **single call date roughly three months before maturity**, at par:

| | Example 2 | Example 3 |
|---|---|---|
| Call date | 05 dic 2029 | 13 feb 2037 |
| Maturity | 05 mar 2030 | 13 may 2037 |
| Gap | **90 days** | **89 days** |

This is a near-universal feature of modern corporate and sovereign issuance. Its purpose is administrative rather than economic: it lets the issuer refinance in the final months without a makewhole payment, and it removes the awkwardness of a new issue overlapping an old one. **The optionality is worth very little** — the issuer gains three months of flexibility on a bond about to redeem anyway — so the yield to call and the yield to maturity are nearly identical, and the bond trades essentially as a bullet.

### 10.2 The perpetual with a dense call schedule (Example 1)

Here the call schedule **is** the instrument:

- **87 call opportunities**, in consecutive six-month windows.
- The first falls **5.5 years** after the first accrual date — a non-call period of NC5.5.
- The schedule then runs to the stated maturity, roughly 43.5 years further out.
- A **two-phase** structure (§4.2): fixed coupon to the first call, then a reset off a Treasury benchmark.

A perpetual of this shape is priced and traded **to its first call date**, not to its nominal maturity, and the market convention is to assume redemption there. The stated maturity — nearly fifty years out — is a legal formality rather than an expected cash flow date. The reset that follows the first call is deliberately structured to give the issuer an incentive to call, which is why the market treats the first call as the effective maturity while acknowledging that it is not contractually guaranteed.

**Extension risk** is the corollary: if the issuer chooses not to call, the holder is left with a very long-dated instrument at a reset coupon. That risk is real and is what distinguishes this instrument from a bullet bond of the same headline yield.

## 11. Worked examples

### 11.1 Example 1 — USD corporate perpetual, 87 semi-annual calls, sell

| Field | Value |
|---|---|
| Direction | **Sell** |
| Instrument | USD corporate perpetual, subordinated |
| Market | Corporate |
| **Bond generator** | **FIX USD 6M H15T5Y** (semi-annual, five-year Treasury reset benchmark) |
| **Phase / Leg** | **1 / 2** (two coupon regimes) |
| Reference capital | 100,000,000 USD |
| First accrual date | 17 ago 2026 |
| Roll date | 17 feb 2027 |
| **Maturity** | **17 ago 2075** (effectively perpetual) |
| Coupon | **7.125000%** |
| Nominal | **1,000,000** (1,000 lots) |
| Clearing / Settlement | Named venue / **1BUSD 1DV (T+1)** |
| Payment / accrued date | 21 ago 2026 |
| Accrual fraction | **4 / 360** |
| Clean price | **100.1100** |
| Accrued coupon | **0.079167** |
| Dirty price | **100.1892** |
| Accrued amount | **791.67** |
| **Margin** | **7.099069** |
| **YTC** | **7.0991** |
| Indexed to / Assumed | 0.000000 |
| **Total amount** | **1,001,891.67** |
| **Calls / Puts / Makewholes** | **87 / 0 / 0** |

**Position:** the book sells the bond, transferring both the credit exposure and the short call position to the buyer.

**Accrued:** four days from the 17 August first accrual to the 21 August settlement — a newly issued bond. 7.125 × 4/360 = **0.079167**, giving an accrued amount of **791.67**.

**Consideration:** 1,000,000 × 100.1100% + 791.67 = **1,001,891.67** ✓

**The call schedule defines the instrument.** Eighty-seven calls in consecutive six-month windows, the first opening **exactly 5.5 years** after issue — an NC5.5 perpetual. Every call is at **par**, with accruals paid and no forfeit or fees. The schedule runs to the 2075 maturity, which is why 87 semi-annual opportunities span 43.5 years.

**Two phases and a Treasury reset.** This bond carries a second coupon phase, and its generator references a five-year Treasury benchmark. Together with the perpetual maturity and the dense call schedule, those features point to a fixed-to-reset structure: the 7.125% coupon runs to the first call, after which it resets off the benchmark. Instruments of this shape are priced to the first call date (§10.2). Note that the phase count alone would not establish this — it describes the coupon structure only, and straight bonds can be multi-phase too (§4.2).

**Price just above par** at 100.1100, with a YTC of 7.0991% marginally below the 7.125% coupon — consistent with a bond expected to be called at par.

**The Margin field** reads 7.099069, identical to the YTC. Despite the label, this is the yield measure, not a reset spread (§7.2).

### 11.2 Example 2 — EUR corporate bullet, single three-month par call, buy

| Field | Value |
|---|---|
| Direction | **Buy** |
| Instrument | EUR corporate bond |
| Market | Corporate |
| **Bond generator** | **FIX EUR 1Y LIN ACT/ACTISMA** (annual) |
| **Phase / Leg** | **1 / 1** |
| Reference capital | 100,000,000 EUR |
| First accrual date | 05 sept 2024 |
| Roll date | 05 mar 2025 |
| **Maturity** | **05 mar 2030** |
| Coupon | **3.125000%** |
| Nominal | **900,000** (900 lots) |
| Clearing / Settlement | Named venue / **2 BUSD 2DV (T+2)** |
| Payment / accrued date | 24 ago 2026 |
| Accrual fraction | **172 / 365** |
| Clean price | **99.0590** |
| Accrued coupon | **1.472603** |
| Dirty price | **100.5316** |
| Accrued amount | **13,253.42** |
| **Yield** | **3.431523** |
| **YTC** | **3.4315** |
| **Total amount** | **904,784.42** |
| **Calls / Puts / Makewholes** | **1 / 0 / 0** |

**Accrued:** the annual coupon accrues over an actual/actual period. 5 March 2026 to 5 March 2027 is 365 days, with **172** elapsed to settlement: 3.125 × 172/365 = **1.472603**, giving **13,253.42**.

**Consideration:** 900,000 × 99.0590% + 13,253.42 = **904,784.42** ✓

**A single call, three months before maturity.** The one clause runs 05 dic 2029 to 05 dic 2029 — start and end identical, so a discrete date rather than a window — at par, exactly **90 days** before the 05 mar 2030 maturity. This is the standard three-month par call (§10.1): administrative flexibility for the issuer, negligible economic value, and the reason YTC and YTM are effectively the same here.

**Trading below par** at 99.0590, with a 3.4315% yield against a 3.125% coupon. A bond at a discount is one the issuer has no incentive to call early, reinforcing that this bond will trade and behave as a bullet.

**Single-phase**, with no reset — a plain fixed-coupon corporate bond that happens to carry a near-maturity call.

### 11.3 Example 3 — USD sovereign bullet, single three-month par call, buy

| Field | Value |
|---|---|
| Direction | **Buy** |
| Instrument | **USD sovereign bond** |
| Market | **Government** |
| **Bond generator** | **FIX USD 6M 30E/360** (semi-annual, 30E/360) |
| **Phase / Leg** | **1 / 1** |
| Reference capital | 100,000,000 USD |
| First accrual date | 13 ene 2025 |
| Roll date | 13 may 2025 |
| **Maturity** | **13 may 2037** |
| Coupon | **6.875000%** |
| Nominal | **5,000,000** (5,000 lots) |
| Clearing / Settlement | Named venue / **1BUSD 1DV (T+1)** |
| Payment / accrued date | 21 ago 2026 |
| Accrual fraction | **98 / 360** |
| Clean price | **103.2100** |
| Accrued coupon | **1.871528** |
| Dirty price | **105.0815** |
| Accrued amount | **93,576.39** |
| **Yield** | **6.447332** |
| **YTC** | **6.4473** |
| **Total amount** | **5,254,076.39** |
| **Calls / Puts / Makewholes** | **1 / 0 / 0** |

**A 30E/360 accrual.** This is the one example where the accrual fraction is a **computed** rather than a calendar count: 30×(8−5) + (21−13) = **98**, against a 360-day year. Applying actual days would give a different figure. The generator states the convention explicitly, and it should be read before assuming a calendar count.

**Accrued:** (6.875 ÷ 2) × 98/180 = **1.871528** — equivalently 6.875 × 98/360, which gives the same result. Accrued amount **93,576.39**.

**Consideration:** 5,000,000 × 103.2100% + 93,576.39 = **5,254,076.39** ✓

**The same three-month par call as Example 2**, on a very different instrument: a single date of 13 feb 2037, **89 days** before the 13 may 2037 maturity, at par. Twelve years of call protection from issue, then one administrative call opportunity.

**Trading well above par** at 103.2100 — a 6.875% coupon against a 6.4473% yield. Note that even at this premium the call is not a live concern: it sits eleven years away and only three months before redemption, so the price is driven by the maturity cash flows rather than by the option.

**A sovereign issuer on a government market**, where the other two examples are corporate — showing that near-maturity par calls are not confined to corporate issuance.

### 11.4 The three examples side by side

| | Example 1 | Example 2 | Example 3 |
|---|---|---|---|
| Issuer type | Corporate (subordinated) | Corporate | **Sovereign** |
| Market | Corporate USD | Corporate EUR | **Government USD** |
| Direction | **Sell** | Buy | Buy |
| Currency | USD | EUR | USD |
| **Structure** | **Perpetual, fix-to-reset** | Bullet | Bullet |
| **Phase / Leg** | **1 / 2** | 1 / 1 | 1 / 1 |
| Bond generator | FIX USD 6M H15T5Y | FIX EUR 1Y LIN ACT/ACTISMA | **FIX USD 6M 30E/360** |
| Coupon | **7.125%** | 3.125% | **6.875%** |
| First accrual | 17 ago 2026 | 05 sept 2024 | 13 ene 2025 |
| Maturity | **17 ago 2075** | 05 mar 2030 | 13 may 2037 |
| Nominal | 1,000,000 | 900,000 | **5,000,000** |
| **Calls** | **87** | **1** | **1** |
| Puts / Makewholes | 0 / 0 | 0 / 0 | 0 / 0 |
| **Call shape** | **Six-month windows** | **Single date** | **Single date** |
| First call | 17 feb 2032 | 05 dic 2029 | 13 feb 2037 |
| **Call protection** | **5.5 years** | 5.25 years | **12.1 years** |
| Call price | 100.0000 | 100.0000 | 100.0000 |
| Call to maturity | 43.5 years | **90 days** | **89 days** |
| Call character | **Defines the instrument** | Administrative | Administrative |
| Accrual fraction | 4 / 360 | 172 / 365 | **98 / 360 (30E/360)** |
| Clean price | 100.1100 | 99.0590 | **103.2100** |
| Accrued coupon | 0.079167 | 1.472603 | 1.871528 |
| Dirty price | 100.1892 | 100.5316 | 105.0815 |
| Accrued amount | 791.67 | 13,253.42 | **93,576.39** |
| Yield field label | **Margin** | Yield | Yield |
| Yield / YTC | 7.099069 / 7.0991 | 3.431523 / 3.4315 | 6.447332 / 6.4473 |
| Price vs par | Above | **Below** | Above |
| **Total amount** | **1,001,891.67** | **904,784.42** | **5,254,076.39** |
| Settlement | **T+1** | T+2 | **T+1** |
| Notice / fees / forfeit | 0 / 0 / No | 0 / 0 / No | 0 / 0 / No |

## 12. Risk profile

A callable bond carries every risk of a straight bond, plus the consequences of the embedded option:

- **Interest rate risk with negative convexity.** As yields fall and the price approaches the call price, the bond's upside compresses because redemption becomes more likely. It does not rally like a bullet. When yields rise, it falls like one. That asymmetry is the defining risk.
- **Call risk (reinvestment risk).** If called, the holder receives par and must reinvest at prevailing rates — which, since the issuer calls when refinancing is cheap, will be lower than the coupon just lost.
- **Extension risk**, the mirror image, and the dominant risk on perpetuals (§10.2). A bond the market expects to be called at the first date may not be, leaving the holder with a much longer-dated instrument at a reset coupon.
- **Uncertain duration.** The bond's effective maturity is not fixed. Duration must be computed to the expected redemption date, and it shifts as yields move — a bond priced to call behaves like a short instrument until the market decides it will not be called, at which point its duration extends abruptly.
- **Credit risk of the issuer**, as on any bond, and with a compounding effect on callables: a deterioration in the issuer's credit both hurts the price and makes a call less likely, extending duration precisely when the holder would prefer to be repaid.
- **Reset risk** on fix-to-reset structures. The post-call coupon depends on a benchmark whose level is unknown today.
- **Yield comparability risk.** A YTC on a callable is not comparable with a YTM on a bullet (§7.2). Comparing them directly overstates the callable's attractiveness, since the callable's yield reflects compensation for the option it has sold.
- **Operational risk around call events.** A call is a lifecycle event with a notice period, a redemption price, accrued treatment and a settlement — none of which occurs on a bullet bond.

## 13. Glossary of fields seen in the Murex screens

**Trade capture**

- **Buy / Sell**: direction (§2).
- **Bond / Market / ISIN**: the security, its market and identifier.
- **Quantity / Nominal amount / LotSize**: position size and the trading unit.
- **Clearing / Settlement**: the venue and the settlement basis code.
- **Pay. conditions**: *Delivery versus payment* throughout.
- **Payment / Accrued coupon date**: settlement date and the date to which accrued is computed, with the accrual fraction beside it (§6).
- **Indexed to / Assumed**: indexation reference; present on one example and zero (§14).
- **Clean price / Accrued coupon / Dirty price / Accrued amount**: standard bond pricing (§6).
- **Yield** or **Margin**: the quoted yield measure — the same value as YTC in every example (§7.2).
- **YTC**: **yield to call**, the distinguishing field on a callable (§7.1).
- **Sales margin price / yield**, **Sales price / yield**: commercial spread and resulting client price; zero throughout.
- **Total amount**: the cash consideration (§8).

**Callable bond definition**

- **Reference capital / First accrual date / Roll date / Maturity / Coupon %**: the bond's core terms (§4).
- **Bond generator**: convention template — frequency, day count, and any reset benchmark (§4.1).
- **Issue price / More… / Special accrual convention**: additional characteristics.
- **Phase / Leg**: the number of distinct **coupon regimes** over the bond's life — one phase for a single coupon basis throughout, more where the coupon steps up, floats or resets. **Independent of callability**: straight bonds can be multi-phase and callables can be single-phase (§4.2).
- **Trigger clauses**: the button opening the call, put and makewhole schedules (§5).
- **Quick calculator**: pricing utility, not captured.

**Trigger clauses**

- **Calls / Puts / Makewholes** tabs, with counts (§5).
- **flex**: unticked on all three.
- **Date Mode**: *Business* on all three.
- **Automatic trigger clauses generation**: generates a schedule rather than requiring manual entry.
- **Effective start / end date**: the call opportunity's window; equal for a single-date call (§5.2).
- **Notice Period**: notice required before redemption; **0** throughout.
- **Repayment Type / Repayment**: how the redemption amount is set (*Price*) and its level (**100.0000** — par) throughout.
- **Maturity**: which date the bond redeems on if called (*End date*).
- **Accruals Paid / Coupon Forfeit**: whether accrued is paid and whether the coupon is lost — *Yes* and *No* throughout.
- **Penalty fee / Rental fee**: additional early-redemption amounts; zero throughout.
- **Capital mode**: the capital base the repayment applies to (*Initial*).

## 14. Open items and gaps in this document

1. **No put and no makewhole example.** Both tabs are present and read zero on all three trades. Makewholes in particular behave quite differently — redemption at a discounted present value of remaining cash flows rather than a fixed price — and would need their own treatment. A puttable bond would also reverse the direction of the optionality, putting the option in the holder's hands.
2. **Every call column is uniform across all three examples.** Notice period 0, repayment type *Price*, repayment 100.0000, accruals paid *Yes*, coupon forfeit *No*, fees zero, capital mode *Initial*. The behaviour of a **non-zero notice period**, a **declining call price schedule**, **coupon forfeit** or **penalty fees** is therefore documented from column headers alone, not from observed behaviour.
3. **The Margin label on Example 1 is not fully explained** (§7.2). The value equals the YTC, so it is not a reset spread — but why the label differs on a two-phase bond should be confirmed.
4. **The reset mechanics of the fix-to-reset perpetual are not captured** (§4.2). The generator references a Treasury benchmark and the bond has two phases, but the second phase's spread, reset frequency and first reset date sit behind the *More…* link, which was not captured. For an instrument whose call economics depend on the reset, this is a material gap.
5. **The `Indexed to / Assumed` field appears on one example only** and is zero there. Its purpose and when it applies are not documented.
6. **No flow schedule captured.** The coupon schedule, the redemption flow and — critically — how a call event is represented in the flows are not visible from static screens.
7. **Yield-to-worst is not shown.** The screen displays a single YTC. On Example 1, with 87 call dates, which call the YTC refers to (presumably the first) and whether a yield-to-worst is computed elsewhere should be confirmed.
8. **No called bond example.** All three are live. How a call event is processed — notice, redemption, accrued settlement and position closure — is described conceptually here but not documented from a real event.
