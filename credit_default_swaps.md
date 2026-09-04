# Credit Default Swaps (CDS)

## Purpose of this document

This is a reference document on credit default swaps: what the product is, how the premium and protection legs work, how the standardized-coupon-plus-upfront convention operates, how credit events and settlement are defined, and how the terms are represented in Murex. It is meant to be read on its own — a new joiner or anyone unfamiliar with the product should come away understanding the mechanics, not just recognizing the trade capture screen.

The three worked examples in §10 are a **5-year USD CDS on a European emerging-market sovereign**, a **5-year USD CDS on a Latin American sovereign** taken in the opposite direction, and a **10-year EUR CDS on a subordinated European financial**. Between them they cover both directions, two currencies and generators, sovereign and financial reference entities, senior and subordinated debt, and two points on the maturity curve.

**A note on identifiers.** Reference entity codes and reference obligation identifiers have been omitted throughout. Each example is described by the characteristics that matter economically — region, sector, seniority — which is sufficient to follow the mechanics.

## 1. Overview: what a credit default swap is

A credit default swap is a bilateral OTC contract that **transfers the credit risk of a reference entity from one party to another**, without either party needing to hold the underlying debt.

It has exactly two legs:

- **The premium leg.** The protection buyer pays a periodic fixed coupon to the protection seller, quarterly in arrears, for as long as no credit event occurs.
- **The protection leg (contingent leg).** If a credit event occurs, the protection seller compensates the buyer for the loss on the reference entity's debt, and the contract terminates.

In effect the buyer pays an insurance-like premium and receives a payout if the reference entity defaults. Three points follow:

- **It is unfunded.** No principal changes hands at inception or maturity — all three examples have initial, intermediate and final capital exchange set to *No*. This is what allows credit risk to be taken or hedged without buying or shorting bonds.
- **The reference entity is not a party to the contract.** It is the subject of the trade, not a counterparty to it. A CDS can be traded on any eligible entity.
- **It is a contingent product, not a linear one.** Value depends on the market's assessment of default probability and recovery, and the payoff is triggered by a discrete event rather than accruing continuously.

## 2. Direction: the terminology trap

CDS direction can be expressed three different ways, and two of them run opposite to each other. Getting this wrong inverts the position, so it is worth setting out explicitly.

The system field is **Buy/Sell risk**, which describes the *credit exposure* being taken — the opposite sense to the more common "buy/sell protection" language, which describes the *insurance* being traded:

| Field or concept | Long credit | Short credit |
|---|---|---|
| **Buy/Sell risk** (system field) | **Buy risk** | **Sell risk** |
| Market phrasing | Sell protection | Buy protection |
| Premium details | **Receive premium** | **Pay premium** |
| Credit information | **Pay protection** | **Receive protection** |
| On a credit event | Pays out | Receives payout |
| Economic analogue | Like owning the bond | Like shorting the bond |
| Gains when | Spreads tighten | Spreads widen |

The four system fields always move together: *Buy risk* pairs with *Receive premium* and *Pay protection*; *Sell risk* pairs with *Pay premium* and *Receive protection*. If they ever disagree on a capture, something is wrong.

## 3. The reference entity, seniority and the default template

### 3.1 Reference entity and reference obligation

The **Issuer** field identifies the reference entity whose credit is being traded. The **Reference obligation** names a specific bond of that entity, which serves to establish the seniority being referenced and to anchor the deliverable universe.

### 3.2 Debt type: seniority is an economic term, not a label

The **Debt type** field records the seniority of the referenced debt. Two levels appear across the examples:

- **Senior Unsecured** (Examples 1 and 2)
- **Subordinated Lower Tier 2** (Example 3)

This is not a descriptive tag — it changes the economics materially. Subordinated debt ranks behind senior debt in a default, so its expected recovery is lower, so the same notional of protection is worth more, so **subordinated CDS trades at a wider spread than senior CDS on the same entity**. A CDS is only defined once seniority is specified.

The suffix `_2014` on both debt types refers to the ISDA Credit Derivatives Definitions vintage governing the seniority classification — see §7.3 for a question this raises.

### 3.3 The default details template

The **Default details** field attaches a standard template defining which credit events apply and how settlement works. The three examples use three different templates:

| Example | Template | Reference entity type |
|---|---|---|
| 1 | STD EURO EM SOV | European emerging-market sovereign |
| 2 | STD LATAM E SOV | Latin American sovereign |
| 3 | STD EURINSUB | European financial/insurance, subordinated |

These templates are economically substantive. Credit event definitions differ by entity type and region: sovereign contracts include repudiation and moratorium, which corporate contracts do not; European corporate contracts conventionally include restructuring, which North American ones typically do not; and subordinated financial contracts carry their own considerations around regulatory intervention and bail-in. **Reading the template name is not sufficient — the definitions behind it determine what actually triggers a payout.**

## 4. The premium leg

### 4.1 Standardized fixed coupon

All three examples carry a **Premium of 1.000000**, i.e. a fixed running coupon of **100 basis points**. This is not a coincidence and not a negotiated rate: since the market standardization of 2009, CDS trade on a small set of fixed coupons — commonly 100bp for investment-grade and 500bp for high-yield names — with the difference between the fixed coupon and the credit's actual market spread settled through an **upfront payment** (§5).

The **Net premium** field shows the coupon after any sales margin (zero throughout, so net equals gross at 100bp).

### 4.2 Frequency, basis and payment timing

From the generator: quarterly payments, **LIN ACT/360 CRD** day count, paid **in arrears**. The generator names themselves state this — *USD 3M ACT/360 - STANDARD* and *EUR 3M ACT/360 - STANDARD*.

### 4.3 Accrual runs from the previous IMM date, not from trade date

This is the mechanic most often misread on the capture screen. The premium start shows **two dates**: the trade's effective date, and the date from which premium accrues.

In all three examples the second date is **22 jun 2026** — a Monday, being the 20 June 2026 IMM coupon date rolled forward because **20 June 2026 falls on a Saturday**.

So regardless of when in the quarter a CDS is traded, the premium leg accrues from the preceding IMM coupon date, and the buyer pays a **full first coupon** at the next payment date. The accrued portion covering the period before the trade is settled through the upfront (§5.3). In Example 1, that accrual runs 58 days and is worth roughly 8,000 USD at the 100bp coupon on a 5,000,000 notional.

### 4.4 Premium on a credit event

**Premium: Paid on default date.** If a credit event occurs mid-period, premium accrued from the last coupon date to the event date is paid — the contract does not simply drop the stub. The related generator field **Coupon payments after default: No Rebate** governs how coupons are treated after the event; its precise semantics should be confirmed (§13).

## 5. Standardized coupons and the upfront payment

### 5.1 Why an upfront exists

If every CDS on every name pays the same 100bp coupon, the coupon cannot by itself reflect the credit's actual risk. The **upfront payment** bridges the gap between the fixed coupon and the market spread:

- **Market spread > fixed coupon** — the credit is riskier than 100bp compensates for, so the **protection buyer pays an upfront** to the seller.
- **Market spread < fixed coupon** — the coupon overpays the seller, so the **seller pays an upfront** to the buyer.

The benefit of the convention is fungibility: every trade on a given name and maturity has identical cash-flow mechanics, differing only in the upfront, which makes positions nettable and assignable.

### 5.2 The relationship, and a worked reconciliation

Upfront is quoted in **points upfront** — a percentage of notional — and relates to spread through the risky annuity (the present value of 1bp of premium, allowing for the probability the contract survives to each payment):

**Upfront points ≈ (Market spread − Fixed coupon) × Risky annuity**

Example 2 lets this be verified directly, because it is the one trade where the *Upfront equiv. spread* field is populated:

- Upfront: 45,139 on 5,000,000 = **0.90278 points**
- Upfront equiv. spread: **0.201761%** = 20.18bp
- Implied risky annuity: 0.90278 / 0.201761 = **4.4745**

A risky annuity of about 4.47 on a 4.84-year contract is exactly what theory predicts, so the field reconciles cleanly. The credit's market spread is therefore approximately **100 + 20.18 = 120bp**.

The same relationship recovers indicative spreads for the other two examples, where the field reads zero (§10).

### 5.3 What the upfront amount contains

The upfront settles both the spread difference and the accrued premium from the previous IMM date (§4.3). When reconciling an upfront figure, both components must be accounted for — the clean upfront alone will not tie out.

### 5.4 Upfront settlement timing

The generator sets **Upfront payment delay: Specific delay, +3 OPEN DAYS**, against a **Start delay of 1 SIMPLE DAY** for the effective date. Example 3 follows this exactly: a Monday 24 August trade date gives a Tuesday 25 August effective date (T+1 calendar) and a Thursday 27 August upfront settlement (T+3 open days). Examples 1 and 2 do not reconcile against the same rule — see §13.

## 6. The protection leg

### 6.1 The payout

On a credit event, the protection seller compensates the buyer for the loss:

**Payout = Notional × (Reference price − Recovery rate) × Leverage factor**

All three examples have **Reference price 100.00000000** and **Leverage factor 1.00000000**, so the payout reduces to the standard **Notional × (1 − Recovery)**. A leverage factor other than 1 would scale the contingent payment without changing the notional; a reference price other than 100 would change the baseline against which loss is measured.

Recovery is not known in advance. It is determined after the event — by auction in the standard market process — which means the size of the payout is itself uncertain at trade date. This is why **recovery risk is a distinct risk from spread risk** (§11).

### 6.2 Settlement method

All three examples specify **Settlement: Delivery** — physical settlement, where the protection buyer delivers a deliverable obligation and receives par. The alternative is cash settlement against a recovery price.

Worth noting: since 2009 the market standard has been **auction settlement**, which establishes a single recovery price through a centralized auction and settles the great majority of contracts in cash. A configuration of physical delivery is worth confirming as intended (§13).

### 6.3 Protection timing

**Protection: Paid on default date** — the contingent payment is made at the event, not deferred to the contract's scheduled maturity.

### 6.4 ISDA definitions version

The **ISDA Version** field records which ISDA Credit Derivatives Definitions govern the contract. All three examples read **isda03** — the 2003 Definitions. See §7.3.

## 7. Dates and conventions

### 7.1 IMM dates

CDS maturities fall on the quarterly IMM credit roll dates — **20 March, 20 June, 20 September, 20 December**. Both maturities in the set sit on 20 June (2031 and 2036), and both are Fridays, so no adjustment applies. Premium accrual likewise anchors to these dates (§4.3).

A consequence: a "5-year" CDS traded in August 2026 does not mature five years later to the day. It matures on the 20 June 2031 IMM date, giving an actual tenor of 4.84 years. Similarly the "10-year" example runs 9.82 years. **Quoted tenor and actual tenor are not the same thing**, which matters when computing annuities or comparing trades.

### 7.2 Generators

The generator supplies the premium leg's structural configuration. Both generators in the set are the same template in two currencies:

| Field | USD 3M A/360STD | EUR 3M A/360STD |
|---|---|---|
| Description | USD 3M ACT/360 - STANDARD | EUR 3M ACT/360 - STANDARD |
| Phases | 1 | 1 |
| Rate | Fixed rate | Fixed rate |
| Payment currency | USD | EUR |
| Start delay | 1 SIMPLE DAY | 1 SIMPLE DAY |
| Upfront payment delay | Specific delay, +3 OPEN DAYS | Specific delay, +3 OPEN DAYS |
| **Payment calendar** | **NEW YORK** | **EUR/GBP** |
| Payment | In arrears | In arrears |
| Rate convention | LIN ACT/360 CRD | LIN ACT/360 CRD |
| Accrual method | cf interest | cf interest |
| Stub period position | Up front | Up front |
| Coupon payments after default | No Rebate | No Rebate |
| Capital exchange (initial/intermediate/final) | No / No / No | No / No / No |
| Roundings | None | None |

The only substantive difference is the payment calendar, which follows the currency. Everything else — quarterly ACT/360, in arrears, no capital exchange, up-front stub — is common, reflecting how standardized this product is relative to interest rate swaps.

### 7.3 A question the version fields raise

All three trades pair **ISDA Version: isda03** (the 2003 Definitions) with a **Debt type suffixed `_2014`**. The 2014 Definitions introduced provisions specifically relevant to these examples: government bail-in triggers for financial reference entities, and asset package delivery for sovereigns and financials. Two of the three examples are sovereigns and the third is a subordinated financial — precisely the population the 2014 changes were designed for. The pairing should be confirmed rather than assumed correct (§13).

## 8. What the trade capture screen shows

- **Financial definition** (upper left): generator, reference entity, debt type, maturity, notional, fixed coupon.
- **Deal entry** (upper right): upfront amount with its direction and settlement date, upfront-equivalent spread, and the Buy/Sell risk direction flag.
- **Premium details** (lower left): premium direction, currency, accrual start dates, day count, sales margin and net premium.
- **Credit information** (lower right): protection direction, settlement method, reference price, leverage factor, ISDA version, default template and reference obligation.
- **Flows / Capital / Events** links give the cash-flow schedule and the credit event history — not captured here (§13).

## 9. Valuation

The mark-to-market of a CDS position is, in essence, the present value of the difference between the market spread and the fixed coupon over the contract's remaining life:

**MTM ≈ (Market spread − Fixed coupon) × Risky annuity × Notional**, plus accrued premium

For a protection seller (long credit), the position gains as spreads tighten. For a protection buyer, it gains as spreads widen. At inception the trade is made whole through the upfront, so the economic position starts flat and moves with the credit thereafter.

Valuation requires a **credit curve** for the reference entity — built from market spreads across maturities and combined with a recovery assumption to imply survival probabilities — plus a discount curve. Both the annuity and the contingent leg depend on that curve, which is why a CDS cannot be valued from a single spread number alone.

## 10. Worked examples

### 10.1 Example 1 — European EM sovereign, senior, 5-year USD (sell protection / buy risk)

| Field | Value |
|---|---|
| Generator | USD 3M A/360STD |
| Reference entity | European emerging-market sovereign |
| Debt type | Senior Unsecured (2014) |
| Default template | STD EURO EM SOV |
| Nominal | 5,000,000 USD |
| Fixed coupon | 1.000000% (100bp) |
| Maturity | 20 jun 2031 (unadjusted = adjusted) |
| Premium start / accrual from | 19 ago 2026 / **22 jun 2026** |
| Day count | LIN ACT/360 CRD |
| **Buy/Sell risk** | **Buy risk** |
| Premium | **Receive** |
| Protection | **Pay** |
| **Upfront** | **Receive 338,839 USD**, settling 20 ago 2026 |
| Upfront equiv. spread | 0.000000 *(not populated)* |
| Settlement | Delivery |
| Reference price / Leverage | 100 / 1.00 |
| ISDA version | isda03 |

**Position:** long credit — protection sold on a sovereign. The book receives 100bp quarterly and would pay out on a credit event.

**Tenor:** 4.84 years to the June 2031 IMM maturity.

**Upfront:** 338,839 on 5,000,000 = **6.777 points**, received. Receiving an upfront as protection seller means the market spread is materially wider than the 100bp coupon. Applying a risky annuity in the 4.0–4.5 range (Example 2 implies 4.47 for a comparable tenor, and a wider credit carries a slightly lower annuity) gives an indicative market spread of roughly **250–270bp**.

**Accrual:** premium accrues from 22 June 2026, 58 days before the effective date, worth approximately 8,056 USD at the coupon — settled within the upfront.

### 10.2 Example 2 — Latin American sovereign, senior, 5-year USD (buy protection / sell risk)

| Field | Value |
|---|---|
| Generator | USD 3M A/360STD |
| Reference entity | Latin American sovereign |
| Debt type | Senior Unsecured (2014) |
| Default template | STD LATAM E SOV |
| Nominal | 5,000,000 USD |
| Fixed coupon | 1.000000% (100bp) |
| Maturity | 20 jun 2031 |
| Premium start / accrual from | 20 ago 2026 / **22 jun 2026** |
| Day count | LIN ACT/360 CRD |
| **Buy/Sell risk** | **Sell risk** |
| Premium | **Pay** |
| Protection | **Receive** |
| **Upfront** | **Pay 45,139 USD**, settling 20 ago 2026 |
| **Upfront equiv. spread** | **0.201761%** |
| Settlement | Delivery |
| Reference price / Leverage | 100 / 1.00 |
| ISDA version | isda03 |

**Position:** short credit — protection bought. The book pays 100bp quarterly and would receive a payout on a credit event.

**The reference trade for the upfront relationship.** This is the only example with the equivalent-spread field populated, and it reconciles exactly: 0.90278 points / 0.201761% = **risky annuity 4.4745**, implying a market spread of about **120bp** (§5.2). That annuity is what makes the indicative spreads quoted for the other two examples possible.

**Relative to Example 1:** same notional, same coupon, same maturity, same day count, same upfront settlement date — and the opposite direction on a different sovereign. Two credits roughly a factor of two apart in spread (approximately 120bp against 250–270bp). The pairing is consistent with a relative-value position expressing a view on the spread between two sovereigns rather than two unrelated outright trades, though nothing on the captures confirms that.

### 10.3 Example 3 — European financial, subordinated Lower Tier 2, 10-year EUR (sell protection / buy risk)

| Field | Value |
|---|---|
| Generator | **EUR 3M A/360STD** |
| Reference entity | European financial / insurance |
| Debt type | **Subordinated Lower Tier 2 (2014)** |
| Default template | STD EURINSUB |
| Nominal | **15,000,000 EUR** |
| Fixed coupon | 1.000000% (100bp) |
| Maturity | **20 jun 2036** (unadjusted = adjusted) |
| Premium start / accrual from | 25 ago 2026 / **22 jun 2026** |
| Day count | LIN ACT/360 CRD |
| **Buy/Sell risk** | **Buy risk** |
| Premium | **Receive** |
| Protection | **Pay** |
| **Upfront** | **Receive 728,382 EUR**, settling 27 ago 2026 |
| Upfront equiv. spread | 0.000000 *(not populated)* |
| Settlement | Delivery |
| Reference price / Leverage | 100 / 1.00 |
| ISDA version | isda03 |
| Payment calendar | EUR/GBP |

**Position:** long credit — protection sold on subordinated financial debt, the largest notional in the set.

**Three things distinguish this trade from the first two:**

- **Subordinated rather than senior.** Lower Tier 2 ranks behind senior debt, implying lower recovery and therefore a wider spread than senior protection on the same entity would command. Seniority is an economic term here, not a descriptor (§3.2).
- **A financial reference entity rather than a sovereign**, hence a different default template with different credit event definitions.
- **Ten years rather than five.** At 9.82 years to the June 2036 IMM maturity, this contract has roughly twice the risky annuity of the five-year trades, so a given spread move produces roughly twice the mark-to-market impact.

**Upfront:** 728,382 on 15,000,000 = **4.856 points**, received. Applying a risky annuity in the 7.5–8.5 range appropriate to a ten-year contract gives an indicative market spread of roughly **155–165bp**.

**Date reconciliation.** This example ties out cleanly against the generator's delay rules: a Monday 24 August 2026 trade date gives a Tuesday 25 August effective date (1 simple day) and a Thursday 27 August upfront settlement (+3 open days). It is the only one of the three that does.

### 10.4 The three examples side by side

| | Example 1 | Example 2 | Example 3 |
|---|---|---|---|
| Generator | USD 3M A/360STD | USD 3M A/360STD | **EUR 3M A/360STD** |
| Currency | USD | USD | **EUR** |
| Reference entity | European EM sovereign | LatAm sovereign | **European financial** |
| Debt type | Senior Unsecured | Senior Unsecured | **Subordinated LT2** |
| Default template | STD EURO EM SOV | STD LATAM E SOV | STD EURINSUB |
| Nominal | 5,000,000 | 5,000,000 | **15,000,000** |
| Fixed coupon | 100bp | 100bp | 100bp |
| Maturity | 20 jun 2031 | 20 jun 2031 | **20 jun 2036** |
| Actual tenor | 4.84y | 4.84y | **9.82y** |
| Buy/Sell risk | **Buy risk** | **Sell risk** | **Buy risk** |
| Position | Long credit | **Short credit** | Long credit |
| Premium | Receive | **Pay** | Receive |
| Protection | Pay | **Receive** | Pay |
| Upfront | **Receive** 338,839 | **Pay** 45,139 | **Receive** 728,382 |
| Points upfront | 6.777 | 0.903 | 4.856 |
| Upfront equiv. spread | *not populated* | **0.201761%** | *not populated* |
| Indicative market spread | ~250–270bp | **~120bp** | ~155–165bp |
| Settlement | Delivery | Delivery | Delivery |
| ISDA version | isda03 | isda03 | isda03 |
| Accrual from | 22 jun 2026 | 22 jun 2026 | 22 jun 2026 |
| Upfront settles | 20 ago 2026 | 20 ago 2026 | **27 ago 2026** |
| Delays reconcile? | No | No | **Yes** |

## 11. Risk profile

- **Credit spread risk (CS01).** The change in value for a one basis point move in the reference entity's spread — the primary continuous exposure. It scales with notional *and* risky annuity, which is why the ten-year example carries roughly twice the spread sensitivity per unit of notional of the five-year ones.
- **Jump-to-default (JTD).** The immediate profit or loss if the reference entity defaults now, approximately Notional × (1 − Recovery) for a protection seller. This is a discrete, non-linear exposure that spread sensitivity does not capture, and for a protection seller it is much larger than CS01. It is the defining risk of the product.
- **Recovery risk.** The payout depends on a recovery rate determined only after the event (§6.1). Two positions with identical spread sensitivity can have very different outcomes in default.
- **Curve risk.** Positions at different maturities on the same name are exposed to the shape of the credit curve, not just its level. The set here spans 5-year and 10-year points.
- **Seniority and template risk.** Recovery, and even whether an event triggers at all, depend on the referenced seniority and the applicable definitions (§3).
- **Counterparty credit risk, including wrong-way risk.** A protection buyer relies on the seller to perform precisely when credit conditions are stressed. Where the counterparty's own credit is correlated with the reference entity — the same region, the same sector — the exposure and the counterparty's ability to pay deteriorate together.
- **Basis risk against cash bonds.** CDS spreads and cash bond spreads on the same issuer do not move identically. A CDS hedge of a bond position leaves the CDS-bond basis as residual exposure.
- **Mark-to-market and funding.** Positions are collateralized under bilateral agreements, so spread moves generate margin calls before any credit event occurs.

## 12. Glossary of fields seen in the Murex screens

**Financial definition**

- **Generator**: the convention template supplying the premium leg's configuration (§7.2).
- **Issuer**: the reference entity whose credit is traded — the subject of the contract, not a party to it.
- **Debt type**: the seniority of the referenced debt, with its definitions vintage (§3.2).
- **Maturity**: the contract end date, on an IMM roll date, shown unadjusted and adjusted.
- **Nominal**: the notional on which premium accrues and the contingent payment is computed. Never exchanged.
- **Premium**: the fixed running coupon, as a percentage (1.000000 = 100bp).
- **Contingency**: unticked on all three examples.

**Deal entry**

- **Upfront amount**: the upfront payment, its direction (Pay/Receive) and its settlement date (§5).
- **Upfront equiv. spread**: the upfront expressed as an equivalent running spread increment over the fixed coupon. Populated on only one of the three examples (§13).
- **Buy/Sell risk**: the direction flag, expressed as credit exposure taken rather than protection traded (§2).

**Premium details**

- **Pay / Receive premium**: which side of the premium leg the book is on.
- **Start date**: two dates — the trade's effective date and the accrual start, the latter being the previous IMM coupon date (§4.3).
- **Convention**: the premium leg day count (LIN ACT/360 CRD throughout).
- **Premium: Paid on default date**: accrued premium is settled at a credit event rather than dropped (§4.4).
- **Sales margin / Net premium**: commercial margin and the resulting net coupon (zero margin throughout).

**Credit information**

- **Pay / Receive protection**: which side of the contingent leg the book is on.
- **Settlement**: how a credit event settles — *Delivery* (physical) on all three (§6.2).
- **Reference price**: the baseline against which loss is measured, 100 throughout (§6.1).
- **Leverage factor**: multiplier on the contingent payment, 1.00 throughout.
- **Protection: Paid on default date**: the contingent payment is made at the event.
- **ISDA Version**: the governing ISDA Credit Derivatives Definitions (§6.4, §7.3).
- **Default details**: the template defining applicable credit events and settlement (§3.3).
- **Reference obligation(s)**: the specific bond anchoring seniority and the deliverable universe.

**Generator**

- **Rate / Payment currency / Payment calendar**: coupon type, settlement currency and holiday calendar.
- **Start delay**: lag from trade date to effective date (1 SIMPLE DAY).
- **Upfront payment delay**: lag to upfront settlement (+3 OPEN DAYS) (§5.4).
- **Payment / Rate convention / Accrual method**: quarterly in arrears, ACT/360, accrual basis.
- **Stub period position**: where an odd period sits (*Up front*).
- **Coupon payments after default**: treatment of coupons following a credit event (*No Rebate*) (§4.4).
- **Initial / Intermediate / Final capital exchange**: all *No* — the product is unfunded (§1).

## 13. Open items and gaps in this document

1. **ISDA Version is isda03 while debt types are suffixed `_2014`** (§7.3). The 2014 Definitions introduced government bail-in provisions for financials and asset package delivery for sovereigns and financials — exactly the population these three trades cover. Confirm whether the 2003 Definitions are correct for these contracts.
2. **Settlement is configured as Delivery (physical) on all three** (§6.2), where the post-2009 market standard is auction settlement. Confirm whether physical delivery is intended or whether auction settlement is handled elsewhere in the lifecycle.
3. **Upfront equivalent spread is populated on only one of three trades** (§5.2). The field reconciles perfectly where present, and its absence elsewhere means the implied spread must be derived rather than read. Confirm whether population is conditional, manual, or a gap.
4. **Upfront settlement dates do not reconcile on the two USD trades** (§5.4). The EUR example ties out exactly against the generator's 1 simple day and +3 open days rules; both USD trades show the same 20 ago 2026 upfront date despite different effective dates, which neither rule produces. Confirm whether those dates were overridden manually.
5. **The default template detail screens were not captured** (§3.3). These hold the actual credit event definitions — the terms that determine what triggers a payout — and are arguably the most economically important configuration on the trade. They should be documented.
6. **The Flows, Capital and Events screens were not captured.** The premium schedule, and the credit event history behind the Events link, would show the product's lifecycle rather than only its static terms.
7. **`Coupon payments after default: No Rebate` semantics not confirmed** (§4.4). The field governs coupon treatment following a credit event; the precise behaviour it selects should be verified.
8. **Recovery assumptions and credit curve construction are not documented.** Valuation (§9) requires both, and neither appears on the captured screens.
9. **No index or basket CDS example.** All three are single-name contracts. Index products (iTraxx, CDX) and tranches have materially different mechanics and would need separate treatment.
