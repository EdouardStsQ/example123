# Bond Lending and Borrowing

## Purpose of this document

This is a reference document on bond lending and borrowing: what the product is, how the security and fees legs work, how the fee accrues on a nominal that can be re-indexed daily to the bond price, how partial returns are handled, and how the terms are represented in Murex. It is meant to be read on its own — a new joiner or anyone unfamiliar with the product should come away understanding the mechanics, not just recognizing the trade capture screen.

Because bond lending and bond repos look extremely similar on screen and are easily confused, **§11 is a dedicated comparison** setting out where they differ and why.

The three worked examples in §12 are a **fee-bearing borrow of a EUR corporate bond** with daily fee indexation, partial returns and a full flow schedule; a **zero-fee borrow of a GBP index-linked gilt** booked as a collateral operation; and a **lend of a USD Treasury bill**. Between them they cover both directions, fee-bearing and zero-fee trades, three price notations, three templates and both fee-nominal conventions.

**A note on identifiers.** Portfolio, counterparty and security identifiers are omitted throughout. Each example is described by the characteristics that matter economically — currency, instrument type, structure.

## 1. Overview: what bond lending and borrowing is

A bond lending or borrowing transaction is the **transfer of a security from one party to another for a period, against a fee**, with an obligation to return equivalent securities at the end.

The trade has two legs:

- **The security leg** — the bond, delivered out at the start and returned at the end.
- **The fees leg** — the lending fee, accruing on the value of the securities on loan.

Three features define the product as configured here:

- **The securities move free of payment.** `Payment Conditions: Free of payment` on all three examples, with `Cash exchange: No` on every template. The bond is delivered without a simultaneous cash payment against it. This is the single clearest marker distinguishing these trades from repos (§11).
- **The consideration is a fee, not interest on cash.** The fees leg carries a rate — 15 basis points on the fee-bearing example — applied to the value of the securities, not to a cash principal.
- **Collateral is handled outside the trade.** `Treat collateral: On pool level` and `Collateral representation: Bilateral` on all three templates. The security movement is booked here; the collateral securing it is managed at pool level under the governing agreement, not as a leg of this trade.

`Purpose: Security driven` on all three templates — these trades exist to move a specific bond, which is the defining motivation of the securities lending market.

## 2. Direction: lend and borrow

The security leg's **Payout** field states the direction, and the sign of the security nominal follows it:

| | Borrow | Lend |
|---|---|---|
| Payout | **Borrow** | **Lend** |
| Security | Received | Delivered out |
| Security Nominal sign | **Positive** | **Negative** |
| Fee | **Paid** | **Received** |
| Fees leg flows | Negative (outflow) | Positive (inflow) |
| Motivation | Obtain a specific bond — cover a short, meet a delivery | Earn a return on an otherwise idle holding |

Examples 1 and 2 are **Borrow** with positive security nominals. Example 3 is **Lend**, and its security nominal is **−69,902,000.00** — negative because the bond is going out.

## 3. The security leg

### 3.1 Quantity, amount and unit denomination

The **Quantity / Amount** pair shows the number of units and the resulting face value, and **the unit denomination differs by security**:

| Example | Quantity | Amount | Implied unit |
|---|---|---|---|
| 1 | 2,000 | 2,000,000 | **1,000** |
| 2 | 193,000,000 | 1,930,000 | **0.01** |
| 3 | 700,000 | 70,000,000 | **100** |

Three securities, three denominations spanning five orders of magnitude. **Reading the quantity field without checking which of the two boxes is the face value will misstate the size dramatically** — Example 2's quantity of 193 million is a nominal of 1.93 million, while Example 3's quantity of 700 thousand is a nominal of 70 million.

**Current Quantity** shows what remains on loan after any partial returns (§6).

### 3.2 Price: clean, accrued, dirty — and three notations

For a conventional coupon bond, **Dirty = Clean + Accrued**, and Example 1 ties exactly: accrued of 3.125% × 168/365 = 1.438356 against a clean price of 99.0384 gives **100.476756**, displayed as 100.4768.

The accrual basis follows the security's market, and all three differ:

| Example | Accrual basis | Convention |
|---|---|---|
| 1 | 168 / 365 | Annual coupon, ACT/365 |
| 2 | 90 / 184 | **Semi-annual coupon, ACT/ACT** — accrued = (coupon ÷ 2) × 90/184 |
| 3 | 350 / 360 | **Zero coupon** — accrued is 0.0000 |

Example 2's accrued of **0.152853** is (0.625 ÷ 2) × 90/184 — the half-yearly coupon accrued across an actual 184-day period, the standard gilt convention. Applying the annual coupon directly would double it.

Example 3 is a **discount instrument**: no coupon, so accrued is zero and clean equals dirty.

Price notation also varies:

- **Decimal percentage** — Examples 1 and 2 (100.4768, 295.1364).
- **Thirty-seconds** — Example 3 shows **99:27+**, the US Treasury convention: 99 plus 27½ thirty-seconds, the `+` denoting the half. That is 99.859375 in decimal, though the price actually applied is 99.86 (§12.3).

### 3.3 Capital factor: two different meanings

Where a security's outstanding principal is not simply its original face, a **Capital Factor** scales the price:

**Dirty Price = (Clean + Accrued) × Capital Factor**

The field serves two economically opposite purposes depending on the instrument:

- **Below 1 — a pool factor.** An amortizing security has repaid part of its principal, so only a fraction remains outstanding.
- **Above 1 — an index ratio.** An inflation-linked bond has been uplifted by accrued indexation, so the claim exceeds original face.

Example 2 is the second case. The capital factor of **1.9581** is an index ratio, and it reconciles exactly:

(150.5700 + 0.152853) × 1.95814 = **295.1364** — the dirty price shown.

The adjusted amount alongside the factor — 1,930,000 × 1.95814 = **3,779,210.20** — is the index-uplifted nominal actually being lent.

A dirty price nearly double the clean price is therefore not an error; it is inflation uplift. Equally, a dirty price far below the clean price on an amortizing bond reflects principal already repaid. **The clean-plus-accrued check does not apply to either without first applying the factor.**

### 3.4 Security nominal and haircut

**Security Nominal = Adjusted face × Dirty Price**, and the haircut then applies:

- Example 1: 2,000,000 × 100.476756% = **2,009,535.90**
- Example 2: 3,779,210.20 × 150.722853% = **5,696,133.44**
- Example 3: 70,000,000 × 99.86% = **−69,902,000.00** (negative for the lend)

All three carry a haircut of **100.00 under the `x` mode**, which multiplies rather than reduces, so **Security Nominal Post Haircut equals Security Nominal** on every example. As elsewhere, the mode indicator determines the formula and the number alone is not interpretable.

### 3.5 Income during the loan

The **Income Period** spans the trade, with an **Income flows** link on the security leg.

Coupons paid while a bond is on loan belong economically to the lender, not the borrower holding it, so they are passed back — conventionally as a **manufactured payment**. The template's **Income/Tax credit** configuration governs this and any withholding treatment. It was not captured on any example (§15), and for a lending book it is material.

## 4. The fees leg

### 4.1 The fee

The fees leg carries a **Rate** — the lending fee, quoted as an annual percentage of the value on loan:

| Example | Rate | Convention |
|---|---|---|
| 1 | **0.1500%** (15bp) | LIN ACT/360 |
| 2 | **0.0000%** | LIN ACT/365 |
| 3 | **0.0000%** | LIN ACT/360 |

Fifteen basis points on roughly 2 million over 18 days is about **151 EUR**. That order of magnitude is the point: a borrow fee compensates for lending the security, and it is a different kind of number from a funding rate (§11).

**Zero-fee trades are not anomalies.** Examples 2 and 3 both carry a rate of 0.0000 with `Interest: 0.00`. Example 2's template is explicitly described as a generator for collateral operations, so the security movement is a **collateral transfer** rather than a fee-earning loan. The same product structure serves both purposes, and the fee rate is what distinguishes them.

On the zero-fee examples, **End Nominal is the Start Nominal with the sign reversed** — 5,696,133.44 against −5,696,133.44, and −699,020.00 against 699,020.00. With no interest to add, the closing entry simply unwinds the opening one.

### 4.2 Fee nominal: initial price or marked to market

The template field **Fees nominal based on** determines whether the fee base is fixed or floating, and the examples show both:

| Value | Behaviour | Example |
|---|---|---|
| **Marked to market** | The fee nominal is **re-indexed to the bond price**, with `Indexed ✔` and an indexations list attached. | Example 1 |
| **Initial price** | The fee nominal is fixed off the price at inception; `Indexed` is unticked. | Examples 2 and 3 |

This is the most consequential setting on the trade. Under the marked-to-market convention the amount the fee accrues on moves every day with the bond; under the initial-price convention it does not.

### 4.3 The indexation mechanism

Where indexation is enabled, the **outstanding capital is indexed to the bond price**, and the flow schedule (§10) shows the mechanism working day by day:

**Outstanding capital = Face on loan × that day's indexation price**
**Daily fee = Outstanding capital × Rate × 1 / 360**

Every row of Example 1's schedule reconciles on this rule:

| Face on loan | Indexation price | Outstanding capital | Daily fee |
|---|---|---|---|
| 2,000,000 | 100.47679500 | 2,009,535.90 | −8.37 |
| 2,000,000 | 100.58616438 | 2,011,723.29 | −8.38 |
| 1,100,000 | 100.76734666 | 1,108,440.81 | −4.62 |
| 700,000 | 100.52109589 | 703,647.67 | −2.93 |

That last figure is also the `Current Nominal` on the trade screen, so the static field and the flow schedule are the same calculation viewed from two angles.

**Weekend handling:** the schedule carries the Friday price through Saturday and Sunday. Each of the repeated prices in Example 1's schedule is dated to a Friday, with the following two rows reusing it.

### 4.4 Payment timing and billing

- **Payment** is configured **Up front** on one template and **In arrears** on the other two.
- **Settlement process: Billing** on all three, against a repo's `Trade`.

The flow schedule shows what billing means in practice: fees **accrue daily** but **settle periodically**. In Example 1 the daily accruals from 21 August to 1 September all carry a payment date of **2 September**, and those from 2 to 7 September carry **2 October** — monthly billing. Rows tied to partial-return events settle on the date of the event itself.

## 5. Haircut

The haircut field appears on both legs and, as elsewhere in the system, carries a **mode indicator**:

| Mode | Formula | Where seen |
|---|---|---|
| **`x`** | Nominal × haircut % | Security leg, all three (100.00 → no reduction) |
| **`1 / (1 +/- x)`** | Divisor form | Fees leg, Examples 2 and 3 (0.00 → no effect) |

None of the three examples applies an effective haircut. Note that the security leg and the fees leg can carry **different modes on the same trade** — Examples 2 and 3 use `x` on one and `1 / (1 +/- x)` on the other.

## 6. Partial returns and re-marking

Borrowed securities are frequently returned in tranches rather than all at once, and Example 1 shows this clearly.

The original quantity of 2,000 units falls to a **Current Quantity of 700**, and the flow schedule records the returns as **AMO** entries on the security leg: −900 units, then −400, then a final −700 at maturity. The three sum to the original 2,000.

The consequence for the fee is that the base moves for **two independent reasons**:

- **Quantity returned** — each partial return reduces the face on loan.
- **Price re-marked** — the daily indexation changes the value of what remains.

The flow schedule separates them cleanly: quantity steps down at discrete events while the indexation price changes daily. Both feed the same outstanding-capital calculation (§4.3).

## 7. Open maturity and the number of days

All three examples read **Maturity: Open** with a current date and a **Number of days** — 18, 18 and 19 respectively, each matching the calendar difference between start and the date shown.

An open loan has no contractual end date. It continues until either party terminates — the lender recalling the security or the borrower returning it — with the fee accruing throughout. `Early Settlement: Yes` on all three templates confirms that returns before any nominal end date are normal behaviour, which is exactly what Example 1's partial returns demonstrate.

## 8. Settlement

- **`Payment Conditions: Free of payment`** on all three. The security is delivered without simultaneous payment against it.
- **`Cash exchange: No`** on every template — no cash principal moves in either direction.
- **`Security exchange: Yes`** — the security genuinely transfers.
- **Clearing Center** is populated and differs across the examples.
- **`Collateral representation: Bilateral`** and **`Treat collateral: On pool level`** — collateral securing the loan is managed outside this trade, at pool level.

The combination of *security exchange yes, cash exchange no, free of payment* is the structural signature of a securities loan.

## 9. Templates

Three templates appear, and their differences are substantive:

| Field | Template A (Ex. 1) | Template B (Ex. 2) | Template C (Ex. 3) |
|---|---|---|---|
| Description | Fixed generator | **Fixed generator for collateral operations** | Fixed generator |
| Evaluation | Accrual | Accrual | Accrual |
| Settlement delay | Inherited from currency | **Inherited from security** | Inherited from currency |
| Accrual delay | Redefined, +1 DAY | Redefined, +1 DAY | Redefined, +1 DAY |
| Flows projection delay | +1 open day | +1 open day | +1 open day |
| Purpose | Security driven | Security driven | Security driven |
| Treat collateral | On pool level | On pool level | On pool level |
| Collateral representation | Bilateral | Bilateral | Bilateral |
| Early settlement | Yes | Yes | Yes |
| Settlement model | Theoretical interest | Theoretical interest | Theoretical interest |
| Haircut applies on | Nominal | Nominal | Nominal |
| **Settlement process** | **Billing** | **Billing** | **Billing** |
| *Security tab* | | | |
| Start delay | +2 OPEN DAYS | +2 OPEN DAYS | +2 OPEN DAYS |
| Payment calendar | **TARGET** | **LONDON** | **NEW YORK** |
| Security exchange | Yes | Yes | Yes |
| *Fees tab* | | | |
| **Fees nominal based on** | **Marked to market** | **Initial price** | **Initial price** |
| **Indexed** | **✔ (indexations list)** | Unticked | Unticked |
| Multicurrency indexation | **Floating Indexation** | — | — |
| Rate convention | LIN ACT/360 | **LIN ACT/365** | LIN ACT/360 |
| Rate | Fixed | Fixed | Fixed |
| **Cash exchange** | **No** | **No** | **No** |
| Fees based on | Dirty Price | Dirty Price | Dirty Price |
| End nominal based on | Start nominal + Interests | Start nominal + Interests | Start nominal + Interests |
| **Payment** | **Up front** | **In arrears** | **In arrears** |
| Stub period position | Up front | Up front | Up front |
| First prices inherited | from trade (customized) | — | — |
| Roundings | None | None | None |

The two settings that change behaviour rather than plumbing are **Fees nominal based on** (§4.2) and the **rate convention**, which differs between ACT/360 and ACT/365 across otherwise similar templates.

## 10. Flow schedules

Example 1's global flow schedule is the clearest artefact in this document. The `Lg` column identifies the leg — 1 security, 2 fees.

**Security leg (Leg 1)** carries flows **denominated in the bond itself**:

| Flow type | Sub-type | Flow | Meaning |
|---|---|---|---|
| PRI | INI | **+2,000** | Securities received at the start |
| AMO | | **−900** | First partial return |
| PRI / AMO | | **−400** | Second partial return |
| PRI | FIN | **−700** | Final return |

The four net to zero: everything borrowed is returned.

**Fees leg (Leg 2)** carries one **INT** row per day, each with:

- **Start / End Date** — a single day (`Nb of Days` = 1).
- **Remaining Capital / Quantity / Amount Capital** — the outstanding position.
- **Fee/Rate** — 0.15000 throughout, with `Sales Margin` 0.
- **Outstanding capital indexations: Date and Price** — the indexation date and the bond price applied that day (§4.3).
- **Haircut Rate and Haircut Formula** — carried into every row.
- **Payment Date** — batched to the billing date (§4.4).
- **Flow** — negative, because this example is a borrow and the fee is paid.

Italic dates and prices denote estimated or projected values rather than fixed ones.

## 11. How bond lending differs from bond repos

The two products look nearly identical on screen — a security leg beside a second leg, a haircut, an open or term maturity, a rate. They are economically different transactions, and the following table is the fastest way to tell them apart.

| | **Bond repo** | **Bond lending / borrowing** |
|---|---|---|
| **Economic substance** | Secured **cash lending**: sale with an agreement to repurchase | **Security lending** against a fee, with collateral held separately |
| **What the trade is really for** | Either funding (GC) or obtaining a specific bond (specials) | Obtaining a specific bond, or moving collateral |
| **Second leg** | **Cash** | **Fees** |
| **Payment Conditions** | **Delivery versus payment** | **Free of payment** |
| **Cash exchange (template)** | **Yes** | **No** |
| **Does cash principal move?** | **Yes** — advanced at the start, repaid at the end | **No** — only a fee is billed |
| **The rate** | **Repo rate** — interest on the cash, at money-market levels (3.88%, ESTR + 18bp in the repo examples) | **Lending fee** — basis points on the value of the securities (15bp; often zero on collateral movements) |
| **Rate applied to** | The cash advanced | The value of the securities on loan |
| **Nominal basis** | `Cash nominal based on: Initial price` | `Fees nominal based on:` **Initial price or Marked to market** |
| **Daily re-indexation of the base** | No — the cash nominal is fixed; price moves trigger **margin** instead | **Yes, where configured** — outstanding capital re-indexed to the bond price daily |
| **Haircut function** | Sizes the cash advanced against collateral value — real protection for the cash lender | Present as a field, but not applied on any of these examples |
| **Interest / End Nominal** | Interest accrues on cash; End Nominal = repurchase amount | Zero-fee trades show End Nominal as the sign-flipped Start Nominal; there is no repurchase |
| **Settlement process** | **Trade** | **Billing** |
| **When consideration settles** | Interest paid with the repurchase at maturity | Fees accrue daily and are **billed periodically**, typically monthly |
| **Collateral** | The security **is** the collateral for the cash | Collateral is separate, managed **on pool level** under the governing agreement |
| **Direction wording** | Borrow / Lend on the collateral leg, with cash sign showing the side | **Lend / Borrow** on the security leg, with the security nominal signed accordingly |
| **Partial unwinds** | Permitted (early settlement) | **Routine** — partial returns appear as AMO events in the flows |

**The three fastest checks** to tell which product you are looking at:

1. **Payment Conditions** — *Delivery versus payment* means repo; *Free of payment* means lending.
2. **The second leg's name** — *Cash* means repo; *Fees* means lending.
3. **The size of the rate** — a money-market rate means repo; a handful of basis points, or zero, means lending.

**Where they genuinely converge.** Both are security-driven in these examples, both use the same haircut field and mode indicators, both share the capital-factor mechanics for amortizing and index-linked collateral, both support open maturities with a running day count, and both apply the same clean/accrued/dirty pricing to the security. The security-leg screens are close to interchangeable; it is the second leg that tells them apart.

**A note on economics.** A repo and a securities loan against cash collateral can be economically near-equivalent — in both cases one party ends up with the bond and the other with cash, for a period, at a price. The distinction that matters operationally is how the transaction is *represented*: a repo prices the cash and treats the security as collateral, while a securities loan prices the security and handles the collateral elsewhere. That difference drives the settlement mechanism, the accrual basis and the accounting path, which is why the two are booked as different products rather than one.

## 12. Worked examples

### 12.1 Example 1 — EUR corporate bond, borrow at 15bp, with indexation and partial returns

| Field | Value |
|---|---|
| Template | Fixed generator, marked-to-market fees |
| Security | EUR corporate bond, 3.125% coupon |
| Start | 20 ago 2026 |
| **Maturity** | **Open** (date shown 07 sept 2026) |
| Number of days | **18** |
| Quantity / Amount | 2,000 / **2,000,000.00** |
| **Current Quantity** | **700** |
| **Payout** | **Borrow** |
| Clean / Accrued / Dirty | 99.0384 / **1.4384** (168/365) / **100.4768** |
| Yield | 3.437314% |
| Security Nominal | **2,009,535.90** |
| Haircut | 100.00, mode `x` → post-haircut unchanged |
| Fees currency | EUR |
| Start Nominal | **2,009,535.90** |
| **Current Nominal** | **703,647.67** |
| **Rate** | **0.1500%** (15bp), fixed |
| Rate convention | LIN ACT/360 |
| Current Price | 100.5211 |
| Payment conditions | **Free of payment** |

**Position:** the book borrows the bond and pays a 15 basis point fee on its value.

**Pricing reconciles:** accrued of 3.125% × 168/365 = 1.438356 against a clean price of 99.0384 gives a dirty price of 100.476756, and the security nominal follows from it.

**Two things reduce the fee base**, and both are visible: 1,300 of the original 2,000 units have been returned, and the price has been re-marked from 100.4768 to 100.5211. The current fee nominal reconciles exactly on the remaining position — 700,000 × 100.5211% = **703,647.67**.

**The indexation mechanism** is documented in §4.3 and §10. This is the only example with `Fees nominal based on: Marked to market` and `Indexed ✔`, and its flow schedule reconciles on every row.

**Billing** is monthly, with event-driven settlements on the partial-return dates (§4.4).

### 12.2 Example 2 — GBP index-linked gilt, zero-fee collateral operation

| Field | Value |
|---|---|
| Template | Fixed generator **for collateral operations** |
| Security | GBP index-linked gilt, 0.625% coupon |
| Start | 20 ago 2026 |
| **Maturity** | **Open** (date shown 07 sept 2026) |
| Number of days | **18** |
| Quantity / Amount | 193,000,000 / **1,930,000.00** (unit 0.01) |
| Current Quantity | 193,000,000 (no returns) |
| **Payout** | **Borrow** |
| Clean Price | 150.5700 |
| Accrued Coupon | **0.1529** (90/184) |
| **Yield** | **−1.993629%** |
| **Capital Factor** | **1.9581** → index-adjusted nominal **3,779,210.20** |
| **Dirty Price** | **295.1364** |
| Security Nominal | **5,696,133.44** |
| Haircut (security) | 100.00, mode `x` |
| Fees currency | GBP |
| Start Nominal | **5,696,133.44** |
| **End Nominal** | **−5,696,133.44** |
| **Interest** | **0.00** |
| Haircut (fees) | 0.00, mode `1 / (1 +/- x)` |
| **Rate** | **0.0000%** |
| Rate convention | **LIN ACT/365** |
| Payment conditions | Free of payment |

**Position:** a zero-fee borrow — a collateral movement rather than a fee-earning loan, as the template's description makes explicit.

**The capital factor is an index ratio, not a pool factor.** At 1.9581 it uplifts the price rather than reducing it:

(150.5700 + 0.152853) × 1.95814 = **295.1364** ✓

and the index-adjusted nominal of 3,779,210.20 × 150.722853% = **5,696,133.44** ✓ — both exact.

**The accrued follows the gilt convention**: (0.625 ÷ 2) × 90/184 = **0.152853**, a half-yearly coupon over an actual 184-day period.

**The negative yield of −1.993629% is not an error** — it is the real yield on an inflation-linked bond, and negative real yields are normal for that instrument class.

**No indexation.** This template sets `Fees nominal based on: Initial price` with `Indexed` unticked, so the fee base would be fixed at inception even if a fee were charged. With a zero rate, `Interest` is 0.00 and `End Nominal` is simply the start nominal sign-reversed.

**Convention differences** from Example 1: ACT/365 rather than ACT/360, payment in arrears rather than up front, a LONDON calendar, and settlement delay inherited from the security rather than the currency.

### 12.3 Example 3 — USD Treasury bill, lend

| Field | Value |
|---|---|
| Template | Fixed generator |
| Security | USD Treasury bill (zero coupon) |
| Start | 20 ago 2026 |
| **Maturity** | **Open** (date shown 08 sept 2026) |
| Number of days | **19** |
| Quantity / Amount | 700,000 / **70,000,000.00** (unit 100) |
| Current Quantity | 700,000 |
| **Payout** | **Lend** |
| **Clean / Dirty Price** | **99:27+** (thirty-seconds) |
| Accrued Coupon | **0.0000** (350/360) |
| Yield | 3.6682% |
| **Security Nominal** | **−69,902,000.00** |
| Haircut (security) | 100.00, mode `x` |
| Fees currency | USD |
| **Start Nominal** | **−699,020.00** |
| End Nominal | 699,020.00 |
| Interest | 0.00 |
| Haircut (fees) | 0.00, mode `1 / (1 +/- x)` |
| **Rate** | **0.0000%** |
| Rate convention | LIN ACT/360 |
| **Current Price** | **0.9986** |
| Payment conditions | Free of payment |

**Position:** the only **lend** in the set — the book delivers the bill out, which is why the security nominal is negative.

**A discount instrument.** A Treasury bill pays no coupon, so accrued is 0.0000 and clean equals dirty. The 3.6682% yield is the return implied by the discount to par, not a coupon.

**Thirty-seconds notation.** The price reads **99:27+** — 99 plus 27½ thirty-seconds, which is 99.859375 in decimal. The price actually applied is **99.86**: 70,000,000 × 99.86% = **69,902,000.00**, matching the security nominal exactly.

**A scale discrepancy between the two legs.** The `Current Price` field reads **0.9986** — a decimal fraction, where Examples 1 and 2 show percentage-form prices (100.5211, 295.1364). The two legs then interpret it differently:

- Security leg: 70,000,000 × 0.9986 = **69,902,000.00**
- Fees leg: 70,000,000 × 0.9986 / 100 = **699,020.00**

The fee nominal is therefore **exactly 1/100 of the security nominal** on the same trade. Because the fee rate is zero, this has no cash consequence here — but on a fee-bearing trade with this price convention it would understate the fee by a factor of 100. This should be confirmed (§15).

**Two portfolio fields** appear on the deal entry, where the other two examples show one.

### 12.4 The three examples side by side

| | Example 1 | Example 2 | Example 3 |
|---|---|---|---|
| Security | EUR corporate bond | **GBP index-linked gilt** | **USD Treasury bill** |
| Currency | EUR | GBP | USD |
| **Direction** | **Borrow** | **Borrow** | **Lend** |
| Security Nominal sign | Positive | Positive | **Negative** |
| Maturity | Open | Open | Open |
| Days | 18 | 18 | 19 |
| Quantity / Amount | 2,000 / 2,000,000 | 193,000,000 / 1,930,000 | 700,000 / 70,000,000 |
| Unit denomination | 1,000 | **0.01** | **100** |
| Price notation | Decimal % | Decimal % | **32nds (99:27+)** |
| Clean / Accrued / Dirty | 99.0384 / 1.4384 / 100.4768 | 150.5700 / 0.1529 / **295.1364** | 99:27+ / **0.0000** / 99:27+ |
| Accrual basis | 168/365 | **90/184 (semi-annual)** | 350/360 (zero coupon) |
| **Capital factor** | — | **1.9581 (index ratio)** | — |
| Yield | 3.437314% | **−1.993629%** | 3.6682% |
| Security Nominal | 2,009,535.90 | 5,696,133.44 | **−69,902,000.00** |
| **Fee rate** | **0.1500% (15bp)** | **0.0000%** | **0.0000%** |
| **Fees nominal based on** | **Marked to market** | Initial price | Initial price |
| **Indexed** | **✔** | Unticked | Unticked |
| Rate convention | LIN ACT/360 | **LIN ACT/365** | LIN ACT/360 |
| Payment | **Up front** | In arrears | In arrears |
| Calendar | TARGET | LONDON | NEW YORK |
| **Partial returns** | **Yes — 2,000 → 700** | No | No |
| Fees nominal vs security nominal | Equal | Equal | **1/100 (§12.3)** |
| Payment conditions | Free of payment | Free of payment | Free of payment |
| Flows captured | **Yes** | No | No |

## 13. Risk profile

- **Counterparty credit risk.** The lender is exposed to the borrower failing to return the securities. This is mitigated by collateral, but that collateral sits **outside the trade** (§8) — so the exposure visible on this screen is not the whole picture, and the pool-level collateral position must be read alongside it.
- **Collateral adequacy and re-marking.** Because collateral is managed at pool level, protection depends on the pool being marked and margined correctly. A loan that looks unsecured on the trade screen may be fully covered at pool level, or may not be.
- **Security price risk.** The value of what is on loan moves daily. Where the fee nominal is indexed (§4.2), the fee follows it; where it is fixed at initial price, fee and exposure diverge over time.
- **Recall and return risk.** An open loan can be recalled by the lender or returned by the borrower at any time. A borrower relying on the security to cover a short faces recall risk; a lender faces the fee stream ending without notice.
- **Corporate action and income risk.** Coupons must be manufactured back to the lender, with withholding handled correctly (§3.5). Other corporate events on the security also need handling while it is away from its owner.
- **Settlement risk from free-of-payment delivery.** Because the security moves without simultaneous payment, there is no delivery-versus-payment protection at the moment of transfer. This is the structural cost of the FOP mechanism and is why the collateral arrangement matters so much.
- **Amortization and indexation risk on factored securities.** A pool factor falls and an index ratio rises over time, so the value on loan changes independently of price (§3.3).
- **Operational risk on partial returns.** Returns in tranches change the fee base at discrete events (§6), and each must be reflected correctly in both the security position and the fee accrual.

## 14. Glossary of fields seen in the Murex screens

**Financial definition**

- **Template**: the configuration template supplying both legs' structural settings (§9).
- **Bond / Market / ISIN**: the security, its pricing source and identifier.
- **Start / Maturity / Maturity structure**: the loan's dates; maturity reads **Open** on all three examples (§7).
- **Number of days**: days in the current period.
- **Triangulation**: *Nominal* on all three.

**Deal information**

- **Clearing Center**: the venue or arrangement through which the trade settles.
- **Payment Conditions**: **Free of payment** on all three — the defining marker versus repo (§8, §11).

**Security leg**

- **Quantity / Amount** and **Current Quantity**: units, face value and what remains on loan after returns (§3.1, §6).
- **Payout**: **Lend** or **Borrow** (§2).
- **Archiving Group / Cutoff**: the pricing group and cutoff basis.
- **Clean Price / Accrued Coupon / Dirty Price / Yield**: the security's valuation, with the accrual day-count fraction beside the accrued figure (§3.2).
- **Capital Factor**: the scaling factor — a pool factor below 1 or an index ratio above 1 — with the adjusted nominal alongside (§3.3).
- **Security Nominal / Security Nominal Post Haircut**: the value on loan, before and after the haircut (§3.4).
- **Haircut** and its **mode indicator** (§5).
- **Income Period** and the **Income flows** link: the window over which security income arises (§3.5).
- **Reset price**: the link through which the security is re-marked.

**Fees leg**

- **Start Nominal / Current Nominal / End Nominal**: the fee base at inception, currently, and at close (§4.1).
- **Interest**: fee accrued; 0.00 on the zero-fee examples.
- **Rate type / Rate**: fixed or floating, and the fee rate itself (§4.1).
- **Rate convention**: the day count — ACT/360 or ACT/365 across the examples.
- **Haircut / Haircut Amount** and mode indicator (§5).
- **Current Price**: the security price at the current mark — note the scale caution in §12.3.

**Template**

- **Evaluation / Accrual delay / Flows projection delay / Settlement delay**: valuation basis and timing offsets.
- **Purpose**: *Security driven* on all three (§1).
- **Treat collateral / Collateral representation**: how collateral is managed and represented (§8).
- **Early Settlement**: whether returns before maturity are permitted (§7).
- **Settlement model / Settlement process**: *Theoretical interest* and **Billing** (§4.4).
- **Haircut applies on**: the base to which the haircut is applied (*Nominal*).
- **Security exchange / Cash exchange**: **Yes** and **No** respectively, throughout (§8).
- **Fees nominal based on**: *Initial price* or *Marked to market* — the key behavioural setting (§4.2).
- **Indexed / Indexations list / Multicurrency Indexation**: the daily re-indexation of outstanding capital to the bond price (§4.3).
- **Fees based on**: *Dirty Price* — the price basis for the fee calculation.
- **End nominal based on**: how the closing nominal is derived.
- **Payment / Stub period position**: fee settlement timing and stub placement.
- **First prices inherited**: where initial prices come from.
- **Income/Tax credit**: manufactured payment and withholding configuration, not captured (§15).

**Flow schedule**

- **Lg**: the leg — 1 security, 2 fees.
- **Flow Tp / Sub. Tp**: *PRI* principal, *INT* interest/fee, *AMO* amortization (partial return); *INI* opening, *FIN* closing.
- **Remaining Capital / Quantity / Amount Capital**: the outstanding position driving the accrual.
- **Fee/Rate / Sales Margin**: the fee rate and any sales margin.
- **Outstanding capital indexations — Date and Price**: the indexation date and bond price applied to that day's accrual (§4.3).
- **Nb of Days**: days in the row — 1 on every fee row, since accrual is daily.
- **Haircut Rate / Haircut Formula**: the haircut carried into the flows.
- **Payment Date**: the billing date to which the accrual settles (§4.4).

## 15. Open items and gaps in this document

1. **The fees-leg nominal is 1/100 of the security nominal on Example 3** (§12.3). The `Current Price` is stored as a decimal fraction (0.9986) rather than in percentage form, and the two legs interpret it differently. With a zero fee rate this has no cash consequence, but on a fee-bearing trade with the same price convention the fee would be understated by a factor of 100. This should be confirmed as the highest-priority item here.
2. **The Income/Tax credit configuration was not captured** on any example (§3.5). This governs manufactured coupon payments and their withholding treatment — material for any lending book, and especially so where securities are lent across jurisdictions.
3. **The Indexations list screen was not captured** (§4.3). The mechanism is documented from the template flags and from observed flow behaviour, both of which agree, but the list itself would confirm exactly what drives the indexation.
4. **No floating-rate fee example.** All three templates offer fixed or floating and all three trades are fixed. A floating-fee trade would exercise the fixing, margin and rate-factor fields that sit unused here.
5. **No flow schedule for a zero-fee or lend trade.** The captured schedule is for the fee-bearing borrow. A lend-side schedule would confirm the sign conventions, and a zero-fee schedule would show how a collateral movement appears in the flows.
6. **The relationship between these trades and the pool-level collateral is not documented** (§8, §13). The trade screen shows the security movement; the collateral securing it is elsewhere. How the two are linked, marked and margined is essential to understanding the actual exposure and is not visible here.
7. **Two portfolio fields appear on Example 3** where the others show one. Whether this indicates a give-up, an internal transfer or something else is not determinable from the capture.
8. **The `End nominal based on: Start nominal + Interests` setting is untested** on these examples, since two carry zero interest and the third does not display an End Nominal. A fee-bearing trade run to close would confirm the behaviour.
