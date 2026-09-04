# Equity Return Swaps (ERS)

## Purpose of this document

This is a reference document on equity return swaps: what the product is, how the performance and financing legs work, how haircuts and mark-to-market conventions are configured, what changes when the equity trades in a different currency from the swap, and how the terms are represented in Murex. It is meant to be read on its own — a new joiner or anyone unfamiliar with the product should come away understanding the mechanics, not just recognizing the trade capture screen.

The three worked examples in §11 are two **same-currency EUR long positions** on European listed equities, and one **cross-currency short** on a Brazilian equity settling in USD, booked on a different template with a fixed-rate financing leg and an open maturity. Between them they cover both directions, floating and fixed financing, single- and cross-currency structures, three mark-to-market conventions and two haircut modes.

**A note on identifiers.** Portfolio and counterparty identifiers are omitted throughout. Equity tickers and their listing venues are retained, since the underlying of an equity swap is a listed instrument rather than a party, and naming it makes the examples concrete.

## 1. Overview: what an equity return swap is

An equity return swap is a bilateral OTC contract with two legs:

- **The performance leg** pays the **total return of a specified equity** — its price change plus dividends over the period.
- **The financing leg** pays a **funding rate**, either a floating index plus a margin or a fixed rate, applied to a notional derived from the position's value.

The party receiving the performance leg has synthetic **long** exposure to the shares; the party paying it is synthetically **short**. Neither needs to own or borrow the stock.

Three consequences follow:

- **It is a financing product as much as an equity product.** One side obtains the economics of holding the shares; the other earns a return on the money it has effectively advanced. The template field **Trade purpose: Delta one** states the intent directly — linear exposure, no optionality.
- **The shares are referenced, not held.** This is what makes the product useful for gaining exposure to markets where direct holding is impractical, for obtaining leverage, for expressing a short without arranging stock borrow, and for managing balance sheet.
- **Cash settled.** All three examples set **Payment Conditions: Cash** — there is no delivery of shares at any point.

### What distinguishes an equity swap from a bond-based return swap

The mechanics are closely related, but three differences are structural and shape the whole capture screen:

- **No accrued interest.** An equity has no coupon accruing daily, so there is no clean price, no accrued figure, no dirty price and no yield. The Financial definition block collapses to dates alone, and the performance leg carries a single **Settlement price** rather than a reference price plus a clean/dirty mode.
- **Income is dividends, not coupons.** Dividends are discrete, uncertain in timing and amount, and typically subject to withholding tax — which makes the income configuration (§5.2) more consequential than it is for government paper.
- **Corporate actions.** Splits, rights issues, spin-offs and mergers change what the swap references. Bonds have no equivalent. See §8.

## 2. Direction

The **Payout** radio buttons set each leg's direction independently, and the performance leg displays a **Long / Short** tag confirming the resulting exposure.

| | Synthetic long | Synthetic short |
|---|---|---|
| Performance leg | **Receive** | **Pay** |
| Tag shown | **Long** | **Short** |
| Financing leg | **Pay** | **Receive** |
| Economic analogue | Financed purchase of shares | Short sale, earning on the proceeds |
| Gains when | Share price rises | Share price falls |
| Dividends | Received (via income pass-through) | Paid away |

Examples 1 and 2 are **Receive performance / Pay financing** — financed longs. Example 3 is **Pay performance / Receive financing** — a synthetic short.

Note the sign consequence: because the short pays the performance leg, a fall in the share price produces a **receipt**, and dividends paid on the stock become an **outflow**.

## 3. The equity and its pricing

The **Financial definition** block identifies the underlying and the swap's dates:

| Field | Meaning |
|---|---|
| **Equity / Market** | The referenced share and the venue from which it is priced (CONTINUO, BRUSELAS, BVSP across the examples). |
| **Archiving Group / Cutoff** | The pricing group and the cutoff basis — **FIXING** on all three. |
| **ValuationShifter** | The lag from a valuation date to its settlement date (§9). |
| **Effective date / Maturity / Maturity structure** | The swap's dates. Maturity may be a date or **Open** (§9.3). |

There is deliberately no price detail here — unlike a bond-referenced swap, there is nothing to decompose. The price appears once, on the performance leg, as the **Settlement price**.

### Nominal, quantity and price

The three tie together exactly:

**Nominal = Quantity × Settlement price**

- Example 1: 643,218 × 24.64 = **15,848,891.52** ✓
- Example 2: 176,223 × 66.46 = **11,711,780.58** ✓

The template field **Performance based on: Shares** confirms the leg is quantity-driven — the position is a number of shares, and the notional is derived from it, not the other way round.

## 4. The performance leg

### 4.1 What it pays

The change in the shares' value between the first and last valuations, plus dividend income over the period. In a cross-currency structure the prices are converted before the comparison (§7).

### 4.2 Settlement price and first valuation

- **Settlement price** — the price against which performance is measured, in the **swap's** currency.
- **First valuation** and **First fx rate** — present only on cross-currency trades, recording the initial price in the **equity's** currency and the initial FX rate (§7).

In Examples 1 and 2 the equity and the swap share a currency, so only the settlement price appears. In Example 3 both are present, with the first valuation quoted in BRL against a USD settlement price.

### 4.3 Valuation and income periods

- **Valuation Period** — the first and last price observation dates.
- **Income Period** — the window over which dividends are captured, shown separately though it coincides with the valuation period on all three examples.
- **Income Payment fraction** — the proportion of dividend income passed through: **1.000000** on all three, so 100%.

### 4.4 Dividends and withholding

An income fraction of 1.000000 means the full dividend is passed through **in the contract's terms**. What is actually economically received depends on the withholding treatment configured behind the template's **Income/Tax credit** setting, which was not captured (§14).

This matters more for equities than for government bonds. Dividend withholding rates vary by jurisdiction and by the holder's tax status, and the economics of a synthetic long can differ materially from holding the shares depending on how withholding and any reclaim or credit is handled. For a synthetic short, dividends are an outflow, and the gross-versus-net question applies in reverse. Any ERS documentation that omits the dividend treatment is incomplete.

## 5. The financing leg

### 5.1 Floating or fixed

The leg may reference a floating index plus a margin, or carry a fixed rate:

| Example | Rate type | Index | Margin / Rate |
|---|---|---|---|
| 1 | Floating | EUR ESTR AVG LB -2 | Margin 0.5000% |
| 2 | Floating | EUR ESTR AVG LB -2 | Margin 0.5000% |
| 3 | **Fixed** | *(none — no index field)* | Rate 0.0000 |

When *Fixed rate* is selected the index and margin fields are replaced by a single **Rate**. The floating examples use **€STR averaged with a two-business-day lookback** — `AVG` denoting an arithmetic average of the daily overnight fixings rather than compounding, and `LB -2` shifting the observation window back two business days so the rate is known before payment falls due.

**Margin mode: Additive** on all three, so the spread is added to the index rather than applied multiplicatively.

### 5.2 The haircut and its modes

The financing notional is the position's value adjusted by a **haircut**, and the field carries a **mode indicator** that determines the formula. Two modes appear here, and the indicator — not the number — determines the meaning:

| Mode indicator | Formula | Example |
|---|---|---|
| **`1 / (1 +/- x)`** | Start Nominal = Nominal / (1 ± haircut) | Examples 1 and 2 (haircut 0.00 → no effect) |
| **`x`** | Start Nominal = Nominal × haircut % | Example 3 (haircut 100.00 → no reduction) |

Both examples happen to produce no adjustment, but by different routes: a haircut of **0.00** under the divisor mode and a haircut of **100.00** under the multiplier mode both leave the financing notional equal to the performance notional. Reading either number without its mode indicator gives the wrong answer.

### 5.3 Mark-to-market convention

The template field **Marked to market** determines whether — and against what — the financing notional resets. Three values appear across the set, and the difference is economically significant:

| Value | Behaviour | Example |
|---|---|---|
| **Based on reset prices** | The financing notional **resets** as the equity marks, so the funded amount tracks the exposure. | Examples 1 and 2 |
| **Independent amount** | The financing leg is driven by an independently specified amount rather than by the position's marked value. | Example 3 |
| *Based on initial price* | The notional is fixed off the initial price and does **not** reset. | *(Not used in these examples; appears on related return-swap templates.)* |

A resetting structure keeps financing aligned with exposure: as the shares rally, the financed amount grows with them. A non-resetting structure lets the two diverge over the life of the trade. Anyone reconciling financing accruals against a marked position needs to know which convention applies before the numbers will agree.

### 5.4 Fixing, payment and compounding

- **Fixing: In arrears** and **Payment: In arrears** on the floating templates — consistent with an averaged overnight index, whose value is only known once the period has run.
- **Rate convention: LIN ACT/360** on all three.
- **Compounding: No compounding** appears on the fixed-rate template, and **Reset Rate: Automatic (on next calc. date)** governs when the rate is refreshed.
- **Rate factor applied: To main index** where a factor is present.

### 5.5 No principal exchange

**Initial exchange**, **Intermediate payments** and **Final exchange** are unticked on both legs of all three examples. No principal flows: the swap settles on performance and financing alone, and the notional exists only as a calculation base.

## 6. Payment conditions

All three set **Payment Conditions: Cash**. The swap settles in cash; shares are never delivered.

## 7. Cross-currency equity return swaps

Example 3 introduces the case where the **equity trades in one currency and the swap settles in another**: a Brazilian listed share, with the settlement price and financing leg both in USD.

The mechanism is visible in the performance leg:

- **First valuation** is recorded in **BRL**, the equity's own currency.
- **First fx rate** records the initial **USD-BRL** rate — 5.2108 on this trade.
- Prices are converted at the prevailing FX fixing, and performance is measured on the converted series.

The consequence is that a cross-currency ERS embeds an **FX position alongside the equity position**. The return the swap pays is the return in the settlement currency, which combines the share price move and the currency move. A share that rises in local terms can produce a loss in the swap's currency if the local currency weakens by more.

Supporting configuration: **Multicurrency Indexation: Fixed Indexation** on both legs, **First prices and FX rate inherited: from trade (customized)**, and **MultiCurrency propagation** / **Multi Currency** unticked.

## 8. Corporate actions

Equities are subject to corporate actions that have no analogue in bond-referenced swaps: stock splits and reverse splits, rights issues, spin-offs, special dividends, mergers and delistings. Each changes what the swap references, and the contract must specify how the position is adjusted so that neither party gains or loses from a purely mechanical event.

The template exposes **Substitution in case of CA** on the security leg — unticked on all three examples — which governs whether the referenced security is substituted when a corporate action makes that necessary.

This is an area where the captured screens are thin relative to the economic importance of the topic. Corporate action handling is one of the main operational risks in an equity swap book, and how adjustments are applied should be documented from the configuration behind the security leg's **Return** and **Schedules definition** links (§14).

## 9. Dates

### 9.1 The valuation shifter

**ValuationShifter** sets the lag between a valuation date and its settlement — `+2 OPEN DAYS` on Examples 1 and 2, `+2 OD BRAZIL` on Example 3, the latter on the Brazilian calendar. It may be inherited from the security or set as a specific delay on the template.

Its effect is that the performance and financing legs need not start together:

| Example | Performance start | Financing start | Effective date | Last valuation | Maturity |
|---|---|---|---|---|---|
| 1 | 21 ago 2026 (Fri) | 25 ago 2026 (Tue) | 25 ago 2026 | 23 nov 2026 (Mon) | 25 nov 2026 (Wed) |
| 2 | 21 ago 2026 (Fri) | 25 ago 2026 (Tue) | 25 ago 2026 | 23 nov 2026 (Mon) | 25 nov 2026 (Wed) |
| 3 | 28 ago 2026 (Fri) | 28 ago 2026 (Fri) | 28 ago 2026 | 08 sept 2026 | 08 sept 2026 |

Examples 1 and 2 show the shift cleanly at **both ends**: the price is observed on Friday 21 August and cash starts on Tuesday 25 August, two open days later; and the final price is observed on Monday 23 November against a Wednesday 25 November maturity. Example 3 has both legs starting together and its last valuation coinciding with maturity, so the shift is not applied there despite being configured.

### 9.2 Calendars follow function, not the trade

The security leg fixes on the **equity's listing venue** while cash settles on the **currency's** calendar:

| Example | Security fixing | Security payment | Interest payment |
|---|---|---|---|
| 1 | **BOLSAMAD** | TARGET | TARGET |
| 2 | **ENEXT_BRUS** | TARGET | TARGET |
| 3 | **BOVESPA** | NEW YORK | NEW YORK |

Worth noting: Examples 1 and 2 use the **same named template**, yet their security fixing calendars differ — Madrid for one, Euronext Brussels for the other. The template detail screen therefore shows configuration **resolved for the trade in hand**, with the equity's venue driving the fixing calendar, rather than a fixed set of values belonging to the template in the abstract. Read a template screen as telling you about that trade.

### 9.3 Open maturity

Example 3 sets **Maturity: Open**, with dates shown alongside. An open or evergreen swap has no contractual end date: it continues until terminated, with periodic calculation and reset dates rather than a single scheduled maturity. The related template settings are **Reset Rate: Automatic (on next calc. date)** and **Increase lot fungibility: Always effective date**, the latter governing how subsequent increases to the position are treated.

This matters operationally: an open swap generates recurring reset and calculation events indefinitely, and its lifecycle is managed by increases, decreases and eventual termination rather than by a maturity schedule.

## 10. Templates

The **Template** field supplies both legs' structural configuration. Two templates appear:

| Field | Floating single-period template (Ex. 1, 2) | SWAPONE template (Ex. 3) |
|---|---|---|
| Description | Based on reset price, floating | SWAPONE template |
| Evaluation | Default | **Accrual** |
| Accrual delay | *(not shown)* | +1 open day |
| Flows projection delay | +1 open day | +1 open day |
| Stub period position | Both ends (forward) | **Up front** |
| Direction | Nominal | Nominal |
| Non-settled cash handling | In future cash (when all but FX rate is fixed) | **In market value** |
| Treat collateral | On pool level | On pool level |
| Early settlement | Yes | Yes |
| Valuation shifter | Inherited from security | **Specific delay** |
| Liquidation | Average price | *(blank)* |
| Reset Rate | *(not present)* | **Automatic (on next calc. date)** |
| Increase lot fungibility | Always effective date | Always effective date |
| Trade purpose | Delta one | Delta one |
| *Security leg* | | |
| Evaluation / Start delay | Inherited / +0 BD | Inherited / +0 BD |
| Payment calendar | TARGET | **NEW YORK** |
| Fixing calendar | BOLSAMAD / ENEXT_BRUS | **BOVESPA** |
| Performance based on | Shares | Shares |
| Indexed | Unticked | **Ticked** (indexations list) |
| Substitution in case of CA | Unticked | Unticked |
| Exchanges (initial/intermediate/final) | All unticked | All unticked |
| *Interest leg* | | |
| **Marked to market** | **Based on reset prices** | **Independent amount** |
| Cash based on | Dirty Price | *(not shown)* |
| Rate | Floating | **Fixed** |
| Payment calendar / Fixing calendar | TARGET / TARGET | NEW YORK / — |
| Compounding | *(not shown)* | **No compounding** |
| Fixing / Payment | In arrears / In arrears | — / In arrears |
| Rate convention | LIN ACT/360 | LIN ACT/360 |
| Margin mode | Additive | *(not shown — fixed rate)* |
| Day count | Yes | Yes |
| Running fee schedule | Inherited | Inherited |
| Interest exposure | Yes | Yes |

Two settings change the economics rather than the plumbing and should be read first on any new trade: **Marked to market** (§5.3) and the **Rate** type (§5.1).

Note also **Early Settlement: Yes** and, on the floating template, **Liquidation: Average price** — partial unwinds are expected behaviour on these books, priced on an average basis, rather than exceptional events.

## 11. Worked examples

### 11.1 Example 1 — BBVA.MC, EUR financed long

| Field | Value |
|---|---|
| Template | Floating single-period return swap template |
| Equity / Market | **BBVA.MC** / CONTINUO (Madrid) |
| Effective date | 25 ago 2026 |
| Maturity | 25 nov 2026 |
| ValuationShifter | +2 OPEN DAYS |
| Payment conditions | Cash |
| **Performance leg** | **Receive — Long** |
| Start date | 21 ago 2026 |
| Quantity | 643,218 |
| Settlement price | **24.64000 EUR** |
| Nominal | **15,848,891.52** |
| Valuation / income period | 21 ago 2026 → 23 nov 2026 |
| Income payment fraction | 1.000000 |
| **Financing leg** | **Pay — Floating** |
| Index | **EUR ESTR AVG LB -2** |
| Start date | 25 ago 2026 |
| Start nominal | 15,848,891.52 EUR |
| Haircut | **0.00**, mode `1 / (1 +/- x)` → amount 0.00 |
| Convention | LIN ACT/360 |
| Margin | **0.5000%** |
| Principal exchange | None |

**Position:** a financed long in a Spanish listed equity. The book receives the share's total return and pays €STR + 50bp on the full position value.

**Reconciliation:** 643,218 × 24.64 = 15,848,891.52, matching the nominal exactly.

**Dates:** performance observed from Friday 21 August with financing starting Tuesday 25 August — the two open days of the valuation shifter — and the same shift at the far end, final observation Monday 23 November against a Wednesday 25 November maturity. Three-month term, 92 days of financing.

**Mark-to-market: based on reset prices**, so the financing notional tracks the position as it marks rather than staying fixed at 15,848,891.52.

### 11.2 Example 2 — ABI.BR (Anheuser-Busch InBev NV), EUR financed long

| Field | Value |
|---|---|
| Template | Same floating single-period template as Example 1 |
| Equity / Market | **ABI.BR** — Anheuser-Busch InBev NV / BRUSELAS (Euronext Brussels) |
| Effective date | 25 ago 2026 |
| Maturity | 25 nov 2026 |
| ValuationShifter | +2 OPEN DAYS |
| **Performance leg** | **Receive — Long** |
| Start date | 21 ago 2026 |
| Quantity | 176,223 |
| Settlement price | **66.46000 EUR** |
| Nominal | **11,711,780.58** |
| Valuation / income period | 21 ago 2026 → 23 nov 2026 |
| **Financing leg** | **Pay — Floating** |
| Index / Margin | EUR ESTR AVG LB -2 / **0.5000%** |
| Haircut | 0.00, mode `1 / (1 +/- x)` → amount 0.00 |
| Principal exchange | None |

**Reconciliation:** 176,223 × 66.46 = 11,711,780.58 exactly.

**What this example isolates.** Almost everything is held constant against Example 1 — same template, same effective and maturity dates, same valuation window, same index and lookback, same margin, same haircut mode and value, same direction, same currency, cash settled. The only variables are the stock, the quantity and the price. Together the two legs total **27,560,672.10 EUR**, split roughly 57.5 / 42.5, which has the shape of a synthetic basket assembled from single-name swaps rather than two unrelated trades — though nothing on the captures confirms that reading.

**The one configuration difference** is the security-leg fixing calendar: **ENEXT_BRUS** here against **BOLSAMAD** in Example 1, under the same template name. The equity's listing venue drives the fixing calendar while cash settlement stays on TARGET for both (§9.2).

### 11.3 Example 3 — BPAC11.SA, cross-currency short with fixed financing and open maturity

| Field | Value |
|---|---|
| Template | **SWAPONE MODEL** |
| Equity / Market | **BPAC11.SA** / BVSP (B3, Brazil) |
| Effective date | 28 ago 2026 |
| **Maturity** | **Open** (dates shown 08 sept 2026) |
| ValuationShifter | **+2 OD BRAZIL** |
| Payment conditions | Cash |
| **Performance leg** | **Pay — Short** |
| Start date | 28 ago 2026 |
| Quantity | **0.00** |
| Settlement price | **0.0000 USD** |
| Nominal | **0.00** |
| **First valuation** | **0.0000 BRL** |
| **First fx rate** | **5.2108 USD-BRL** |
| Valuation / income period | 28 ago 2026 → 08 sept 2026 |
| Income payment fraction | 1.000000 |
| **Financing leg** | **Receive — Fixed** |
| Start nominal | **0.00 USD** |
| Haircut | **100.00**, mode `x` → amount 0.00 |
| Convention | LIN ACT/360 |
| **Rate** | **0.0000** |
| Principal exchange | None |

**Position:** a synthetic short in a Brazilian listed equity, with the economics settled in USD.

**Four structural departures from the first two examples:**

- **Short rather than long.** The book pays the equity's total return and receives financing — the mirror of Examples 1 and 2. Dividends on the stock become an outflow.
- **Cross-currency.** The share prices in BRL and the swap settles in USD, with conversion at the prevailing FX fixing. The trade carries an FX position as well as an equity position (§7). The initial rate of 5.2108 USD-BRL is recorded on the trade.
- **Fixed-rate financing.** No index and no margin — a single **Rate** field. The template correspondingly shows **Compounding: No compounding** and **Reset Rate: Automatic (on next calc. date)**.
- **Open maturity.** No contractual end date; the swap runs until terminated (§9.3).

**Mark-to-market: Independent amount** — the financing leg is driven by a separately specified amount rather than by the marked position, a third convention distinct from both the reset-price basis used in Examples 1 and 2 and the initial-price basis used elsewhere in the product family.

**The position is empty.** Quantity, settlement price, nominal and start nominal all read zero, and the first valuation is 0.0000 BRL. Only the FX rate is populated. This capture therefore documents the trade's **structure** but carries no position — consistent with an open swap whose exposure is built through subsequent increases, or with a trade fully unwound, or with a shell awaiting population. Which of these applies is not determinable from the screens (§14), and no arithmetic can be reconciled from this example.

### 11.4 The three examples side by side

| | Example 1 | Example 2 | Example 3 |
|---|---|---|---|
| Equity / Venue | BBVA.MC / Madrid | ABI.BR / Euronext Brussels | **BPAC11.SA / B3** |
| Template | Floating single-period | Floating single-period | **SWAPONE MODEL** |
| Direction | **Receive — Long** | **Receive — Long** | **Pay — Short** |
| Currency structure | Single currency EUR | Single currency EUR | **Cross-currency BRL→USD** |
| Quantity | 643,218 | 176,223 | **0.00** |
| Settlement price | 24.64000 EUR | 66.46000 EUR | 0.0000 USD |
| Nominal | 15,848,891.52 | 11,711,780.58 | **0.00** |
| First valuation / fx | — | — | **0.0000 BRL / 5.2108** |
| Financing rate type | Floating | Floating | **Fixed** |
| Index | ESTR AVG LB -2 | ESTR AVG LB -2 | *(none)* |
| Margin / Rate | 0.5000% | 0.5000% | Rate 0.0000 |
| **Haircut mode** | **`1 / (1 +/- x)`** | **`1 / (1 +/- x)`** | **`x`** |
| Haircut value / amount | 0.00 / 0.00 | 0.00 / 0.00 | 100.00 / 0.00 |
| **Marked to market** | **Based on reset prices** | **Based on reset prices** | **Independent amount** |
| Effective date | 25 ago 2026 | 25 ago 2026 | 28 ago 2026 |
| Maturity | 25 nov 2026 | 25 nov 2026 | **Open** |
| Valuation shifter | +2 OPEN DAYS | +2 OPEN DAYS | +2 OD BRAZIL |
| Legs start together? | No (+2 days) | No (+2 days) | **Yes** |
| Security fixing calendar | BOLSAMAD | **ENEXT_BRUS** | **BOVESPA** |
| Cash calendar | TARGET | TARGET | **NEW YORK** |
| Income fraction | 1.000000 | 1.000000 | 1.000000 |
| Principal exchange | None | None | None |
| Payment conditions | Cash | Cash | Cash |

## 12. Risk profile

An ERS is a **delta-one** product — linear exposure to the shares, no optionality — but the exposures extend well beyond price:

- **Equity price risk**, for the full performance notional. The receiver is long, the payer short.
- **Dividend risk.** Dividends are discrete and uncertain in both timing and amount. A synthetic long's return depends on dividends actually declared; a short pays them away. Withholding treatment (§4.4) determines what is economically received.
- **Financing risk.** The floating examples reprice with €STR while the margin is fixed for the life of the trade. Where the notional does not reset with the marked position (§5.3), the financed amount and the exposure diverge over time.
- **FX risk on cross-currency structures.** A first-order exposure, not a residual: the currency move can exceed the equity move and reverse the sign of the return.
- **Corporate action risk** (§8). Splits, rights issues, spin-offs, mergers and delistings all require the position to be adjusted correctly, and this is among the principal operational risks in an equity swap book.
- **Haircut and collateral risk.** The haircut determines how much of the position is financed; **Treat collateral: On pool level** indicates collateral is managed at pool rather than trade level, which affects how exposure is measured and margined.
- **Counterparty credit risk** over the life of the swap — a bilateral OTC exposure, mitigated by collateral rather than eliminated.
- **Open-maturity and rollover risk** (§9.3). A swap with no end date carries indefinite recurring resets, and the financing terms on an evergreen position are not locked for any defined horizon.
- **Early termination.** With early settlement enabled and liquidation priced on an average basis, partial unwinds are routine, and each is a valuation and settlement event.
- **Basis against the physical.** The referenced price comes from a specified venue and fixing; a hedge held in the physical shares will not track perfectly.

## 13. Glossary of fields seen in the Murex screens

**Financial definition**

- **Template**: the configuration template supplying both legs' structural settings (§10).
- **Equity / Market**: the referenced share and its pricing venue.
- **Archiving Group / Cutoff**: pricing group and cutoff basis (*FIXING*).
- **ValuationShifter**: lag from valuation date to settlement date (§9.1).
- **Effective date / Maturity / Maturity structure**: the swap's dates; maturity may read **Open** (§9.3).
- **Payment Conditions**: *Cash* on all three (§6).

**Performance leg**

- **Payout (Pay / Receive)** and the **Long / Short** tag: direction and resulting exposure (§2).
- **Equity × factor / Market**: the referenced share and its multiplier.
- **Quantity / Nominal**: the share count and the derived notional (§3).
- **Settlement price**: the price against which performance is measured, in the swap's currency.
- **First valuation / First fx rate**: on cross-currency trades, the initial price in the equity's currency and the initial FX rate (§7).
- **Valuation Period / Income Period**: observation windows for price and for dividends (§4.3).
- **Income Payment fraction**: proportion of dividend income passed through (§4.4).

**Financing leg**

- **Payout / Fixed or Floating**: direction and rate type (§5.1).
- **Index × factor**: the financing index and its multiplier. `AVG` denotes averaging, `LB -n` an n-day lookback.
- **Start Nominal**: the financing notional after the haircut.
- **Haircut**, its **mode indicator** (`x`, `1 +/- x`, `1 / (1 +/- x)`) and **Haircut Amount** (§5.2).
- **Convention**: financing day count (LIN ACT/360 throughout).
- **1st fixing / Margin**, or **Rate** on a fixed leg.
- **Payout spreads (Pay / Receive)**: additional spreads, zero throughout.

**Template**

- **Evaluation / Accrual delay / Flows projection delay**: valuation method and timing offsets.
- **Stub period position / Direction / Non-settled cash handling**: schedule and cash treatment.
- **Treat collateral / Early Settlement / Liquidation / Increase lot fungibility**: collateral and lifecycle handling.
- **Reset Rate**: when the financing rate is refreshed (§9.3).
- **Trade purpose**: *Delta one*.
- **Marked to market**: whether and against what the financing notional resets (§5.3).
- **Cash based on**: the price basis used for cash calculations.
- **Performance based on**: the driver of the security leg (*Shares*).
- **Compounding**: whether the financing rate compounds within a period.
- **Indexed / Multicurrency Indexation / First prices and FX rate inherited**: indexation and cross-currency settings (§7).
- **Substitution in case of CA**: corporate-action substitution of the referenced security (§8).
- **Fixing / Payment**: rate-setting and settlement timing (§5.4).
- **Initial / Intermediate / Final exchange**: principal exchange flags — all unticked (§5.5).
- **Interest exposure / Running fee schedule definition**: exposure treatment and fee schedule source.
- **Income/Tax credit / Return / Schedules definition**: sub-configurations reached by Edit links, not captured (§14).

## 14. Open items and gaps in this document

1. **Example 3 carries no position.** Quantity, price, nominal and start nominal are all zero, with only the FX rate populated. Whether this is an open swap awaiting increases, a fully unwound trade, or an unpopulated shell cannot be determined from the screens — and no arithmetic can be reconciled from it. A populated cross-currency short would be worth capturing.
2. **The Income/Tax credit configuration was not captured** (§4.4). For equities this governs dividend withholding and any reclaim or credit, which materially affects the economics of both a synthetic long and a synthetic short. It is the most significant gap in this document.
3. **Corporate action handling is not documented** (§8). Only the *Substitution in case of CA* flag is visible. How splits, rights issues, spin-offs and mergers adjust the position sits behind the security leg's **Return** and **Schedules definition** links and should be documented, given that it is a principal operational risk on these books.
4. **No flow schedules were captured.** The Performance flows and Interest flows links on each trade would show the calculation explicitly — first and last prices, FX conversion where applicable, dividend flows and the financing accrual. Static screens cannot demonstrate how income and performance actually settle.
5. **The Evaluation conditions and Termination Fees tabs were not captured.** Given that early settlement is enabled and partial unwinds are expected, termination fee configuration is a real economic term.
6. **The `Marked to market: Independent amount` convention is not explained by the captures** (§5.3). Where the independent amount is set, and how it relates to the position, is not visible.
7. **The valuation shifter is applied inconsistently** (§9.1). Examples 1 and 2 shift both ends by two open days; Example 3 has both legs starting together and its final valuation on the maturity date, despite a shifter being configured.
8. **No dividend event is present in any example.** All three run over periods where no dividend appears on the captures, so the income mechanics are documented from configuration rather than from observed behaviour.
