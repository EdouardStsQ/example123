# Bond Deals

## Purpose of this document

This is a reference document on outright cash bond trades: what the product is, how the bond's own definition drives the calculation, how clean price, accrued interest and yield combine into the consideration actually settled, and how the terms are represented in Murex. It is meant to be read on its own — a new joiner or anyone unfamiliar with the product should come away understanding the mechanics, not just recognizing the trade capture screen.

The four worked examples in §11 are two **zero-coupon sovereign bills**, a **semi-annual government bond** and an **annual corporate covered bond**. That spread is deliberate: zero-coupon and coupon-bearing instruments build their consideration differently and price off different yield conventions, while the two coupon bonds differ again in frequency, day-count basis and market.

**Scope.** This document covers straight (bullet) bonds. **Callable bonds are documented separately** and their embedded optionality is not addressed here.

**A note on identifiers.** Portfolio, counterparty and security identifiers are omitted throughout. Each example is described by the characteristics that matter economically — currency, instrument type, coupon, maturity.

## 1. Overview: what a bond deal is

A bond deal is the **outright purchase or sale of a debt security** for cash, settling on a standard market date. There is no derivative element: the buyer pays a consideration and receives the bond, together with all rights to its future coupons and its redemption.

Three things determine the trade economically:

- **Which bond** — identified on the trade and defined in full behind it (§3).
- **How much** — a nominal amount, constrained by the security's lot size and minimum increment (§5).
- **At what price** — quoted either as a price or as a yield, with the other derived from it (§6, §7).

Everything else on the screen — settlement basis, calendars, accrual conventions — is inherited from the security's own definition and its market.

## 2. Direction

The **Buy / Sell** selector sets the direction:

| | Buy | Sell |
|---|---|---|
| Bond | Received | Delivered |
| Cash | **Paid** — the Total amount | **Received** |
| Position | Long the bond | Short, or reducing a holding |
| Accrued interest | **Paid** to the seller | **Received** from the buyer |

All four examples are **Buy**.

The accrued interest point is worth stating explicitly: the buyer compensates the seller for interest earned but not yet paid, because the buyer will receive the whole of the next coupon (§7.2).

## 3. The bond definition

Behind the trade sits the security's own definition, which supplies the terms the trade calculation depends on.

| Field | Meaning |
|---|---|
| **Reference capital** | The bond's total issue size — 100,000,000 on all four examples. Not the trade size. |
| **Bond generator** | The convention template for the instrument: coupon frequency, day count and rate type. |
| **First accrual date** | The date from which interest begins to accrue — for a new issue, its dated date. |
| **Roll date** | The anchor for the coupon schedule, present on coupon-bearing bonds. |
| **Maturity** | Redemption date. |
| **Coupon %** | The annual coupon rate; **0.000000** on a zero-coupon instrument. |
| **Issue price** | The price at issue. |
| **Additional features / Special accrual convention / Strippable / Issuance asset swap / Tera convention** | Flags for non-standard characteristics. |

### 3.1 The bond generator determines how the instrument behaves

Three generators appear, and they describe fundamentally different instruments:

| Generator | Instrument | Implication |
|---|---|---|
| **FIX EUR ZC ACT/360** | Zero coupon, ACT/360 | No coupon, no accrued; price derived by **simple money-market discounting** (§7.3) |
| **EUR 6M A** | **Semi-annual** coupon | Each period carries **half** the annual coupon, accruing on an actual/actual basis |
| **FIX EUR 1Y ACT/ACT** | **Annual** coupon, ACT/ACT | Each period carries the **full** annual coupon over a 365- or 366-day period |

Reading the generator first tells you which set of rules applies to everything else on the screen — and in particular whether the accrued calculation divides the coupon or not (§7.2).

### 3.2 Roll date and the coupon schedule

A **Roll date** anchors the coupon payment schedule where one is needed. In Example 3 the roll date of 1 March, with a semi-annual generator, produces coupon dates of **1 March and 1 September** each year — which the accrual fraction on the trade confirms directly (§7.2).

Not every coupon bond shows one. Example 4, an annual bond, carries **no roll date**: with a single coupon a year, the maturity date is sufficient to fix the schedule (25 May in that case). Zero-coupon bills have no roll date either, since there is no schedule to anchor.

## 4. Market information

A second screen behind the security holds its trading and settlement characteristics:

| Field | Meaning |
|---|---|
| **Market / Trading clauses** | The market the bond trades on and the standard clauses applying to it. |
| **Quotation** | The price quotation convention (**STD** on all four). |
| **Settlement** | The standard settlement basis for the instrument — a coded convention such as `2BSD2DV` with a venue suffix. |
| **Lot size / Nominal** | The trading unit and its nominal value — 1,000 on all four, though the paired nominal box varies. |
| **Minimum piece / Minimum increment** | The smallest tradable holding and the increment above it. |
| **First settlement date** | The security's first settlement, typically its issue settlement. |
| **Amortizing type** | *Nominal* on three examples, blank on the corporate bond — where set, the bond redeems at nominal rather than amortizing. |
| **Cut-off** | The pricing group and cutoff basis (*FIXING*). |

Two things vary across the examples and are worth checking on any new security:

- **Market and trading clauses follow the issuer type.** The three sovereign examples sit on a government market with government clauses; the corporate covered bond in Example 4 sits on a **corporate market with corporate clauses**, and its cut-off group differs accordingly. The clause set governs the standard terms applying to the trade.
- **Minimum piece and minimum increment are inconsistent** — 1,000 on both bills and on the corporate bond, but **0.00** on the semi-annual government bond. Similarly, **amortizing type** reads *Nominal* on three examples and is **blank** on the corporate one. Both look like static-data gaps rather than deliberate settings (§14).

## 5. Quantity, nominal and lot size

The trade carries a **Quantity / Nominal amount** pair alongside a **LotSize**. The nominal amount is what drives every calculation on the screen; the quantity expresses the same position in lots.

| Example | Nominal amount | Lot size | Lots |
|---|---|---|---|
| 1 | 8,000,000 | 1,000 | 8,000 |
| 2 | 50,000 | 1,000 | 50 |
| 3 | 284,000,000 | 1,000 | 284,000 |
| 4 | 1,800,000 | 1,000 | 1,800 |

The two display boxes are not formatted consistently across screens — one uses thousands separators the other does not, and decimal places vary. **Take the nominal amount as authoritative** and cross-check it against the Total amount rather than reading the quantity box literally.

## 6. Price, accrued and dirty price

Three price fields appear, and the relationship between them is the core of bond pricing:

**Dirty price = Clean price + Accrued coupon**

- **Clean price** — the quoted price, excluding interest accrued since the last coupon. This is what the market quotes and what traders talk about.
- **Accrued coupon** — interest earned by the seller but not yet paid, expressed as a percentage of nominal.
- **Dirty price** — what the buyer actually pays per unit of nominal.

On a **zero-coupon** instrument there is no coupon to accrue, so accrued is zero and **clean equals dirty**. Both bills show identical clean and dirty prices; the coupon bond does not.

## 7. Accrued interest

### 7.1 The accrual fraction

Beside the payment date the screen shows an accrual fraction — the days accrued over the days in the period. Its meaning depends on the instrument:

| Example | Fraction | Basis | Meaning |
|---|---|---|---|
| 1 | **164 / 360** | ACT/360 | Days since the bond's first accrual date |
| 2 | **17 / 360** | ACT/360 | Days since the bond's first accrual date |
| 3 | **176 / 184** | ACT/ACT, semi-annual | Days into the **current coupon period** |
| 4 | **91 / 365** | ACT/ACT, annual | Days into the **current coupon period** |

On the bills the denominator is the year basis and the numerator counts from the first accrual date — 13 March to 24 August is 164 days, 7 August to 24 August is 17. The fraction is populated even though the accrued amount is zero, because the **coupon rate** is zero, not because no time has elapsed.

On the coupon bonds the fraction is a genuine coupon-period measure, and the denominator reveals the frequency at a glance:

- Example 3 (semi-annual): 1 March to 1 September 2026 is **184 days**, and 1 March to the 24 August settlement is **176**.
- Example 4 (annual): 25 May 2026 to 25 May 2027 is **365 days**, and 25 May to 24 August is **91**.

A denominator near 182–184 signals a semi-annual bond; one near 365–366 signals an annual one.

### 7.2 Computing accrued on a coupon bond

**Accrued = (Annual coupon ÷ Coupon frequency) × Days accrued ÷ Days in period**

The frequency divisor is where the two coupon bonds part company:

**Example 3 — semi-annual**, so each period carries half the annual coupon:

(4.75 ÷ 2) × 176 ÷ 184 = **2.2717391**, displayed as 2.2717

Dirty price: 103.3720 + 2.271739 = **105.643739**, displayed 105.6437. Accrued amount: 284,000,000 × 2.27174% = **6,451,741.60** ✓

**Example 4 — annual**, so the full coupon applies with no division:

1.75 × 91 ÷ 365 = **0.43630137**, displayed as 0.436301

Dirty price: 99.2700 + 0.436301 = **99.706301**, displayed 99.7063. Accrued amount: 1,800,000 × 0.43630137% = **7,853.42** ✓

**Getting the divisor wrong is the classic error.** Applying the annual coupon directly to a semi-annual bond doubles the accrued; dividing an annual bond's coupon by two halves it. The generator (§3.1) and the accrual denominator (§7.1) both tell you which applies, and they should agree.

Note also that the two bonds display accrued to different precision — four decimals on one, six on the other — while the underlying calculation uses full precision in both cases (§8).

### 7.3 Yield: two different conventions

The **Yield** field means something different depending on the instrument, and the two are not comparable.

**Zero-coupon bills — simple money-market discounting:**

**Price = 100 ÷ (1 + Yield × Days to maturity ÷ 360)**

- Example 1: 100 ÷ (1 + 2.589% × 200/360) = **98.5820614**
- Example 2: 100 ÷ (1 + 2.7279% × 347/360) = **97.4379732**

Both reproduce the displayed prices and, more importantly, both reproduce the Total amounts exactly (§8).

**Coupon bonds — yield to maturity:**

The yield is the internal rate of return that discounts all remaining coupons and the redemption to the dirty price. It is a compound measure, solved iteratively rather than by a closed formula, and it is **not** comparable with a money-market yield on a bill even at the same maturity.

Example 3 shows a yield of 3.040570% against a 4.75% coupon and a clean price of 103.3720 — the bond trades above par precisely because its coupon exceeds the market yield.

### 7.4 Sales margin and sales price

Beneath the price sit **Sales margin price / yield** and **Sales price / yield**. The sales margin is a commercial spread applied to the traded level, and the sales price is the resulting client-facing price.

On all four examples the margin is **0.0000** and the sales price equals the traded price. The mechanism is therefore documented from configuration only, not from behaviour (§14).

## 8. The consideration: how the Total amount is built

This is where the two instrument types diverge, and where the most common reconciliation error arises.

### 8.1 Coupon bonds: clean consideration plus accrued, separately

**Total = (Nominal × Clean price ÷ 100) + Accrued amount**

Both coupon bonds reconcile exactly on this rule:

| | Example 3 | Example 4 |
|---|---|---|
| Clean consideration | 284,000,000 × 103.3720% = **293,576,480.00** | 1,800,000 × 99.2700% = **1,786,860.00** |
| Accrued amount | **6,451,741.60** | **7,853.42** |
| **Total** | **300,028,221.60** ✓ | **1,794,713.42** ✓ |

**The dirty price will not reliably reproduce this.** On Example 3, 284,000,000 × 105.6437% = 300,028,108.00 — **€113.60 short**. The two components are computed and rounded separately, and the displayed dirty price is a rounded presentation of their sum rather than an input to the calculation.

The error scales with ticket size and with how much the rounding bites: on Example 4's 1.8 million nominal the same shortcut is only two cents out, which is precisely why it is dangerous — the method looks sound on small trades and breaks on large ones.

### 8.2 Zero-coupon bills: nominal times price, at full precision

**Total = Nominal × Price ÷ 100**, with the price taken at full precision rather than as displayed.

- Example 1: 8,000,000 × 98.5820614% = **7,886,564.91** ✓
- Example 2: 50,000 × 97.4379732% = **48,718.99** ✓

**The displayed price will not reproduce these either.** Using 98.5821 gives 7,886,568.00 — **€3.09 too much**. Using 97.4380 gives 48,719.00, a cent out. The screen rounds the price to four decimals; the calculation uses the full precision implied by the yield.

### 8.3 The practical rule

**Never reconcile a bond consideration from the displayed price.** For a coupon bond, rebuild it as clean consideration plus accrued amount. For a zero-coupon instrument, rebuild the price from the yield first. The discrepancies are small in percentage terms but scale with ticket size — on Example 3's 284 million nominal, a naive dirty-price calculation is out by over a hundred euros, while the same shortcut on Example 4 is out by two cents.

## 9. Settlement

- **`Pay. conditions: Delivery versus payment`** on all four — the bond and the cash move simultaneously, so neither party is exposed at the moment of settlement.
- **Settlement basis** is `2 BUSD 2DV` on the trade, matching the security's `2BSD2DV` convention: **T+2**. Example 1's settlement date of Monday 24 August implies a Thursday 20 August trade date.
- **Clearing / Settlement** names the venue. Two examples carry a named venue; the third reads **UNKNOWN** (§14).
- The security-level settlement code carries a **venue suffix** that differs between examples on the same T+2 basis, which matters for settlement routing.
- **Payment / Accrued coupon date** is the settlement date, and it is the date to which accrued interest is calculated.

## 10. What the Total amount does and does not include

The Total amount is the **cash consideration** — clean value plus accrued interest. It does not include fees, commissions or taxes, which would appear separately. The **Additional flows** checkbox is unticked on all four examples, so no supplementary flows are attached (§14).

## 11. Worked examples

### 11.1 Example 1 — EUR sovereign zero-coupon bill, buy

| Field | Value |
|---|---|
| Direction | **Buy** |
| Instrument | EUR sovereign zero-coupon bill |
| Bond generator | **FIX EUR ZC ACT/360** |
| Reference capital | 100,000,000 EUR |
| First accrual date | 13 mar 2026 |
| Maturity | **12 mar 2027** |
| **Coupon %** | **0.000000** |
| Nominal amount | **8,000,000** (8,000 lots of 1,000) |
| Clearing / Settlement | Named venue / **2 BUSD 2DV** |
| Payment conditions | Delivery versus payment |
| Payment / accrued date | 24 ago 2026 |
| Accrual fraction | **164 / 360** |
| **Clean price** | **98.5821** |
| **Dirty price** | **98.5821** (equal — no coupon) |
| Accrued coupon / amount | 0.0000 / 0.00 |
| **Yield** | **2.589000%** |
| Sales margin | 0.0000 |
| **Total amount** | **7,886,564.91** |

**A discount instrument.** With a zero coupon there is nothing to accrue, so clean equals dirty and the accrued amount is zero. The return comes entirely from buying below par and redeeming at 100.

**Priced from the yield.** 200 days run from the 24 August settlement to the 12 March 2027 maturity, and on the ACT/360 basis of the generator:

100 ÷ (1 + 2.589% × 200/360) = **98.5820614**

**Total:** 8,000,000 × 98.5820614% = **7,886,564.91** ✓ exactly.

Using the displayed 98.5821 instead would give 7,886,568.00 — **€3.09 too much** (§8.2).

**The 164/360 fraction** counts from the bond's first accrual date of 13 March to the 24 August settlement. It is populated despite the zero accrued amount, because the coupon rate rather than the elapsed time is what makes the accrual nil.

### 11.2 Example 2 — EUR sovereign zero-coupon bill, buy (small ticket, different venue)

| Field | Value |
|---|---|
| Direction | **Buy** |
| Instrument | EUR sovereign zero-coupon bill |
| Bond generator | **FIX EUR ZC ACT/360** |
| Reference capital | 100,000,000 EUR |
| First accrual date | 07 ago 2026 |
| Maturity | **06 ago 2027** |
| **Coupon %** | **0.000000** |
| Nominal amount | **50,000** (50 lots of 1,000) |
| Clearing / Settlement | Different named venue / **2 BUSD 2DV** |
| Payment conditions | Delivery versus payment |
| Payment / accrued date | 24 ago 2026 |
| Accrual fraction | **17 / 360** |
| Clean / Dirty price | **97.4380** / **97.4380** |
| Accrued coupon / amount | 0.000000 / 0.00 |
| **Yield** | **2.727900%** |
| **Total amount** | **48,718.99** |

**The same mechanics at a very different scale.** Structurally identical to Example 1 — same generator, same market, same lot size, same settlement basis — but 160 times smaller and with a much longer remaining life.

**Priced from the yield:** 347 days to maturity, so

100 ÷ (1 + 2.7279% × 347/360) = **97.4379732**

**Total:** 50,000 × 97.4379732% = **48,718.99** ✓ exactly. The displayed 97.4380 would give 48,719.00 — one cent out, the same rounding effect as Example 1 but negligible at this size.

**Only 17 days since first accrual**, against 164 on Example 1 — this bill was issued a fortnight before the trade, while the other was already five months into its life.

**A different clearing venue and settlement suffix**, on the same T+2 basis. Settlement routing differs even where the timing convention does not.

**Yield comparison:** 2.7279% over 347 days against 2.589% over 200 days — about 14 basis points more for 147 additional days. Consistent with an upward-sloping short-end curve, though as different sovereign issuers there is a credit component in the difference too.

### 11.3 Example 3 — EUR government coupon bond, buy

| Field | Value |
|---|---|
| Direction | **Buy** |
| Instrument | EUR government bond, **4.75% coupon**, Sept 2028 maturity |
| **Bond generator** | **EUR 6M A** (semi-annual) |
| Reference capital | 100,000,000 EUR |
| First accrual date | 22 ene 2013 |
| **Roll date** | **01 mar 2013** |
| Maturity | **01 sept 2028** |
| **Coupon %** | **4.750000** |
| Nominal amount | **284,000,000** (284,000 lots of 1,000) |
| Clearing / Settlement | **UNKNOWN** / 2 BUSD 2DV |
| Payment conditions | Delivery versus payment |
| Payment / accrued date | 24 ago 2026 |
| **Accrual fraction** | **176 / 184** |
| **Clean price** | **103.3720** |
| **Accrued coupon** | **2.2717** |
| **Dirty price** | **105.6437** |
| **Accrued amount** | **6,451,741.60** |
| **Yield** | **3.040570%** |
| Sales margin | 0.0000 |
| **Total amount** | **300,028,221.60** |

**The instrument that exercises the full pricing machinery.** Unlike the two bills, this bond pays a coupon, so accrued interest is real, clean and dirty prices differ, and the consideration has two components.

**The coupon schedule comes from the roll date.** A 1 March roll date on a semi-annual generator gives coupons on **1 March and 1 September**. The trade confirms it: 1 March to 1 September 2026 is **184 days**, and 1 March to the 24 August settlement is **176** — exactly the fraction shown.

**Accrued:**

(4.75 ÷ 2) × 176/184 = **2.2717391**, displayed 2.2717

and applied to the nominal: 284,000,000 × 2.27174% = **6,451,741.60** ✓

**Dirty price:** 103.3720 + 2.271739 = **105.643739**, displayed 105.6437 ✓

**Total consideration — built from two components:**

| Component | Calculation | Amount |
|---|---|---|
| Clean consideration | 284,000,000 × 103.3720% | **293,576,480.00** |
| Accrued interest | 284,000,000 × 2.27174% | **6,451,741.60** |
| **Total** | | **300,028,221.60** ✓ |

**And the dirty price does not reproduce it**: 284,000,000 × 105.6437% = 300,028,108.00, **€113.60 short**. On a ticket this size that is the difference between a reconciliation that breaks and one that does not (§8.1).

**Trading above par.** A clean price of 103.3720 against a par redemption reflects a 4.75% coupon well above the 3.040570% market yield. The buyer pays a premium now and recovers it through above-market coupons.

**A note on the yield.** This is a yield to maturity — a compound internal rate of return over roughly two remaining years — and it is not comparable with the money-market yields quoted on the two bills, even though the same field holds both.

**Static data gaps:** the clearing venue reads **UNKNOWN**, and the minimum piece and increment are **0.00** where both bills carry 1,000 (§14).

### 11.4 Example 4 — EUR corporate covered bond, annual coupon, buy

| Field | Value |
|---|---|
| Direction | **Buy** |
| Instrument | **EUR corporate covered bond**, 1.75% coupon, May 2027 maturity |
| **Market / Trading clauses** | **Corporate market / corporate clauses** |
| **Bond generator** | **FIX EUR 1Y ACT/ACT** (annual) |
| Reference capital | 100,000,000 EUR |
| First accrual date | 25 ago 2022 |
| Roll date | **(none)** |
| Maturity | **25 may 2027** |
| **Coupon %** | **1.750000** |
| Nominal amount | **1,800,000** (1,800 lots of 1,000) |
| Clearing / Settlement | Named venue / 2 BUSD 2DV |
| Payment conditions | Delivery versus payment |
| Payment / accrued date | 24 ago 2026 |
| **Accrual fraction** | **91 / 365** |
| **Clean price** | **99.2700** |
| **Accrued coupon** | **0.436301** |
| **Dirty price** | **99.7063** |
| **Accrued amount** | **7,853.42** |
| **Yield** | **2.739716%** |
| Sales margin | 0.0000 |
| **Total amount** | **1,794,713.42** |

**The first non-sovereign example.** This bond sits on a **corporate market with corporate trading clauses** and its own cut-off group, where the other three sit on the government market. The clause set governs the standard terms of the trade, so this is a substantive distinction rather than a label.

**An annual coupon, and no roll date.** The generator is annual actual/actual, so — unlike the semi-annual bond in Example 3 — **the full coupon applies with no division by frequency**:

1.75 × 91 ÷ 365 = **0.43630137**, displayed 0.436301

The coupon period runs 25 May 2026 to 25 May 2027, exactly **365 days**, with **91** elapsed to the 24 August settlement. With one coupon a year, the maturity date fixes the schedule and no roll date is needed (§3.2).

**Dirty price:** 99.2700 + 0.436301 = **99.706301**, displayed 99.7063 ✓

**Total consideration:**

| Component | Calculation | Amount |
|---|---|---|
| Clean consideration | 1,800,000 × 99.2700% | **1,786,860.00** |
| Accrued interest | 1,800,000 × 0.43630137% | **7,853.42** |
| **Total** | | **1,794,713.42** ✓ |

**Trading below par — the mirror of Example 3.** A clean price of 99.2700 against a 1.75% coupon and a 2.739716% yield: the coupon sits *below* the market yield, so the bond trades at a discount. Example 3's 4.75% coupon against a 3.04% yield put it at a premium. Same relationship, opposite sign, and the clearest illustration in the set of why coupon and yield must be read together.

**Static data:** **amortizing type is blank** here where the other three read *Nominal*, and the nominal box beside lot size reads 0.00 rather than 1.00 (§14).

### 11.5 The four examples side by side

| | Example 1 | Example 2 | Example 3 | Example 4 |
|---|---|---|---|---|
| Instrument | Zero-coupon bill | Zero-coupon bill | **Coupon bond** | **Coupon bond** |
| Issuer type | Sovereign | Sovereign | Sovereign | **Corporate (covered)** |
| **Market / clauses** | Government | Government | Government | **Corporate** |
| **Bond generator** | FIX EUR ZC ACT/360 | FIX EUR ZC ACT/360 | **EUR 6M A** | **FIX EUR 1Y ACT/ACT** |
| **Coupon frequency** | — | — | **Semi-annual** | **Annual** |
| **Coupon %** | 0.000000 | 0.000000 | **4.750000** | **1.750000** |
| Roll date | — | — | **01 mar 2013** | **(none)** |
| Maturity | 12 mar 2027 | 06 ago 2027 | 01 sept 2028 | 25 may 2027 |
| Direction | Buy | Buy | Buy | Buy |
| Nominal | 8,000,000 | **50,000** | **284,000,000** | 1,800,000 |
| Lots | 8,000 | 50 | 284,000 | 1,800 |
| **Accrual fraction** | 164 / 360 | 17 / 360 | **176 / 184** | **91 / 365** |
| Accrual basis | ACT/360 from first accrual | ACT/360 from first accrual | ACT/ACT semi-annual | **ACT/ACT annual** |
| **Coupon divisor** | — | — | **÷ 2** | **÷ 1** |
| Clean price | 98.5821 | 97.4380 | **103.3720** | **99.2700** |
| Accrued coupon | 0.0000 | 0.000000 | **2.2717** | **0.436301** |
| Dirty price | 98.5821 | 97.4380 | **105.6437** | **99.7063** |
| Clean = dirty? | **Yes** | **Yes** | No | No |
| Accrued amount | 0.00 | 0.00 | **6,451,741.60** | **7,853.42** |
| Yield | 2.589000% | 2.727900% | 3.040570% | 2.739716% |
| **Yield convention** | Simple, money market | Simple, money market | **Yield to maturity** | **Yield to maturity** |
| **Price vs par** | Below | Below | **Above** (coupon > yield) | **Below** (coupon < yield) |
| Sales margin | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| **Total amount** | **7,886,564.91** | **48,718.99** | **300,028,221.60** | **1,794,713.42** |
| **Total built as** | Nominal × price (full precision) | Nominal × price (full precision) | **Clean + accrued** | **Clean + accrued** |
| Dirty-price shortcut error | +€3.09 | +€0.01 | **−€113.60** | −€0.02 |
| Settlement | T+2 DVP | T+2 DVP | T+2 DVP | T+2 DVP |
| Clearing venue | Named | Named (different) | **UNKNOWN** | Named |
| Min piece / increment | 1,000 / 1,000 | 1,000 / 1,000 | **0.00 / 0.00** | 1,000 / 1,000 |
| Amortizing type | Nominal | Nominal | Nominal | **(blank)** |

## 12. Risk profile

An outright bond position is a **funded, linear** exposure — the cash is paid up front and the return depends on the bond's price and its coupons:

- **Interest rate risk.** The dominant exposure. Price moves inversely with yield, and the sensitivity grows with maturity. The coupon bond in Example 3 has roughly two years to run; a longer bond on the same notional would carry several times the exposure.
- **Credit risk of the issuer.** Sovereign on three examples and corporate on the fourth. The spread between issuers is why two bills of similar tenor trade at different yields, and why the corporate covered bond yields more than a government bond of comparable maturity.
- **Funding cost.** Unlike a derivative, an outright purchase is funded. The position must be financed — often through repo — and the carry is the difference between the bond's yield and the funding rate.
- **Reinvestment risk** on coupons received, for coupon-bearing bonds.
- **Liquidity risk.** The ability to exit depends on the specific issue. Lot size and minimum increment constrain how a position can be broken up.
- **Settlement risk**, largely addressed by delivery versus payment (§9).
- **Accrued interest and ex-date risk.** Buying close to a coupon date means paying substantial accrued interest; the treatment around ex-dividend dates and record dates must be right or the coupon lands on the wrong side.
- **Rounding and reconciliation risk.** Not a market risk but a real operational one: as §8 shows, rebuilding the consideration incorrectly produces breaks that are small proportionally but material in absolute terms on large tickets.

## 13. Glossary of fields seen in the Murex screens

**Trade capture**

- **Buy / Sell**: direction (§2).
- **Internal deal**: flags a trade between internal books.
- **Bond**: the security traded, with its market, ISIN and description alongside.
- **Quantity / Nominal amount**: the position in lots and in nominal; the nominal drives the calculation (§5).
- **LotSize**: the security's trading unit.
- **Clearing / Settlement**: the clearing venue and the settlement basis code (§9).
- **Pay. conditions**: *Delivery versus payment* on all four.
- **Payment / Accrued coupon date**: the settlement date and the date to which accrued is computed, with the accrual fraction beside it (§7.1).
- **Clean price / Dirty price**: price excluding and including accrued (§6).
- **Accrued coupon / Accrued amount**: accrued as a percentage of nominal, and in cash (§7.2).
- **Yield**: money-market yield on a bill, yield to maturity on a coupon bond (§7.3).
- **Sales margin price / yield** and **Sales price / yield**: commercial spread and the resulting client price (§7.4).
- **Currency**: the settlement currency.
- **Additional flows**: supplementary flows attached to the trade — unticked throughout.
- **Total amount**: the cash consideration (§8).
- **Risk section**: analytical grouping; unpopulated on all four.

**Bond definition**

- **Reference capital**: the issue size, not the trade size.
- **Bond generator**: the instrument's convention template — coupon frequency, day count, rate type (§3.1).
- **First accrual date**: when interest begins to accrue.
- **Roll date**: the anchor for the coupon schedule (§3.2).
- **Maturity / Coupon % / Issue price**: redemption date, annual coupon rate, price at issue.
- **Additional features / Special accrual convention / Strippable / Issuance asset swap / Tera convention**: flags for non-standard characteristics.
- **Phase / Leg**: the number of distinct **coupon regimes** over the bond's life — 1/1 on all four examples here, meaning a single coupon basis throughout. A straight bond can carry **more than one phase** where its coupon changes basis part-way through (a step-up, or a fixed period followed by a floating one), so a phase count above one does not by itself imply anything unusual about the instrument.

**Market information**

- **Market / Trading clauses / Quotation**: where and how the security trades.
- **Settlement**: the standard settlement convention with its venue suffix.
- **Lot size / Nominal / Minimum piece / Minimum increment**: trading unit and size constraints (§4).
- **First settlement date**: the security's first settlement.
- **Amortizing type**: *Nominal* — redeems at nominal rather than amortizing.
- **Settlement rounding rule**: unpopulated on all four.
- **Cut-off**: the pricing group and cutoff basis (*FIXING*).

## 14. Open items and gaps in this document

1. **Clearing venue reads UNKNOWN on the semi-annual government bond** (§11.3), where the other three carry a named venue. Settlement routing depends on it, so this looks like a static-data gap rather than a deliberate setting.
2. **Minimum piece and minimum increment are 0.00 on the semi-annual government bond** and 1,000 on the other three (§4), and **amortizing type is blank on the corporate bond** where the others read *Nominal*. Confirm whether either is deliberate or whether the fields are simply unpopulated.
3. **Sales margin is zero on all four examples** (§7.4). The mechanism — how a margin adjusts the sales price and whether it affects the consideration — is therefore documented from field names alone. A trade with a non-zero margin would close this.
4. **No sell example.** All four are buys. The mechanics are symmetric, but a sell would confirm the direction of the accrued payment and the sign conventions.
5. **No flow schedule captured.** The coupon schedule, the redemption flow and the accrued treatment across a coupon date would all be visible there, and none of it can be shown from static screens.
6. **The Additional flows mechanism is unused** on all four (§10), so fees, commissions and taxes are not documented.
7. **No non-EUR example.** All four settle in EUR. A bond in another currency would exercise day-count and settlement conventions these four share — a US Treasury on a 30/360 or ACT/ACT basis, or a gilt, would each behave differently.
8. **The Quick Calculator and Collateral haircut tabs on the bond definition were not captured**, nor the User definable fields. The collateral haircut in particular links this security to the repo and lending products.
9. **Display formatting of the quantity/nominal pair is inconsistent** across screens (§5). Not an economic issue, but a reading hazard worth noting.
