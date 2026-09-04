# Equity OTC Options

## Purpose of this document

This is a reference document on over-the-counter equity option trades: what the product is, how the trade screen and the option contract interact, how the premium and its settlement are computed, and how the terms are represented in Murex. It is meant to be read on its own — a new joiner or anyone unfamiliar with the product should come away understanding the mechanics, not just recognizing the trade capture screen.

The three worked examples in §11 are an **American call on a single stock, physically settled**, a **European call on an index, cash settled**, and a **European put on an index, sold rather than bought**. Between them they cover both option types, both directions, both exercise styles, both settlement methods, both underlying types and both settings of the nominal flag.

**A note on identifiers.** Portfolio and counterparty identifiers are omitted throughout. Instrument and contract identifiers are retained, since the underlying of an equity option is a listed instrument rather than a party.

## 1. Overview: what an equity OTC option is

An equity OTC option is a **bilaterally negotiated contract giving the buyer the right, but not the obligation, to buy (a call) or sell (a put) an equity underlying at an agreed strike price**, on or before an agreed date, in exchange for a premium paid to the seller.

Three features distinguish it from an exchange-listed option:

- **Terms are negotiated, not standardized.** Strike, maturity, size, exercise style and settlement method are all chosen per trade rather than selected from a listed series. The examples here carry strikes to three decimal places and sizes to six — precision no listed contract would offer.
- **No clearing house, no margining.** The trades sit bilaterally between the two parties. `Margining: No` on all three contracts, so there is no daily variation margin: the buyer pays a premium up front and carries counterparty exposure to the seller thereafter.
- **The contract is a template, not a listing.** An OTC option still references a **contract** (§4), but that contract defines conventions for a family of trades rather than a specific tradable series.

The buyer's risk is limited to the premium; the seller's, on a naked position, is not.

## 2. Direction

Direction is set by the portfolio action — *buys from* or *sells to* the counterparty:

| | Buy | Sell |
|---|---|---|
| Premium | **Paid** at inception | **Received** at inception |
| Right of exercise | **Held** | Granted to the counterparty |
| Maximum loss | The premium | **Unbounded** on a naked call; strike less premium on a put |
| Maximum gain | Unbounded on a call; strike less premium on a put | The premium |
| Counterparty exposure | To the seller performing at exercise | Limited once premium is received |

Examples 1 and 2 are **buys**; Example 3 is a **sell**.

The asymmetry matters: a bought option carries credit exposure to the seller for the life of the trade, since the seller must perform if the option finishes in the money. A sold option carries no such exposure once the premium is received — only market risk.

## 3. The financial definition

The trade screen's central block defines the option:

| Field | Meaning |
|---|---|
| **In Nominal** | Whether the size is expressed as a nominal amount (*Yes*) or a quantity of underlying units (*No*) — see §5. |
| **Call / Put** | Option type. |
| **Delivery / Cash** | Settlement method — physical delivery of the underlying, or a cash difference (§6.2). |
| **American / European** | Exercise style (§6.1). |
| **Digital** | Whether the payoff is a fixed amount rather than the difference between spot and strike. *No* on all three. |
| **Fwd start** | Whether the option starts at a future date, with that date alongside (§7.2). |
| **Maturity** | Expiry date. |
| **Cap** | Whether the payoff is capped, with a third option whose label varies by option type (§6.3). |
| **Strike** | The exercise price. |
| **Total return** | Whether the option references a total-return underlying. *No* on all three. |
| **Flex details / Exercise convention** | Sub-screens for non-standard exercise arrangements; unpopulated and not captured (§14). |
| **Payment date / Premium / Total / Sales margin** | The premium and its settlement (§8). |
| **Fx Rule / Use another currency for total** | How currency conversion applies to the premium. *Basic* and *No* on all three. |

## 4. The option contract

Every trade references a **contract**, whose definition sits behind it:

| Field | Meaning |
|---|---|
| **Contract** | The contract identifier. |
| **Contract type** | **Otc** on all three, as against a listed contract. |
| **Market** | The market grouping — an OTC market denominated in a currency. |
| **Underlying group** | *Equity* on all three. |
| **Type** | **Simple** for a single stock, **Index** for an index (§4.1). |
| **Description** | Free text naming the family. |
| **Trading clauses** | The convention set applying to trades on this contract (§4.2). |

### 4.1 Contract Type drives the settlement default

The three contracts differ in exactly the way that matters:

| | Stock contract | Index contract (EUR) | Index contract (USD) |
|---|---|---|---|
| **Type** | **Simple** | **Index** | **Index** |
| Market | OTC EUR | OTC EUR | **OTC USD** |
| Description | OTC stock options in EUR | OTC index options in EUR | OTC index options in USD |
| **Default settlement** | **Delivery** | **Cash** | **Cash** |
| Maturities | EUR STK OP | *(blank)* | *(blank)* |

The settlement default follows from the underlying: **shares can be delivered, an index cannot**. An index option is therefore always cash settled, and the contract encodes that as the default.

### 4.2 Trading clauses

The clauses are otherwise near-identical across all three contracts:

| Clause | Value on all three |
|---|---|
| **Style** | **European** |
| Total return | No |
| Underlying conventions | Inherited |
| **Margining** | **No** |
| **Premium payment** | **+2 OPEN DAYS** |
| Option lot size | 1.00 |
| Strike quotation | Inherited from underlying |
| Premium quotation | **Price** |
| Premium notation | **Decimal, 4 decimals** |
| Premium / Cash / Settlement Price Rounding Rules | None |
| Cash Rounding applied on | Unitary Premium, 0 decimals |
| Strike step | 0.0000 |
| Option with parity | No |

Two of these carry real weight:

- **`Premium payment: +2 OPEN DAYS`** is the settlement convention for the premium, and it reconciles on the trades (§8.2).
- **`Strike step: 0.0000`** means strikes are unconstrained — any value is bookable. This is what allows the strike of 28,599.172 in Example 3, and it is a defining freedom of OTC against listed options, where strikes come in fixed increments.

### 4.3 The contract sets defaults; the trade can override them

**All three contracts specify a European style. Example 1 is booked American.**

This is the single most important thing to understand about the relationship between the two screens: the contract supplies conventions, but the **trade carries the actual terms**. Reading exercise style off the contract definition would get Example 1 wrong.

The same applies to settlement: the contract holds a default, the trade holds what was agreed.

## 5. Size: quantity or nominal

The **In Nominal** flag determines how the size figure is interpreted:

| Example | In Nominal | Size | Interpretation |
|---|---|---|---|
| 1 | **No** | 5,300,000.000000 | A quantity — shares of the underlying |
| 2 | **Yes** | 1,669.000000 | A nominal amount |
| 3 | **No** | 143.360794 | A quantity |

Note that the flag does **not** change how the premium is billed — `Total = size × premium` holds in all three cases (§8.1). What it changes is how the size is interpreted for the payoff at exercise.

Sizes are carried to six decimal places. Example 3's 143.360794 is not a share count in any ordinary sense; it is the output of a sizing calculation, and OTC trades routinely carry such figures where a listed contract would require whole lots.

## 6. Exercise, settlement and payoff modifiers

### 6.1 Exercise style

- **European** — exercisable only at maturity. Examples 2 and 3.
- **American** — exercisable at any time up to maturity. Example 1.

American style matters most on a physically settled single-stock option, where early exercise can be rational ahead of a dividend. It is also why Example 1's American style, against a European contract default, is worth noticing rather than glossing over (§4.3).

A third style, Bermudan — exercisable on a defined set of dates — would be configured through the *Flex details* or *Exercise convention* screens, neither of which is populated here (§14).

### 6.2 Settlement

- **Delivery** — physical settlement: on exercise of a call, the buyer pays the strike and receives the shares. Example 1.
- **Cash** — the in-the-money amount settles as cash. Examples 2 and 3, and necessarily so for an index (§4.1).

### 6.3 The Cap field, and a label that changes

The **Cap** radio offers three settings, and **the third option's label depends on the option type**:

| Example | Type | Cap options offered |
|---|---|---|
| 1 | Call | No / Yes / **MFloor** |
| 2 | Call | No / Yes / **MFloor** |
| 3 | **Put** | No / Yes / **MCap** |

All three are set to **No**, so no example exercises the feature. A capped option limits the payoff beyond a second level — a capped call stops gaining above it, a floored put stops gaining below it — which is why the label flips with the option type. The mechanism is documented here from the field labels only, not from behaviour (§14).

### 6.4 Digital and Total return

- **Digital** — a payoff of a fixed amount if the option finishes in the money, rather than the difference between spot and strike. *No* on all three.
- **Total return** — whether the underlying is a total-return series including dividends, rather than a price series. *No* on all three, at both trade and contract level.

## 7. Dates

### 7.1 The date fields

| Field | Meaning |
|---|---|
| **Fwd start** and its date | Whether the option starts forward, and when (§7.2). |
| **Maturity** | Expiry. |
| **Payment date** | When the premium settles (§8.2). |

### 7.2 Forward start

All three examples have **`Fwd start: Yes`**. The option's life begins at the stated start date rather than at trade date, and the premium settles relative to that start.

Note that a forward-starting option in this sense — a defined start date — is not the same thing as a forward-start option in the structured sense, where the strike itself is fixed at a future date by reference to the then-prevailing spot. All three examples carry a strike agreed at inception (§14).

### 7.3 A maturity falling on a Saturday

Example 3's maturity is **7 August 2027, a Saturday**. Option expiries conventionally fall on business days, and a weekend expiry would normally be rolled. This appears to be an unadjusted date and should be confirmed (§14).

## 8. The premium

### 8.1 How the Total is built

**Total = Size × Premium**

All three reconcile:

| Example | Size | Premium | Total |
|---|---|---|---|
| 1 | 5,300,000.000000 | 0.0050 | **26,500.0000** ✓ |
| 2 | 1,669.000000 | 21.5760 | **36,010.3440** ✓ |
| 3 | 143.360794 | 1,221.1846 | **175,070.0000** ✓ |

The premium is quoted **per unit** — per share on a single-stock option, per index unit on an index option — consistent with `Premium quotation: Price` and `Premium notation: Decimal, 4 decimals` on the contract.

**Sales margin** is a commercial spread on the premium; zero on all three, so the mechanism is documented from the field alone (§14).

### 8.2 Premium settlement: +2 open days

The contract sets **`Premium payment: +2 OPEN DAYS`**, and the trades bear it out:

| Example | Start date | Premium payment | Business days |
|---|---|---|---|
| 1 | Thursday 18 sept 2025 | Monday 22 sept 2025 | Fri 19, Mon 22 = **+2** ✓ |
| 2 | Friday 22 may 2026 | Tuesday 26 may 2026 | Mon 25, Tue 26 = **+2** ✓ |
| 3 | Wednesday 06 may 2026 | Monday 11 may 2026 | Thu 7, Fri 8, Mon 11 = **+3** |

Examples 1 and 2 confirm the convention directly. Example 3 appears to be three business days on a plain weekday count — but reconciles with +2 open days **if 8 May is a holiday on the applicable calendar**, which it is in several European markets. The calendar attached to the contract should be confirmed rather than the gap treated as an error (§14).

### 8.3 A negative premium

Example 2's premium reads **−21.5760** while its Total is positive at 36,010.3440, on a bought option — where Example 1's bought option shows a positive premium. The magnitude reconciles exactly against the size, so this is a **sign convention rather than a calculation difference**, but what the sign denotes is not determinable from the screens and should be confirmed (§14).

## 9. Currency and the underlying quotation

Two currency-related points are worth checking on any new trade.

**The contract's market currency and the trade's premium currency need not agree.** Example 3 is booked on a contract whose market is **OTC USD** and whose description reads "OTC index options in USD", yet its premium is denominated in **EUR** and its underlying is a euro-denominated index. Example 2 books the **same underlying** on the equivalent **EUR** contract. Same instrument, two different contracts, one of them in the wrong currency family. This should be confirmed (§14).

**The strike levels on the index examples sit well above the headline level of the widely quoted price index.** Example 3's premium of 1,221.1846 against a strike of 28,599.172 is 4.27% of strike — a proportion entirely normal for a 1.25-year put near the money, which implies the underlying is trading near that strike rather than far below it. The series referenced therefore appears to be quoted on a different basis from the familiar price index — a total-return or rebased series. Worth confirming, since it affects how any strike on that underlying should be read (§14).

## 10. What the trade does not show

Two things a reader might expect are absent from these screens:

- **No valuation or Greeks.** The capture shows the premium paid, not the option's current value, delta, gamma, vega or theta. Those come from the pricing and risk screens, which were not captured (§14).
- **No exercise or expiry record.** Whether an option has been exercised, and on what terms, is a lifecycle event not visible here.

## 11. Worked examples

### 11.1 Example 1 — American call on a single stock, physically settled, bought

| Field | Value |
|---|---|
| Direction | **Buys from** |
| Contract | OTC STK EU — OTC stock options in EUR |
| Contract type / Market / Type | Otc / OTC EUR / **Simple** |
| Instrument | TEF.MC, market CONTINUO |
| Cut-off | CONTINUO / FIXING |
| **In Nominal** | **No** — size is a share quantity |
| Size | **5,300,000.000000** shares |
| **Type / Settlement / Style** | **Call / Delivery / American** |
| Digital / Cap / Total return | No / No (No·Yes·MFloor) / No |
| **Fwd start** | **Yes — 18 sept 2025** |
| **Maturity** | **07 sept 2026** |
| **Strike** | **6.000** |
| Payment date | 22 sept 2025 |
| **Premium** | **0.0050** EUR, Fx Rule Basic |
| **Total** | **26,500.0000** |
| Sales margin | 0.00000 |

**Position:** a bought call — the right to buy 5.3 million shares at 6.00 EUR, exercisable at any time to the September 2026 expiry, with physical delivery on exercise.

**Premium:** 5,300,000 × 0.0050 = **26,500.00** ✓. At 0.083% of the strike this is a cheap option, consistent with a strike well above the prevailing share price.

**Premium settlement** falls two open days after the 18 September start — Friday the 19th, then Monday the 22nd ✓ (§8.2).

**American style against a European contract default.** The contract specifies European; this trade is booked American (§4.3). On a physically settled single-stock call that is a substantive choice, not a formality — early exercise ahead of a dividend can be rational, which a European option would not permit.

**Physical delivery** is available here because the underlying is a share. Exercise means paying 6.00 per share and receiving 5.3 million shares — a considerable settlement obligation, and the reason delivery-settled single-stock options need operational attention that cash-settled index options do not.

### 11.2 Example 2 — European call on an index, cash settled, bought

| Field | Value |
|---|---|
| Direction | **Buys from** |
| Contract | OTC IND EU — OTC index options in EUR |
| Contract type / Market / Type | Otc / OTC EUR / **Index** |
| Instrument | .STOXX50E, market FB |
| Cut-off | FB / FIXING |
| **In Nominal** | **Yes** — size is a nominal amount |
| Size | **1,669.000000** |
| **Type / Settlement / Style** | **Call / Cash / European** |
| Digital / Cap / Total return | No / No (No·Yes·MFloor) / No |
| **Fwd start** | **Yes — 22 may 2026** |
| **Maturity** | **18 dic 2026** |
| **Strike** | **19,778.000** |
| Payment date | 26 may 2026 |
| **Premium** | **−21.5760** EUR |
| **Total** | **36,010.3440** |

**Position:** a bought index call, cash settled at the December 2026 expiry — roughly seven months.

**Premium:** 1,669 × 21.5760 = **36,010.344** ✓, reconciling on the magnitude despite the negative sign (§8.3).

**Cash settlement is not a choice here.** An index cannot be delivered, so the contract's default and the trade agree (§4.1, §6.2).

**`In Nominal: Yes`** — the only example where the size is a nominal rather than a quantity. Note that this does not change the premium calculation, which is size × premium in every case (§5).

**Two things to confirm** on this trade: the **negative premium** (§8.3), and the **strike level** relative to the underlying's quoted basis (§9).

### 11.3 Example 3 — European put on an index, cash settled, sold

| Field | Value |
|---|---|
| Direction | **Sells to** |
| Contract | OTC IND US — OTC index options in **USD** |
| Contract type / Market / Type | Otc / **OTC USD** / Index |
| Instrument | .STOXX50E, market FB |
| Cut-off | FB / FIXING |
| **In Nominal** | **No** |
| Size | **143.360794** |
| **Type / Settlement / Style** | **Put / Cash / European** |
| Digital / Cap / Total return | No / No (No·Yes·**MCap**) / No |
| **Fwd start** | **Yes — 06 may 2026** |
| **Maturity** | **07 ago 2027** — a **Saturday** |
| **Strike** | **28,599.172** |
| Payment date | 11 may 2026 |
| **Premium** | **1,221.1846** EUR |
| **Total** | **175,070.0000** |

**Position:** the only **sold** option in the set. The book receives the premium and grants the counterparty the right to put the index at 28,599.172 in August 2027. Market risk runs the other way from Examples 1 and 2: the book loses if the index falls below the strike, and its exposure is bounded only by the strike itself.

**Premium:** 143.360794 × 1,221.1846 = **175,069.99**, matching the displayed 175,070.0000 to display precision ✓

**A realistic premium.** At **4.27% of strike** for a 1.25-year put, this is a normal option price — and it is the observation that prompts the question in §9 about how the underlying is quoted, since a premium of that proportion implies the index is trading near the strike.

**The Cap label reads MCap** rather than MFloor, because this is a put (§6.3).

**Two items to confirm:** the **Saturday maturity** (§7.3), and the **contract currency mismatch** — a euro-denominated index with a euro premium, booked on a USD contract, where Example 2 books the same underlying on the EUR equivalent (§9).

**Premium settlement** is three business days after the start rather than two, which reconciles with the contract's +2 open days if 8 May is a holiday on the applicable calendar (§8.2).

### 11.4 The three examples side by side

| | Example 1 | Example 2 | Example 3 |
|---|---|---|---|
| **Direction** | Buy | Buy | **Sell** |
| Contract | OTC STK EU | OTC IND EU | **OTC IND US** |
| Contract Type | **Simple** (stock) | **Index** | **Index** |
| Contract market | OTC EUR | OTC EUR | **OTC USD** |
| Underlying | Single stock | Index | Index |
| **Option type** | **Call** | **Call** | **Put** |
| **Settlement** | **Delivery** | Cash | Cash |
| **Style** | **American** | European | European |
| Contract default style | European | European | European |
| Style overridden? | **Yes** | No | No |
| **In Nominal** | No | **Yes** | No |
| Size | 5,300,000.000000 | 1,669.000000 | 143.360794 |
| **Strike** | 6.000 | 19,778.000 | 28,599.172 |
| Digital / Cap / Total return | No / No / No | No / No / No | No / No / No |
| Cap third option label | MFloor | MFloor | **MCap** |
| Fwd start | 18 sept 2025 | 22 may 2026 | 06 may 2026 |
| Maturity | 07 sept 2026 | 18 dic 2026 | **07 ago 2027 (Sat)** |
| Option life | ~0.97 y | ~0.58 y | ~1.25 y |
| Payment date | 22 sept 2025 | 26 may 2026 | 11 may 2026 |
| Premium lag | **+2 open days** ✓ | **+2 open days** ✓ | +3 business days |
| **Premium** | 0.0050 | **−21.5760** | 1,221.1846 |
| Premium as % of strike | 0.08% | 0.11% | **4.27%** |
| Premium currency | EUR | EUR | EUR |
| **Total** | **26,500.0000** | **36,010.3440** | **175,070.0000** |
| Sales margin | 0 | 0 | 0 |
| Margining (contract) | No | No | No |

## 12. Risk profile

An option is a **non-linear** instrument, and its risks differ in kind from the delta-one products documented elsewhere:

- **Delta** — sensitivity to the underlying's price. Unlike a linear product, it changes continuously and ranges between zero and one (or minus one for a put).
- **Gamma** — the rate at which delta itself changes. A bought option is long gamma; a sold option is short it, and short gamma is the exposure that turns a small adverse move into a large one near expiry.
- **Vega** — sensitivity to implied volatility. The buyer is long volatility, the seller short. On a sold option like Example 3, a rise in implied volatility is a loss even if the index does not move.
- **Theta** — time decay, working for the seller and against the buyer.
- **Rho and dividend risk** — sensitivity to rates and to expected dividends on the underlying. Dividend risk is specific to equity options and is a genuine exposure on single-stock names, where a dividend change alters the forward and can trigger early exercise on an American option.
- **Counterparty credit risk.** With `Margining: No`, a bought option is an unsecured claim on the seller for the life of the trade. This is the principal structural difference from an exchange-listed option, where the clearing house stands between the parties.
- **Early exercise risk** on American options — the seller can be assigned at any time, which on a physically settled single-stock call means delivering shares at short notice.
- **Physical settlement risk** on delivery-settled options (§11.1). Exercise creates an obligation to deliver or take delivery of the underlying, with the operational and funding consequences that follow.
- **Assignment and expiry risk.** Options finishing near the money create uncertainty about whether they will be exercised, which is a real operational exposure around expiry.

## 13. Glossary of fields seen in the Murex screens

**Trade header**

- **Portfolio / buys from / sells to**: the book and the direction (§2).
- **Internal deal**: flags a trade between internal books; unticked on all three.
- **Contract**: the option contract the trade is booked under (§4).
- **Instrument**: the underlying, with its market alongside.
- **Cut-off**: the pricing source and cutoff basis (*FIXING* on all three).

**Financial definition**

- **In Nominal**: whether the size is a nominal amount or a quantity (§5).
- **Call / Put**: option type.
- **Delivery / Cash**: settlement method (§6.2).
- **American / European**: exercise style (§6.1).
- **Digital**: fixed-payoff option flag (§6.4).
- **Fwd start**: forward start flag and date (§7.2).
- **Maturity**: expiry date.
- **Cap**: payoff cap, with a third option labelled **MFloor** on a call and **MCap** on a put (§6.3).
- **Strike**: the exercise price.
- **Total return**: total-return underlying flag (§6.4).
- **Flex details / Exercise convention**: non-standard exercise configuration; unpopulated (§14).
- **Payment date**: premium settlement date (§8.2).
- **Premium**: per-unit premium (§8.1).
- **Fx Rule / Use another currency for total**: currency handling for the premium; *Basic* and *No* throughout.
- **Total**: size × premium (§8.1).
- **Sales margin**: commercial spread; zero throughout.
- **Additional flows**: supplementary flows; unticked throughout.

**Option contract**

- **Contract / Contract type**: the identifier and whether it is OTC or listed (*Otc* throughout).
- **Market**: the OTC market grouping and its currency (§9).
- **Underlying group / Type**: *Equity*, and **Simple** for a single stock or **Index** for an index (§4.1).
- **Description / Category / Cut-off**: descriptive fields.

**Trading clauses**

- **Style**: the contract's default exercise style — overridable on the trade (§4.3).
- **Settlement**: the contract's default settlement method (§4.1).
- **Total return / Maturities / Underlying conventions**: contract-level defaults.
- **Margining**: whether trades are margined; **No** throughout, which is what makes the premium an unsecured exposure (§12).
- **Premium payment**: the premium settlement lag (**+2 OPEN DAYS**) (§8.2).
- **Option lot size**: the trading unit (1.00 throughout).
- **Strike quotation**: how strikes are expressed (*Inherited from underlying*).
- **Premium quotation / Premium notation**: how the premium is quoted (*Price*, *Decimal* to 4 decimals).
- **Premium / Cash / Settlement Price Rounding Rules**: rounding; *None* throughout.
- **Cash Rounding applied on**: the base for cash rounding (*Unitary Premium*).
- **Strike step**: the permitted strike increment — **0.0000**, meaning unconstrained (§4.2).
- **Option with parity**: parity handling; *No* throughout.

## 14. Open items and gaps in this document

1. **The negative premium on Example 2** (§8.3). The magnitude reconciles exactly against the size, so this is a sign convention — but what a negative premium denotes on a bought option, when the other bought example shows a positive one, is not determinable from the screens.
2. **The contract currency mismatch on Example 3** (§9). A euro-denominated index with a euro premium is booked on a USD contract, while Example 2 books the same underlying on the EUR equivalent. Confirm whether the contract is merely a convention container or whether this is a booking error.
3. **The strike basis on the index examples** (§9). Strikes of 19,778 and 28,599 sit well above the headline level of the widely quoted price index, while Example 3's premium implies the underlying is trading near its strike. The series appears to be quoted on a different basis, and this should be confirmed since it governs how any strike on that underlying is read.
4. **Example 3's maturity falls on a Saturday** (§7.3). Confirm whether this is an unadjusted date and what adjustment applies.
5. **Example 3's premium settles three business days after start** where the contract specifies +2 open days (§8.2). This reconciles if 8 May is a holiday on the applicable calendar; confirm which calendar the contract uses.
6. **Digital, Cap, Total return, Flex details and Exercise convention are all unused** across the three examples. Those features are documented from field labels alone. A digital option, a capped option, or a Bermudan exercise schedule would each need its own treatment.
7. **Sales margin is zero on all three** (§8.1), so how a margin adjusts the premium and the total is undocumented.
8. **No valuation or Greeks captured** (§10). The premium paid is visible; the option's current value and sensitivities are not, and those are what a risk view depends on.
9. **No exercise or expiry example.** How an exercise is processed — notice, settlement, delivery on a physically settled option, assignment on a sold one — is described conceptually here but not documented from an actual event.
10. **No listed-option comparison.** All three are OTC. Where a listed equity option differs — standardized strikes and maturities, clearing, daily margining — is described in §1 but not documented from screens.
