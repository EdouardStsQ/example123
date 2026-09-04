# Long Futures (Bond Futures)

## Purpose of this document

This is a reference document on bond futures — exchange-traded futures on long-term government debt: what the product is, how the notional bond and deliverable basket work, how the quotation and valuation conventions differ from other futures, and how the terms are represented in Murex. It is meant to be read on its own — a new joiner or anyone unfamiliar with the product should come away understanding the mechanics, not just recognizing the trade capture screen.

The three worked examples in §9 are a **Euro-Bund**, a **French government bond (OAT)** and a **Long Gilt** contract. They share a contract size and a quotation setup, which makes the places where they differ — currency, direction, expiry convention, notional coupon and price level — the instructive part.

## 1. Overview: what a bond future is

A bond future is an **exchange-traded, standardized contract to deliver a government bond at a future date at a price agreed today**.

Three features define it:

- **Standardization.** Contract size, the notional bond specification, the eligible delivery basket, delivery dates and settlement mechanics are all fixed by the exchange. Only the number of lots and the price are chosen by the trader.
- **Central clearing and daily margining.** The clearing house is the counterparty to both sides. Positions are marked to market daily, with variation margin exchanged in cash on top of initial margin posted at inception. Bilateral counterparty credit exposure is replaced by exposure to the CCP.
- **Physical delivery against a basket.** This is the defining characteristic and the one that generates most of the product's complexity. At expiry the seller delivers an actual government bond — chosen by the seller from a list of eligible issues — rather than settling a cash difference. The contract references a **notional bond that does not exist**, and a conversion mechanism translates between that notional bond and whatever real bond is delivered.

Everything in §2 to §4 follows from that third point.

## 2. The notional bond and the deliverable basket

### 2.1 The notional bond

A bond future is not written on a specific security. It is written on a **hypothetical bond with a fixed coupon and a maturity band** — for example a 6% coupon bond with 8.5 to 10.5 years remaining term for the Eurex contracts, or a lower notional coupon for the Long Gilt. The exact specification is set by each exchange and should be read from the contract specification rather than assumed.

This matters more than it first appears. Because the notional coupon is fixed by convention and rarely revised, while market yields move continuously, the **price level of a bond future is largely a function of where market yields sit relative to that notional coupon**:

- When market yields are well **below** the notional coupon, the notional bond is worth more than par and the future trades well above 100.
- When market yields are **above** the notional coupon, the future trades below 100.

This is why the three examples in §9 sit at such different price levels — 123.940, 116.260 and 85.870 — and why **bond futures prices are not comparable across contracts**. A future at 85 is not "cheap" relative to one at 124; they reference different notional bonds in different markets. See §9.4.

### 2.2 The deliverable basket

Each contract has a list of **eligible bonds** that satisfy the issuer, maturity band and other criteria. The seller (the short) chooses which one to deliver. Because eligible bonds have different coupons and maturities, they are not worth the same amount, and a mechanism is needed to make them interchangeable at a single futures price.

### 2.3 Conversion factors

Each deliverable bond is assigned a **conversion factor** by the exchange: approximately the price of that bond, per unit of face value, at which it would yield the notional coupon. The conversion factor normalizes each eligible bond onto the notional bond's basis.

The amount the buyer pays the seller at delivery — the **invoice amount** — is:

**Invoice amount = (Final settlement price × Conversion factor + Accrued interest) × Contract size / 100**

Two things follow. First, the invoice amount is *not* the position value shown on the trade screen (§5). Second, accrued interest enters here even though the future itself is quoted on a **clean** price basis (§3.2).

### 2.4 Cheapest-to-deliver (CTD)

Conversion factors are calculated at a single assumed yield and therefore only approximately equalize the deliverable bonds. In practice one bond in the basket is always marginally the most economical for the short to deliver — the **cheapest-to-deliver**.

The consequence is that a bond future does not track "the 10-year government bond" in the abstract; it **tracks its CTD**. The CTD determines the future's price behaviour, its duration and its sensitivity to yield moves. When yields move enough, the CTD can change to a different bond in the basket, and the future's risk characteristics shift with it — see §10.

### 2.5 The short's delivery options

Because the seller chooses what to deliver and, on some contracts, when within the delivery window, the short holds a bundle of embedded options: which bond (the **quality option**), and on some contracts timing flexibility within the delivery month. These options have value, and they are one reason a bond future does not price as a simple forward on the CTD. This is the main structural pricing difference between a bond future and an equivalent OTC forward.

## 3. Quotation conventions

### 3.1 Quoted on price, not on rate

Bond futures are quoted **directly as a price**, expressed as a percentage of face value. A quotation of 123.940 means 123.940% of face. The configuration field *Main quotation* reads **Price** on all three examples.

This is worth stating explicitly because other futures families invert the relationship — short-term interest rate contracts typically quote 100 minus the rate, and some bond futures markets (notably Australia and New Zealand) quote 100 minus yield rather than a price. **The quotation field must be read before any number on the trade screen is interpreted**; the same displayed figure means entirely different things under a *Price* convention and a *100-X* convention.

Under the price convention the directional logic is straightforward: **the price rises as yields fall**. A long position is long duration and gains when yields fall; a short position gains when yields rise.

### 3.2 Clean price — and why accrued interest still matters

The configuration carries a second field, *Price T.*, set to **Clean** on all three contracts. The future is quoted **excluding accrued interest**.

The distinction:

- **Clean price** — the quoted price, excluding interest accrued on the underlying bond since its last coupon.
- **Dirty price** (or invoice/settlement price) — clean price plus accrued interest; what actually changes hands.

Bond futures are quoted clean because a clean price moves only with yields, not with the mechanical daily accrual of coupon interest, which makes prices comparable over time. But accrued interest does not disappear — it re-enters at delivery through the invoice amount in §2.3. **Anyone reconciling a delivery amount against the futures price will not tie out unless both the conversion factor and accrued interest are applied.**

### 3.3 How the convention is configured

All three contracts share the same quotation setup, so the convention is configured at the family level rather than per contract:

| Quotation field | Bund | OAT | Long Gilt |
|---|---|---|---|
| Quotation | FUTPR 3DEC | FUTPR 3DEC | FUTPR 3DEC |
| **Main quotation** | **Price** | **Price** | **Price** |
| **Price type** | **Clean** | **Clean** | **Clean** |
| Notation | Std | Std | Std |
| Decimals | 3 | 3 | 3 |
| Price factor | 1 | 1 | 1 |
| Tick rounding rule | None | None | None |
| Tick decimals | 0 | 0 | 0 |
| Time factor rounding rule | None | None | None |
| Time factor decimals | 0 | 0 | 0 |
| Price expression | Percentage | Percentage | Percentage |
| Historized quotation | Main | Main | Main |

- **Main quotation: Price** and **Price type: Clean** together define how to read the quoted level — a clean price as a percentage of face.
- **Decimals: 3** matches the captures: 123.940, 116.260, 85.870.
- **Price expression: Percentage** is why the position value formula in §5 divides by 100.
- **Historized quotation: Main** means the stored price history is the quoted clean price.
- **Tick and time-factor rounding rules are set to None** on all three, so the tick decimal settings are not applied as rounding. Exchange tick sizes are real constraints on tradable levels, so this is worth confirming as intentional.

## 4. Contract size and tick value

All three contracts have a **contract size of 100,000** units of face value in their respective currencies. Since the price is a percentage of face:

**Value of one contract = Contract size × Price / 100**

and one tick of 0.01 price points is worth **Contract size × 0.0001 = 10 currency units per contract** — EUR 10 on the Bund and OAT, GBP 10 on the Long Gilt.

Note that tick value is a *price* sensitivity, not a yield sensitivity. Unlike a short-term interest rate future, where the basis point value is fixed by contract size and tenor, a bond future's sensitivity to yield depends on the duration of its cheapest-to-deliver — see §6.

## 5. Position value: how the "Total" field is built

For all three examples the Total reconciles exactly as:

**Total = Number of contracts × Contract size × Price / 100**

There is **no tenor fraction** in this formula. That is a structural difference from short-term interest rate futures, where the position value is scaled by the length of the reference period: a bond future's quoted price is already the full value of the notional bond as a percentage of face, so nothing further is applied.

Two cautions:

- This is the **clean** position value. It is not the delivery invoice amount, which additionally requires the conversion factor and accrued interest (§2.3).
- It is a market value, not a risk measure. Comparing Totals across contracts says nothing useful about relative risk (§6).

## 6. Risk measurement: why notional and Total mislead

The price sensitivity of a bond future is driven by the **modified duration of its cheapest-to-deliver**, scaled by the conversion factor:

**DV01 of the future ≈ DV01 of the CTD / Conversion factor of the CTD**

The practical consequences:

- **Notional is not risk.** A 10-year contract and a 2-year or 5-year contract on the same notional carry very different DV01s, because their deliverable baskets have very different durations. Comparing positions across the curve by notional or by Total is meaningless.
- **DV01 is not constant.** It changes as yields move, as the contract approaches delivery, and discontinuously if the CTD switches to another bond in the basket.
- **DV01 is not on the screen.** It has to be computed from the CTD and its conversion factor, neither of which appears on the trade capture. Any risk view built from the captured fields alone will be incomplete.

## 7. Expiry and delivery conventions

The delivery month is set by a quarterly cycle (March, June, September, December), but the rule converting a contract month into a last trading date **differs by exchange**, and the difference is material — the two Eurex contracts and the Long Gilt below share a SEP 26 contract month yet expire three weeks apart:

| Contract | Expiry rule | Example |
|---|---|---|
| Bund (Eurex) | Two exchange days before the **10th calendar day** of the delivery month, which is the delivery day | SEP 26 → **08 sept 2026** (delivery day 10 Sept, a Thursday; two exchange days prior is Tuesday the 8th) |
| OAT (Eurex) | Same Eurex convention | SEP 26 → **08 sept 2026** |
| Long Gilt (LIFFE / ICE) | Two business days before the **last business day** of the delivery month | SEP 26 → **28 sept 2026** (last business day is Wednesday 30 Sept; two business days prior is Monday the 28th) |

Both check out against the calendar. The lesson for a reference document is the same as for any futures family: **the contract month label does not determine the expiry date** — the exchange convention does, and it must be read from the contract definition rather than inferred.

## 8. Margining

**Initial margin** is posted at inception as collateral against potential future exposure. **Variation margin** is the daily cash exchange of the mark-to-market move. The *First margin call date* field marks where daily margining begins; in all three examples it sits shortly after the trade date and is driven by the booking date rather than by anything contract-specific.

Two consequences:

- **Funding.** Variation margin is a real daily cash flow. An adverse move consumes cash immediately, irrespective of whether the position is eventually profitable.
- **Credit.** Counterparty credit risk is largely replaced by exposure to the clearing house, collateralized daily. This is the main structural risk difference from an OTC forward on the same bond.

## 9. Worked examples

### 9.1 Example 1 — Euro-Bund (Buy)

| Field | Value |
|---|---|
| Future | EUROBUND EUREX — *EUROBUND 10Y EUREX* |
| Exchange | EUREX |
| Contract code | DE000C16GSR0 (ISIN) |
| Underlying field | DEM LONG FUTURE |
| Currency | EUR |
| Contract size | 100,000 |
| Direction | **Buy** |
| Maturity | SEP 26 → 08 sept 2026 |
| Quantity | 100,00 contracts → 10,000,000 |
| Settlement quotation | 123.940 |
| First margin call date | 18 ago 2026 |
| Total | 12,394,000 EUR |

**Notional:** 100 × 100,000 = **EUR 10,000,000**.

**Total reconciliation:** 100 × 100,000 × 123.940% = **12,394,000**, matching the screen. Per contract, EUR 123,940.

**Tick value:** EUR 10 per contract per 0.01 price point, so EUR 1,000 for the position.

**Direction:** long the future is **long duration**. The book gains if German government bond yields fall (price rises) and loses if they rise.

**Price level:** at 123.940 the contract trades well above par, consistent with a notional coupon materially above prevailing German yields (§2.1).

### 9.2 Example 2 — French government bond / OAT (Buy)

| Field | Value |
|---|---|
| Future | FRENCH FUT — *FUT CONT ON LONG TERM FREN GOV BOND* |
| Exchange | BD EUR GVT |
| Contract code | DE000C1J3L18 (ISIN) |
| Underlying field | EUR 1M A |
| Currency | EUR |
| Contract size | 100,000 |
| Direction | **Buy** |
| Maturity | SEP 26 → 08 sept 2026 |
| Quantity | 37,00 contracts → 3,700,000 |
| Settlement quotation | 116.260 |
| First margin call date | 18 ago 2026 |
| Total | 4,301,620 EUR |

**Notional:** 37 × 100,000 = **EUR 3,700,000**.

**Total reconciliation:** 37 × 100,000 × 116.260% = **4,301,620**, matching the screen. Per contract, EUR 116,260.

**Direction:** long duration in French government debt.

**Relationship to the Bund position:** both contracts are EUR-denominated, share a contract size, a quotation setup and an expiry date, and reference a comparable segment of their respective sovereign curves. Held together, a long Bund and long OAT position is an outright duration position; held in opposite directions and sized by DV01, the pair expresses a **sovereign spread view** between French and German debt. Note that the 7.68-point gap between the two prices is *not* a direct read of that spread — each contract prices off its own cheapest-to-deliver and conversion factor, so extracting an implied yield spread requires that detail (§2.4).

### 9.3 Example 3 — Long Gilt (Sell)

| Field | Value |
|---|---|
| Future | LONG GILT LIFFE |
| Exchange | LIFFE (now ICE Futures Europe) |
| Contract code | GB00H44WPL97 (ISIN) |
| Underlying field | GBP 6M ANACT |
| Currency | GBP |
| Contract size | 100,000 |
| Direction | **Sell** |
| Maturity | SEP 26 → 28 sept 2026 |
| Quantity | 1,00 contract → 100,000 |
| Settlement quotation | 85.870 |
| First margin call date | 18 ago 2026 |
| Total | 85,870 GBP |

**Notional:** 1 × 100,000 = **GBP 100,000**.

**Total reconciliation:** 1 × 100,000 × 85.870% = **85,870**, matching the screen.

**Direction:** this is the only **short** position of the three. Short the future is **short duration**: the book gains if UK gilt yields rise (price falls) and loses if they fall. As the seller, this is also the side that holds the delivery options described in §2.5 — the choice of which eligible gilt to deliver.

**Price level below par.** At 85.870 this contract trades well below 100, while both Eurex contracts trade well above it. This is not a signal that gilts are distressed relative to Bunds; it is a direct consequence of the notional coupon convention (§2.1). The Long Gilt contract uses a **lower notional coupon** than the Eurex contracts, so with UK yields above that notional coupon the contract prices below par, while the Eurex contracts — with a higher notional coupon and lower prevailing yields — price well above it. This is the clearest illustration in the set of why bond futures prices cannot be compared across contracts.

**Size.** A single-lot position. Useful as a clean illustration of per-contract economics, but not a representative ticket size.

**Different expiry.** Despite sharing a SEP 26 contract month with both Eurex contracts, this contract expires on 28 September rather than 8 September, because ICE and Eurex use different last-trading-day rules (§7).

### 9.4 The three examples side by side

| | Bund | OAT | Long Gilt |
|---|---|---|---|
| Exchange (as configured) | EUREX | BD EUR GVT | LIFFE |
| Contract code | DE000C16GSR0 | DE000C1J3L18 | GB00H44WPL97 |
| Underlying field | DEM LONG FUTURE | EUR 1M A | GBP 6M ANACT |
| Currency | EUR | EUR | GBP |
| Contract size | 100,000 | 100,000 | 100,000 |
| Quotation | Price / Clean | Price / Clean | Price / Clean |
| Quoted price | 123.940 | 116.260 | 85.870 |
| Price vs par | Well above | Above | **Below** |
| Contracts | 100 | 37 | 1 |
| Notional | EUR 10,000,000 | EUR 3,700,000 | GBP 100,000 |
| Direction | Buy (long duration) | Buy (long duration) | **Sell** (short duration) |
| Contract month | SEP 26 | SEP 26 | SEP 26 |
| Expiry rule | Eurex — 2 exch. days before the 10th | Eurex — 2 exch. days before the 10th | ICE — 2 bus. days before last bus. day |
| Maturity | 08 sept 2026 | 08 sept 2026 | **28 sept 2026** |
| Tick value per contract | EUR 10 | EUR 10 | GBP 10 |
| Total | 12,394,000 EUR | 4,301,620 EUR | 85,870 GBP |

The set is useful precisely because so much is held constant. Identical contract size, identical quotation configuration and an identical contract month make the genuine differences stand out: two currencies, both directions, two expiry conventions, and three price levels that reflect notional coupon conventions rather than relative value.

## 10. Risk profile

Bond futures are **linear in the price of the underlying deliverable**, but their risk is more involved than that suggests because the underlying is a basket rather than a single security.

- **Directional duration risk.** The dominant exposure, measured by DV01 (§6) rather than by notional. Long the future is long duration.
- **CTD switch risk.** The future tracks its cheapest-to-deliver. A large enough yield move can make a different bond in the basket cheapest, at which point the contract's duration and DV01 change — a discontinuity that a simple duration hedge will not anticipate.
- **Delivery option risk.** The short holds the quality and timing options (§2.5). For the long, this is a risk: the bond received is the one least favourable to them among the eligible set.
- **Basis risk.** The relationship between the future and the cash bond — the net basis, and its expression as an implied repo rate — is a market in its own right. A futures position hedging a cash bond position leaves basis exposure that a DV01-matched hedge does not eliminate.
- **Sovereign spread risk.** Positions across contracts (Bund against OAT, or against Gilt) are spread rather than outright positions. Their combined DV01 may be near zero while significant spread risk remains.
- **FX risk.** The Long Gilt contract is GBP-denominated. In a EUR-reporting book, its value and its daily variation margin carry GBP/EUR exposure on top of the rate exposure.
- **Roll risk.** Contracts expire quarterly. Maintaining exposure requires rolling into the next delivery month at the prevailing calendar spread, which carries both execution cost and market risk.
- **Delivery and operational risk.** Unlike a cash-settled contract, an open short position at expiry creates an obligation to deliver an actual security. Positions must be rolled or closed before the last trading day unless delivery is intended, and delivery itself requires the bond to be available and settleable.
- **Margin funding risk.** Daily variation margin is a cash obligation (§8).

Counterparty credit risk, by contrast, is largely absent — the clearing house is the counterparty and the position is collateralized daily.

## 11. Glossary of fields seen in the Murex screens

- **Future / Description**: the contract traded, pointing to the contract definition holding exchange, currency, underlying and contract size.
- **Exchange**: the venue and clearing house. Determines expiry rules, delivery mechanics and margining. Populated inconsistently across these contracts — see §12.
- **Contract code**: the contract's external identifier. An ISIN on all three bond futures here (DE-prefixed on both Eurex-style contracts, GB-prefixed on the Long Gilt).
- **Underlying**: the reference recorded against the contract. Note that on these contracts it does *not* identify the notional bond or the deliverable basket — see §12.
- **Contract size**: face value per contract (100,000 on all three). Combined with the price convention it gives the per-contract value and the tick value (§4).
- **Maturity**: the contract month, with the resolved last trading date alongside. The rule linking the two differs by exchange (§7).
- **Quantity**: the number of contracts, with the resulting notional (contracts × contract size) shown alongside.
- **Settlement quotation**: the contract's clean price, as a percentage of face value.
- **First margin call date**: when daily variation margining begins for the trade. Driven by the booking date, not by the contract.
- **Total**: the position value at the quoted price — contracts × contract size × price/100 (§5). A clean market value, not the delivery invoice amount.

Fields on the **quotation configuration** screen behind the contract (§3.3):

- **Main quotation**: the convention — *Price* on all three here, meaning the quoted level is a price rather than a rate or a yield-derived figure.
- **Price type**: *Clean* or dirty. Clean on all three: the quoted price excludes accrued interest (§3.2).
- **Price expression**: *Percentage* — the price is a percentage of face, which is why the position value formula divides by 100.
- **Historized quotation**: which value is stored in the contract's price history (*Main* — the quoted clean price — on all three).
- **Decimals**: precision of the quoted price (3 on all three).
- **Price factor**: 1 on all three.
- **Tick / Time factor rounding rule and decimals**: rounding applied to quoted levels and time factors. Set to *None* on all three, so the decimal settings are not applied as rounding.

## 12. Open items and gaps in this document

1. **The `Underlying` field does not identify the notional bond on any of the three contracts.** It reads *DEM LONG FUTURE* on the Bund, *EUR 1M A* on the OAT and *GBP 6M ANACT* on the Long Gilt — the latter two resembling money-market index references rather than long-term government bond specifications. A plausible benign explanation is that this field points at a curve or index used for valuation rather than at the deliverable, but that should be confirmed. For a physically deliverable contract, the notional bond specification and the eligible basket are the economically defining features, and neither is visible on the captured screens.
2. **The `Exchange` field is populated inconsistently.** The Bund carries *EUREX* and the Long Gilt *LIFFE* — actual venues — while the OAT carries *BD EUR GVT*, which looks like an internal grouping code, despite its contract code being a DE-prefixed ISIN of the same form as the Bund's. Confirm which contracts should carry venue names and which an internal taxonomy, since inconsistent identification of the same kind of attribute creates reconciliation problems downstream.
3. **Conversion factors, deliverable baskets and CTD data are not captured.** These drive the contract's economics (§2), its DV01 (§6) and its delivery invoice amount (§2.3), and none of them appears on the trade or contract screens documented here. Where this data is held, and how it feeds valuation and risk, should be documented to make this a complete reference.
4. **Notional coupon and maturity band per contract are not shown.** §2.1 and §9.3 explain the price levels in terms of the notional coupon convention, but the actual specifications should be verified against each exchange's current contract specification rather than taken from this document.
5. **Tick rounding rules are set to None on all three contracts** (§3.3), so configured tick decimals are not applied as rounding. Confirm this is intended given that exchange tick sizes constrain tradable levels.
6. **No 100 − yield example.** Some bond futures markets — Australia and New Zealand in particular — quote on 100 minus yield rather than on price, which changes how the quoted level, the position value and the direction of risk must all be read (§3.1). If such contracts are booked, they need separate treatment and an example would be worth adding.
7. **No delivery or margin screens captured.** Initial margin parameters, the delivery process and final settlement mechanics are described conceptually here but not documented as configured.
