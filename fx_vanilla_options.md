# FX Vanilla Options

## Purpose of this document

This is a reference document on FX vanilla option trades: what the product is, why every FX option is simultaneously a call and a put, how the two currency amounts relate to the strike, how premiums are quoted and settled, and how the terms are represented in Murex. It is meant to be read on its own — a new joiner or anyone unfamiliar with the product should come away understanding the mechanics, not just recognizing the trade capture screen.

The seven worked examples in §11 span four currency pairs, both directions, both exercise styles, both settlement methods, three premium quotation conventions, three expiry cuts, and a **two-leg straddle** — which §10 explains as a strategy rather than treating as two unrelated tickets.

**A note on identifiers.** Portfolio and counterparty identifiers are omitted throughout. Currency pairs, strikes and amounts are retained, since those are the economics of the trade.

## 1. Overview: what an FX vanilla option is

An FX vanilla option is a bilaterally negotiated contract giving the buyer the **right, but not the obligation, to exchange one currency for another at an agreed rate on an agreed date**, in exchange for a premium.

Everything else in this document follows from one fact:

### 1.1 Every FX option is a call on one currency and a put on the other

An FX rate is a *ratio between two currencies*. Buying one currency necessarily means selling the other, so an option to buy currency A against currency B is, in exactly the same breath, an option to sell B against A. There is no such thing as a standalone "call" in FX — only a call on one leg and a put on the other, describing the same right.

This is why the screen shows the option type as a **pair**:

| Example | Notation | Which way it points |
|---|---|---|
| 1 | **Put CNH / Call USD** | Gains if USD strengthens against CNH |
| 2 | **Call AUD / Put EUR** | Gains if AUD strengthens against EUR |
| 3 | **Put PLN / Call EUR** | Gains if EUR strengthens against PLN |
| 4 | **Put USD / Call GBP** | Gains if GBP strengthens against USD |

**Reading only half the notation is the classic error.** "Call USD" alone is meaningless until you know what it is a call against. Always read both halves, and translate into a direction on the quoted pair before reasoning about the position.

A practical rule for a pair quoted as *base/quote* — CNH per USD, USD per EUR, and so on:

> **A call on the base currency gains when the quoted rate rises. A put on the base currency gains when it falls.**

### 1.2 What distinguishes these from listed options

- **Bilateral and unmargined.** `Margining` is unticked on every example, so there is no daily variation margin: the buyer pays a premium and carries counterparty exposure to the seller thereafter.
- **Fully negotiated terms.** Strikes carry four or five decimals, amounts carry seven, and expiries fall on any business day. Nothing is drawn from a standardized series.
- **Physical delivery is the default.** Six of the seven examples settle by delivery of both currencies (§6).

## 2. Direction

Direction is stated as **Buy** or **Sell** beside the call/put pair:

| | Buy | Sell |
|---|---|---|
| Premium | **Paid** | **Received** |
| Right of exercise | **Held** | Granted to the counterparty |
| Maximum loss | The premium | Potentially large — bounded by the currency move |
| Counterparty exposure | To the seller performing at exercise | None once premium is received |

Four of the seven examples are **buys**, three are **sells**.

## 3. The two currency amounts and the strike

Every FX option screen carries **two currency amounts**, and they are not independent:

**Amount(quote) = Amount(base) × Strike**

All seven reconcile exactly:

| Example | Pair | Amount 1 | Amount 2 | Ratio | Strike |
|---|---|---|---|---|---|
| 1 | USD/CNH | CNH 201,900,000 | USD 30,000,000 | 6.73000 | **6.7300** ✓ |
| 2 | EUR/AUD | AUD 49,050,000 | EUR 30,000,000 | 1.63500 | **1.6350** ✓ |
| 3 | EUR/PLN | PLN 3,277,500 | EUR 750,000 | 4.37000 | **4.3700** ✓ |
| 4 | GBP/USD | USD 47,477,500 | GBP 35,000,000 | 1.35650 | **1.35650** ✓ |
| 5–6 | USD/CNH | CNH 66,795,000 | USD 10,000,000 | 6.67950 | **6.6795** ✓ |
| 7 | EUR/USD | USD 43,146,389 | EUR 37,698,898.2088248 | 1.14450 | **1.1445** ✓ |

### 3.1 Which amount was the input

The decimals tell you which side was keyed and which was derived. In Examples 1 to 6 the base-currency amount is round (30,000,000 USD; 30,000,000 EUR; 750,000 EUR; 35,000,000 GBP; 10,000,000 USD) and the quote amount follows from multiplying by the strike.

**Example 7 reverses this.** The USD amount is the round-ish figure (43,146,389) and the **EUR amount carries seven decimals** — 37,698,898.2088248 — because it was derived by *dividing* by the strike. That is the signature of a trade sized in the quote currency rather than the base.

This matters when reconciling: knowing which amount is authoritative tells you which one to trust when rounding differences appear.

## 4. Expiry, cut and settlement dates

Three dates appear:

| Field | Meaning |
|---|---|
| **Maturity** | The expiry date — when the option can be exercised. |
| **Cut** | The **time of day** on the expiry date at which the option expires (§4.1). |
| **Settlement** | When the currencies are exchanged if the option is exercised. |

**Settlement is T+2 from expiry on all seven examples**, without exception:

| Example | Expiry | Settlement |
|---|---|---|
| 1 | Thu 18 mar 2027 | Mon 22 mar 2027 |
| 2 | Thu 17 sept 2026 | Mon 21 sept 2026 |
| 3 | Wed 09 sept 2026 | Fri 11 sept 2026 |
| 4 | Tue 19 ene 2027 | Thu 21 ene 2027 |
| 5–6 | Fri 20 nov 2026 | Tue 24 nov 2026 |
| 7 | Wed 02 sept 2026 | Fri 04 sept 2026 |

This mirrors the FX spot convention: exercise on the expiry date, deliver two business days later.

### 4.1 The cut

The **cut** is the expiry *time*, named after the market centre whose close it follows. Three appear across the examples:

| Cut | Centre |
|---|---|
| **TOK** | Tokyo |
| **NY** | New York |
| **WAR** | Warsaw |

The cut is not a formality. An FX option expires at a specific moment, and whether it finishes in or out of the money is decided by the rate at that instant. A position that is in the money at the Tokyo cut may be out of the money hours later at the New York cut on the same calendar day. The cut generally follows the currency pair's natural market — the Asian pair here uses Tokyo, the Polish pair Warsaw, the others New York.

## 5. Exercise style

| Setting | Meaning | Examples |
|---|---|---|
| **Standard** (American unticked) | **European** — exercisable only at expiry, at the cut | 1–6 |
| **American** ticked | Exercisable at any time up to expiry | **7** |

Six of the seven are European, which is the FX market norm — the interbank vanilla market is overwhelmingly European-style, and volatility is quoted on that basis. Example 7 is the single American option in the set.

A **Warrant** flag also appears on the screen, unticked throughout.

## 6. Settlement method: delivery or cash

| Setting | What happens at exercise | Examples |
|---|---|---|
| **Delivery** | Both currency amounts are exchanged in full at the strike | 1–6 |
| **Cash** | Only the in-the-money difference settles, **in a named currency** | **7** |

Example 7 shows `Cash` with a settlement currency of **EUR** alongside it. That second field matters: a cash-settled FX option produces a single net amount, and the currency it settles in has to be specified because either leg would be a valid choice.

The distinction is economically significant in FX in a way it is not for a cash-settled equity index option. A **delivery-settled** option that finishes in the money moves the full notional of both currencies — in Example 1, USD 30,000,000 against CNH 201,900,000. That is a substantial settlement obligation and a genuine funding and operational event. Cash settlement replaces it with a single difference payment.

## 7. The premium

### 7.1 Three quotation conventions, and why the unit label matters

The premium field is meaningless without the unit beside it, and **three different conventions appear across these seven trades**:

| Example | Quoted as | Applied to | Flat amount |
|---|---|---|---|
| 1 | **% USD** — 0.358400 | USD 30,000,000 | **107,520.00** ✓ |
| 2 | **% EUR** — 0.332500 | EUR 30,000,000 | **99,750.00** ✓ |
| 3 | **% PLN** — 0.000000 | — | 0.00 |
| 4 | **USD/GBP** — 0.020900 | GBP 35,000,000 | **731,500.00** ✓ |
| 5 | **% USD** — 0.446250 | USD 10,000,000 | **44,625.00** ✓ |
| 6 | **% USD** — 0.455000 | USD 10,000,000 | **45,500.00** ✓ |
| 7 | **% EUR** — 0.573844 | EUR 37,698,898.21 | **216,333.00** ✓ |

Three things to notice:

- **The percentage can be of either currency.** Examples 1, 2 and 7 quote a percentage of the base currency; Example 3 quotes a percentage of the **quote** currency (PLN, not EUR). The convention is not fixed by the pair.
- **Example 4 is not a percentage at all.** `USD/GBP` means **points** — USD per GBP of notional. 35,000,000 GBP × 0.0209 USD/GBP = 731,500 USD. Treating 0.0209 as a percentage would understate the premium by a factor of about 350.
- **The Flat amount is the reconciliation.** Whatever the convention, `Flat` is the resulting cash premium, and it is the figure that actually settles.

**In short: read the unit label before the number.** This is the single most error-prone field on the screen.

### 7.2 Premium timing: upfront or deferred

The **Value** field is the premium's payment date, and the examples show two distinct patterns:

| Example | Expiry | Settlement | Premium value | Pattern |
|---|---|---|---|---|
| 1 | 18 mar 2027 | 22 mar 2027 | **22 mar 2027** | **Deferred** — paid at settlement |
| 2 | 17 sept 2026 | 21 sept 2026 | **21 sept 2026** | **Deferred** |
| 3 | 09 sept 2026 | 11 sept 2026 | **21 ago 2026** | **Upfront** |
| 4 | 19 ene 2027 | 21 ene 2027 | **21 ene 2027** | **Deferred** |
| 5–6 | 20 nov 2026 | 24 nov 2026 | **24 nov 2026** | **Deferred** |
| 7 | 02 sept 2026 | 04 sept 2026 | **28 jul 2026** | **Upfront** |

An **upfront** premium is paid spot from the trade date, which is the FX market default. A **deferred** premium is paid at the option's settlement date instead — economically a different trade, since the payer has the use of the money until then and the receiver carries the credit exposure for it.

Five of the seven defer; two pay upfront. Which applies should be read off the Value date rather than assumed (§14).

### 7.3 Margin and Flat Margin

**Margin** is a commercial spread on the premium and **Flat Margin** its cash equivalent. Both are **zero on all seven examples**, so the mechanism is documented from the fields alone (§14).

## 8. Other flags on the screen

| Flag | Meaning | Value across all seven |
|---|---|---|
| **Standard** | The trade is a plain vanilla | Shown on all |
| **American** | Exercise style (§5) | Ticked on Example 7 only |
| **Warrant** | Warrant treatment | Unticked |
| **Margining** | Whether the option is margined (§1.2) | **Unticked** |
| **Convert** | Currency conversion of the premium | Unticked |
| **Other flows** | Supplementary flows | Unticked |
| **Hedges / Initial data** | A second tab, not captured | — (§14) |

## 9. What the screen does not show

- **No valuation or Greeks.** The premium paid is visible; the option's current value, delta, gamma, vega and theta are not. Those come from pricing and risk screens (§14).
- **No link between strategy legs.** Examples 5 and 6 form a straddle, but nothing on either ticket says so — see §10.3.

## 10. Straddles and multi-leg strategies

### 10.1 What a straddle is

A **straddle** is the simultaneous purchase (or sale) of **a call and a put at the same strike, same expiry, same notional, on the same underlying**.

Its defining property is that it has **no directional view**. A long straddle profits if the underlying moves far enough in *either* direction, and loses if it stays near the strike. It is therefore a **position on volatility itself**, not on direction:

- **Long straddle** — pays both premiums, profits from a large move either way. Maximum loss is the total premium, suffered if the rate finishes exactly at the strike. Long volatility, long gamma.
- **Short straddle** — receives both premiums, profits if the rate stays near the strike. Loss grows with the size of any move, in either direction. Short volatility, short gamma.

Only one leg can finish in the money, so at expiry at most one is exercised.

**Why FX in particular.** The at-the-money straddle is the instrument off which FX implied volatility is quoted — when a dealer quotes "one-year EUR/USD at 8%", that is the volatility of the ATM straddle. Struck at the forward, the call and put have equal value and equal-and-opposite deltas, so the straddle is delta-neutral at inception: pure volatility exposure with no directional component. That is exactly why it is the market's benchmark.

A **strangle** is the same idea with the two strikes set apart — an out-of-the-money call and an out-of-the-money put. It costs less than a straddle and needs a larger move to pay off.

### 10.2 The worked straddle

Examples 5 and 6 are a **long USD/CNH straddle**. Everything matches across the two legs except which way each points:

| | Leg 1 | Leg 2 |
|---|---|---|
| Direction | **Buy** | **Buy** |
| Type | **Call CNH / Put USD** | **Put CNH / Call USD** |
| Gains if | USD/CNH **falls** | USD/CNH **rises** |
| Strike | **6.6795** | **6.6795** |
| Expiry / Cut | 20 nov 2026 / TOK | 20 nov 2026 / TOK |
| Settlement | 24 nov 2026 | 24 nov 2026 |
| Notional | USD 10,000,000 | USD 10,000,000 |
| Premium | 0.446250 % USD | 0.455000 % USD |
| **Flat** | **44,625.00** | **45,500.00** |

**Total cost: 90,125.00 USD**, or **0.90125%** of the USD 10m notional.

**The notional is 10 million, not 20.** Each leg carries USD 10,000,000, but they are two views of the same 10m position and only one can be exercised. Reading the strategy as 20m of exposure overstates it — a common and consequential error.

**Breakevens.** The total premium of 0.90125% of USD notional converts to roughly **0.0602 CNH per USD** at the strike, putting breakevens at approximately:

> **6.6193 and 6.7397** — the rate must move about **0.9% in either direction** before the position profits.

That is the concrete cost of being long volatility on this trade.

**The two premiums are not equal**, and the difference is informative. The leg gaining when USD/CNH rises costs 0.455%; the leg gaining when it falls costs 0.446%. By put–call parity, the call being worth more than the put means **the strike sits slightly below the forward**. A textbook at-the-money-forward straddle prices both legs identically; this one is struck close to, but not exactly at, the forward.

### 10.3 Strategy legs are booked separately — and are not linked on this screen

Both straddle legs appear as **independent tickets**. Nothing on either one indicates it belongs to a strategy: no strategy identifier, no reference to the sibling leg. They are recognisable as a pair only because strike, expiry, cut, settlement, notional and counterparty all coincide while the call/put pair is inverted.

This has practical consequences worth stating:

- **Risk and P&L must be aggregated deliberately.** Viewed leg by leg, one is a USD call and the other a USD put; only together are they a volatility position.
- **Partial unwinds break the structure.** Closing one leg leaves a directional position where a neutral one existed.
- **Other structures behave the same way.** A strangle, a risk reversal, a collar or a butterfly will all appear as separate vanilla tickets sharing dates and counterparty.

**Example 3 is very likely such a leg.** It carries a **zero premium** with a genuine strike and expiry — which no standalone option would. A free option is not a market trade; it is almost certainly one side of a package whose premium was booked on the other leg or netted across the structure (§14).

## 11. Worked examples

### 11.1 Example 1 — USD/CNH, bought USD call, delivery

| Field | Value |
|---|---|
| Contract | USD/CNH |
| Direction / Type | **Buy — Put CNH / Call USD** |
| Strike | **6.7300** USD-CNH |
| Expiry / Cut | 18 mar 2027 / **TOK** |
| Settlement | 22 mar 2027 — **Delivery** |
| Amounts | CNH 201,900,000 / **USD 30,000,000** |
| Premium | **0.358400 % USD** |
| Flat | **107,520.00** |
| Premium value | 22 mar 2027 — **deferred** |
| Style | Standard (European) |

**Position:** the right to buy USD 30,000,000 and sell CNH at 6.7300 — a position that gains if USD strengthens against CNH beyond the strike.

**Amounts:** 30,000,000 × 6.7300 = 201,900,000 ✓

**Premium:** 30,000,000 × 0.3584% = **107,520.00** ✓, paid at settlement rather than upfront (§7.2).

**Tokyo cut**, appropriate to an Asian pair — the option expires at the Tokyo close, not at a European or US time.

### 11.2 Example 2 — EUR/AUD, sold EUR put, delivery

| Field | Value |
|---|---|
| Contract | EUR/AUD |
| Direction / Type | **Sell — Call AUD / Put EUR** |
| Strike | **1.6350** EUR-AUD |
| Expiry / Cut | 17 sept 2026 / **NY** |
| Settlement | 21 sept 2026 — Delivery |
| Amounts | AUD 49,050,000 / **EUR 30,000,000** |
| Premium | **0.332500 % EUR** |
| Flat | **99,750.00** |
| Premium value | 21 sept 2026 — deferred |

**Position:** sold, so the book **receives** the premium and grants the counterparty the right to sell EUR against AUD at 1.6350. The book loses if EUR weakens against AUD below the strike.

**Amounts:** 30,000,000 × 1.6350 = 49,050,000 ✓

**Premium:** 30,000,000 × 0.3325% = **99,750.00** ✓ received.

### 11.3 Example 3 — EUR/PLN, bought EUR call, zero premium

| Field | Value |
|---|---|
| Contract | EUR/PLN |
| Direction / Type | **Buy — Put PLN / Call EUR** |
| Strike | **4.3700** EUR-PLN |
| Expiry / Cut | 09 sept 2026 / **WAR** |
| Settlement | 11 sept 2026 — Delivery |
| Amounts | PLN 3,277,500 / **EUR 750,000** |
| **Premium** | **0.000000 % PLN** |
| Flat | **0.00** |
| Premium value | 21 ago 2026 — upfront |

**Amounts:** 750,000 × 4.3700 = 3,277,500 ✓

**Two things distinguish this trade.**

**The premium is quoted as a percentage of PLN** — the *quote* currency — where Examples 1, 2 and 7 quote a percentage of the base. The convention varies by trade, not by pair (§7.1).

**The premium is zero.** A genuine option with a real strike and a real expiry does not cost nothing. This is almost certainly a **leg of a package** — one side of a collar, risk reversal or restructuring — with the premium carried on another leg or netted across the structure. Nothing on this screen links it to anything else (§10.3, §14).

**Warsaw cut**, following the PLN market.

### 11.4 Example 4 — GBP/USD, sold GBP call, premium in points

| Field | Value |
|---|---|
| Contract | GBP/USD |
| Direction / Type | **Sell — Put USD / Call GBP** |
| Strike | **1.35650** GBP-USD |
| Expiry / Cut | 19 ene 2027 / **NY** |
| Settlement | 21 ene 2027 — Delivery |
| Amounts | USD 47,477,500 / **GBP 35,000,000** |
| **Premium** | **0.020900 USD/GBP** |
| Flat | **731,500.00** |
| Premium value | 21 ene 2027 — deferred |

**Amounts:** 35,000,000 × 1.35650 = 47,477,500 ✓

**The premium is quoted in points, not as a percentage.** `USD/GBP` means USD per GBP of notional:

35,000,000 GBP × 0.0209 USD/GBP = **731,500 USD** ✓

Had 0.0209 been read as a percentage, the premium would have come out at 7,315 — wrong by a factor of a hundred. This example is the reason §7.1 insists on reading the unit label first.

### 11.5 Examples 5 and 6 — USD/CNH long straddle

Two tickets forming a single volatility position. The full analysis is in §10.2; in summary:

| | Leg 1 | Leg 2 |
|---|---|---|
| Direction / Type | Buy — **Call CNH / Put USD** | Buy — **Put CNH / Call USD** |
| Strike | 6.6795 | 6.6795 |
| Expiry / Cut | 20 nov 2026 / TOK | 20 nov 2026 / TOK |
| Settlement | 24 nov 2026 — Delivery | 24 nov 2026 — Delivery |
| Amounts | CNH 66,795,000 / USD 10,000,000 | CNH 66,795,000 / USD 10,000,000 |
| Premium | 0.446250 % USD | 0.455000 % USD |
| Flat | **44,625.00** | **45,500.00** |
| Premium value | 24 nov 2026 — deferred | 24 nov 2026 — deferred |

**Combined: USD 90,125 for a 10 million straddle**, breakevens around 6.6193 / 6.7397, long volatility with no directional view at inception.

### 11.6 Example 7 — EUR/USD, sold EUR call, American, cash settled

| Field | Value |
|---|---|
| Contract | EUR/USD |
| Direction / Type | **Sell — Put USD / Call EUR** |
| Strike | **1.1445** EUR-USD |
| Expiry / Cut | 02 sept 2026 / **NY** |
| **Settlement** | 04 sept 2026 — **Cash, in EUR** |
| Amounts | **USD 43,146,389** / EUR 37,698,898.2088248 |
| Premium | **0.573844 % EUR** |
| Flat | **216,333.00** |
| Premium value | **28 jul 2026 — upfront** |
| **Style** | **American** |

**The only American and the only cash-settled trade in the set**, and the two features are worth taking separately.

**American style** means the counterparty can exercise at any time up to expiry, not only at the New York cut. For the seller that is assignment risk throughout the option's life rather than at a single known moment.

**Cash settlement, in EUR.** Rather than exchanging USD 43.1m against EUR 37.7m, the option settles as a single net amount in the named currency. The settlement currency field is required because either leg would be a valid choice.

**The amounts run the other way.** The USD figure is the round one and the **EUR amount carries seven decimals** — 43,146,389 ÷ 1.1445 = **37,698,898.2088248** ✓ — so this trade was sized in USD and the EUR amount derived (§3.1).

**Premium:** 37,698,898.2088248 × 0.573844% = **216,332.87**, shown as 216,333.00 ✓, and paid **upfront** on 28 July rather than deferred to settlement (§7.2).

### 11.7 The seven examples side by side

| | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| Pair | USD/CNH | EUR/AUD | EUR/PLN | GBP/USD | USD/CNH | USD/CNH | EUR/USD |
| Direction | Buy | **Sell** | Buy | **Sell** | Buy | Buy | **Sell** |
| Type | Put CNH / Call USD | Call AUD / Put EUR | Put PLN / Call EUR | Put USD / Call GBP | **Call CNH / Put USD** | **Put CNH / Call USD** | Put USD / Call EUR |
| Strike | 6.7300 | 1.6350 | 4.3700 | 1.35650 | 6.6795 | 6.6795 | 1.1445 |
| Expiry | 18 mar 2027 | 17 sept 2026 | 09 sept 2026 | 19 ene 2027 | 20 nov 2026 | 20 nov 2026 | 02 sept 2026 |
| **Cut** | **TOK** | NY | **WAR** | NY | TOK | TOK | NY |
| Settlement | +2 Delivery | +2 Delivery | +2 Delivery | +2 Delivery | +2 Delivery | +2 Delivery | **+2 Cash (EUR)** |
| **Style** | European | European | European | European | European | European | **American** |
| Base amount | USD 30,000,000 | EUR 30,000,000 | EUR 750,000 | GBP 35,000,000 | USD 10,000,000 | USD 10,000,000 | EUR 37,698,898.21 |
| Sized in | Base | Base | Base | Base | Base | Base | **Quote** |
| **Premium unit** | **% USD** | **% EUR** | **% PLN** | **USD/GBP (points)** | % USD | % USD | % EUR |
| Premium | 0.358400 | 0.332500 | **0.000000** | 0.020900 | 0.446250 | 0.455000 | 0.573844 |
| **Flat** | **107,520.00** | **99,750.00** | **0.00** | **731,500.00** | **44,625.00** | **45,500.00** | **216,333.00** |
| Premium timing | Deferred | Deferred | **Upfront** | Deferred | Deferred | Deferred | **Upfront** |
| Margin / Flat margin | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| Margining | No | No | No | No | No | No | No |
| Part of a strategy | — | — | **Likely** | — | **Straddle** | **Straddle** | — |

## 12. Risk profile

An FX option is a **non-linear** instrument, and in FX it carries an exposure structure that equity or rates options do not.

- **Delta** — sensitivity to the spot rate, and in FX it can be expressed in either currency. A delta hedge is itself an FX position, so the currency in which delta is measured has to be stated.
- **Gamma** — the rate at which delta changes. The straddle in §10.2 is a long gamma position; a sold option is short gamma, which is what turns a large move into an outsized loss near expiry.
- **Vega** — sensitivity to implied volatility, and the reason the straddle exists as an instrument. FX volatility is quoted per pair and per tenor, and a vega position is exposure to that surface moving.
- **Theta** — time decay, working for the seller and against the buyer.
- **Rho on both currencies.** This is specific to FX: an option's value depends on the interest rates of **both** currencies, since the forward is set by their differential. A single-currency rates shift changes the forward and therefore the option's value.
- **Counterparty credit risk.** With `Margining: No` throughout, a bought option is an unsecured claim on the seller for the option's life (§1.2).
- **Settlement risk on delivery-settled options** (§6). Exercise moves the full notional of both currencies — tens of millions on these examples — with the funding and Herstatt-risk consequences that follow. Cash settlement replaces this with a net payment.
- **Assignment risk on American options** (§11.6), which for the seller runs throughout the trade rather than at a known moment.
- **Cut risk.** An option finishing near the money is decided by the rate at one specific instant (§4.1). Which cut applies is a real exposure around expiry.
- **Strategy decomposition risk** (§10.3). Legs booked separately can be closed, netted or reported separately, converting a neutral structure into a directional one without any single ticket looking wrong.

## 13. Glossary of fields seen in the Murex screens

- **Contract**: the currency pair.
- **Call/Put**: the direction (**Buy** / **Sell**) followed by the option type expressed as a **pair** — a call on one currency and a put on the other (§1.1).
- **Strike**: the exchange rate at which the option may be exercised, with the quoting convention alongside (e.g. EUR-USD).
- **Maturity / Cut**: the expiry date and the market centre whose close sets the expiry time (§4.1).
- **Settlement**: the delivery date, with the settlement method — **Delivery** or **Cash** — and, for cash, the settlement currency (§6).
- **Currency amount pair**: the two notionals, linked by the strike (§3).
- **Premium**: the premium, with its **unit label** — a percentage of one of the two currencies, or points of one per unit of the other (§7.1).
- **Flat**: the resulting cash premium — the figure that settles.
- **Value**: the premium's payment date; **upfront** or **deferred to settlement** (§7.2).
- **Margin / Flat Margin**: commercial spread on the premium and its cash equivalent; zero throughout (§7.3).
- **American**: exercise style; unticked means European (§5).
- **Standard**: the trade is a plain vanilla.
- **Warrant**: warrant treatment; unticked throughout.
- **Margining**: whether the option is margined; **unticked throughout**, which is what leaves the premium an unsecured exposure (§1.2).
- **Convert**: premium currency conversion; unticked throughout.
- **Other flows**: supplementary flows; unticked throughout.
- **Hedges / Initial data**: a second tab holding hedge and initial-data configuration; not captured (§14).

## 14. Open items and gaps in this document

1. **Example 3 carries a zero premium** (§11.3). A real strike and expiry with no cost is not a standalone market trade. Confirm which package it belongs to and where its premium sits — this is the clearest instance of the linkage problem in §10.3.
2. **Strategy legs carry no link to one another** (§10.3). The straddle is identifiable only by coincidence of terms. Whether a strategy identifier exists elsewhere in the system, and how risk is aggregated across legs, should be documented — it bears directly on how these positions are reported.
3. **Premium timing varies with no visible driver** (§7.2). Five trades defer the premium to settlement and two pay upfront. Confirm what determines which applies, since deferred premium changes the credit profile of the trade.
4. **The Hedges / Initial data tab was not captured** on any example. It may hold the strategy linkage and the initial market data used at inception — both directly relevant to items 1 and 2.
5. **Margin and Flat Margin are zero throughout** (§7.3), so how a commercial spread flows into the premium and the flat amount is undocumented.
6. **No valuation or Greeks captured** (§9). The premium is visible; the option's current value and sensitivities are not, and those are what a risk view depends on.
7. **Only one American and one cash-settled example**, and they are the same trade (§11.6). The two features could not be observed independently.
8. **The Warrant, Convert and Other flows flags are unused** across all seven, so they are documented from labels alone.
9. **No exercise or expiry example.** How exercise is processed — notice, delivery of both currencies on a physically settled option, net payment on a cash-settled one, assignment on a sold American — is described conceptually but not documented from an actual event.
10. **No barrier or other exotic example.** All seven are vanillas. Barriers, digitals and average-rate options are separate products with different mechanics and would need their own treatment.
