# Bond Repos

## Purpose of this document

This is a reference document on bond repurchase agreements: what the product is, how the collateral and cash legs work, how haircuts and amortizing collateral are handled, how re-marking adjusts the cash leg during the life of the trade, and how the terms are represented in Murex. It is meant to be read on its own — a new joiner or anyone unfamiliar with the product should come away understanding the mechanics, not just recognizing the trade capture screen.

The three worked examples in §12 are a **fixed-rate open repo on a USD corporate bond**, a **floating-rate term repo on a EUR government bond** with its flow schedule, and a **floating-rate term repo on an amortizing EUR asset-backed floater** that has been re-marked since inception. Between them they cover fixed and floating rates, open and term maturities, haircut and no haircut, straightforward and factor-adjusted collateral, and both the initial and the re-marked state of the cash leg.

**A note on identifiers.** Portfolio, counterparty and security identifiers are omitted throughout. Each example is described by the characteristics that matter economically — currency, collateral type, structure.

## 1. Overview: what a repo is

A repurchase agreement is the **simultaneous sale of a security and an agreement to repurchase it** at a fixed future date and price. Economically it is **secured cash lending**: one party gets cash, the other gets collateral, and the difference between the sale and repurchase prices is the interest.

The trade has two legs:

- **The collateral leg** — the security, delivered at the start and returned at maturity.
- **The cash leg** — the money, advanced at the start and repaid with interest at maturity.

Three features distinguish a repo from the return-swap family:

- **Both legs are actually exchanged.** `Payment Conditions: Delivery versus payment` on all three examples, with `Security exchange: Yes` and `Cash exchange: Yes` on the templates. The security genuinely moves, against simultaneous payment. Nothing here is a reference or a notional.
- **The cash amount is derived from the collateral's market value**, not agreed independently — and reduced by a haircut (§6).
- **The position is re-marked during its life.** As the collateral's price moves, the cash leg is adjusted to keep the exposure covered (§8).

## 2. Direction: repo and reverse repo

The collateral leg's **Payout** field states the direction from the security's point of view:

| | Repo | Reverse repo |
|---|---|---|
| Collateral leg Payout | Lend (security out) | **Borrow** (security in) |
| Cash | **Received** at start | **Paid out** at start |
| Cash leg Start Nominal sign | Positive | **Negative** |
| Economic position | Borrowing cash against collateral | **Lending cash, taking collateral** |
| Exposure | To the cash lender | **To the collateral, and to the counterparty returning cash** |
| Also called | Repo, sell/buy-back | Reverse repo, security borrowing |

All three examples read **`Payout: Borrow`** with a **negative cash Start Nominal** — reverse repos. The book advances cash and takes the bond as collateral.

The sign convention is worth internalising: cash out at the start is negative, cash back at maturity is positive, and the End Nominal exceeds the Start Nominal by the interest earned.

## 3. Why repos are done

Two motivations, and the template records which applies:

- **Cash driven** — the trade is a funding transaction. One side needs cash and pledges whatever eligible collateral it holds. This is *general collateral* (GC) repo, where the specific bond is largely interchangeable.
- **Security driven** — the trade is done to obtain a **particular** bond, typically to cover a short or meet a delivery. This is the *specials* market, where a bond in demand is financed at a rate below GC, because the party wanting the security compensates by lending cash cheaply.

All three examples set **`Purpose: Security driven`** — these are specials trades, done for the collateral rather than for the funding. That is the single most useful line on the template for understanding why a repo exists.

## 4. The collateral leg

### 4.1 Bond pricing

| Field | Meaning |
|---|---|
| **Quantity / Amount** | The number of units and the face value of collateral delivered. |
| **Current Quantity** | The quantity currently outstanding on the trade, which differs from the original after a partial unwind. |
| **Clean Price** | Price excluding accrued interest. |
| **Accrued Coupon** | Interest accrued since the last coupon, with its day-count fraction shown alongside. |
| **Yield** | The yield implied by the price. |
| **Dirty Price** | The price actually used to value the collateral. |
| **Capital Factor** | The proportion of original principal still outstanding on an amortizing security (§4.2). |
| **Security Nominal** | The collateral's market value: face × dirty price. |
| **Security Nominal Post Haircut** | That value less the haircut (§6) — the amount of cash it supports. |

For a conventional bullet bond, **Dirty = Clean + Accrued**, and both examples where that applies tie exactly:

- Example 1: 97.4400 + 1.1000 = **98.5400** ✓ (the accrued itself being 4.125% × 96/360 = 1.10)
- Example 2: 113.3360 + 0.409589 = **113.745589** ✓ (5.75% × 26/365 = 0.409589)

### 4.2 Amortizing collateral and the capital factor

Example 3 breaks that rule, and the reason is the **Capital Factor**.

An amortizing security — an asset-backed note, a mortgage pool, an amortizing covered bond — repays principal over its life. The **capital factor** (or pool factor) is the fraction of original principal still outstanding. Here it reads **0.3526**, meaning roughly 35% of the original notional remains.

The price is then scaled by that factor:

**Dirty Price = Clean Price × Capital Factor**

97.5997 × 0.3526233 = **34.4159**, matching the screen exactly. So a dirty price of 34.42 against a clean price of 97.60 does **not** mean the bond is distressed — it means only 35% of the principal is still outstanding, and the price has been factor-adjusted to reflect the actual claim.

Two consequences follow:

- **The clean-plus-accrued check does not apply** to factored collateral. Anyone applying it mechanically will conclude the screen is wrong.
- **The displayed yield becomes unreliable.** Example 3 shows a yield of **48.826753%**, which is not a credible bond yield. It appears to be computed from the factor-adjusted price against a par redemption, without accounting for the fact that only a fraction of principal remains. Treat the yield field on amortizing collateral with caution (§15).

The field alongside the capital factor shows the **current outstanding face** — face × factor — which is the amount actually being financed.

### 4.3 Income during the repo

The **Income Period** runs the length of the trade, and an **Income flows** link sits at the bottom of the collateral leg.

If the collateral pays a coupon while it is on repo, the economic benefit belongs to the party that gave the collateral, not the one holding it — so the coupon is passed back, conventionally as a **manufactured payment**. The template's **Income/Tax credit** configuration governs how this is handled, including any withholding treatment. It was not captured on any of the three examples (§15), and for a repo book it is a material piece of configuration.

## 5. The cash leg

| Field | Meaning |
|---|---|
| **Start Nominal** | Cash advanced at the start — negative on a reverse repo. Equals the post-haircut collateral value. |
| **Interest** | The repo interest over the period. |
| **End Nominal** | The repurchase amount. |
| **Current Nominal** | The cash amount as currently marked (§8). |
| **Haircut / Haircut Amount / Current Haircut Amount** | The collateral reduction, at inception and as currently marked (§6). |
| **Rate type / Rate or Index + Margin** | Fixed or floating repo rate (§5.2). |
| **Rate convention** | The day count — LIN ACT/360 on all three. |
| **Current Price** | The collateral's price at the current mark. |

### 5.1 The interest calculation

**Interest = Cash nominal × Rate × Days / 360**, and **End Nominal = Nominal + Interest**.

Example 1 reconciles perfectly end to end:

1,872,260.00 × 3.88% × 18/360 = **3,632.18**, and 1,872,260.00 + 3,632.18 = **1,875,892.18** ✓

The `Number of days` field on the Financial definition states the period explicitly — 18, 184 and 147 across the three examples, each matching the calendar difference between start and maturity.

### 5.2 Fixed and floating repo rates

| Example | Rate type | Rate / Index + Margin |
|---|---|---|
| 1 | **Fixed** | 3.8800% |
| 2 | **Floating** | EUR ESTR AVG + 0.1800% |
| 3 | **Floating** | EURIBOR3M + 0.5000% |

On a floating repo the cash leg carries an index, a **Margin** and a **Rate factor** (1.000000 on both floating examples), with `Margin mode: Additive`. The flow schedule makes the combination explicit through a **Convert Rate** column:

**Convert Rate = Rate + Net Margin** — in Example 2, 2.18940 + 0.1800 = **2.36940**.

Note that the two floating templates differ on fixing timing: **In arrears** on one, **Up front** on the other (§10).

## 6. The haircut

### 6.1 What it does

The haircut is the margin of protection for the **cash lender**. Rather than advancing the full market value of the collateral, the lender advances less, so that a fall in the collateral's price does not immediately leave the loan under-secured.

**Cash advanced = Security Nominal − Haircut Amount**

The template records **`Haircut applies on: Nominal`** on all three.

### 6.2 Modes

As elsewhere in the system, the haircut field carries a **mode indicator** that determines the formula, and the number alone is not interpretable:

| Mode | Formula | Examples |
|---|---|---|
| **`1 +/- x`** | Haircut Amount = Security Nominal × x; cash = nominal − amount | Examples 1 and 3 (x = 5.00) |
| **`1 / (1 +/- x)`** | Divisor form | Example 2 (x = 0.00 → no effect) |

### 6.3 Worked reconciliations

**Example 1** — 5% haircut on a USD corporate bond:

- Security Nominal = 2,000,000 × 98.54% = **1,970,800.00**
- Haircut Amount = 1,970,800.00 × 5% = **98,540.00**
- Post-haircut = 1,970,800.00 − 98,540.00 = **1,872,260.00** = cash advanced ✓

**Example 2** — no haircut on EUR government collateral:

- Security Nominal = 5,800,000 × 113.745589% = **6,597,244.16**
- Haircut 0.00 → Post-haircut = **6,597,244.16** = cash advanced ✓

**Example 3** — 5% haircut on amortizing collateral:

- Security Nominal = **64,323,378.28** (on the factor-adjusted price)
- Haircut Amount = **3,216,168.91** ✓
- Post-haircut = **61,107,209.36** = cash advanced ✓

The contrast between Examples 1 and 2 is instructive: government collateral financed at no haircut, corporate and asset-backed collateral at 5%. The haircut reflects the credit and liquidity of what is being pledged.

## 7. Term, open and the number of days

| Example | Maturity | Days |
|---|---|---|
| 1 | **Open** (dates shown 08 sept 2026) | 18 |
| 2 | 25 feb 2027 | 184 |
| 3 | 19 ene 2027 | 147 |

A **term** repo has a fixed maturity fixed at inception. An **open** repo has no contractual end date: it rolls until either party terminates, typically on notice, with the rate re-set periodically. Example 1 is open, with a current period of 18 days.

`Early Settlement: Yes` on all three templates — partial or full unwinds before maturity are expected behaviour, not exceptions.

## 8. Re-marking: how the cash leg moves during the trade

This is the mechanic that Examples 1 and 2 cannot show, because on both of them the current values equal the initial ones. Example 3 has been re-marked, and the whole chain is visible.

Four fields carry the current state:

- **Current Price** — the collateral's price now.
- **Current Haircut Amount** — the haircut recomputed on that price.
- **Current Nominal** — the cash amount now supported.
- **Current Quantity** — the collateral quantity now on the trade.

In Example 3 the collateral has appreciated from **34.4159** to **35.2175**, and the cash leg has followed:

| Step | At inception | Currently |
|---|---|---|
| Price | 34.4159 | **35.2175** |
| Security nominal | 64,323,378.28 | **65,821,415.60** |
| Haircut (5%) | 3,216,168.91 | **3,291,070.78** |
| Cash nominal | 61,107,209.36 | **62,530,344.86** |

Each step reconciles: 65,821,415.60 is 35.2175% of the 186,900,000 face, its 5% haircut is 3,291,070.78, and the difference is 62,530,344.86 — the current nominal shown on the screen.

**And the repurchase amount is computed off the current nominal, not the original one:**

62,530,344.86 + 393,878.64 = **62,924,223.50** = End Nominal ✓

Start Nominal plus interest would give 61,501,088.00, which is not what the screen shows. This matters: on a re-marked repo, the End Nominal is a moving figure that tracks the collateral, and any reconciliation that assumes it was fixed at inception will fail.

Note also that the template's **`End nominal based on: Start nominal + Interests`** describes the inception relationship, while the observed behaviour uses the *current* nominal. The two should be reconciled (§15).

The template's **`Treat margining: On pool level`** indicates that margin is managed across a pool of trades rather than trade by trade, which affects how the exposure is actually collateralized in practice.

## 9. Settlement and clearing

- **`Payment Conditions: Delivery versus payment`** on all three — security and cash move simultaneously, eliminating principal risk at settlement.
- **Clearing Center** is populated and differs across the examples, indicating the venue or arrangement through which the trade settles.
- **`Collateral representation: Bilateral`** on all three templates — the collateral is held bilaterally between the two parties rather than through a tri-party agent. A tri-party arrangement would introduce an agent managing collateral selection, substitution and margining.
- **`Settlement model: Theoretical interest`** and **`Settlement process: Trade`** govern how the settlement amounts are derived and at what level.

## 10. Templates

Three templates appear, and the differences are substantive rather than cosmetic:

| Field | Fixed-rate template | Floating template A | Floating template B |
|---|---|---|---|
| Description | Repo a Tipo Fijo | Repo a Tipo Flotante | Repo a Tipo Flotante |
| **Evaluation** | **MTM** | **MTM** | **Accrual** |
| Accrual delay | +1 open day | +1 open day | **Redefined, +1 DAY** |
| Flows projection delay | +1 open day | +1 open day | +1 open day |
| Triangulation | Nominal | Nominal | Nominal |
| Purpose | Security driven | Security driven | Security driven |
| Treat margining | On pool level | On pool level | On pool level |
| Collateral representation | Bilateral | Bilateral | Bilateral |
| Early settlement | Yes | Yes | Yes |
| Settlement model | Theoretical interest | Theoretical interest | Theoretical interest |
| Haircut applies on | Nominal | Nominal | Nominal |
| *Collateral tab* | | | |
| Start delay | **0 DAY** | **+2 OPEN DAYS** | **+2 OPEN DAYS** |
| Payment calendar | **NEW YORK** | **TARGET** | **TARGET** |
| Security exchange | Yes | Yes | Yes |
| *Cash tab* | | | |
| Cash nominal based on | Initial price | Initial price | Initial price |
| Start delay | 0 DAY | +2 OPEN DAYS | **0 DAY** |
| Payment calendar | NEW YORK | TARGET | TARGET |
| Rate | **Fixed** | **Floating** | **Floating** |
| Rate convention | LIN ACT/360 | LIN ACT/360 | LIN ACT/360 |
| Interest flows rounding | **Nearest, 2 dp** | **Nearest, 2 dp** | **None** |
| Nominal rounding rule | Inherited from currency | Inherited from currency | **None** |
| Cash exchange | Yes | Yes | Yes |
| Cash based on | Dirty Price | Dirty Price | Dirty Price |
| End nominal based on | Start nominal + Interests | Start nominal + Interests | Start nominal + Interests |
| Payment | In arrears | In arrears | In arrears |
| Stub period | Both ends (forward) | Both ends (forward) | Both ends (forward) |
| **Fixing** | — | **In arrears** | **Up front** |
| Fixing calendar | — | TARGET | TARGET |
| Rate factor applied | — | To main index | To main index |
| Margin mode | — | Additive | Additive |

Three points worth noting:

- **Evaluation differs**: MTM on two templates, **Accrual** on the third. This changes how the trade is valued and is the kind of setting that should be deliberate rather than inherited by accident.
- **The collateral and cash legs can carry different start delays** — floating template B has +2 open days on the collateral and 0 days on the cash, an asymmetry the other two do not have.
- **Rounding is configured inconsistently.** Two templates round interest flows to the nearest 2 decimals; the third applies no rounding at all. On large notionals this produces differences that will show up in reconciliation.

## 11. Flow schedules

Example 2's global flow schedule shows what a repo actually does, and is the clearest demonstration in this document that both legs genuinely move. The `Lg` column identifies the leg — 1 is collateral, 2 is cash.

| Leg | Flow type | Sub-type | Date | Flow | Denominated in |
|---|---|---|---|---|---|
| 1 | PRI | INI | 25 ago 2026 | **+5,800** | **the bond** |
| 2 | PRI | INI | 25 ago 2026 | **−6,597,244.16** | EUR |
| 1 | PRI | FIN | 25 feb 2027 | **−5,800** | **the bond** |
| 2 | INT | | 25 feb 2027 | **+4,342.09** | EUR |
| 2 | PRI | FIN | 25 feb 2027 | **+6,597,244.16** | EUR |

The structure reads directly: collateral in and cash out at the start, collateral back and cash back plus interest at maturity. **The collateral leg's flows are denominated in the security itself**, not in currency — the schedule is recording a movement of bonds, not a cash equivalent.

Other columns worth knowing:

- **PRI / INT** distinguish principal from interest; **INI / FIN** distinguish the opening from the closing exchange.
- **Rate**, **Margin**, **Net Margin** and **Convert Rate** show the floating rate build-up (§5.2). A rate shown in italics is estimated rather than fixed.
- **First fixing / Last fixing dates** — in Example 2, 25 ago 2026 and 24 feb 2027, the last fixing falling one day before payment, consistent with in-arrears fixing.
- **Nb of Days** — 184, matching the trade screen.
- **Haircut Rate** and **Haircut Formula** are carried into the flows, the formula column showing the same mode indicator as the trade screen.
- **Non indexed Flow / Non indexed Cur** show the flow before any indexation is applied.

## 12. Worked examples

### 12.1 Example 1 — Fixed-rate open reverse repo, USD corporate collateral

| Field | Value |
|---|---|
| Template | Fixed-rate repo |
| Collateral | USD corporate bond, 4.125% coupon |
| Start | 21 ago 2026 |
| **Maturity** | **Open** (dates shown 08 sept 2026) |
| Number of days | **18** |
| Quantity / Amount | 2,000 / **2,000,000.00** |
| Payout | **Borrow** |
| Clean / Accrued / Dirty | 97.4400 / **1.1000** (96/360) / **98.5400** |
| Yield | 4.811773% |
| Security Nominal | **1,970,800.00** |
| **Haircut** | **−5.00**, mode `1 +/- x` → amount **−98,540.00** |
| Security Nominal Post Haircut | **1,872,260.00** |
| Cash currency | USD |
| Start Nominal | **−1,872,260.00** |
| **Interest** | **3,632.18** |
| **End Nominal** | **1,875,892.18** |
| Current Nominal | −1,872,260.00 (unchanged) |
| Rate type / Rate | **Fixed** / **3.8800%** |
| Rate convention | LIN ACT/360 |
| Current Price | 98.5400 (unchanged) |
| Payment conditions | Delivery versus payment |

**Position:** a reverse repo — the book lends USD 1,872,260 for 18 days against USD 2,000,000 face of corporate collateral, at 3.88%.

**This example reconciles completely, end to end**, and is the cleanest demonstration of the product's arithmetic:

- Accrued: 4.125% × 96/360 = **1.1000**
- Dirty: 97.4400 + 1.1000 = **98.5400**
- Security nominal: 2,000,000 × 98.54% = **1,970,800.00**
- Haircut: 5% = **98,540.00**
- Cash advanced: **1,872,260.00**
- Interest: 1,872,260.00 × 3.88% × 18/360 = **3,632.18**
- Repurchase: **1,875,892.18**

**The haircut in context:** the book lends 95% of the collateral's market value, keeping a 98,540 cushion against a fall in the bond's price over the 18 days.

**Rate versus yield:** the repo rate of 3.88% sits below the collateral's 4.81% yield — as expected, since the repo rate is a short-term secured funding rate, not a return on the bond.

**Current values equal initial values**, so this trade has not been re-marked.

### 12.2 Example 2 — Floating-rate term reverse repo, EUR government collateral

| Field | Value |
|---|---|
| Template | Floating-rate repo (template A) |
| Collateral | EUR government bond, 5.75% coupon |
| Start | 25 ago 2026 |
| **Maturity** | **25 feb 2027** (term) |
| Number of days | **184** |
| Quantity / Amount | 5,800 / **5,800,000.00** |
| Payout | **Borrow** |
| Clean / Accrued / Dirty | 113.3360 / **0.4096** (26/365) / **113.7456** |
| Yield | 3.240370% |
| Security Nominal | **6,597,244.16** |
| **Haircut** | **0.00**, mode `1 / (1 +/- x)` → amount **0.00** |
| Security Nominal Post Haircut | **6,597,244.16** |
| Cash currency | EUR |
| Start Nominal | **−6,597,244.16** |
| Interest | **4,342.09** |
| End Nominal | **6,601,586.25** |
| Rate type | **Floating** — EUR ESTR AVG + **0.1800%**, factor 1.000000 |
| Rate convention | LIN ACT/360 |
| Payment conditions | Delivery versus payment |

**Position:** a six-month term reverse repo against government collateral, financed at ESTR plus 18bp.

**The collateral chain reconciles exactly.** Accrued of 5.75% × 26/365 = 0.409589 gives a dirty price of 113.745589 — displayed rounded to 113.7456 — and 5,800,000 × 113.745589% = **6,597,244.16**, the security nominal to the cent. End Nominal = 6,597,244.16 + 4,342.09 = **6,601,586.25** ✓

**No haircut.** Government collateral financed at full market value, against 5% on the corporate and asset-backed examples.

**The interest does not reconcile against the displayed rate.** At the flow schedule's Convert Rate of 2.36940% over 184 days on 6,597,244.16, interest should be **79,894.39**; the screen shows **4,342.09**, an implied net rate of 0.12877%. Notably, 4,342.09 is **exactly 10 days** of accrual at the convert rate — and 10 days from the 25 August start reaches the capture date. The figure therefore looks like accrual to the valuation date rather than to maturity, yet the flow schedule presents the same number as the maturity flow with `Nb of Days 184`. The two readings conflict (§15).

**Flow schedule** — see §11. This is the example that shows the security moving in and out against cash.

### 12.3 Example 3 — Floating-rate term reverse repo, amortizing EUR collateral, re-marked

| Field | Value |
|---|---|
| Template | Floating-rate repo (template B) |
| Collateral | EUR asset-backed floating-rate note (amortizing) |
| Start | 25 ago 2026 |
| **Maturity** | **19 ene 2027** (term) |
| Number of days | **147** |
| Quantity / Amount | 1,869 / **186,900,000.00** |
| Payout | **Borrow** |
| Clean Price | 97.5997 |
| Accrued Coupon | **0.0000** (0/360) |
| **Capital Factor** | **0.3526** → outstanding face **65,905,294.77** |
| **Dirty Price** | **34.4159** |
| Yield | **48.826753%** *(see below)* |
| Security Nominal | **64,323,378.28** |
| **Haircut** | **−5.00**, mode `1 +/- x` → amount **−3,216,168.91** |
| Security Nominal Post Haircut | **61,107,209.36** |
| Cash currency | EUR |
| Start Nominal | **−61,107,209.36** |
| **Current Nominal** | **−62,530,344.86** |
| **Current Haircut Amount** | **−3,291,070.78** |
| **Current Price** | **35.2175** |
| Interest | **393,878.64** |
| **End Nominal** | **62,924,223.50** |
| Rate type | **Floating** — EURIBOR3M + **0.5000%**, factor 1.000000 |
| Rate convention | LIN ACT/360 |
| Payment conditions | Delivery versus payment |

**Position:** a reverse repo against amortizing asset-backed collateral, at EURIBOR 3M plus 50bp, over 147 days.

**The capital factor is the defining feature.** The collateral has amortized to roughly 35% of its original principal, and the price is scaled accordingly:

97.5997 × 0.3526233 = **34.4159** — the dirty price, exactly.

So the clean-plus-accrued rule does **not** hold here (accrued is zero and the factor does the work instead), and the outstanding face being financed is 186,900,000 × 0.3526233 = **65,905,294.77**, not the full 186.9m.

**The yield of 48.826753% is not meaningful.** It appears to be derived from the factor-adjusted price of 34.42 against a par redemption, ignoring that only 35% of principal remains outstanding. It should not be read as the collateral's economic yield (§15).

**This is the only re-marked example**, and it shows the full chain (§8):

| | At inception | Currently |
|---|---|---|
| Price | 34.4159 | **35.2175** |
| Security nominal | 64,323,378.28 | **65,821,415.60** |
| Haircut (5%) | 3,216,168.91 | **3,291,070.78** |
| Cash nominal | 61,107,209.36 | **62,530,344.86** |

And the repurchase amount is built on the **current** figure: 62,530,344.86 + 393,878.64 = **62,924,223.50** ✓, not on the original 61,107,209.36.

**The interest again does not reconcile against the displayed rate.** 393,878.64 over 147 days implies about 1.58% on the start nominal or 1.54% on the current nominal — well below EURIBOR 3M plus 50bp on any plausible EUR curve for the period (§15).

**Template differences:** this trade runs on `Evaluation: Accrual` rather than MTM, an `Accrual delay` redefined to +1 calendar day, **`Fixing: Up front`** rather than in arrears, no interest-flow rounding, and asymmetric start delays between the collateral and cash legs.

### 12.4 The three examples side by side

| | Example 1 | Example 2 | Example 3 |
|---|---|---|---|
| Collateral | USD corporate bond | EUR government bond | **EUR asset-backed, amortizing** |
| Currency | USD | EUR | EUR |
| Direction | Borrow — reverse repo | Borrow — reverse repo | Borrow — reverse repo |
| **Maturity** | **Open** | Term, 25 feb 2027 | Term, 19 ene 2027 |
| Days | 18 | 184 | 147 |
| Face amount | 2,000,000 | 5,800,000 | **186,900,000** |
| **Capital factor** | — | — | **0.3526** |
| Clean / Accrued / Dirty | 97.4400 / 1.1000 / 98.5400 | 113.3360 / 0.4096 / 113.7456 | 97.5997 / **0.0000** / **34.4159** |
| Clean + accrued = dirty? | **Yes** | **Yes** | **No — factor-adjusted** |
| Security nominal | 1,970,800.00 | 6,597,244.16 | 64,323,378.28 |
| **Haircut** | **5.00**, mode `1 +/- x` | **0.00**, mode `1 / (1 +/- x)` | **5.00**, mode `1 +/- x` |
| Cash advanced | 1,872,260.00 | 6,597,244.16 | 61,107,209.36 |
| **Rate type** | **Fixed 3.8800%** | ESTR AVG + 0.1800% | EURIBOR3M + 0.5000% |
| Interest | **3,632.18** ✓ reconciles | 4,342.09 — does not reconcile | 393,878.64 — does not reconcile |
| End nominal | 1,875,892.18 | 6,601,586.25 | **62,924,223.50** |
| **Re-marked?** | No | No | **Yes** (34.4159 → 35.2175) |
| End nominal built on | Start nominal | Start nominal | **Current nominal** |
| Evaluation | MTM | MTM | **Accrual** |
| Fixing | — (fixed) | **In arrears** | **Up front** |
| Calendars | NEW YORK | TARGET | TARGET |
| Interest flows rounding | Nearest, 2 dp | Nearest, 2 dp | **None** |
| Settlement | DVP | DVP | DVP |
| Purpose | Security driven | Security driven | Security driven |

## 13. Risk profile

A repo is a **secured financing** transaction, and its risks follow from that:

- **Counterparty credit risk, but collateralized.** The cash lender's exposure is to the counterparty failing while the collateral is worth less than the cash advanced. The haircut and the re-marking process (§8) exist precisely to keep that gap negative.
- **Collateral price risk.** Between marks, a fall in the collateral's value erodes the cushion. This is why the haircut is sized to the collateral's volatility and liquidity — zero on government paper in Example 2, 5% on corporate and asset-backed collateral in Examples 1 and 3.
- **Wrong-way risk.** Where the collateral's value is correlated with the counterparty's own credit, both deteriorate together and the protection is worth least when it is most needed. Financing a bank's own paper, or paper from the same sector or sovereign, is the classic case.
- **Concentration and liquidity risk.** A haircut protects only if the collateral can actually be sold at something near its marked price. Amortizing and structured collateral, as in Example 3, can be materially less liquid than the mark implies.
- **Amortization risk on factored collateral.** The capital factor moves as the pool repays, so the collateral value declines over time independently of price. The financing must be sized and re-marked accordingly.
- **Interest rate risk on the cash leg**, small on short-dated trades but real on term repos, and floating on two of the three examples.
- **Settlement risk**, largely mitigated by delivery versus payment (§9) — the security and the cash move together, so neither side is exposed to the other at the moment of exchange.
- **Coupon and income risk.** Where the collateral pays during the repo, the manufactured payment must be passed back correctly, with any withholding handled (§4.3).
- **Legal and re-use risk.** Whether collateral is held bilaterally or through a tri-party agent, and whether it can be re-used, determines what happens on a default. All three examples are bilateral.

## 14. Glossary of fields seen in the Murex screens

**Financial definition**

- **Template**: the configuration template supplying both legs' structural settings (§10).
- **Bond / Market / ISIN**: the collateral security, its pricing source and identifier.
- **Start / Maturity / Maturity structure**: the repo's dates; maturity may read **Open** (§7).
- **Number of days**: the days in the current period, driving the interest calculation.
- **Triangulation**: *Nominal* on all three.

**Deal information**

- **Clearing Center**: the venue or arrangement through which the trade settles.
- **Payment Conditions**: *Delivery versus payment* on all three (§9).

**Collateral leg**

- **Quantity / Amount** and **Current Quantity**: units and face value delivered, and the amount currently outstanding.
- **Payout**: *Borrow* (security in — reverse repo) or lend (§2).
- **Clean Price / Accrued Coupon / Dirty Price / Yield**: the collateral's valuation, with the accrual day-count fraction beside the accrued figure (§4.1).
- **Capital Factor**: the fraction of original principal outstanding on amortizing collateral, with the resulting outstanding face alongside (§4.2).
- **Security Nominal**: the collateral's market value.
- **Security Nominal Post Haircut**: that value less the haircut — the cash it supports (§6).
- **Income Period** and the **Income flows** link: the window over which collateral income arises (§4.3).
- **Reset price**: the link through which the collateral is re-marked (§8).

**Cash leg**

- **Start Nominal / Current Nominal**: cash advanced at inception and as currently marked. Negative on a reverse repo (§2).
- **Interest / End Nominal**: the repo interest and the repurchase amount (§5.1).
- **Haircut**, its **mode indicator**, **Haircut Amount** and **Current Haircut Amount** (§6, §8).
- **Rate type**: fixed or floating.
- **Rate**, or **Index / Margin / Rate factor** on a floating leg (§5.2).
- **Rate convention**: the day count (LIN ACT/360 throughout).
- **Current Price**: the collateral price at the current mark (§8).

**Template**

- **Evaluation**: MTM or Accrual — the valuation basis.
- **Accrual delay / Flows projection delay / Settlement delay**: timing offsets.
- **Purpose**: *Security driven* (specials) or cash driven (GC) (§3).
- **Treat margining**: the level at which margin is managed (*On pool level*).
- **Collateral representation**: *Bilateral* or tri-party (§9).
- **Early Settlement**: whether unwinds before maturity are permitted.
- **Settlement model / Settlement process**: how settlement amounts are derived and at what level.
- **Haircut applies on**: the base to which the haircut is applied (*Nominal*).
- **Security exchange / Cash exchange**: whether each leg physically settles — *Yes* on both, throughout (§1).
- **Cash nominal based on**: *Initial price*.
- **Cash based on**: *Dirty Price* — the price basis for the cash calculation.
- **End nominal based on**: how the repurchase amount is derived (§8, §15).
- **Fixing / Fixing calendar**: rate-setting timing and calendar on floating legs.
- **Margin mode / Rate factor applied / Rate formula**: how the spread and factor combine with the index.
- **Rounding fields**: applied to rates, interest flows, capital and nominal — configured inconsistently across the three templates (§10).
- **Income/Tax credit**: manufactured payment and withholding configuration, not captured (§15).

**Flow schedule**

- **Lg**: the leg — 1 collateral, 2 cash.
- **Flow Tp / Sub. Tp**: *PRI* principal or *INT* interest; *INI* opening or *FIN* closing.
- **Amount Capital / Remaining Capital**: the face and outstanding amounts.
- **Rate / Margin / Net Margin / Convert Rate**: the floating rate build-up (§5.2).
- **First / Last fixing Date**: the fixing window.
- **Nb of Days**: days in the period.
- **Haircut Rate / Haircut Formula**: the haircut carried into the flows.
- **Non indexed Flow / Cur**: the flow before indexation.

## 15. Open items and gaps in this document

1. **Interest does not reconcile on two of the three examples.** Example 1 ties exactly (1,872,260 × 3.88% × 18/360 = 3,632.18). Example 2's 4,342.09 corresponds to **exactly 10 days** at the stated convert rate rather than the 184 shown, and 10 days from the start reaches the capture date — suggesting accrual to valuation date, except that the flow schedule labels the same figure as the 184-day maturity flow. Example 3's 393,878.64 implies about 1.58%, well below EURIBOR 3M plus 50bp. Whether the field means accrual-to-date or full-term interest needs to be settled, and it is the most consequential open item here for accounting purposes.
2. **`End nominal based on: Start nominal + Interests` conflicts with observed behaviour** (§8). Example 3's End Nominal is built on the *current* nominal, not the start nominal. Confirm which the system actually applies and whether the template label is accurate.
3. **The yield field on amortizing collateral is not meaningful** (§4.2). Example 3 shows 48.826753%, apparently computed from the factor-adjusted price against par. Confirm how the field is derived and whether it should be relied on for factored securities.
4. **The Income/Tax credit configuration was not captured** on any example (§4.3). For a repo book this governs manufactured coupon payments and their withholding treatment — material whenever collateral pays during the trade.
5. **Rounding is configured inconsistently across templates** (§10): nearest-2-decimals on two, none on the third. On a 186.9m notional this is not immaterial.
6. **Evaluation differs across templates** — MTM on two, Accrual on one — with no visible rationale.
7. **Only one flow schedule was captured**, and only for a trade with no haircut and no re-marking. A flow schedule for the amortizing, re-marked example would show how factor changes and margin adjustments appear as flows.
8. **No cash-driven (GC) example.** All three are security driven. A GC funding repo would show the other side of the motivation described in §3.
9. **No repo direction example.** All three are reverse repos (Borrow). The mechanics are symmetric, but a trade lending collateral and borrowing cash would confirm the sign conventions.
10. **Substitution and margin call events are not documented.** The re-marking in Example 3 is visible as a state, but the events that produce it — margin calls, collateral substitution — are not captured.
