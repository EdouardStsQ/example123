# Short-Term Interest Rate Futures (STIR)

## Purpose of this document

This is a reference document on short-term interest rate futures: what the product is, how the quotation and valuation conventions work, how margining and settlement differ from OTC equivalents, and how the terms are represented in Murex. It is meant to be read on its own — a new joiner or anyone unfamiliar with the product should come away understanding the mechanics, not just recognizing the trade capture screen.

The four worked examples in §8 are deliberately different from one another: a **EURIBOR 3M** contract on a forward-looking term rate, a **SOFR 1M** contract on a backward-looking overnight average, a **SOFR 3M** contract on a backward-looking compounded rate, and a Brazilian **DDI (cupom cambial)** contract quoted on a completely different basis and settled in a second currency. Between them they cover two quotation conventions, four expiry conventions, four underlying rate constructions and both trade directions — which is why they work as the reference set. The two SOFR contracts are the most instructive pair: same exchange, same currency, same price convention, yet different settlement mathematics and different expiry logic.

## 1. Overview: what a STIR future is

A short-term interest rate future is an **exchange-traded, standardized contract whose value derives from a short-term interest rate** — typically a three-month or one-month rate — for a specified future period.

Three features define the product and separate it from an OTC equivalent such as a FRA:

- **Standardization.** Contract size, reference period, expiry date and settlement mechanics are fixed by the exchange. Nothing is negotiated bilaterally; you choose the contract and the number of lots, and that is all.
- **Central clearing.** The exchange's clearing house becomes the counterparty to both sides. Bilateral counterparty credit exposure is replaced by exposure to the CCP, backed by margin.
- **Daily margining.** Positions are marked to market every day and the profit or loss is exchanged in cash daily as variation margin, on top of initial margin posted at the outset. Nothing is deferred to maturity. This has a real economic consequence — see §7 on convexity.

Almost all STIR futures are **cash-settled**: at expiry there is no delivery of a deposit or a security, only a final cash settlement against the exchange's official final settlement price, computed from the underlying rate fixing.

## 2. Quotation conventions

This is where the examples diverge most, and where most misreadings of the screen originate.

### 2.1 The "100 minus rate" price convention

The dominant convention for STIR futures — used by the EURIBOR and SOFR contracts here — quotes the contract as:

**Price = 100 − implied interest rate (in %)**

So a price of 97.3950 implies a rate of 2.6050%, and a price of 96.1250 implies 3.8750%. The consequences of this inversion are worth stating explicitly because they are counter-intuitive:

- **Buying the future is a bet that rates will fall.** A long position gains as the price rises, and the price rises as the implied rate falls. In duration terms, a long STIR future behaves like receiving fixed — long duration.
- **Selling the future is a bet that rates will rise.** Short the price, long the rate.
- Rate moves and price moves are equal and opposite in size: one basis point of rate is 0.01 of price.

### 2.2 The PU (*preço unitário*) convention

Brazilian B3 contracts, including the DDI in §8.3, are not quoted as 100 − rate. They are traded on a **yield**, and the contract's value is expressed as a **PU** — the discounted present value of 100,000 points at that yield:

**PU = 100,000 / (1 + r × days / 360)**

where *r* is the quoted yield and *days* is the actual number of calendar days from the valuation date to expiry (the cupom cambial convention is ACT/360; note that the domestic DI1 contract uses business days / 252 instead — do not carry one convention across to the other).

Under this convention the relationship is still inverse but arithmetically different: PU falls as the yield rises, and the sensitivity of PU to yield is not constant — it decays as the contract approaches expiry and depends on the level of rates. A 100 − rate contract has a fixed basis point value; a PU-quoted contract does not.

### 2.3 How the convention is configured

The quotation convention is not an implicit property of the contract — it is explicit static data, and reading it is the fastest way to know how to interpret a quoted level before doing any arithmetic.

| Quotation field | EURIBOR 3M | SOFR 1M | SOFR 3M | DDI |
|---|---|---|---|---|
| Quotation | SFUTPR 3D | RFR 1M | RFR 3M | FUT_DI |
| **Main quotation** | **100-X** | **100-X** | **100-X** | **Yield** |
| Yield type | — | — | — | Annual |
| Notation | Std | Std | Std | Std |
| Decimals | 3 | 4 | 4 | 8 |
| Price factor | 1 | 1 | 1 | 0 |
| Tick rounding rule | None | None | None | None |
| Tick decimals | 0 | 2 | 0 | 5 |
| Time factor rounding rule | None | None | None | None |
| Time factor decimals | 0 | 0 | 0 | 7 |
| **Price expression** | **Percentage** | **Percentage** | **Percentage** | **Flat on 100,000.0000** |
| **Historized quotation** | **Main** | **Main** | **Main** | **Price** |

What the key fields tell you:

- **Main quotation** is the convention itself. *100-X* means the quoted level is a price from which the rate is recovered as 100 − price (§2.1). *Yield* means the quoted level is the rate itself, and the price is derived from it (§2.2). This single field determines how every other number on the trade screen should be read.
- **Price expression** says what the price is expressed against. *Percentage* for the three 100-X contracts — the price is a percentage figure, which is why the position value in §4 multiplies by price/100. *Flat on 100,000.0000* for the DDI — this is the **PU base**, and it confirms directly that the 100,000-point denominator in the §2.2 formula is a configured contract property rather than a market convention inferred from the numbers.
- **Historized quotation** says which value is stored as the contract's history. For the 100-X contracts it is *Main* — the price, which is also the traded quotation. For the DDI it is *Price* even though the main quotation is *Yield*: the contract trades on yield but historizes the PU. Anyone pulling a DDI time series should expect PU values, not yields, and convert accordingly.
- **Decimals** is the precision of the main quotation, and it matches the trade captures: three decimals for EURIBOR (97.395), four for SOFR (96.1250), and eight for the DDI yield — reflecting that a yield-quoted contract needs far more precision in the rate than a price-quoted one, because the rate is then discounted into a five-figure PU.
- **Price factor** is 1 on the price-quoted contracts and 0 on the yield-quoted one, tracking the same distinction.
- **Tick and time-factor rounding rules are set to None on all four**, so the tick and time-factor decimal settings are not being applied as rounding. Worth confirming this is intended, since exchange tick sizes are real constraints on tradable levels (the EURIBOR contract in particular trades in half-ticks at the front of the curve). Note also that the two SOFR setups carry different tick decimals (2 on RFR 1M, 0 on RFR 3M) despite being the same contract family on the same exchange — inert while the rounding rule is None, but an inconsistency worth resolving.

## 3. Contract size, tick and basis point value

The basis point value (BPV, or DV01 per contract) follows directly from the contract size and the length of the reference period:

**BPV per contract = Contract size × 0.0001 × Tenor fraction**

| Contract | Contract size | Reference period | Tenor fraction | BPV per contract |
|---|---|---|---|---|
| EURIBOR 3M | 1,000,000 EUR | 3 months | 0.25 | **EUR 25.00** |
| SOFR 1M | 5,000,000 USD | 1 month | 1/12 | **USD 41.67** |
| SOFR 3M | 1,000,000 USD | 3 months | 0.25 | **USD 25.00** |
| DDI | 50,000 USD notional (100,000 PU points) | to expiry, ACT/360 | varies with time to expiry | **not constant — see §8.3** |

The tenor fraction is what makes a 1M contract on a 5m notional and a 3M contract on a 1m notional comparable in the first place: the SOFR 1M contract is five times the size of the SOFR 3M but covers a third of the period, so a single 1M contract carries USD 41.67 per basis point against the 3M's USD 25.00 — a ratio of 5/3, exactly as the size and tenor imply.

**Position DV01 = BPV per contract × number of contracts.** This is the single most useful number on the screen for a rates desk, and it is not displayed — it has to be derived.

## 4. Position value: how the "Total" field is built

For the 100 − rate contracts, the Total reconciles exactly as:

**Total = Number of contracts × Contract size × Tenor fraction × Price / 100**

This is the quarterly- or monthly-adjusted value of the position at the quoted price, not the raw notional. Both examples in §8.1 and §8.2 tie out to the cent on this formula, which is the quickest way to sanity-check a capture.

For the PU-quoted DDI contract the construction is different — PU is already a value per contract in points, converted to currency by the contract's point value and then translated into the settlement currency. See §8.3.

## 5. Underlying rate types

The contract's price convention tells you nothing about what the underlying rate actually is. Three distinct types appear in these examples:

- **Forward-looking term rate — EURIBOR 3M.** The rate is published as a term rate for a three-month period and is known at the start of that period. The future settles against the fixing on the final settlement day.
- **Backward-looking overnight average — SOFR.** There is no term rate; the settlement rate is constructed from daily overnight fixings across the reference period, so it is only fully known at the end of it. The convention differs between the two SOFR contracts, and the contract definitions state it explicitly in the *Underlying* field: the **1-month contract settles against the arithmetic average** of daily SOFR over the calendar month (*USD SOFR AVG*), whereas the **3-month contract settles against the compounded rate** over its reference quarter (*USD SOFR CMP*). Averaging and compounding are not the same operation and produce different settlement values, so the distinction is not cosmetic — and it is visible on the screen rather than something to be inferred.
- **FX-linked onshore rate — cupom cambial (DDI).** The underlying is the USD interest rate implied in the Brazilian onshore market — effectively the local USD funding rate embedded in the BRL/USD forward. It is an interest rate contract, but its economics are bound up with the FX market, and it is margined and settled in BRL while the notional is denominated in USD. That makes it the only one of the three with a currency dimension.

## 6. Expiry and settlement conventions

Each contract expires on a different rule, and the resolved expiry date frequently does not sit in the month the contract is named after. There is no universal convention and it must be read off the contract definition:

| Contract | Expiry rule | Example |
|---|---|---|
| EURIBOR 3M | **IMM date** — two business days before the third Wednesday of the delivery month | SEP 26 → 14 Sept 2026 (third Wednesday is 16 Sept; two business days prior is Monday the 14th) |
| SOFR 1M | **Month-end** — the reference period *is* the calendar month, so the contract runs to the last day of it | DEC 26 → 31 Dec 2026 |
| SOFR 3M | **Third Wednesday of the month three months after the contract month** — the contract month marks the *start* of the reference quarter, not its end | MAR 27 → 16 June 2027 (reference period runs from the third Wednesday of March 2027 to the third Wednesday of June 2027) |
| DDI | **First business day of the contract month** | APR 27 → 1 Apr 2027 (a Thursday) |

### 6.1 The principle behind the expiry dates

These rules look arbitrary until they are read against §5. The underlying rate type determines when the contract *can* settle:

- **Forward-looking term rates settle at the start of the reference period.** EURIBOR for a three-month period is published at the beginning of that period, so the SEP 26 contract can expire in September 2026 even though the rate it references covers September to December. The rate is known on day one; there is nothing to wait for.
- **Backward-looking overnight rates settle at the end of the reference period.** A compounded or averaged SOFR rate does not exist until every daily fixing in the period has been published. The contract must therefore survive to the end of its reference period. This is why the SOFR 1M DEC 26 contract expires on 31 December 2026 (end of the December reference month), and why the SOFR 3M MAR 27 contract expires on 16 June 2027 — the end of a reference quarter that *began* on the third Wednesday of March.

So the same "MAR 27" label means opposite things depending on the rate type: on a term-rate contract it would name the expiry, while on the compounded SOFR contract it names the start of the accrual period and the contract lives three months beyond it. Reading a SOFR 3M contract month as an expiry month is a straightforward way to misstate a book's maturity profile by a full quarter.

### 6.2 The IMM cycle

The IMM cycle (March, June, September, December) is the backbone of the quarterly STIR market and is what allows contracts to be traded as strips, packs and bundles — sequences of consecutive expiries traded as a single unit to express a view on a section of the curve. Because consecutive quarterly contracts reference consecutive, non-overlapping three-month periods, a strip of them approximates a term rate over the whole span. Monthly contracts such as the SOFR 1M fill in the gaps between IMM dates.

## 7. Margining, and why futures are not quite forwards

**Initial margin** is posted at inception as collateral against potential future exposure. **Variation margin** is the daily exchange of the mark-to-market move, settled in cash. The *First margin call date* field on the trade capture is where this starts — in all four examples it sits on or immediately after the trade date, and it is driven by the booking date rather than by anything contract-specific.

Two consequences matter:

- **Funding.** Daily variation margin is a real cash flow. A position that is losing money consumes cash daily even though the underlying view may only pay off at expiry. This is a genuine funding and liquidity exposure that an unmargined forward does not create.
- **Convexity.** Because margin flows daily and interest rates move, the timing of those cash flows correlates with the level of rates: a short-rate position that profits when rates rise receives cash precisely when it can be reinvested at higher rates, and pays out when reinvestment is cheaper. This asymmetry is worth money, and it means **the rate implied by a futures price is not identical to the equivalent forward (FRA) rate**. The futures-implied rate sits slightly above the forward rate, and the difference — the **convexity adjustment** — grows with maturity and with rate volatility. It is small at the front of the curve and material further out. Anyone using futures prices to build a curve must apply this adjustment rather than reading futures rates as forward rates directly.

## 8. Worked examples

### 8.1 Example 1 — EURIBOR 3M (Buy)

| Field | Value |
|---|---|
| Future | EURIBOR3M LIFFE |
| Exchange | LIFFE (now ICE Futures Europe) |
| Contract code | GB00H6FCHH28 (ISIN) |
| Underlying | EURIBOR3M |
| Currency | EUR |
| Contract size | 1,000,000 |
| Direction | **Buy** |
| Maturity | SEP 26 → 14 sept 2026 |
| Quantity | 265,00 contracts → 265,000,000 |
| Settlement Quotation | 97.3950 |
| First margin call date | 18 ago 2026 |
| Total | 64,524,187 EUR |

**Implied rate:** 100 − 97.3950 = **2.6050%**.

**Notional:** 265 × 1,000,000 = **EUR 265,000,000**.

**Total reconciliation:** 265 × 1,000,000 × 0.25 × 97.3950% = **64,524,187.50**, matching the screen. Per contract that is EUR 243,487.50.

**Risk:** BPV of EUR 25.00 per contract, so the position carries a **DV01 of EUR 6,625** per basis point.

**Direction:** a long position in a 100 − rate contract. The book gains if the September 2026 three-month EURIBOR fixing comes in below 2.6050%, and loses if it comes in above — long duration.

**Expiry check:** the third Wednesday of September 2026 is the 16th; two business days before that is Monday 14 September, which is exactly the maturity date shown. The IMM convention is being applied correctly.

### 8.2 Example 2 — SOFR 1M (Buy)

| Field | Value |
|---|---|
| Future | SOFR 1MONTHFUT |
| Exchange | CME |
| Contract code | *(blank)* |
| Underlying | USD SOFR AVG |
| Currency | USD |
| Contract size | 5,000,000 |
| Direction | **Buy** |
| Maturity | DEC 26 → 31 dic 2026 |
| Quantity | 40,00 contracts → 200,000,000 |
| Settlement Quotation | 96.1250 |
| First margin call date | 18 ago 2026 |
| Total | 16,020,833 USD |

**Implied rate:** 100 − 96.1250 = **3.8750%**.

**Notional:** 40 × 5,000,000 = **USD 200,000,000**.

**Total reconciliation:** 40 × 5,000,000 × (1/12) × 96.1250% = **16,020,833.33**, matching the screen. Per contract that is USD 400,520.83.

**Risk:** BPV of USD 41.67 per contract, so the position carries a **DV01 of USD 1,666.67** per basis point. Note that despite a notional 75% smaller in EUR-equivalent terms than Example 1, this position's DV01 is a quarter of it — because the reference period is one month rather than three. Notional is a poor guide to risk across STIR contracts; DV01 is the only comparable measure.

**Direction:** long, so the book gains if the December 2026 average overnight SOFR settles below 3.8750%.

**Settlement mechanics:** this contract settles against the **arithmetic average** of daily SOFR across December 2026, which is why the maturity is month-end rather than an IMM date — the reference period is the calendar month itself.

### 8.3 Example 3 — DDI / cupom cambial (Sell)

| Field | Value |
|---|---|
| Future | DDI_FUT (DDI FUTURE) |
| Exchange | BMF (B3) |
| Contract code | *(blank)* |
| Underlying | BRL BMF DDI (cupom cambial) |
| Contract currency | DOL (USD-denominated notional) |
| Contract size | 50,000 (shown signed negative for the sell) |
| Direction | **Sell** |
| Maturity | APR 27 → 01 abr 2027 |
| Quantity | 1.000,00 contracts → −50,000,000 |
| Settlement Yield | 6.0130% |
| Settlement Price (PU) | 96,346.9800 |
| First margin call date | 17 ago 2026 |
| Total | −251,639,042 BRL |

**Notional:** 1,000 × USD 50,000 = **USD 50,000,000**, signed negative for the short.

**PU reconciliation:** applying the §2.2 formula with a 227-day ACT/360 period,

100,000 / (1 + 6.0130% × 227/360) = **96,346.975**, matching the quoted Settlement Price of 96,346.98.

The 227 days runs from 17 August 2026 — the same date as the first margin call — to 1 April 2027, which confirms both the day count basis and that the PU is being discounted from trade date to expiry.

**Total reconciliation:** the quotation configuration expresses this contract *flat on 100,000.0000* (§2.3), and the contract notional is USD 50,000 — so one PU point equals USD 0.50. On that basis:

1,000 × 96,346.98 × USD 0.50 = **USD 48,173,490**, and translating at an implied USD/BRL of **5.2236** gives **BRL 251,639,042**, matching the screen exactly (signed negative for the sell). The PU base and point value follow from configured contract properties; the FX rate is the one figure here that is inferred from the Total rather than displayed, so it should be confirmed against the rate actually applied.

**Risk:** unlike the 100 − rate contracts, the BPV is not constant. At the quoted level, a one basis point rise in the cupom cambial moves PU by 5.85 points, worth USD 2.93 per contract, so the position runs approximately **USD 2,926 (≈ BRL 15,287) per basis point**. That sensitivity decays as the contract approaches expiry, because the discounting period shortens.

**Direction:** the book is **short PU**. PU falls as the yield rises, so the position gains if the cupom cambial rises and loses if it falls — the opposite rate exposure to Examples 1 and 2. Because the buy/sell convention on PU-quoted contracts inverts relative to the 100 − rate intuition, the sign convention should be confirmed against desk convention rather than assumed from the screen alone.

**Currency dimension:** the notional is in USD, the PU is in USD points, and the margin and settlement are in BRL at the prevailing FX rate. The position therefore carries **both interest rate risk and BRL/USD exposure**, and the daily variation margin is a BRL cash flow whose size depends on the FX rate as well as the rate move. This is the only one of the four contracts with that characteristic.

### 8.4 Example 4 — SOFR 3M (Sell)

| Field | Value |
|---|---|
| Future | SOFR 3MONTHFUT |
| Exchange | CME |
| Contract code | *(blank)* |
| Underlying | USD SOFR CMP (compounded) |
| Currency | USD |
| Contract size | 1,000,000 |
| Direction | **Sell** |
| Maturity | MAR 27 → 16 jun 2027 |
| Quantity | 400,00 contracts → 400,000,000 |
| Settlement Quotation | 95.9600 |
| First margin call date | 18 ago 2026 |
| Total | 95,960,000 USD |

**Implied rate:** 100 − 95.9600 = **4.0400%**.

**Notional:** 400 × 1,000,000 = **USD 400,000,000**.

**Total reconciliation:** 400 × 1,000,000 × 0.25 × 95.96% = **95,960,000**, matching the screen exactly.

**Risk:** BPV of USD 25.00 per contract, so the position carries a **DV01 of USD 10,000** per basis point — the largest of the four, despite the contract being a fifth the size of the SOFR 1M contract, because of the number of lots and the three-month reference period.

**Direction:** this is the only **short** position in a 100 − rate contract in this set. Short the price means long the rate: the book gains if the compounded SOFR rate over the reference quarter settles **above** 4.0400%, and loses if it settles below. Short duration — the opposite exposure to Examples 1 and 2, which are both long.

**Expiry — the point worth dwelling on.** The contract month is MAR 27 but the maturity resolves to **16 June 2027**. This is not an inconsistency: the March 2027 contract references the three-month period running from the third Wednesday of March 2027 (17 March) to the third Wednesday of June 2027 (16 June), and because the settlement rate is **compounded SOFR over that quarter**, it cannot be known until the quarter has elapsed. The contract therefore expires at the *end* of its reference period. Both dates check out against the calendar, and the logic is set out in §6.1.

**Contrast with Example 1.** Both are three-month contracts with a EUR/USD 1,000,000 contract size and an identical BPV of 25 per contract. The difference is entirely in the rate construction: EURIBOR is a forward-looking term rate published at the start of the period, so its contract expires at the start; compounded SOFR only exists once the period has run, so its contract expires at the end. Same product shape, opposite date logic.

### 8.5 The four examples side by side

| | EURIBOR 3M | SOFR 1M | SOFR 3M | DDI |
|---|---|---|---|---|
| Exchange | LIFFE / ICE | CME | CME | B3 (BMF) |
| Underlying type | Forward-looking term rate | Backward-looking overnight **average** | Backward-looking overnight **compounded** | FX-linked onshore USD rate |
| Underlying field | EURIBOR3M | USD SOFR AVG | USD SOFR CMP | BRL BMF DDI |
| Quotation | 100 − rate | 100 − rate | 100 − rate | Yield + PU |
| Quoted level | 97.3950 → 2.6050% | 96.1250 → 3.8750% | 95.9600 → 4.0400% | 6.0130% → PU 96,346.98 |
| Contract size | EUR 1,000,000 | USD 5,000,000 | USD 1,000,000 | USD 50,000 |
| Contracts | 265 | 40 | 400 | 1,000 |
| Notional | EUR 265,000,000 | USD 200,000,000 | USD 400,000,000 | USD 50,000,000 |
| Direction | Buy (long duration) | Buy (long duration) | **Sell** (short duration) | Sell (short PU, gains if rate rises) |
| Expiry rule | IMM — 2 bd before 3rd Wed | Month-end | 3rd Wed, 3 months after contract month | First business day of month |
| Expiry vs reference period | **Start** of period | **End** of period | **End** of period | Discounted to expiry |
| Maturity | 14 sept 2026 | 31 dic 2026 | 16 jun 2027 | 01 abr 2027 |
| BPV per contract | EUR 25.00 | USD 41.67 | USD 25.00 | ≈ USD 2.93 (decays to expiry) |
| Position DV01 | EUR 6,625 | USD 1,666.67 | **USD 10,000** | ≈ USD 2,926 / BRL 15,287 |
| Settlement currency | EUR | USD | USD | BRL (notional in USD) |
| Total | 64,524,187 EUR | 16,020,833 USD | 95,960,000 USD | −251,639,042 BRL |

## 9. Risk profile

STIR futures are **linear in the underlying rate**: there is no optionality, no premium and no volatility input. The exposures that matter are:

- **Directional rate risk**, measured by DV01 (§3). Linear and symmetric — a long position loses as much on a rate rise as it gains on an equivalent fall.
- **Curve risk.** A position is exposed to a specific point on the curve, defined by the contract's reference period. Positions in different expiries of the same contract express curve views (spreads, butterflies) rather than outright direction, and their combined DV01 can be near zero while significant risk remains.
- **Basis risk.** A futures position hedging an OTC exposure leaves residual basis: different reference periods, different fixing conventions, and — for SOFR versus EURIBOR or versus a term rate — different underlying rate constructions entirely. A hedge that matches DV01 does not necessarily match risk.
- **Roll risk.** Contracts expire. Maintaining an exposure beyond the current expiry requires rolling into the next contract at whatever the calendar spread is trading, which is an execution cost and a market risk in itself.
- **Margin funding and liquidity risk.** Variation margin is a daily cash obligation (§7). Adverse moves consume cash immediately regardless of the eventual outcome.
- **FX risk**, where the settlement currency differs from the notional currency — as in the DDI example, where a BRL-settled contract carries USD notional.
- **Convexity/model risk.** Treating a futures-implied rate as a forward rate without the convexity adjustment introduces a systematic error that grows with maturity (§7).

Counterparty credit risk, by contrast, is largely absent: the clearing house is the counterparty and the position is collateralized daily. This is the main structural risk difference from an OTC equivalent.

## 10. Glossary of fields seen in the Murex screens

- **Future / Description**: the contract traded, pointing to the contract definition that holds exchange, currency, underlying and contract size.
- **Exchange**: the venue and clearing house. Determines expiry rules, settlement mechanics and margining.
- **Contract code**: the contract's external identifier (an ISIN on the EURIBOR contract; blank on the other two — see §11).
- **Underlying**: the reference rate the contract settles against — a term rate, an overnight average, or an onshore FX-linked rate. Determines how the final settlement price is computed (§5).
- **Contract size**: the notional per contract. Combined with the reference period it determines the basis point value (§3).
- **Maturity**: the contract month, with the resolved expiry date alongside it. The rule linking the two differs by contract (§6).
- **Quantity**: the number of contracts, with the resulting notional (contracts × contract size) shown alongside. Signed negative for a sell.
- **Settlement Quotation**: the contract price under the 100 − rate convention; implied rate = 100 − quotation.
- **Settlement Yield / Settlement Price**: the yield-and-PU pair used by PU-quoted contracts in place of a single price (§2.2).

Fields on the **quotation configuration** screen behind the contract (§2.3):

- **Quotation**: the named quotation setup attached to the contract, holding the convention below.
- **Main quotation**: the convention itself — *100-X* (quoted as a price, rate = 100 − price) or *Yield* (quoted as the rate, with the price derived from it). Determines how every quoted level on the trade screen is interpreted.
- **Yield type**: the annualization basis of a yield-quoted contract (*Annual* on the DDI).
- **Price expression**: what the price is expressed against — *Percentage* for the 100-X contracts, or *Flat on <base>* for PU-quoted contracts, where the base is the PU denominator (100,000 for the DDI).
- **Historized quotation**: which value is stored in the contract's price history — *Main* (the traded quotation) or *Price*. The DDI trades on yield but historizes PU, so its time series is in PU terms.
- **Decimals**: precision of the main quotation. Yield-quoted contracts carry more decimals than price-quoted ones because the rate is discounted into a five-figure PU.
- **Price factor**: 1 on the price-quoted contracts here, 0 on the yield-quoted one.
- **Tick / Time factor rounding rule and decimals**: rounding applied to quoted levels and time factors. Set to *None* on all four contracts here, so the decimal settings are not applied as rounding.
- **First margin call date**: when daily variation margining begins for the trade. Driven by the booking date, not by the contract.
- **Total**: the position value at the quoted price — for 100 − rate contracts, contracts × contract size × tenor fraction × price/100 (§4); for PU contracts, contracts × PU × point value, translated into the settlement currency.

## 11. Open items and gaps in this document

1. **Contract code populated inconsistently.** The EURIBOR contract carries an ISIN; both SOFR contracts and the DDI have the field blank. Confirm whether this is a deliberate static-data choice or a gap, since an external identifier matters for reconciliation and reporting.
2. **DDI FX rate is inferred, not sourced** (§8.3). The PU base of 100,000 and the resulting USD 0.50 point value are confirmed by the quotation configuration (§2.3), but the implied USD/BRL of 5.2236 is reverse-engineered from the Total. Confirm the rate actually applied and its date convention (PTAX in particular).
3. **Tick and time-factor rounding rules are set to None on all four contracts** (§2.3), so the configured tick decimals are not applied as rounding. Confirm this is intended, given that exchange tick sizes constrain tradable levels — and resolve why the two SOFR quotation setups carry different tick decimals (2 on RFR 1M, 0 on RFR 3M) despite being the same contract family.
4. **PU buy/sell sign convention** (§8.3). The direction semantics of PU-quoted contracts invert relative to 100 − rate contracts. Confirm the desk and system convention rather than inferring it from the screen.
5. **No margin or settlement screens captured.** Initial margin parameters, the variation margin account and the final settlement price mechanics are described conceptually here but not documented as configured. Those screens should be added to make this a complete operational reference.
6. **Convexity adjustment treatment not documented** (§7). Whether and how the adjustment is applied when futures are used in curve construction is a valuation question this document raises but cannot answer from the captures.
7. **No non-USD/EUR RFR example.** The SOFR pair documents the average-versus-compounded distinction directly (§5, §8.4). An equivalent SONIA or €STR contract would confirm whether the same expiry-at-end-of-period logic (§6.1) is configured consistently across RFR families.
