# NY_SCH — Branch Onboarding (Live Case)

The running record for this one specific branch, and the **main reference for what's done**. Not a
template. The orchestrator (`../../agents/branch-onboarding-orchestrator/AGENT.md`) names this file as
the single place anyone should have to look to answer *"where is NY_SCH"* — so stale status here is a
defect, not an administrative oversight.

Status: **scope agreed, execution not started; still blocked on Tier 2 DB access.**

---

## 1. The six workstreams `[stated: BOX Lead, meeting 2026-09-10]`

Agreed with the BOX Lead as the decomposition of NY_SCH onboarding. **The list carries no priority or
sequence** — it was explicitly given as unordered, and the `W1`–`W6` labels below exist only so other
documents can cite a workstream, not to imply an order. Dependencies between them are noted per row
and are the only real ordering signal we have.

Two status columns, deliberately separate — conflating them is how a project reports itself green:

- **Repo coverage** — does this repo hold the knowledge needed to do the work? (`documented` /
  `partial` / **`absent`**)
- **Work status** — has the work actually been done for NY_SCH? Currently `not started` everywhere.

| # | Workstream | Scope as agreed | Repo coverage | Work status |
|---|---|---|---|---|
| **W1** | **Software** | Local software to migrate from GBO to BOX — instrument-type logics, local conditions on portfolio properties, and the rest of the branch-specific logic that lives in code rather than config | `partial` | not started |
| **W2** | **SIGOM configs** | BOX FE configs (the eight-tab MIS aggregate, fixing curves, …) and BOX ACC configs (portfolio properties, topics, GL accounts, …). **A tool already exists that maps GBO Topics → BOX Topics** and should be used rather than re-deriving that mapping | `documented` (FE), `partial` (ACC) | not started |
| **W3** | **Jobs** | FE and ACC Job-as-code / MBJ, plus the Data Lake jobs that feed the RAW tables | `partial` | not started |
| **W4** | **Reporting** | Specific reports currently run for Madrid and SLB off Data Lake data. **Take the SLB reports and adapt them to NY** | **`absent`** | not started |
| **W5** | **GL integration** | Integration with the General Ledger. Expected to be low-complexity: the SLB integration already exists and **SLB also uses Equation as its GL** — see `../reference/system-overview.md` | `partial` | not started |
| **W6** | **FDH integration** | Integration with the **Financial Data Hub**. Expected to be easy to adapt *if* NY trades only already-configured products | **`absent`** | not started |

### What this list tells us that the repo didn't

**Four of the six workstreams are outside the current agent architecture.** The orchestrator delegates
to `box-datalake-expert` and `branch-config-agent`, which between them cover **W2** and part of **W3**.
W1, W4, W5 and W6 have no agent, no procedure and — for W4 and W6 — no reference documentation at all.
`FDH` and `Financial Data Hub` appear **nowhere** in this repo prior to this meeting; "reporting" appears
only in unrelated senses (a SIGOM balance-report screen, reporting currency). That is a scope finding,
not a criticism of the plan: the agreed project is materially wider than the machinery built for it,
and the gap should be visible rather than discovered late. `[inferred]`

**W5 and W6 are the two most likely to be cheap, and both rest on an "if".** W5's ease depends on the
Equation integration genuinely being branch-parameterised rather than SLB-specific; W6's depends on NY
trading *only* already-configured products — which is open question 4 below, unanswered. Neither "easy"
should be treated as established until its condition is checked. `[inferred]`

**W2's Topics tool is the single biggest scope reduction in the list.** Topic mapping was assumed to be
a mining-and-proposal exercise (`../../agents/sigom-box-acc-configs-agent/AGENT.md`). If an existing tool
already maps GBO topics to BOX topics, that assumption is wrong in a good way — see that agent's file.

---

## 2. Testing without booking trades in Murex `[stated: BOX Lead, meeting 2026-09-10]`

**No one needs to book a trade in Murex to test NY_SCH.** NY's existing GBO trades are *already in the
Data Lake tables*. For technical tests we can take those trades and feed the RAW tables
(`T_BOX_RAW_{DEAL|FLOW|MARKET}_DATA_S`) manually.

This removes what looked like a hard external dependency — FO booking capacity in a test environment —
and it is the most immediately actionable thing to come out of the meeting. Two caveats came with it,
and both are load-bearing:

**The trade status will not be `BOValidated`.** That status is the AUKI status; NY's GBO trades carry
something else. This directly contradicts a claim already in this repo — `../reference/job-chains/control-m-batch-layer.md`
§2 lists `status_vr`/`status_native_vr` = `BOValidated` under **boilerplate**. For NY it is not
boilerplate: it is a filter that would exclude exactly the trades we want. See that document's
correction note.

**The online entry has to be simulated.** The online path is what validates the accounting attributes
(strategy, portfolio properties) a trade needs before accounting can be generated — see
`../reference/system-overview.md`'s *Two Arrival Paths*. Feeding RAW alone skips that validation, so
something has to stand in for it.

**That second caveat needs a decision, and it is not a detail.** The orchestrator explicitly puts
BOX_TRD / online (CROSS_REF) **out of scope**, and instructs: *establish in Phase 0 whether NY_SCH needs
it, and stop if the answer is yes*. "Simulate the online entry" sits exactly on that line. Two readings,
with very different consequences:

- **A test harness** that injects the accounting attributes the online path would have set — online stays
  out of scope, the orchestrator's boundary holds, and this is a tooling task inside W3.
- **NY genuinely needs the online path** in production, and simulation is only the test-environment
  stand-in for it — in which case BOX_TRD onboarding is in scope, the orchestrator's Phase 0 says stop,
  and the project is larger than the six workstreams suggest.

Nobody has stated which. Resolve it with the BOX Lead before building either. `[open-question]`

**A caution on what this test path proves.** Hand-fed RAW rows with a non-AUKI status and a simulated
online entry exercise the *plumbing* — RAW → FE → ACC — but they are not a production-shaped flow. The
orchestrator's definition-of-done criterion 3 (reconcile against GBO Tier 2) gets harder to interpret
against hand-fed data, not easier: a break could be the config, or could be the hand-feeding. Keep the
technical test and the reconciliation test distinct. `[inferred]`

---

## 3. What we know about the branch itself

- NY_SCH exists in **GBO Tier 2** (the US data center, per `../reference/system-overview.md`); it does
  **not** exist in BOX yet.
- Tier 1 (Madrid) static data shows NY_SCH's GBO identity: entity `20007.4`, USD, New York calendar,
  United States group — but this is Tier 1's *copy* of GBO identity data, not Tier 2's live operational
  state.
- Every downstream surface checked against Tier 1 comes back empty for NY_SCH: zero
  `T_BOX_ENGCONF_X` (FE config) rows, zero product-readiness rows, zero BOX_ACC rows, zero
  Control-M/queue rows. Per `../reference/branch-config/branch-trading-readiness.md`, **this is not
  evidence NY is unready** — it's evidence that NY's real state lives in Tier 2, which hasn't been
  queried yet. Don't read the Tier 1 zeros as a readiness conclusion.
- NY_SCH's GBO branch-config row has `FK_MISCONFIG = 2.22`, which doesn't resolve to anything in Tier
  1's `DEVENG.T_PGT_ENGCONF_S` — again, a Tier 2 lookup, not a gap.
- **NY uses Equation as its GL, the same as SLB/London** `[stated: BOX Lead, 2026-09-10]` — the basis
  for W5 being expected to be straightforward.

## 4. Why "pattern it on Madrid/London" needs a caveat

Every piece of empirical evidence we have — the Madrid/London config diff, the Tier 1
branch/property/topic counts, the batch-layer job templates — comes from **Tier 1** (Madrid + SLB/London,
both in the Madrid data center). NY_SCH is **Tier 2** (a separate physical install, alongside Brazil and
Mexico). None of the current docs compare against a Tier 2 branch.

Tier 1's own finding is that concrete config (GL accounts, property breakdowns) does **not** transfer
even between two Tier-1 branches in the same data center (Madrid and London share 0 properties, 11 of
~300-450 GL accounts — see `../reference/branch-config/branch-config-madrid-london-diff.md`). If values
don't transfer within a tier, there's no basis yet to assume Madrid is even the right *structural*
template across tiers. **Brazil or Mexico (both Tier 2) are the analogues to check first, not
Madrid/London** — that comparison hasn't been run.

The Control-M batch layer reinforces this: its naming convention already branches by region — Europe
(`Mx3EU`, `SCIB` token) vs LatAm-local (`Mx3LT`, country letter embedded in the job name) — per
`../reference/job-chains/control-m-batch-layer.md`. NY's `source_system` (which Murex instance) and
`country_code_vr` aren't documented anywhere in this set of docs. That's an open question, not an
oversight to route around by guessing.

**Note the deliberate exception.** W4 and W5 both say *take the SLB version and adapt it* — SLB being a
Tier 1 branch. That is not in tension with the above: reports and GL integrations are adapted as
**artifacts**, where SLB's Equation GL makes it the right starting point, whereas the caveat is about
copying **config values** between branches. Keep the two kinds of reuse separate. `[inferred]`

## 5. Open questions (blocking, in order of what unblocks the most)

1. **Tier 2 DB access** — until this exists, nothing below can move from "proposed" to "confirmed." A
   newly-provided Ansible inventory/Vault repo may be the actual provisioning mechanism for this — see
   the *Infrastructure / deployment repos* section of `../reference/repo-index.md` before assuming this
   is stalled elsewhere.
2. **Is the online path in scope, or only simulated for testing?** (§2 above.) Changes the size of the
   project and whether the orchestrator's Phase 0 says stop.
3. **NY_SCH's Murex source_system and country_code** — needed before any Control-M/batch config can even
   be drafted.
4. **Does NY_SCH join an existing branch group, or form a new one?** (`FK_LOCALGROUP` in Tier 2). If
   existing group → it inherits that group's BOX_ACC config, likely little new config needed. If new
   group → full config build from scratch. One query once Tier 2 access exists, and it changes the size
   of the whole effort.
5. **Explicit product scope for NY_SCH**, from the business/FO SME — never inferred from what
   Madrid/London happen to trade. `branch-trading-readiness.md` is explicit that product coverage is not
   branch-wide. This also gates **W6**, whose "easy" depends on NY trading only already-configured
   products.
6. **A Tier 2 analogue** (Brazil or Mexico) run through the same diff methodology as
   `branch-config-madrid-london-diff.md`, to check whether "scope transfers, values don't" still holds
   across tiers the way it holds within Tier 1.
7. **Which GBO→BOX Topics tool, and who owns it?** (W2.) Named in the meeting, not yet identified as a
   repo, service or spreadsheet — and the difference matters for whether an agent can call it.
8. **What are the SLB reports, and where do they live?** (W4.) No repo coverage at all.
9. **What is the FDH interface?** (W6.) No repo coverage at all.

## 6. Plan

Mapped onto the orchestrator's Phase 0–4 (`../reference/branch-config/agent-architecture.md`) — one
workflow definition for this project, not two. **The phases and the workstreams are different axes**:
phases are sequence, workstreams are scope. A workstream does not "reach Phase 3" on its own; the
phases run across the workstreams the agent architecture covers (W2, part of W3), and W1/W4/W5/W6 have
no phase mapping yet because they have no owner yet.

**Phase 0 — Gate.** Get Tier 2 DB access. Get the explicit product scope from the FO SME. Resolve open
questions 2, 3 and 4 (online-in-scope; source_system/country_code; branch-group existing vs. new) — all
gate everything downstream, and question 2 can end the project's current shape.

**Phase 1 — Build** (delegated to the two delegates — see `agent-architecture.md`'s "The three agents"
for why FE and ACC config work is one agent, not two):
   - `box-datalake-expert`: expand `(country, source_system, books)` per the 5-step method in
     `control-m-batch-layer.md`. Flag any `eventsToWaitFor` feed that isn't a known Data-Lake event.
     Also owns the manual RAW test-feed path (§2) and the `BOValidated` status problem.
   - `branch-config-agent`, ACC side: before proposing values, first resolve open question 6 — re-run the
     Madrid/London-style comparison against a Tier 2 branch (Brazil or Mexico) to confirm or correct
     whether Madrid's `(instrument, topic)` scope is a usable template for NY. This is methodology
     internal to this agent's mining step, not a separate phase. Then propose the `(instrument, topic)`
     matrix NY_SCH's selected products require — **using the GBO→BOX Topics tool rather than deriving
     the mapping** — plus GL account values and portfolio-property breakdown (jurisdiction-specific
     pattern — Madrid splits by product/strategy, London by counterparty sector for UK regulatory
     reasons; NY's own logic is unknown and SME-owned).
   - `branch-config-agent`, FE side: rank existing FE configurations by evidence-backed compatibility
     (currency, calendar, source systems) and propose the smallest adaptation, or a new configuration
     aggregate if nothing fits.

**Phase 2 — Sign-off** (never automated, never invented — per the golden rule in
`../process/checklists/branch-onboarding-checklist.md`): GL account values, portfolio-property
breakdown, and instrument-type configuration rows (only if the SME confirms configuration, rather than
product fallback, is required) all go to SME confirmation here. Also verify external dependencies —
MDR→Infrastructure replication, Asset Control FX quote files, MIC integration — flagging gaps rather
than building around an assumed answer.

**Phase 3 — Apply.** Each expert applies its own confirmed config.

**Phase 4 — Validate.** Once NY_SCH trades flow, walk the full trace in `accounting-resolution-chain.md`
(deal → instrument type → portfolio property → topic → GLTA → account key → Historic Standard → posted
movement), confirm FINANCST records generate per product, and reconcile against GBO Tier 2 per the
orchestrator's Definition of done — the trace resolving cleanly is not sufficient on its own, and §2's
caution on hand-fed data applies here.

## Sources

Meeting with **BOX Lead, 2026-09-10** (workstreams, testing approach, Equation/GL, Topics tool) —
`[stated]`, not independently verified against the systems.
`../reference/system-overview.md`, `../reference/branch-config/branch-trading-readiness.md`,
`../reference/branch-config/fe-branch-configuration.md`,
`../reference/branch-config/branch-config-surface.md`,
`../reference/branch-config/branch-config-madrid-london-diff.md`,
`../reference/job-chains/control-m-batch-layer.md`, `../reference/fe-raw-data-stage.md`,
`../reference/branch-config/accounting-resolution-chain.md`,
`../process/checklists/branch-onboarding-checklist.md`.
