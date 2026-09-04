# Physical Commodities — Spot & Forward

## Purpose of this document

This is a reference document on physically-settled commodity trades: what the product is, how spot and forward trades differ, how the economics and risk work, and how the terms are represented in Murex. It is meant to be read on its own — a new joiner or anyone unfamiliar with the product should come away understanding the mechanics, not just recognizing the trade capture screen.

The two worked examples in §7 are **carbon emissions allowances** (EUA and UKA), because those are the trades available. Emissions are an atypical physical commodity — dematerialized and delivered by registry transfer rather than by moving goods — so §3 sets out how physical delivery works across the main commodity families (gold and precious metals, base metals, energy, agriculturals, emissions) before the carbon-specific detail in §4. That context matters when reading the product setup screens, because several fields that carry real meaning for gold or crude are deliberately left empty for emissions.

## 1. Overview: what a physical commodity trade is

A physical commodity trade is a bilateral agreement to exchange a **quantity of a commodity** against **cash**, at an **agreed price**, on an **agreed date**, with the commodity actually delivered rather than cash-settled against a reference price.

Three structural choices define the trade:

- **Delivery mode — Physical vs. Financial.** Physical means the seller must actually deliver the commodity — transfer allowances between registry accounts, move bullion between vault accounts, hand over warehouse warrants, lift barrels at a terminal — and the buyer must take delivery. Financial (cash-settled) means no commodity moves; the trade settles as a cash difference against a reference price. This single field determines whether the back office must generate a delivery instruction or merely a cash flow, so it drives the entire downstream settlement and accounting path.
- **Commodity vs. Currency vs. Commodity vs. Commodity.** "Commodity vs. Currency" is the standard case documented here — commodity on one leg, cash on the other. A commodity-vs-commodity trade exchanges one product for another (e.g. a grade, location or quality swap) and is a different structure.
- **Spot vs. Forward** — how far out delivery sits. See §4.

Both parties are obliged to perform: there is no premium and no election. The buyer takes the full upside and downside of the price move, and the seller takes the mirror image.

## 2. Anatomy of the trade — the economic terms

| Term | What it does |
|---|---|
| **Commodity** | The specific product being delivered (EUA, UKA, gold, a crude grade, a metal). Points to a product definition holding the physical characteristics — see §6. |
| **Direction (Buy / Sell)** | Whether our book receives the commodity and pays cash (Buy) or delivers the commodity and receives cash (Sell). |
| **Quantity + Unit** | How much, in the product's unit of measure — metric tonnes (MT) for carbon and base metals, troy ounces for gold, barrels for crude, MMBtu or MWh for gas and power. |
| **Price + Currency per Unit** | The agreed price per unit, and the currency it is paid in. |
| **Volume factor** | Multiplier converting the booked quantity into underlying commodity units — relevant where trades are booked in lots (an LME copper lot is 25 MT; a gold bar is ~400 troy oz). A factor of 1.00000 means the quantity is stated directly in the underlying unit. |
| **Physical Delivery date** | When the commodity must be delivered. |
| **Payment date** | When the cash must be paid. **Not necessarily the same date** — see §4.3. |
| **Series** | The price fixing series used for revaluation and mark-to-market (here CLOSE — the closing price series). |

**Notional = Quantity × Price × Volume factor.** This is the cash amount that changes hands at settlement, and also the size of the price exposure.

## 3. Commodity families: what "physical" actually means by product

"Physical delivery" means something different in each commodity family, and that difference is exactly what the quality, form and delivery-term fields in the product setup exist to capture.

| Family | Examples | Typical unit | What delivery actually is | Quality / form / delivery term |
|---|---|---|---|---|
| **Emissions** | EUA, UKA | MT (1 MT = 1 allowance = 1 t CO₂e) | Transfer between registry accounts | **None** — dematerialized, no physical specification |
| **Precious metals** | Gold, silver, platinum | Troy ounce (also kg) | Transfer of allocated bars, or of an unallocated account balance, at a named vault location | Fineness (e.g. 995 / 999), bar form (400 oz Good Delivery, 1 kg), *loco* (London, Zurich) |
| **Base metals** | Copper, aluminium, zinc | MT (LME lots of 25 MT) | Transfer of warehouse warrants | Exchange grade (e.g. Grade A copper), form (cathode, ingot, billet), named warehouse |
| **Crude & refined products** | Brent, WTI, gasoil | Barrels or MT | Lifting at a terminal, pipeline nomination, or cargo transfer | Grade and assay (API gravity, sulphur), Incoterms (FOB, CIF, DES), load/discharge port and date window |
| **Natural gas / LNG** | TTF, Henry Hub, JKM | MMBtu, MWh, therms | Delivery at a hub or entry/exit point, or a cargo discharge | Calorific value, delivery point, delivery window |
| **Power** | Baseload, peak | MWh | Delivery to a grid node across a delivery period | Load shape (baseload/peak), delivery zone — **not storable** |
| **Agriculturals** | Wheat, corn, coffee | MT, bushels | Delivery of graded lots at an approved elevator or warehouse | Grade, moisture, origin, crop year |

### 3.1 Gold as the contrasting case

Gold is worth spelling out because it exercises nearly every field that emissions leaves blank, and because it is the family most often traded alongside carbon on a commodities desk.

- **Unit.** Gold is quoted per **troy ounce** (31.1035 g), not per metric tonne — so a gold trade uses a different unit of measure from the carbon examples in §7, and the volume factor becomes relevant where trades are booked in bars or kilos rather than ounces.
- **Quality.** Fineness is a real contractual term: London Good Delivery gold requires a minimum fineness of 995 parts per thousand, while retail-style kilobars are typically 999.9. This is what the *Default quality* field is for.
- **Form.** A 400 oz Good Delivery bar, a 1 kg bar and a 100 oz bar are not interchangeable for delivery purposes even at the same fineness. This is what *Default form* is for.
- **Delivery term.** Gold delivery is quoted *loco* — loco London, loco Zurich, loco Hong Kong — meaning the location where title transfers. Metal in London and metal in Zurich trade at different prices precisely because location is part of the contract. This is the precious-metals analogue of an Incoterm, and what *Default delivery term* is for.
- **Allocated vs. unallocated.** Allocated metal is title to identified, numbered bars held for the client; unallocated metal is a general claim on the dealer's metal balance and therefore an **unsecured credit exposure to that dealer**, not ownership of bullion. Economically similar, legally and operationally very different — this distinction has no analogue in emissions, where a registry holding is always a holding.
- **Carry.** Gold has genuine storage and insurance costs, and a genuine convenience yield in the form of the **lease rate** — metal can be lent out for income. Gold forwards therefore price off the funding rate *net of* the lease rate (§4.2), and because above-ground stocks are enormous relative to consumption, the gold curve sits in contango almost permanently. Carbon, base metals and crude behave quite differently.

The practical point for reading the screens: when the product is gold, the quality, form and delivery-term fields carry contractual meaning and must be populated. When the product is an emissions allowance, they are blank because there is nothing to populate.

## 4. Spot vs. Forward

### 4.1 The distinction

- A **spot** trade delivers at (or within the market's standard settlement lag of) the trade date, at the prevailing market price. Economically it is an immediate exchange: you own the commodity now, and price risk between trade and delivery is negligible.
- A **forward** trade delivers at an agreed future date, at a price fixed today. Between trade date and delivery the trade carries a live mark-to-market, counterparty credit exposure, and funding implications. Nothing settles until the delivery and payment dates arrive.

The economic exposure is the same in both cases — full, linear exposure to the commodity price. The difference is *when* it crystallizes and what happens in between.

### 4.2 Forward pricing: cost of carry

The forward price is not a forecast of where the spot price will be. It is the spot price adjusted for the cost of holding the commodity until delivery:

**F = S × (1 + (r + storage − convenience yield) × T)**

where *r* is the funding rate, *storage* is the cost of holding the physical, *convenience yield* is the benefit of having the physical in hand, and *T* is time to delivery. What separates the commodity families is which of those terms actually matters:

- **Emissions** — storage cost is effectively zero (an allowance is a registry entry) and there is no meaningful convenience yield, because allowances are not consumed in production but surrendered against an annual compliance cycle. The formula collapses to **roughly pure funding cost**, so carbon curves normally sit in contango at approximately the risk-free rate, and a carbon forward is close to a spot position plus a funding position. Distortions appear around compliance surrender deadlines, when short-dated demand can tighten the front of the curve.
- **Gold** — storage and insurance are real but small relative to value, and the convenience yield takes the concrete form of the **lease rate**, so gold forwards price at roughly **F ≈ S × (1 + (r − lease rate) × T)**. With above-ground stocks vastly exceeding annual consumption, gold is rarely physically squeezed and the curve is in contango almost permanently.
- **Base metals and crude** — storage is expensive and capacity-constrained, and convenience yield is large and volatile because a refinery or smelter genuinely needs the physical input. When the physical market is tight, convenience yield exceeds carry and the curve flips into **backwardation**. Curve shape here carries real information about physical tightness.
- **Power** — electricity cannot be stored at scale, so the cost-of-carry arbitrage that links spot and forward simply does not hold. A power forward is an expectation of the average spot price over the delivery period plus a risk premium, not a carried spot position.

Do not carry the carbon intuition across to the other families.

### 4.3 Delivery date vs. payment date — a settlement risk worth naming

These are two separate fields and they do not have to match. When they match, the exchange is effectively delivery-versus-payment: neither side is exposed to the other at the moment of settlement. When payment lags delivery, **the delivering party is unsecured for the length of the lag** — it has given up the commodity and is waiting for cash. This is a genuine counterparty exposure, not a booking detail, and it is exactly the kind of thing that has to be modelled correctly downstream in settlement and accounting. Example 2 in §7.2 has a three-day lag.

## 5. Emissions allowances as a physical commodity

Both worked examples are carbon allowances, so the specifics matter:

- **EUA (EU Allowance)** is the tradable unit of the EU Emissions Trading System. One EUA confers the right to emit one tonne of CO₂-equivalent. It is quoted and settled in EUR.
- **UKA (UK Allowance)** is the equivalent unit under the UK ETS, the separate scheme the UK has operated since 2021. It is quoted and settled in GBP.
- **They are not fungible.** A UKA cannot be surrendered for EU compliance, or vice versa, so the two instruments trade at independent prices and a position in one is only an imperfect hedge for the other — a real basis risk if the two are ever used as proxies for each other. (The EU and UK have committed to linking their schemes; linkage would materially change this relationship, so the current status should be checked rather than assumed from this document.)
- **Delivery is a registry transfer**, not a physical movement. There is no vault, warehouse, terminal, transport, quality specification or Incoterm — which is what distinguishes emissions from every other family in §3.
- **Demand is driven by an annual compliance cycle**: installations covered by each scheme must surrender allowances equal to their verified emissions, which concentrates flow around surrender deadlines and auction calendars.
- **The unit "MT" is nominally a mass unit but here counts allowances** — one MT = one allowance = one tonne CO₂e. Worth being explicit about, because it can read as if physical tonnage is being shipped.

## 6. Reading the Physical Product Description screen

The product definition sits behind the Commodity field and describes what is actually being delivered. For the two carbon products it reads as follows.

| Field | EUA | UKA | What it configures |
|---|---|---|---|
| Label / Description | EUA / CARBON EUA | UKA / CARBON UKA | The product identifier and its description. |
| Type | EMISSIONS | EMISSIONS | The commodity family. Drives which characteristics and conversions are relevant. |
| Past Cash Evaluation | Spot Price | Spot Price | How already-realized cash flows are evaluated. |
| Physical deliverables generation | ✔ | ✔ | Whether the product generates downstream **delivery obligations** (here, registry transfer instructions) rather than cash flows alone. Ticked here — this is what makes the trade genuinely physical in operational terms. |
| Default quality | *(blank)* | *(blank)* | Grade or specification of the delivered product — gold fineness (995/999), Grade A copper, a crude assay. Not applicable: an allowance has no quality dimension. |
| Default form | *(blank)* | *(blank)* | Physical form — a 400 oz Good Delivery gold bar, a copper cathode, an aluminium billet. Not applicable. |
| Default delivery term | *(blank)* | *(blank)* | Delivery basis — *loco London* for gold, a named LME warehouse for metals, FOB/CIF/DES for crude. Not applicable: a registry transfer has no location or shipping terms. |
| Product denomination | **Gross amount** | **Net amount** | How the traded amount is denominated. **These two products are configured differently — see below.** |
| Volumetric density conversion | ✗ | ✗ | Volume↔mass conversion — barrels to tonnes for crude via API gravity. Not applicable. |
| Caloric value conversion | ✗ | ✗ | Mass↔energy conversion — used for gas, LNG and coal. Not applicable. |

**Open item — Gross vs. Net denomination.** EUA is set up as *Gross amount* and UKA as *Net amount*, despite the two being economically analogous instruments configured identically in every other respect. This may be deliberate, or it may be a static-data inconsistency between two product definitions created at different times. It should be confirmed with whoever owns the commodity static data before this document asserts a meaning for the difference, because the denomination basis can affect how amounts are computed and booked downstream.

## 7. Worked examples

### 7.1 Example 1 — EUA Carbon Spot (Buy)

| Field | Value |
|---|---|
| Delivery mode | Physical |
| Structure | Commodity vs. Currency |
| Commodity | EUA (CARBON EUA) |
| Direction / Quantity | **Buy** 32,000,000 MT |
| Currency | EUR |
| Price | 81.9600 EUR per MT |
| Series | CLOSE |
| Volume factor | 1.00000 |
| Physical Delivery | 27 ago 2026 |
| Payment | 27 ago 2026 |

**Notional:** 32,000,000 × 81.96 = **2,622,720,000 EUR**.

**Direction:** our book **buys** the allowances — long EUA, paying cash and receiving allowances into the registry account. We gain if EUA prices rise and lose if they fall, on the full notional.

**Why this is a spot trade:** physical delivery and payment fall on the same date (27 ago 2026), at or immediately after trade date, and the price is the prevailing market level. Delivery and payment coinciding means this settles delivery-versus-payment — no settlement lag exposure, in contrast to Example 2.

**Sanity check on the terms:** the price of 81.96 EUR/tonne is consistent with where EUA has traded in 2026 ([EUA around €82/t in 2026](https://www.openpr.com/news/4618478/eu-ets-carbon-price-tracker-2026-epignosis-insights-reports-eua)), so the price is market-realistic. The **size is not**: 32 million allowances in a single bilateral clip is on the order of an entire day's traded volume in the EUA market and a material share of the annual EU cap. Treat this as a test-environment volume rather than a market-representative one.

### 7.2 Example 2 — UKA Carbon Forward (Sell)

| Field | Value |
|---|---|
| Delivery mode | Physical |
| Structure | Commodity vs. Currency |
| Commodity | UKA (CARBON UKA) |
| Direction / Quantity | **Sell** 14,000,000 MT |
| Currency | GBP |
| Price | 59.2500 GBP per MT |
| Series | CLOSE |
| Volume factor | 1.00000 |
| Physical Delivery | 14 dic 2026 |
| Payment | 17 dic 2026 |

**Notional:** 14,000,000 × 59.25 = **829,500,000 GBP**.

**Direction:** our book **sells** the allowances forward — short UKA. We are obliged to deliver 14 million UKAs in December 2026 at 59.25, whatever the market price is by then. If UKA rallies, we deliver at below market and lose on the full notional; the loss is unbounded in principle. This is the opposite exposure to Example 1, in a different scheme and a different currency.

**Why this is a forward trade:** delivery sits roughly three and a half months after trade date at a price fixed today. Until December the trade carries a live mark-to-market against the UKA forward curve, counterparty credit exposure, and funding cost on the position.

**The three-day settlement lag.** Delivery is 14 dic 2026 but payment is 17 dic 2026. As the seller, our book transfers 14 million allowances on the 14th and does not receive the £829.5m until the 17th — three days unsecured against the counterparty, for the full notional. Whether that is intended (a market or scheme convention) or a booking artifact is worth confirming; either way it is real credit exposure and needs to be reflected in settlement and exposure reporting, not netted away as if the trade were DVP.

**Sanity check on the terms:** a UKA price in the high £50s is plausible — UKA has historically traded at a discount to EUA, with the gap sensitive to the EU–UK linkage process. As with Example 1, the size (14 million UKAs) is far larger than a normal single bilateral clip in a market as small as the UK ETS, so treat it as test data.

### 7.3 What the two examples show together

| | Example 1 — EUA | Example 2 — UKA |
|---|---|---|
| Type | Spot | Forward |
| Direction | Buy (long) | Sell (short) |
| Scheme / Currency | EU ETS / EUR | UK ETS / GBP |
| Quantity | 32,000,000 MT | 14,000,000 MT |
| Price | 81.9600 EUR/MT | 59.2500 GBP/MT |
| Notional | 2,622,720,000 EUR | 829,500,000 GBP |
| Delivery vs. payment | Same day (DVP) | Payment 3 days after delivery |
| Time to delivery | Immediate | ~3.5 months |
| Product denomination | Gross amount | Net amount |

Between them they cover both directions, both carbon schemes, both currencies, both settlement timing patterns, and both denomination settings — which is why they work well as the pair of reference examples.

## 8. Risk profile

These are **linear, delta-one products**. The payoff is symmetric and proportional to the price move:

**P&L = Quantity × (Market price − Trade price)** for a long position; the reverse for a short.

The practical consequences:

- **Price risk is the full notional.** A €1/tonne move on Example 1 is €32,000,000 of P&L. A £1/tonne move on Example 2 is £14,000,000. There is no buffer: the first unit of price movement hits the position at full size.
- **Downside is unbounded on the short.** The seller in Example 2 has no cap on its loss if UKA rallies before December.
- **FX risk.** Example 2 is denominated in GBP. In a EUR-functional book, the position carries GBP/EUR translation exposure on top of the commodity price exposure, and the two need to be hedged separately.
- **Delivery and settlement risk.** This is the risk dimension that does not exist for a cash-settled trade at all: the commodity must actually arrive in the right account, vault or terminal on the right date. Failed or delayed registry transfers, account restrictions, and the payment lag in §4.3 are operational and credit exposures specific to physical settlement. For gold this extends to the allocated/unallocated distinction (§3.1); for warehoused metals, to warrant transfer and storage arrangements.
- **Basis risk between related products.** EUA and UKA are separate instruments. A long EUA position does not hedge a short UKA position — the two prices are correlated but not linked, and the residual is a real exposure. The same applies across grades, locations and *loco* points in other families: metal in London is not metal in Zurich.
- **Counterparty credit over the forward's life.** A spot trade extinguishes credit exposure almost immediately. A forward carries mark-to-market exposure to the counterparty from trade date until delivery — three and a half months in Example 2.

## 9. Valuation

- **Spot trade:** at or after its delivery date, it is essentially a settled transaction — the commodity and the cash have moved. Before that, mark-to-market against the spot price is trivially small given the short horizon.
- **Forward trade:** MTM = (Forward price for the delivery date at valuation − Trade price) × Quantity, discounted from the payment date to today. The forward price comes from the commodity forward curve for that product, built on the carry relationship in §4.2; the *Series* field (CLOSE) identifies the fixing series used to construct it. For a short position, a rise in the forward curve produces a loss.

## 10. Glossary of fields seen in the Murex screens

- **Delivery mode**: Physical or Financial — whether the commodity is actually delivered or the trade is cash-settled. Drives whether delivery obligations are generated downstream.
- **Commodity vs. Currency**: the trade structure — a quantity of commodity exchanged against cash, as opposed to commodity-vs-commodity.
- **Commodity**: the product being traded; points to the Physical Product Description (§6).
- **Buy / Sell + quantity + unit**: direction and size, in the product's unit of measure — MT for carbon and base metals, troy ounces for gold, barrels for crude. For emissions, one MT = one allowance = one tonne CO₂e.
- **Price + currency per unit**: the agreed price and its currency; notional = quantity × price × volume factor.
- **Series**: the price fixing series used for revaluation and curve construction (CLOSE = closing price series).
- **Volume factor**: multiplier converting booked quantity into underlying commodity units; 1.00000 means quantity is already in the underlying unit. Relevant where trades are booked in lots or bars.
- **Physical Delivery date**: when the commodity must be delivered (for emissions, when the registry transfer must occur).
- **Payment date**: when cash must be paid. May differ from the delivery date — see §4.3.
- **Portfolio / Counterpart**: the book carrying the position and the counterparty to the trade.
- **Type (EMISSIONS)**: the commodity family in the product definition, determining which physical characteristics and conversions are relevant. Other values drive the precious metals, base metals, energy and agricultural behaviours described in §3.
- **Past Cash Evaluation**: how already-realized cash flows are evaluated (Spot Price on both products here).
- **Physical deliverables generation**: whether the product generates delivery obligations downstream — ticked on both, which is what makes these operationally physical trades.
- **Default quality / form / delivery term**: physical characteristics and delivery basis — fineness, bar form and *loco* for gold; grade, form and warehouse for base metals; assay and Incoterms for crude. Blank for emissions, which have no physical specification.
- **Product denomination (Gross / Net amount)**: how the traded amount is denominated. Configured inconsistently between the two carbon products — see the open item in §6.
- **Volumetric density / Caloric value conversions**: unit conversions for liquids, gases and solid fuels (volume↔mass via density, mass↔energy via calorific value). Not applicable to emissions and unticked on both.

## 11. Open items and gaps in this document

1. **Gross vs. Net product denomination** (§6) — the two carbon products are configured differently with no evident economic reason. Confirm whether deliberate.
2. **The Delivery and Settlement Details tabs were not captured.** For a physically-settled product these carry the mechanics that matter most operationally — delivery accounts, delivery instructions, settlement instructions and any delivery tolerances. This document describes physical delivery conceptually but cannot yet document how it is actually configured. These screens should be added.
3. **Trade sizes are not market-representative** (§7). Prices are realistic; volumes look like test-environment values. Flagged so the examples are not read as indicative of normal ticket size.
4. **Payment lagging delivery in Example 2** (§4.3) — confirm whether this reflects a market or scheme convention or a booking choice, and that the resulting unsecured exposure is captured in credit and settlement reporting.
5. **EU–UK ETS linkage status** (§5) — the relationship between EUA and UKA is subject to an ongoing policy process. Verify current status before relying on the non-fungibility and basis-risk commentary.
6. **No non-emissions worked example.** §3 describes how gold, base metals, energy and agriculturals differ, but both captured trades are carbon. A gold or base-metals trade capture would exercise the quality, form, delivery-term and conversion fields that sit empty here, and would turn this into a complete physical-commodities reference rather than a carbon-centred one with generic context.
