# SIGOM Reference Documentation

> **Scope note:** This document is built strictly from screenshots provided by the user. Nothing is inferred or assumed beyond what is visibly shown in a screenshot. Anything unclear or not yet shown is tracked in the **Open Questions** section rather than guessed at.

## What is SIGOM

SIGOM is the configuration UI used at Santander for BOX (Back Office Express — a derivatives back-office accounting system) and its predecessor, GBO. SIGOM itself is a front end; it is backed by Oracle SQL tables.

SIGOM runs as two environments:

- **Tier 1** — physically located in Madrid; covers the Madrid and SLB branches.
- **Tier 2** — located in the US; covers the NY, Brazil, and Mexico branches. Described as very similar to Tier 1.

**Scope of this document:** the screenshots being reviewed here are all from **Tier 1**. Anything documented below reflects Tier 1 specifically. Where Tier 2 is known to differ, or where a difference simply hasn't been shown, it will be flagged in Open Questions rather than assumed.

*(Further detail to be added as screenshots are reviewed.)*

## Global UI Elements

These elements appear to be part of the application chrome, not tied to any one screen.

- **Window title:** `Sigom Evolution 5.8.2-19-g02c07e6a (igbomd)` — includes a version/build string (`5.8.2-19-g02c07e6a`, the trailing part looks like a git short-hash) and an instance/host identifier (`igbomd`).
- **Menu bar:** File, Edit, View, Tools, User, Window, Help. (Menu contents not yet shown.)
- **Toolbar:** a row of icon-only buttons — home, a list/notepad icon, save, print, print preview, cut, copy, paste, a console/terminal-like icon, a green "play" triangle, a lightning-bolt icon, a red "stop" icon, a bar-chart icon, another small icon, an info ("i") icon, and a help ("?") icon. Icons are not labeled in this screenshot, so their exact functions are open questions (see below).
- **Environment badge:** a green pill-shaped label reading `IGBOMD (copia 23-Dec-17)`, next to the toolbar. Appears to indicate which environment/database instance is currently connected — `IGBOMD` matches the identifier in the window title and in the status bar session info. `(copia 23-Dec-17)` suggests this may be a copy/snapshot dated 23-Dec (year unclear), though this is not confirmed by anything else visible.
- **Work View Explorer** (left panel, pinned): the main navigation tree for the application.
  - Has a search box at the top (with a magnifying-glass icon) to filter the tree.
  - Three tabs: **All**, **Favorites**, **History**.
  - Under "All", a flat list of top-level, collapsible (all currently collapsed) nodes, in this order:
    `<ADMIN>`, `<PROJECTS>`, `<Security>`, `<TOOLS>`, `AFM`, `BOX`, `BOX - Accounting`, `BOX - Financial Engine`, `BOX - Migration`, `BOX - Settlement`, `Document Status Monitor`, `GBO`, `General Loader PT`, `Madrid`, `Mantenimiento`, `Master Product Catalogue`, `MDR Adapter`, `Settlement Interface`, `Spain`.
    Nodes wrapped in `<...>` (ADMIN, PROJECTS, Security, TOOLS) are visually/naming-distinct from the others — possibly a different category of node (e.g. system/admin areas vs. functional/product areas), but this is not confirmed yet.
  - None of these nodes have been expanded yet in the screenshots provided, so their contents are open questions.
- **Status bar** (bottom of window):
  - Bottom-left: a `Trace` tab/label (blue background). **Function confirmed (user-provided, not from a screenshot):** this relates to a **Trace view** that reveals the underlying database table(s) behind the screen currently open. It can be activated two ways: **Ctrl+Shift+Click** (on the screen/field in question, presumably), or via the menu path **View > Trace View**. This is likely the mechanism SIGOM itself uses to expose the Screen → Database Table Mapping information recorded elsewhere in this document — worth using directly in-app to confirm/discover further table mappings rather than relying solely on the user recalling them.
  - Below/beside the `Trace` tab, a second line showing the **name of the currently selected top-level Work View Explorer node** (e.g. shows `GBO` while the `GBO` node is selected, replacing the earlier `Ready` text seen on the plain Start Page). Acts as a breadcrumb/context indicator for the current tree selection.
  - Right side: `Local:x700072@IGBOMD` (a session identity string — `x700072` is likely a user/employee ID, `IGBOMD` the connected environment) and `Last login: 2026-09-10 09:18:03`.
- **Work View Explorer node behavior:**
  - Nodes with children show a `+` (collapsed) / `−` (expanded) icon plus a chevron (`>` collapsed, rotated when expanded) to their left.
  - Clicking a node selects/highlights it (blue background) and, if it has children, expands it inline — children appear indented directly beneath, pushing subsequent siblings down (the tree does not open a separate panel).
  - **Two distinct node icons confirmed:** folder-like nodes (which contain further children) show a slanted flag/triangle icon; terminal/leaf nodes — the actual openable screens — show a different icon resembling a small box with an upward arrow (suggesting "open/launch this screen"). Leaf nodes have no expand chevron since they have no children.
  - Opening a leaf node adds a new tab next to `Start Page` (tabs are closable via an `x`). **Note:** the tab's title does not necessarily match the tree leaf's label verbatim — e.g. the tree leaf `Assign Instrument Type` (under `BOX - Accounting > Config.`) opens a tab titled `BOX Instrument Type`. The selected leaf's label is shown highlighted (blue text) in the tree while its tab is active.

## Work View Explorer — Tree Contents (as expanded so far)

Documenting the tree structure as branches get expanded. Only branches explicitly shown expanded are listed with children; everything else remains an unexpanded top-level node (see the full top-level list in Global UI Elements above).

- **GBO** (top-level node)
  - Accounting — fully expanded; leaf screens listed below each folder
    - Documents (folder)
      - Check Documents
      - Edit Documents
    - General (folder)
      - Check Port Properties
      - Config Metal
      - Cost Center
      - Currency Mark To Market
      - Global Accounts
      - Portfolio Properties
      - Standard Historic
    - Grouped Movements (folder)
      - Grouped Accounting Conf(iguration?) — *label was visually truncated in the screenshot; exact full name unconfirmed*
      - Grouped Accounting Move(ments?) — *label was visually truncated; exact full name unconfirmed*
    - Interfaces (folder)
      - Balance Files
    - Manual Movements (folder)
      - Accounting Entries
      - Config Account
      - Manual Movements *(leaf screen with the same name as its parent folder)*
      - User/Profile
    - Reports (folder)
      - Analytic Account Report
      - Analytic Registry Report
      - Balance Registry Report
      - Balance Report
      - Grouping Balance Report
      - Hierarchy Balance Report
      - Instrument Balance Report
      - Movements Report
    - Settle to Market (folder — same name as its parent "Accounting" sub-item)
      - Settle to Market *(leaf screen with the same name as its parent folder)*
      - SwapAgent Cpty Br Conf — *abbreviated; likely "SwapAgent Counterparty Branch Configuration" but not confirmed*
  - Agreement
  - Catalog
  - Collaterals
  - Conciliation
  - Confirmation
  - Documentation
  - File System
  - Financial Engine
    - Control
    - Financial Status
    - OBB Module
    - Process Management
    - Static MIS Data
  - Financial Engine G1
  - GBO - Msg Service
  - General
  - Interfaces
  - Market Data
  - Portfolio Reconciliation
  - Process
  - Regulatory
  - Replic
  - Settlement
  - Static Data
  - STP
  - Swift
  - SYS
  - Trading

  None of GBO's second-level children other than Accounting and Financial Engine have been expanded yet — their contents are open questions.

- **BOX - Accounting** (top-level node, separate from the plain `BOX` node)
  - Config. (folder — note: label includes a trailing period)
    - Assign Instrument Type
    - Condition Port Properties
    - Config. Acct By StdHist
    - Config. Local Properties
    - Cross Account Config
    - FX Liquid Config
    - Grouped Accounting Config
    - Net EOM to CCS
    - Portfolio Properties
  - Data (folder)
    - Accounting Topics
    - Documents
    - Global Accounts
    - Net Contract
    - Standard Historic
    - Standard Historic Group
    - Topic Group
  - MBJ Config *(a leaf screen directly under BOX - Accounting, at the same level as the Config./Data/Reports folders — not itself a folder)*
  - Reports (folder)
    - Balance Deal Report
    - Balance Report
    - Grouped Acc Movemt Report
    - Instrument Balance Report
    - Movements Report

**Observation, now confirmed:** `BOX - Accounting` is indeed a standalone top-level tree node (as it appeared on the Start Page top-level list), not a sub-node nested inside a plain `BOX` node — its internal structure (`Config.`, `Data`, `MBJ Config`, `Reports`) is organized differently from `GBO > Accounting` (`Documents`, `General`, `Grouped Movements`, `Interfaces`, `Manual Movements`, `Reports`, `Settle to Market`). So BOX and GBO are structurally parallel concepts (both have an "Accounting" area) but organize their sub-screens differently and BOX's is exposed as its own top-level tree node rather than nested under a `BOX` parent. What's inside the plain `BOX` top-level node itself is still unknown.

**Start Page cross-reference confirmed:** the `MBJ Config` tile shown in "Most Used Applications" on the Start Page corresponds exactly to the `MBJ Config` leaf found under `BOX - Accounting` — confirming Start Page tiles do map directly to specific Work View Explorer tree leaves.

- **BOX - Financial Engine** (top-level node, separate from `BOX`, `BOX - Accounting`, `BOX - Migration`, `BOX - Settlement`)
  - BOX Deal Data (leaf)
  - BOX Flow Data (leaf)
  - BOX MarketValue & Risk (leaf)
  - BOX MarketValue Camara (leaf)
  - Control (folder) — fully expanded; see below
    - Configuration (folder)
      - Accrual Configuration
      - Book Configuration
      - Days Matured
      - FE Parameters
      - Fixing Curve
      - MIS
    - Historical Data (folder)
      - Accrual Data Lake
      - Branch - MIS
      - Fixing Curve *(same leaf name as one under `Configuration` above — reused across sibling folders, same as `Settle to Market`/`Manual Movements` reusing folder names for a leaf seen earlier under GBO)*
      - Market Data
    - Tools (folder)
      - Management Status FE
      - Scheduling *(a folder, not yet expanded — icon suggests it has children)*
  - Financial Status (folder) — per the user, this is where financial data lives per product. Contains one sub-folder per product family:
    - BRS (folder, not yet expanded — Bond Return Swap)
    - C&F (folder, not yet expanded)
    - CCS (folder) — fully expanded:
      - BOX CCS Deal Data (leaf)
      - BOX CCS Financial Data (leaf)
      - BOX CCS MtM Data (leaf)
    - CDS (folder) — fully expanded:
      - BOX CDS Deal Data (leaf)
      - BOX CDS Financial Data (leaf)
      - BOX CDS MtM Data (leaf)
    - CES (folder, not yet expanded)
    - CFM (folder, not yet expanded)
    - Depo (folder, not yet expanded)
    - FRA (folder, not yet expanded)
    - FX (folder, not yet expanded)
    - OTC (folder, not yet expanded)
    - Swap (folder, not yet expanded)
  - Process Management (folder) — fully expanded:
    - Allowed Errors (leaf)
    - Log (leaf)
    - Monitor (leaf)
    - Process Queues (leaf)
  - Static IT Data (folder) — fully expanded:
    - Deal Status (leaf)
    - Event (leaf)
    - Event Parameter (leaf)
    - Exec Direction (leaf)
    - Fee Type (leaf)
    - Procedures (leaf)
    - Process (leaf)
    - Process Status (leaf)
    - Processed Instruments (leaf)

**Confirmed naming pattern for `Financial Status` product sub-folders:** each product folder appears to hold exactly 3 leaves named `BOX <PRODUCT> Deal Data`, `BOX <PRODUCT> Financial Data`, `BOX <PRODUCT> MtM Data` (confirmed for CCS and CDS; the other 9 product folders are not yet expanded but likely follow the same 3-leaf pattern).

**Start Page cross-reference confirmed:** the `MIS` tile on the Start Page's "Most Used Applications" maps to the leaf `BOX - Financial Engine > Control > Configuration > MIS`.

**Start Page "History" cross-reference confirmed:** two of `BOX - Financial Engine`'s direct leaves — `BOX Flow Data` and `BOX MarketValue & Risk` — match tile names shown in the Start Page's "History" section exactly, extending the earlier `MBJ Config` (Most Used Applications) confirmation to the History tiles as well.

**Comparison with GBO's Financial Engine:** `GBO > Financial Engine` (documented earlier) has children `Control`, `Financial Status`, `OBB Module`, `Process Management`, `Static MIS Data` — no direct leaf screens, only folders. `BOX - Financial Engine` has `Control`, `Financial Status`, `Process Management`, `Static IT Data` (folders) **plus** 4 direct leaf screens (`BOX Deal Data`, `BOX Flow Data`, `BOX MarketValue & Risk`, `BOX MarketValue Camara`). Differences noted: BOX's Financial Engine has no `OBB Module` equivalent, and uses `Static IT Data` where GBO uses `Static MIS Data` — another instance of similar-but-not-identical naming/structure between the GBO and BOX sides of SIGOM.

**Top-level siblings reconfirmed:** a later screenshot showed the tree scrolled to reveal, immediately below `BOX - Accounting`'s branch: `BOX - Financial Engine`, `BOX - Migration`, `BOX - Settlement`, `Document Status Monitor`, `GBO`, `General Loader PT`, `Madrid`, `Mantenimiento` — confirming these are indeed separate top-level nodes at the same level as `BOX - Accounting` (matching their original appearance in the Start Page's top-level list), rather than nested under a single `BOX` parent. None of `BOX - Financial Engine`, `BOX - Migration`, or `BOX - Settlement` have been expanded yet.

## Screen → Database Table Mapping

SIGOM is a UI layer backed by Oracle SQL tables. Where the user provides the underlying table for a screen directly (not inferred from a screenshot), it's recorded here.

| SIGOM tree path | Screen | Oracle table |
|---|---|---|
| BOX - Financial Engine > BOX Deal Data | BOX Deal Data | `BOX_FE.T_BOX_DEAL_DATA_S` |
| BOX - Financial Engine > BOX Flow Data | BOX Flow Data | `BOX_FE.T_BOX_FLOW_DATA_S` |
| BOX - Financial Engine > BOX MarketValue & Risk | BOX MarketValue & Risk | `BOX_FE.T_BOX_MTM_DATA_S` |
| BOX - Financial Engine > BOX MarketValue Camara | BOX MarketValue Camara | `BOX_FE.T_BOX_MTM_CAM_S` |
| BOX - Financial Engine > Control > Configuration > Days Matured | Days Matured | `BOX_FE.T_BOX_ENGDAYS_MATURED_S` |
| BOX - Financial Engine > Control > Configuration > FE Parameters | FE Parameters | `BOX_FE.T_BOX_ENGSETUP_S` |
| BOX - Financial Engine > Control > Configuration > Fixing Curve | Fixing Curve | `BOX_FE.T_BOX_ENGFCURVE_S` |
| BOX - Financial Engine > Control > Configuration > MIS | MIS (tab: "ENG Config Selection") | `BOX_FE.T_BOX_ENGCONF_S` |
| BOX - Financial Engine > Financial Status > CCS > BOX CCS Deal Data | BOX CCS Deal Data | `BOX_FE.T_BOX_DATADEAL_S` (shared/generic table — see rule below) |
| BOX - Financial Engine > Financial Status > CCS > BOX CCS Financial Data | BOX CCS Financial Data | `BOX_FE.T_BOX_CCSFINANCST_S` |
| BOX - Financial Engine > Financial Status > CCS > BOX CCS MtM Data | BOX CCS MtM Data | `BOX_FE.V_BOX_ENGCCSDATAMIS_S` (view) |
| BOX - Accounting > Config. > Assign Instrument Type | Assign Instrument Type | `BOX_ACC.T_BOX_CONF_INSTRUM_TYPE_S` |
| BOX - Accounting > Config. > Condition Port Properties | Condition Port Properties | `BOX_ACC.T_BOX_CONDPAR_PROP_S` |
| BOX - Accounting > Config. > Config. Local Properties | Config. Local Properties | `BOX_ACC.T_BOX_CONF_LO_PROP_S` |
| BOX - Accounting > Config. > Cross Account Config | Cross Account Config | `BOX_ACC.T_BOX_CROSS_ACCTCONF_S` |
| BOX - Accounting > Config. > Portfolio Properties | Portfolio Properties | `BOX_ACC.T_BOX_ACCT_PORT_PROP_S` |
| BOX - Accounting > Data > Accounting Topics | Accounting Topics | `BOX_ACC.T_BOX_ACCT_TOPICS_S` |
| BOX - Accounting > Data > Documents | Documents | `BOX_ACC.T_BOX_ACCT_DOC_S` |
| BOX - Accounting > Data > Global Accounts | Global Accounts | `BOX_ACC.T_BOX_ACCT_GLTA_S` |
| BOX - Accounting > Data > Net Contract | Net Contract | `BOX_ACC.T_BOX_NETCONTRACT_S` |
| BOX - Accounting > Data > Standard Historic | Standard Historic (not yet screenshotted) | `BOX_ACC.T_BOX_ACCT_HISTSTD` |
| BOX - Accounting > Data > Standard Historic Group | Standard Historic Group (not yet screenshotted) | `BOX_ACC.T_BOX_ST_HIST_GROUP_S` |
| BOX - Accounting > Data > Topic Group | Topic Group (not yet screenshotted) | `BOX_ACC.T_BOX_TOPICS_GROUP_S` |
| BOX - Accounting > MBJ Config | MBJ Config | `BOX_ACC.T_BOX_MBJ_PROPERTIES_S` |

**Observation:** all `BOX - Financial Engine` tables use schema `BOX_FE`, while all `BOX - Accounting` tables use schema `BOX_ACC` — **confirming the Oracle schema name follows the top-level SIGOM tree branch** (`BOX - Financial Engine` → `BOX_FE`, `BOX - Accounting` → `BOX_ACC`). Nearly all tables also follow a `T_BOX_<NAME>_S` naming convention. Meaning of the trailing `_S` suffix not confirmed (possibly "Staging"/"Source"/a versioning convention, or simply part of the shop's table-naming standard) — flagged as an open question.

**Exception noted, and independently confirmed as real (not a transcription slip):** `BOX_ACC.T_BOX_ACCT_HISTSTD` (Standard Historic) is the first table seen **without** the trailing `_S` suffix that every other table so far has. `../reference/box-data-model.md` lists this exact table the same way (with a parenthetical alternate name `T_BOX_ACCT_BY_STD_HIST_S`), so this is a genuine, cross-confirmed naming exception — not an artifact of how it was transcribed here. *Why* it's the exception is still unexplained.

**General naming rule for `Financial Status` product screens (stated directly by the user, not inferred):** under `BOX - Financial Engine > Financial Status`, each product family (see tree section below) has up to 3 leaf screens following a fixed naming/table pattern:
- `BOX <PRODUCT> Deal Data` → **always** the same shared table `BOX_FE.T_BOX_DATADEAL_S`, regardless of product (i.e. this one table is NOT product-specific — all products' deal data screens query the same underlying table, presumably filtered by product/instrument type).
- `BOX <PRODUCT> Financial Data` → `BOX_FE.T_BOX_<PRODUCT>FINANCST_S` (product-specific table). Confirmed example: CCS → `BOX_FE.T_BOX_CCSFINANCST_S`.
- `BOX <PRODUCT> MtM Data` → `BOX_FE.V_BOX_ENG<PRODUCT>DATAMIS_S` — note the `V_` prefix (a **database view**, not a table, unlike the other two), and the `ENG` infix (consistent with the `ENG` = "Engine" pattern already seen under Control > Configuration). Confirmed example: CCS → `BOX_FE.V_BOX_ENGCCSDATAMIS_S`.

**Not yet individually confirmed by name, but the shared-table part is independently corroborated:** `CDS`'s three leaves (`BOX CDS Deal Data`, `BOX CDS Financial Data`, `BOX CDS MtM Data`) and every other product family's leaves would, per the stated general rule, resolve to `BOX_FE.T_BOX_DATADEAL_S` (shared), `BOX_FE.T_BOX_CDSFINANCST_S`, and `BOX_FE.V_BOX_ENGCDSDATAMIS_S` respectively — but only the CCS instantiation was explicitly given as an example here. Separately, `../reference/fe-raw-data-stage.md` already sampled `T_BOX_DATADEAL_S` directly at the DB level and found it holding **both** IRS (2,096 rows) and CCS (904 rows) at once, explicitly confirming it as "a shared cross-product processing surface" — real evidence for the shared-Deal-Data-table half of this rule, from a source independent of these screenshots. The per-product `FINANCST`/`DATAMIS` table names for CDS and the other nine families are still derived from the stated naming pattern only, not confirmed by name.

**Sub-pattern strengthened further:** four tables under `Control > Configuration` now share an `ENG` infix — `T_BOX_ENGDAYS_MATURED_S` (Days Matured), `T_BOX_ENGSETUP_S` (FE Parameters), `T_BOX_ENGFCURVE_S` (Fixing Curve), `T_BOX_ENGCONF_S` (MIS) — plausibly short for "Engine". The four direct `BOX - Financial Engine` leaf screens' tables (`DEAL_DATA`, `FLOW_DATA`, `MTM_DATA`, `MTM_CAM`) still don't use this infix. With 4 of 4 Control > Configuration screens now following this pattern, this looks like a solid naming convention for that branch specifically.

## Screens

### Start Page

- **Purpose:** Landing/home screen shown when SIGOM opens. Appears to be a dashboard for quickly launching frequently- or recently-used configuration screens ("applications").
- **Location / navigation:** Opens by default as the initial tab; also reachable via the home icon in the toolbar (unconfirmed — inferred from icon position, flagged as open question below).
- **Sections:**
  - **Most Used Applications** — a grid of tiles, each presumably a shortcut to a specific SIGOM configuration screen. Visible tiles: `MIS`, `MBJ Config`, `Global Accounts`, `Assign Instrument Type`, `Label Config`, `Branch Configuration`. The grid appears to be cut off / horizontally scrollable on the right edge, so there may be additional tiles not visible in this screenshot.
  - **History** — a similar tile grid, presumably recently-opened screens. Visible tiles: `Deal Lite Query`, `BOX IRS Financial Data`, `BOX CCS Financial Data`, `BOX C&F Financial Data`, `BOX MarketValue & Risk`, `BOX Flow Data`. Also appears cut off on the right edge.
  - **Favorites** — empty in this screenshot except for a `+` tile, presumably used to add a screen to favorites.
- **Fields:** none (this is a launcher screen, not a data-entry screen).
- **Relationships to other screens:** each tile name (e.g. `MIS`, `Global Accounts`, `BOX Flow Data`) likely corresponds to a node or leaf somewhere in the Work View Explorer tree, but no such correspondence has been confirmed yet since the tree nodes haven't been expanded.
- **Screenshot source:** "main screen when you open Sigom" (Tier 1).

### BOX - Accounting > Config. > Assign Instrument Type (tab title: "BOX Instrument Type")

This is the first leaf/config screen opened, so its layout is documented here in detail as a possible template for other leaf screens — to be confirmed or revised as more screens are seen.

- **Purpose:** appears to let a user look up and manage instrument-type assignment records — parameters/configuration values keyed by branch, instrument, and a code/value pair, optionally scoped to a counterparty.
- **Location / navigation:** opened from the Work View Explorer via `BOX - Accounting > Config. > Assign Instrument Type`. Opens in a new tab (titled "BOX Instrument Type") alongside the Start Page tab.
- **Layout — three areas:**
  1. **Filter/search header** (top), fields:
     - `Branch:` — dropdown/combobox (shown set to `MADRID REAL`), with an eye icon next to it.
     - `Code:` — free-text field.
     - `Counterparty:` — free-text field, with a search (magnifying glass) icon and an eye icon next to it.
     - `Instrument:` — free-text field, with a search (magnifying glass) icon and an eye icon next to it.
     - `Value:` — free-text field.
     - `Inst. Type:` — dropdown/combobox (empty in this screenshot).
     - `Type:` — free-text field.
  2. **Vertical icon toolbar** (left edge of the grid area), top to bottom: `+` (add), trash bin (delete), pencil (edit), a copy/duplicate icon, a magnifying glass (search), and a funnel-shaped icon (filter). Exact behavior of each not yet confirmed by interaction, but icon shapes strongly suggest add/delete/edit/copy/search/filter row-level actions on the grid below.
  3. **Data grid**, columns: `Branch`, `Instrument`, `Instrument Type`, `Code`, `Value`, `Type`, `Counterparty` — these appear to correspond directly to the filter header fields above (`Branch`→Branch, `Instrument`→Instrument, `Inst. Type`→Instrument Type, `Code`→Code, `Value`→Value, `Type`→Type, `Counterparty`→Counterparty). The grid is scrollable; one row can be selected/highlighted.
- **Status bar (screen-specific additions when this tab is active):** `Sel: 0 / Count: 99` (selected-row count / total row count for the current filter) and `Current auth-code: 21 - Madrid` (a numeric code paired with a branch/entity name — here `21` corresponds to `Madrid`, matching the `MADRID REAL` branch selected in the filter header).
- **Data note:** per instruction, specific row values (instrument types, codes, counterparty codes, etc.) are intentionally *not* transcribed here — only the screen's structure and column/field set are documented.
- **Screenshot source:** BOX - Accounting > Config. > Assign Instrument Type, filtered to branch MADRID REAL (Tier 1).

### BOX - Accounting > Config. > Condition Port Properties (tab title: "Conditions Portfolio")

Second leaf/config screen opened — confirms and refines the template seen on `Assign Instrument Type`.

- **Purpose:** appears to be a reference/definition list of reusable "conditions" — named predicates or lookups that other parts of BOX configuration can reference. Each condition is typed as either `Field` (referencing a data field) or `Function` (referencing a callable function), and carries a human-readable description.
- **Location / navigation:** opened from `BOX - Accounting > Config. > Condition Port Properties`. Opens in a new tab titled "Conditions Portfolio" — again the tab title does not match the tree leaf label verbatim (same pattern noted on `Assign Instrument Type` → "BOX Instrument Type").
- **Layout — same three areas as `Assign Instrument Type`:**
  1. **Filter/search header:** `Internal Id:` (text), `Condition Type:` (dropdown), `Function:` (text, wide), `Field:` (dropdown, with an eye icon next to it). Notably, this screen has **no Branch filter field**, unlike `Assign Instrument Type` — suggesting this condition list is not branch-scoped (i.e. it may be a global/shared reference table rather than per-branch data).
  2. **Vertical icon toolbar:** same icon set as `Assign Instrument Type` (`+`, trash/delete, pencil/edit, copy, search, filter) — **confirms this toolbar is a recurring template across Config sub-screens**, not a one-off.
  3. **Data grid**, columns: `Internal Id`, `Condition Type`, `Function`, `Field`, `Description`. `Condition Type` values seen are `Field` or `Function`; when `Field`, the `Field` column is populated and `Function` is blank, and vice versa — the two columns appear mutually exclusive depending on the condition's type.
- **Status bar:** shows `Sel: 0 / Count: 20 | Current auth-code: 21 - Madrid` — the same `Current auth-code: 21 - Madrid` seen on the previous screen, **even though this screen has no Branch selector of its own**. This suggests `Current auth-code` is a **global/session-level indicator** (tied to whatever branch was last selected elsewhere, e.g. on `Assign Instrument Type`) rather than something each screen sets independently. Not fully confirmed — flagged as open question.
- **Data note:** as with the previous screen, specific row contents (internal IDs, function names, field names, descriptions) are intentionally not transcribed here — only the screen's structure and column set are documented.
- **Screenshot source:** BOX - Accounting > Config. > Condition Port Properties (Tier 1).

### BOX - Accounting > Config. > Config. Local Properties (tab title: "Split Config. Local Prop")

Third leaf/config screen opened.

- **Purpose:** appears to define per-instrument, per-branch-group overrides/splits of the "conditions portfolio properties" concept seen on the previous screen (`Condition Port Properties`) — the description text on several rows explicitly references "Conditions Portfolio Properties", suggesting this screen localizes or splits that configuration by instrument type and branch group. Relationship is inferred from description wording, not explicitly confirmed by the UI.
- **Location / navigation:** opened from `BOX - Accounting > Config. > Config. Local Properties`. Opens in a tab titled "Split Config. Local Prop" (likely truncated — probably "Split Config. Local Properties"; not confirmed).
- **Layout — same three-area template again:**
  1. **Filter/search header:** `Internal Id:` (text), `Instrument:` (text, with search + eye icons), `Branch Group:` (dropdown, with an eye icon), `Initial Date:` (text).
  2. **Vertical icon toolbar:** same recurring icon set (`+`, delete, edit, copy, search, filter).
  3. **Data grid**, columns: `Internal Id`, `Instrument`, `Branch Group`, `Initial Date`, `Descripcion` (note: this column header is in Spanish here, vs. "Description" in English on the `Condition Port Properties` screen — an inconsistency in the UI's language, not something we're normalizing).
- **Confirmed cross-screen pattern:** on all three Config screens seen so far, the grid's last/rightmost descriptive column (`Description` / `Descripcion`) has no corresponding filter field in the header — the filter header always covers all grid columns except that trailing description column.
- **New field distinction noted, and resolved from elsewhere in this repo — not just this screen:** this screen filters by **Branch Group** (a dropdown), which is a different concept from the **Branch** field seen on `Assign Instrument Type` (also a dropdown, but a specific operating branch like `MADRID REAL`). `../reference/branch-config/branch-config-surface.md` already proves this relationship at the DB level: BOX_ACC's manual config (portfolio properties, topic→GL maps — exactly the tables `Config. Local Properties`, `Portfolio Properties`, and `Accounting Topics` surface) is keyed by branch **group** (`T_PGT_BRANCH_S.FK_LOCALGROUP`), not by the specific branch PK — e.g. Madrid (`22.21`) and London (`20087.4`) each resolve to 0 properties when queried by their own PK, but 80/101 respectively when queried by their `FK_LOCALGROUP`. So "Branch" (a specific booking branch) and "Branch Group" (the shared config-keying dimension, which is what this screen's own filter uses) are genuinely different granularities, and this screen filtering by Branch Group rather than Branch is expected, not a UI inconsistency. Separately, that same doc's §6 confirms `T_PGT_BRANCH_S` is an overloaded ~137-row registry (legal entities, SPVs, counterparties, test/parallel records — not 137 booking branches), so Branch Group values reaching beyond Madrid/SLB (e.g. resembling London, Colombia) are expected too — Branch Group is a bank-wide accounting-config dimension, independent of the Tier 1/Tier 2 physical data-center split described at the top of this document. Those two splits (Branch Group vs. Tier) answer different questions and shouldn't be conflated.
- **Status bar:** shows `Current auth-code: 21 - Madrid` as before, but — unlike the two previous screens — **no `Sel: n / Count: n` segment appears here**. Not clear whether that segment is conditional on something (e.g. whether a search was explicitly executed) or simply not part of this screen; flagged as an open question.
- **Data note:** row content is not transcribed verbatim per the same approach as prior screens. That said, the visible **Branch Group** values on this screen include entries beyond Tier 1's Madrid/SLB scope (e.g. groupings resembling "Spain", "London", "Colombia"), and the **Instrument** column lists general product-type categories (e.g. OTC Option, Cross Currency Swap, Swap, Cash Flow Matching, Deposit & Loan, Credit Derivatives, Forward Rate Agreement, Caps and Floors, Commodity Swap) — recorded here only to help understand the screen's structure (a product-type × branch-group matrix), not as reference data. This raises an open question about how "Branch Group" (which spans other bank branches) relates to the Tier 1 / Tier 2 environment split described at the top of this document.
- **Screenshot source:** BOX - Accounting > Config. > Config. Local Properties (Tier 1).

### BOX - Accounting > Config. > Cross Account Config (tab title: "Cross Account Config")

Fourth leaf/config screen opened. Tab title matches the tree leaf label exactly this time (no mismatch, unlike the previous three screens).

- **Purpose:** appears to configure cross-account mappings — associating a branch/instrument/currency/entity combination with a specific account, topic, and account type.
- **Location / navigation:** opened from `BOX - Accounting > Config. > Cross Account Config`.
- **Layout — same three-area template, two-column filter header (like `Assign Instrument Type`):**
  1. **Filter/search header,** left column: `Internal Id:` (text), `Branch:` (dropdown, shown set to `MADRID REAL`, with an eye icon), `Instrument:` (text, with search + eye icons), `Entity:` (text, with search + eye icons — field appears visually greyed out/disabled in this screenshot), `Account Type:` (dropdown, empty); right column: `Currency:` (text, with search + eye icons), `Account:` (text, with search + eye icons — also appears greyed out/disabled), `Topic:` (text, with search + eye icons).
     - **Note:** `Entity` and `Account` look visually disabled (lighter background) compared to the other fields in this screenshot — possibly enabled conditionally (e.g. only after another field is set). Not confirmed by interaction.
  2. **Vertical icon toolbar:** same recurring icon set.
  3. **Data grid**, columns: `Internal ID`, `Branch`, `Instrument`, `Currency`, `Entity`, `Account`, `Topic`, `Acc Type`.
- **Status bar:** shows `Sel: 1 | Current auth-code: 21 - Madrid` — note this appears as just `Sel: 1` with **no `/ Count: n` suffix**, unlike the `Sel: 0 / Count: 99` / `Sel: 0 / Count: 20` format seen on the first two Config screens. Possibly the count portion only displays in certain states (e.g. after an explicit search); not confirmed.
- **Data note:** row content (account codes, topics, etc.) not transcribed, consistent with prior screens. The `Instrument` column values are again general product-type categories (Swap, OTC Option, Caps And Floors, Cross Currency Swap, Cash Flow Matching, Credit Derivatives), consistent with categories seen on other screens.
- **Screenshot source:** BOX - Accounting > Config. > Cross Account Config, filtered to branch MADRID REAL (Tier 1).

### BOX - Accounting > Config. > Portfolio Properties (tab title: "Portfolio Properties")

Fifth leaf/config screen opened.

- **Purpose:** appears to be a reference list of named portfolio-property definitions per branch/branch-group and instrument type, each with a validity status and description.
- **Location / navigation:** opened from `BOX - Accounting > Config. > Portfolio Properties`.
- **Layout — same three-area template:**
  1. **Filter/search header:** `Internal Id:` (text), `Intrument:` (text, with search + eye icons — **note: this is a label typo in the actual UI**, missing the "s" in "Instrument", transcribed here exactly as shown), `Initial Date:` (text), `Branch Group:` (dropdown, with an eye icon).
  2. **Vertical icon toolbar:** same recurring icon set.
  3. **Data grid**, columns: `Internal ID`, `Branch`, `Instrument`, `Initial Date`, `Status`, `Descripcion`.
     - **Naming inconsistency noted:** the filter field is labeled `Branch Group` but the corresponding grid column is labeled `Branch` (not `Branch Group`) — similar to the earlier `Description`/`Descripcion` spelling inconsistency seen between screens. The values in this `Branch` column look like branch-group-style groupings (e.g. resembling "London", "Spain") rather than specific operating branches like `MADRID REAL`, consistent with `Branch Group` from `Config. Local Properties`.
     - **New controlled-vocabulary column:** `Status`, with values seen as `Valid` / `InValid` — not seen on prior screens.
- **Status bar:** shows `Sel: 1 | Current auth-code: 21 - Madrid` — again no `/ Count:` suffix shown, consistent with `Cross Account Config` above but different from the first two Config screens.
- **Data note:** row descriptions not transcribed verbatim; only the `Status` controlled vocabulary (`Valid`/`InValid`) is recorded as it's structural.
- **Tab bar context:** at the time of this screenshot, open tabs were `Start Page`, `Split Config. Local Prop`, `Cross Account Config`, `FX Liquid`, `Grouped Movements Config`, `Portfolio Properties` — indicating `FX Liquid Config` and `Grouped Accounting Config` (tree leaves) were also opened at some point, though no content from those two has been shown/documented yet.
- **Screenshot source:** BOX - Accounting > Config. > Portfolio Properties (Tier 1).

### BOX - Accounting > MBJ Config (tab title: "MBJ Config")

Sixth leaf screen opened — this is the leaf that sits directly under `BOX - Accounting` (not inside `Config.`/`Data`/`Reports`), and matches the `MBJ Config` tile seen on the Start Page.

- **Purpose:** appears to configure/list batch jobs ("MBJ" likely = some batch-job naming convention) tied to a branch, instrument, and a group/label classification.
- **Location / navigation:** opened from `BOX - Accounting > MBJ Config` (a leaf directly under `BOX - Accounting`, a sibling of the `Config.`/`Data`/`Reports` folders, not inside them).
- **Layout:**
  1. **Filter/search header:** `Branch:` (dropdown, shown set to `MADRID REAL`, with an eye icon), `Job Name:` (text), `Instrument:` (text, with search + eye icons), `Group:` (text, appears visually disabled/greyed, no icons shown), `Label:` (text, appears visually disabled/greyed, with search + eye icons), `SubLabel:` (text, appears visually disabled/greyed, with search + eye icons). A thin horizontal scrollbar-like bar appears directly under the filter header, suggesting the header area itself may scroll to reveal more fields, similar to the grid below (not confirmed).
  2. **Vertical icon toolbar:** same recurring icon set (`+`, delete, edit, copy, search, filter).
  3. **Data grid:** columns visible (left-to-right, before horizontal scrolling): `Internal Id`, `Branch`, `Instanze` (this appears to be **another UI label typo**, likely meant to read "Instance" — transcribed here exactly as shown), `Job Name`, `Instrument`, `Group Id`, `Group Name`, and a further column cut off at the right edge (label truncated to "La...", likely "Label"). **Per the user, there are additional columns further to the right not captured in this screenshot** — the grid is wider than what's visible.
- **Observation:** the `Instanze` column shows the same value (`AUKI`) across all visible rows in this screenshot — consistent with AUKI being the name of the broader migration programme this SIGOM/BOX environment belongs to, though this screen may simply have been filtered/sorted such that only one instance value is visible; not confirmed as the only possible value.
- **Numeric format correction (revises earlier documentation):** the `Group Id` column here shows values like `2.755,65`, `2.408,65`, `2.735,65` — clearly using a **period as thousands separator and a comma as decimal separator** (standard Spanish/European number formatting), e.g. `2.755,65` = 2755.65. This strongly suggests the `Internal Id` values documented on earlier screens (e.g. `895,21`, `1.399,21`, `4,65`) are **single decimal numbers in this same European format**, not two separate comma-joined figures as originally (and tentatively) hypothesized. The `Internal Id` open question about a "branch code" second component is very likely simply the decimal portion of a European-formatted number, not a meaningful separate code — this weakens that hypothesis further, close to resolving it as a documentation formatting artifact rather than a real substructure.
- **Status bar:** `Sel: 1 | Current auth-code: 21 - Madrid` — again no `/ Count:` suffix, consistent with `Cross Account Config` and `Portfolio Properties`.
- **Data note:** specific Job Name/Group Name/Label content not transcribed, consistent with the approach on prior screens.
- **Screenshot source:** BOX - Accounting > MBJ Config, filtered to branch MADRID REAL (Tier 1).

### BOX - Accounting > Data > Accounting Topics (tab title: "Topics")

Seventh leaf screen opened — first screen documented from the `Data` folder (previously only `Config.` screens had been shown).

- **Purpose, confirmed:** this screen is the maintenance UI for `T_BOX_ACCT_TOPICS_S`, the catalogue of reusable accounting *concepts* — e.g. notional, accrual, cash transit, MTM, gain/loss, revaluation. **These are explicitly not GL accounts.** A topic is a named idea ("what kind of accounting event is this"); it only becomes a specific GL account once combined with a Portfolio Property, via `T_BOX_ACCT_LIST_TOPIC_S` (see `## Cross-Screen Relationships` below). Each row here is one topic: a short code with a description, plus maintenance/audit metadata.
- **Location / navigation:** opened from `BOX - Accounting > Data > Accounting Topics`. Tab titled "Topics" (again, shorter than the tree leaf label).
- **Layout — same three-area template. No Branch field** (consistent with `Condition Port Properties` — this looks like global/shared reference data, not branch-scoped):
  1. **Filter/search header:** `Internal Id:` (text), `Code:` (text), `Description:` (text, wide).
  2. **Vertical icon toolbar:** same recurring icon set.
  3. **Data grid**, columns: `Internal Id`, `Code`, `Description`, `Last Maint Date`, `Last Maint User`, `Last Maint Source`.
- **Pattern-breaking observation:** on this screen, `Description` **does** have a corresponding filter field — breaking the pattern seen on the three Config screens (`Assign Instrument Type`, `Condition Port Properties`, `Config. Local Properties`) where the trailing description column had no filter field. So that earlier pattern looks specific to those Config screens, not universal.
- **New column type confirmed:** `Last Maint Date` / `Last Maint User` / `Last Maint Source` — audit/maintenance metadata columns not seen on earlier screens, showing when a reference entry was last changed, by whom, and from which source system. Two distinct `Last Maint Source` values were visible: one resembling a master-data-repository feed and one resembling BOX's own accounting module — suggesting this reference data can originate either from an upstream master data system or be maintained directly in BOX. Exact source system names not transcribed here.
- **Data note:** specific topic codes/descriptions not transcribed, consistent with the approach on prior screens.
- **Screenshot source:** BOX - Accounting > Data > Accounting Topics (Tier 1).

### BOX - Accounting > Data > Documents (tab title: "Documents(All Movements)")

Eighth leaf screen opened.

- **Purpose:** appears to list generated accounting documents/movements for a branch and date, with an owner (system/service account) and cancellation flag.
- **Location / navigation:** opened from `BOX - Accounting > Data > Documents`. Tab titled "Documents(All Movements)" — again differs from the tree leaf label ("Documents").
- **Layout — same three-area template:**
  1. **Filter/search header:** `Branch:` (dropdown, shown set to `MADRID REAL`, with an eye icon), `Name:` (text, wide), `Date:` (text — **defaulted to the current date** in this screenshot, i.e. it pre-fills with today rather than being blank, unlike other screens' filter fields), `Code:` (text), `User:` (text, wide).
  2. **Vertical icon toolbar:** same recurring icon set.
  3. **Data grid**, columns: `Document PK`, `Branch`, `Name`, `Date`, `Owner`, `Cancelled`.
- **Filter/grid mismatches observed:** the filter header's `Code:` field has **no corresponding grid column** (no `Code` column in the grid), and the filter's `User:` field most likely corresponds to the grid's `Owner` column (differently named) rather than there being a separate `User` column. Both are open questions — not confirmed.
- **Observation (structure only, not specific data):** the `Name` column values follow a pattern of `<short prefix><job/batch number>_<sub-number>_<date>` (e.g. resembling `IRBOX70945430_413_20260910`), where the trailing date component matches the `Date` column value. The short prefixes vary (at least two or three distinct ones were visible) and likely encode a document/movement type, but their meanings are not confirmed. All visible rows shared the same `Owner` value, which reads as a system/service account name rather than an individual person — consistent with these being system-generated documents rather than manually entered ones.
- **Status bar:** `Sel: 0 / Count: 6` — full `Sel/Count` format is back here (unlike the last few screens), reinforcing that this segment's presence/format is inconsistent across screens for reasons not yet understood.
- **Data note:** specific document names/codes not transcribed, consistent with the approach on prior screens.
- **Screenshot source:** BOX - Accounting > Data > Documents, filtered to branch MADRID REAL, date 10/09/2026 (Tier 1).

### BOX - Accounting > Data > Global Accounts (tab title: "Split for Glta Acct")

Ninth leaf screen opened.

- **Purpose:** appears to be a reference list of global (branch-independent) account definitions, each with a code, short name, description, account type, accounting direction, and FX-adjustment/host-interface flags.
- **Location / navigation:** opened from `BOX - Accounting > Data > Global Accounts`. Tab titled "Split for Glta Acct" — an unusually abbreviated title compared to the tree leaf label, continuing the pattern of tab titles not matching tree labels verbatim.
- **Layout — same three-area template. No Branch field**, consistent with this being global (non-branch-specific) reference data:
  1. **Filter/search header:** `Code:` (text), `ShortName:` (text), `Description:` (text, wide), `Local Code:` (text), `Account Type:` (dropdown, with an eye icon), `FX Adjust Ind:` (dropdown, empty), `Host Interface:` (dropdown, empty), `Internal ID:` (text, wide).
  2. **Vertical icon toolbar:** same recurring icon set.
  3. **Data grid**, columns visible (grid scrolls further right per the scrollbar, more columns likely exist): `PK`, `Code`, `Short Name`, `Description`, `Account Type`, `Direction`, `Local Code`, `FX Adjust`.
- **Naming inconsistency noted:** this screen's first grid column is labeled `PK`, whereas every other screen so far has labeled its equivalent first column `Internal Id`/`Internal ID` — another instance of inconsistent naming across screens (alongside the earlier `Description`/`Descripcion` and `Branch`/`Branch Group` cases).
- **Controlled vocabularies observed (structure, not row data):** `Account Type` includes at least `Balance` and `Profit And Loss`; `Direction` includes at least `Credit`, `Debit`, and (notably, in Portuguese rather than English) `Ordem`; `FX Adjust` is a `Yes`/`No` flag.
- **Data note:** specific account codes/short names/descriptions not transcribed, consistent with the approach on prior screens.
- **Screenshot source:** BOX - Accounting > Data > Global Accounts (Tier 1).

### BOX - Accounting > Data > Net Contract (tab title: "Net Contract")

Tenth leaf screen opened. Tab title matches the tree leaf label exactly.

- **Purpose:** appears to list netting/contract records tied to a branch, instrument, currency, portfolio, and security, referencing a deal and a contract reference, along with who/what input the record.
- **Location / navigation:** opened from `BOX - Accounting > Data > Net Contract`.
- **Layout — same three-area template, two-column filter header:**
  1. **Filter/search header,** left column: `Date From:` (text), `Branch:` (dropdown, shown set to `MADRID REAL`, with an eye icon), `Instrument:` (text, with search + eye icons), `Portfolio:` (text, with search + eye icons — appears visually disabled/greyed, same as `Entity`/`Account` on `Cross Account Config`, reinforcing that this greyed-out-field pattern recurs across multiple screens); right column: `Date To:` (text), `Currency:` (text, with search + eye icons), `Contract:` (text, wide), `Security:` (text, with search + eye icons).
  2. **Vertical icon toolbar:** same recurring icon set.
  3. **Data grid**, columns visible (more exist off-screen per the horizontal scrollbar, including a column starting "Inp..." likely "Input Date"): `Internal Id`, `Branch`, `Instrument`, `Currency`, `Portfolio`, `Deal Id`, `Security`, `Contract`, `Input User`.
- **Visual formatting observation (not confirmed in meaning):** one full row appears highlighted in green rather than the usual black "selected row" highlight seen on other screens, and various individual cell values elsewhere in the grid (particularly in the `Contract` and `Input User` columns) are rendered in green text rather than black. This may indicate some kind of status distinction (e.g. system-generated vs. user-entered records — some rows' `Input User` shows what looks like a personal user code, others a system/service account name), but the exact rule is not confirmed and is flagged as an open question rather than asserted.
- **Data note:** specific contract references, user codes, and numeric values not transcribed, consistent with the approach on prior screens.
- **Screenshot source:** BOX - Accounting > Data > Net Contract, filtered to branch MADRID REAL (Tier 1).

### BOX - Accounting > Reports > Movements Report (tab title: "Movem. between Two Dates")

Eleventh leaf screen opened, and the **first screen from the `Reports` folder** documented — its toolbar and filter richness differ from the Config/Data screens seen so far in some useful ways.

- **Purpose:** a report of accounting movements/entries between two dates, showing per-movement debit/credit amounts and running balances by account and currency.
- **Location / navigation:** opened from `BOX - Accounting > Reports > Movements Report`. Tab titled "Movem. between Two Dates" — a descriptive title reflecting the screen's date-range nature, again different from the tree leaf label.
- **Layout — filter header / toolbar / grid, but with two notable differences from prior screens:**
  1. **Filter/search header** (two columns, the richest set of fields seen so far): left column — `Branch` (dropdown, `MADRID REAL`, eye icon), `Instrument` (text, search+eye), `Entity` (text, search+eye — visually disabled/greyed), `Port.Properties` (text, search+eye — greyed), `Deal Id` (text, search icon only, no eye — greyed), `Date From` (text, defaulted to `01/09/2026`), `Topic` (text, search+eye), `Manual Only` (a **checkbox**, unticked — the first checkbox-type field seen on any screen so far); right column — `Account` (text, search+eye — greyed), `Currency` (text, search+eye), `Security` (text, search+eye — greyed), `Settle. Account` (text, search+eye — greyed), `Folder` (text, search+eye — greyed), `Date To` (text, defaulted to `10/09/2026`, i.e. today), `Standard Hist.` (text, wide, search+eye), `Group Acct` (text, wide, no icons).
     - **Strongest evidence yet of the recurring greyed/disabled-field pattern:** 7 of the ~15 fields here appear visually disabled simultaneously (Entity, Port.Properties, Deal Id, Account, Security, Settle. Account, Folder) — reinforcing that this is a deliberate, recurring UI behavior (seen previously on `Cross Account Config` and `Net Contract`) rather than a one-off. Still not confirmed what enables them (a plausible guess is that selecting a specific `Instrument` unlocks the fields relevant to that instrument type, but this is not confirmed by interaction).
     - **Default date range observed:** `Date From` = the 1st of the current month, `Date To` = today — suggesting this report may default to a "month-to-date" range. Based on a single observation only; not confirmed as a general rule.
  2. **Vertical icon toolbar — differs from every Config/Data screen seen so far:** this toolbar shows **only the filter (funnel) icon** — none of the `+` / delete / edit / copy / search icons seen on Config and Data screens. This is a meaningful, consistent-seeming distinction: **Report-type screens appear to be read-only (filter/view only)**, whereas Config and Data screens support full add/edit/delete/copy actions on their records.
  3. **Data grid**, columns visible (more columns exist further right — confirmed by the user): `Internal Id`, `Group Acct`, `Reg Date`, `Branch`, `Account`, `Currency`, `Ccy Debit`, `Ccy Credit`, `CCY Balance`, and at least one further column cut off at the right edge.
- **Numeric-format observation:** this screen's `Internal Id` values are large-magnitude **negative** numbers in European decimal format (e.g. resembling `-2.950.110,21`), unlike the small positive `Internal Id`/`Internal ID` values seen on Config/Data screens. This may indicate a different, larger, system-wide sequence generator for report/movement records, and/or that negative values specifically denote reversing or contra entries — both are speculative and not confirmed. By contrast, `Group Acct` values here are plain integers with no decimal component, suggesting `Group Acct` is a true identifier rather than a value in the same decimal-sequence family as `Internal Id`.
- **Data note:** this screen displays actual monetary debit/credit/balance figures (in EUR) per movement — as with all prior screens, none of these specific amounts, account codes, or dates-per-row are transcribed here; only the column structure and general observations above are documented.
- **Screenshot source:** BOX - Accounting > Reports > Movements Report, filtered to branch MADRID REAL, date range 01/09/2026–10/09/2026 (Tier 1).

### BOX - Accounting > Reports > Balance Report (tab title: "Balance Consulting")

Twelfth leaf screen opened, second from the `Reports` folder.

- **Purpose:** a point-in-time balance query — shows account balances (in transaction currency and, likely, an equivalent reporting/base currency) as of a single given date, as opposed to `Movements Report`'s date-range movement listing.
- **Location / navigation:** opened from `BOX - Accounting > Reports > Balance Report`. Tab titled "Balance Consulting".
- **Layout — filter header / toolbar / grid:**
  1. **Filter/search header** (two columns): left — `Branch` (dropdown, `MADRID REAL`, eye icon), `Instrument` (text, search+eye), `Entity` (text, search+eye — greyed/disabled), `Properties` (text, search+eye — greyed), `Deal Id` (text, search icon only — greyed), `Topic` (text, search+eye), `Acct. Strategy` (dropdown, eye icon — greyed); right — `Account` (text, search+eye), `Currency` (text, search+eye), `Security` (text, search+eye — greyed), `Settle. Account` (text, search+eye — greyed), `Folder` (text, search+eye — greyed), `Date` (text, defaulted to `10/09/2026`, i.e. today — a **single date**, unlike `Movements Report`'s `Date From`/`Date To` range), `Source Ccy` (text, search+eye). Below both columns: `View zero values:` — a **checkbox** (second checkbox-type field seen, after `Manual Only` on `Movements Report`).
     - Same greyed/disabled-field pattern as before, again affecting several fields simultaneously (Entity, Properties, Deal Id, Security, Settle. Account, Folder, Acct. Strategy).
  2. **Vertical icon toolbar:** shows **only the filter (funnel) icon**, same as `Movements Report` — now confirmed on 2 of 2 Reports screens, strengthening the hypothesis that Reports-type screens are read-only/filter-only, distinct from the full CRUD toolbar on Config/Data screens.
  3. **Data grid**, columns visible (more exist further right per the user, e.g. likely a "Value Credit"/"Value Balance" pair alongside the visible `Value Debit`): `Date Store`, `Account`, `Currency`, `Ccy Debit`, `Ccy Credit`, `Ccy Balance`, `Value Debit`.
     - The `Ccy …` columns appear to be transaction-currency amounts, and `Value Debit` (plus likely further `Value …` columns off-screen) may be the equivalent amounts converted to a reporting/base currency — a common pairing in accounting systems, though not explicitly confirmed here.
- **Data observation (structure, not asserting real figures):** the visible amounts in this screenshot are round, large figures (e.g. patterns resembling exactly 10,000,000 or 100,000,000 in the transaction currency), and the `Account` column mixes a generic `INTERNAL` placeholder with specific-looking codes and even a literal `0`. Combined with the `(copia 23-Dec-17)` environment badge noted earlier, this is consistent with — though does not by itself confirm — the SIGOM instance being connected to a **test/copy environment rather than live production data**. Flagged as a supporting observation for that earlier open question, not a confirmed conclusion.
- **Screenshot source:** BOX - Accounting > Reports > Balance Report, filtered to branch MADRID REAL, date 10/09/2026 (Tier 1).

### BOX - Financial Engine > Control > Configuration > Days Matured (tab title: "Days Matured")

Thirteenth leaf screen opened — first leaf screen documented from `BOX - Financial Engine` (all previous leaf screens were under `BOX - Accounting`). Tab title matches the tree leaf label exactly.

- **Purpose:** appears to define a "days to maturity"-style parameter per instrument type (e.g. how many days before/after maturity something is still considered matured/active), with maintenance-audit metadata.
- **Location / navigation:** opened from `BOX - Financial Engine > Control > Configuration > Days Matured`.
- **Layout:**
  1. **Filter/search header:** just one field this time — `Instrument` (text, with search + eye icons). The simplest filter header seen on any screen so far (every other screen had at least 3-4 fields).
  2. **Vertical icon toolbar:** the full recurring icon set (`+`, delete, edit, copy, search, filter) — **confirms that the filter-only toolbar seen on `Movements Report`/`Balance Report` is specific to the `Reports` folder, not to some other property** (this screen sits under `Control > Configuration`, a non-Reports branch, and has full CRUD icons).
  3. **Data grid**, columns: `Internal_ID` (note: **underscore** this time — yet another variant of this column's name, joining `Internal Id`, `Internal ID`, and `PK` seen on earlier screens), `Instrument`, `Days`, `MaintDate` (a single-word variant of the `Last Maint Date` audit column seen on `Accounting Topics`, here also carrying a time-of-day component).
- **Instrument categories confirmed again:** the same recurring product-type list appears (OTC Option, Cross Currency Swap, Swap, Cash Flow Matching, Deposit & Loan, Credit Derivatives, Forward Rate Agreement, Caps And Floors, Commodity Swap), plus one new one: **Bond Return Swap**.
- **Strong supporting evidence for "test/copy environment":** the user explicitly noted the row values on this screen "might be wrong" and that they don't matter — reinforcing (more directly than the earlier circumstantial evidence on `Balance Report`) that this SIGOM instance is showing non-authoritative/test data rather than values that should be taken as real reference facts.
- **Data note:** specific `Days` values and dates not treated as reliable reference data, per the user's explicit note above; only column structure is documented.
- **Screenshot source:** BOX - Financial Engine > Control > Configuration > Days Matured (Tier 1).

### BOX - Financial Engine > Control > Configuration > FE Parameters (tab title: "FE Parameters")

Fourteenth leaf screen opened. Tab title matches the tree leaf label exactly. DB table: `BOX_FE.T_BOX_ENGSETUP_S` (provided directly by the user — see Database Table Mapping section above).

- **Purpose:** appears to be a generic engine settings/parameters store — a list of named parameters (technical/system-level configuration keys, e.g. batch/queue/processing settings) each holding a typed value.
- **Location / navigation:** opened from `BOX - Financial Engine > Control > Configuration > FE Parameters`.
- **Layout:**
  1. **Filter/search header: none.** This is the **first screen with no filter fields at all** above the grid — every other screen so far had at least one.
  2. **Vertical icon toolbar:** the full recurring icon set (`+`, delete, edit, copy, search, filter).
  3. **Data grid**, columns: `InternalID` (yet another naming variant of this ID column — joining `Internal Id`, `Internal ID`, `PK`, and `Internal_ID` from earlier screens; five distinct spellings now seen across the SIGOM screens documented so far), `Parameter`, `Date`, `Number`, `String`.
- **Structural pattern (EAV-style config table):** each row names one `Parameter` (an all-caps, underscore-separated key, e.g. resembling `MTM_ADJUST_BRANCH`, `NUM_ITER_FOR_COMMIT`, `BATCH_MODE`), and its value is stored in exactly one of the three typed columns (`Date`, `Number`, or `String`) depending on the parameter's data type — a classic entity-attribute-value pattern for storing heterogeneous engine settings in one table.
- **Data note:** consistent with the user's note on the previous screen that row values may not be reliable/real, specific parameter names and values are not catalogued exhaustively here — only the general structure and naming convention (all-caps with underscores) are recorded.
- **Screenshot source:** BOX - Financial Engine > Control > Configuration > FE Parameters (Tier 1).

### BOX - Financial Engine > Control > Configuration > Fixing Curve (tab title: "FixingCurve")

Fifteenth leaf screen opened. Tab title is a close-but-not-exact match to the tree label (no space: "FixingCurve" vs. "Fixing Curve"). DB table: `BOX_FE.T_BOX_ENGFCURVE_S` (user-provided).

- **Purpose:** appears to define named FX-fixing curves, each tied to a local currency.
- **Location / navigation:** opened from `BOX - Financial Engine > Control > Configuration > Fixing Curve`.
- **Layout:**
  1. **Filter/search header: none** — same as `FE Parameters`, reinforcing that at least some Control/Configuration screens have no filter header at all.
  2. **Vertical icon toolbar:** the full recurring icon set.
  3. **Data grid**, columns: `InternalID`, `Name`, `Local Currency`.
- **Tier 1 scope cross-reference:** the two rows visible are named along the lines of "Tipos Cambio - SCH (ESP)" and "Tipos Cambio - SCH (SLB)" ("Tipos Cambio" = Spanish for "exchange rates") — the `(ESP)`/`(SLB)` suffixes line up with the Tier 1 branches (Madrid/Spain and SLB) described at the start of this document, giving a concrete confirmation that Tier 1 configuration data is organized per those two branches.
- **Screenshot source:** BOX - Financial Engine > Control > Configuration > Fixing Curve (Tier 1).

#### Record detail view: opening a specific Fixing Curve entry

Opening a specific record from the `Fixing Curve` list (double-clicking or similar on row 1, "Tipos Cambio - SCH (ESP)") reveals a **new, previously undocumented UI pattern**: a record-detail/edit view, distinct from the flat list/grid screens documented so far.

- **New tab behavior:** opening the record adds a new tab titled "Fixing Curve" (with a space) **alongside** the still-open list tab titled "FixingCurve" (no space) — both tabs coexist, list and detail are separate tabs rather than one replacing the other.
- **Record-detail layout:**
  - A row of **sub-tabs** at the top of the content area: `Generic`, `Array of Quotes`, `Array of Yield Curve`.
  - A **second, right-hand pinned panel** called "Navigation Tree" (distinct from the left-hand "Work View Explorer") listing the same three sections (`Generic`, `Array of Quotes`, `Array of Yield Curve`) — clicking an entry there presumably navigates the same sub-tabs shown at the top (not confirmed by interaction, but they visibly mirror each other and highlight in sync).
  - This "record has multiple sub-tabs plus a mirrored right-side Navigation Tree" structure has not been seen on any flat-grid screen documented so far (e.g. `Assign Instrument Type`, `Condition Port Properties`) — whether those screens also support a similar record-detail drill-down (not yet tried) or whether this is specific to `Fixing Curve` (a more structurally complex config object) is an open question.
- **`Generic` sub-tab:** shows `Name` (text, editable, populated with the record's name) and `Local Currency` (text, with search + eye icons, populated with `EUR`) — i.e. the same two data fields already visible as columns in the parent list grid, now shown as an edit form for the single selected record.
- **`Array of Quotes` sub-tab:** a data grid, columns `InternalId`, `Quote Type`, `Quote Source`, `Quote Instrument`, `Maturity`. For this record, all visible rows share `Quote Type` = `Foreign Exchange`, `Quote Source` = `ACCOUNTING RATES`, and `Maturity` = `SPOT`, with `Quote Instrument` varying across many EUR/xxx currency pairs (e.g. EUR/USD, EUR/GBP, EUR/JPY, and roughly two dozen others visible) — i.e. this "Array of Quotes" appears to be the list of currency-pair quotes that make up this particular fixing curve.
  - This sub-tab's toolbar shows the full recurring icon set (`+`, delete, edit, copy, search, filter) — record-level CRUD is available for the quotes within a curve.
- **`Array of Yield Curve` sub-tab:** not yet shown/documented — content unknown.
- **Possible DB structure implication (not confirmed):** given `Fixing Curve` (the parent list) maps to `BOX_FE.T_BOX_ENGFCURVE_S`, the `Array of Quotes` sub-tab plausibly comes from a related child table (one curve definition → many quote rows), but no such table name has been provided or confirmed.
- **Data note:** specific currency-pair values are recorded above only as illustrative examples of the column's range, not as an exhaustive or authoritative list.

### BOX - Financial Engine > Control > Configuration > MIS (tab title: "ENG Config Selection")

Sixteenth leaf screen opened. This is the same leaf confirmed earlier to match the Start Page's `MIS` tile — its tab title ("ENG Config Selection") doesn't reference "MIS" at all, continuing the pattern of tab titles differing (sometimes substantially) from tree labels. DB table: `BOX_FE.T_BOX_ENGCONF_S` (user-provided).

- **Purpose:** appears to hold a general "engine configuration" record per branch/entity — a calendar convention and local currency, at minimum.
- **Location / navigation:** opened from `BOX - Financial Engine > Control > Configuration > MIS`.
- **Layout:**
  1. **Filter/search header: none** — same as `FE Parameters` and the `Fixing Curve` list, reinforcing that several Control/Configuration screens skip the filter header entirely.
  2. **Vertical icon toolbar:** the full recurring icon set.
  3. **Data grid**, columns: `Internal_ID` (matches the underscore variant seen on `Days Matured`), `Name`, `Calendar`, `Local Currency`.
- **Tier 1 scope cross-reference reinforced again:** the two rows are named "Configuracion -SCH (ESP)" and "Configuracion -SCH (SLB)" ("Configuracion" = Spanish for "Configuration") — the same ESP/SLB pairing seen on `Fixing Curve`, further confirming Tier 1 config data is organized per the Madrid(ESP)/SLB branch split.
- **New column:** `Calendar`, holding a settlement-calendar convention name (e.g. resembling "TARGET Settlement Day" — TARGET being the well-known Eurosystem settlement calendar/system) — not seen as a column on any earlier screen.
- **Screenshot source:** BOX - Financial Engine > Control > Configuration > MIS (Tier 1).

#### Record detail view: opening a specific MIS config entry

Opening a specific record from the `MIS` list ("Configuracion -SCH (ESP)") shows the same record-detail pattern first seen on `Fixing Curve` — but with **8 sub-tabs** this time: `Generic`, `Yield Curve`, `Accrual`, `Fixing Exceptions`, `Accrual Exceptions`, `Currency Basis`, `Branch`, `Book`. **This resolves the earlier open question about whether the multi-sub-tab record-detail pattern is specific to `Fixing Curve`** — it is not; it's a general SIGOM pattern for structurally complex config records, with the number/set of sub-tabs varying per config type. (`Yield Curve`, `Fixing Exceptions`, and `Currency Basis` were not shown — content unknown for those three.)

- **`Generic` sub-tab:** `Name` (text, "Configuracion -SCH (ESP)"), `Local Currency` (`EUR`), `Calendar` (`TARGET Settlement Day`) — matching the parent list's columns — plus four fields not visible on the list grid: `Man. Fixing` (dropdown, referencing a **Fixing Curve record by name**, e.g. "Tipos Cambio - SCH (ESP)"), `Acc. Fixing` (dropdown, same kind of Fixing Curve reference), `Source Front` (text, with search+eye icons, showing a value resembling "MUREX FXFI"), `Source Back` (text, showing "BOX").
  - **Cross-screen relationship discovered:** `MIS`'s `Man. Fixing`/`Acc. Fixing` fields reference `Fixing Curve` records directly by name — confirming a real, concrete link between the `MIS` and `Fixing Curve` config screens (a MIS configuration selects which fixing curve to use for manual vs. accounting fixing purposes).
  - **New concept:** `Source Front`/`Source Back` suggest this configures the upstream (front-office) and downstream (back-office) systems feeding this MIS configuration — the front-office value resembles a Murex FX-fixing feed identifier, and the back value is `BOX` itself. This is a structural/systems-integration detail, not customer data.
- **`Accrual` sub-tab:** a data grid, columns: `InternalID`, `FeeCalcInterval`, `Interest Interval`, `Instrument`, then several columns whose headers were truncated in the screenshot (visually resembling something like `InCurrency`, `Dea...`, `Co...`, `Dea...`, `TriggerI...`, `Ba...`), the last of which shows day-count-convention-style values (resembling "Actual/365 (Fixed)"). Rows cover the by-now-familiar 10 instrument categories (OTC Option, Cross Currency Swap, Swap, Cash Flow Matching, Deposit & Loan, Credit Derivatives, Forward Rate Agreement, Caps And Floors, Commodity Swap, Bond Return Swap) — the fullest confirmation yet of this exact 10-item instrument-type list, consistent across multiple screens now.
- **`Accrual Exceptions` sub-tab:** columns `Instrument`, `Instr Type`, `Strategy`, `Branch`, `Acc Policy`. All visible rows show `Strategy` = `Trading` and `Acc Policy` = `Market Value`; `Branch` alternates between `MADRID REAL` and a second branch whose description resembles "Branch for Test and Trials" (Spanish: "BRANCH PARA TEST Y PRUEBAS").
- **`Branch` sub-tab:** columns `Internal Id`, `Code`, `Description`, `Entity`, `Currency`, `Calendar`. Two rows: one with `Code` = `TEST`, `Description` resembling "Branch for Test and Trials", the other `Code` = `MADRID`, `Description` = `MADRID REAL`. Both show `Entity` = **Banco Santander S.A.** (the bank's own legal entity — not sensitive, already established context), `Currency` = EUR, `Calendar` = TARGET Settlement Day.
  - **Notable:** this confirms a literal, explicitly-coded `TEST` branch exists alongside `MADRID` in this branch reference data — i.e. "test" isn't only an informal description of the environment, there's a real branch code dedicated to testing within this configuration data.
- **`Book` sub-tab:** columns `Branch`, `Instrument`, `Label/Book`. All visible rows are `MADRID REAL`; `Label/Book` values include a generic "0 - EMPTY" default alongside named books resembling "Commodity Derivatives" and "ALM Strategies" (ALM = Asset-Liability Management, a standard treasury concept) — suggesting `Book` maps a branch+instrument combination to a specific trading/accounting book label, defaulting to an empty/unassigned book.
- **Data note:** per the user's explicit reminder, specific values above (exact day-count conventions, trigger-interval numbers, book codes) are recorded only as illustrative structural examples, not as confirmed/authoritative reference data.

<!--
Template for each screen entry, to be filled in as screenshots arrive:

### <Screen / Tab Name>

- **Purpose:** what this screen appears to configure or display
- **Location / navigation:** how it's reached, if visible (menu path, tab position, etc.)
- **Tabs / sub-sections:** list, if any
- **Fields:**
  - `Field name` — type (text/dropdown/checkbox/etc. if visible), description of what it appears to control, any visible constraints or sample values
- **Relationships to other screens/tables:** any visible keys, references, or navigation links to other parts of SIGOM
- **Screenshot source:** short label/date so entries stay traceable to what was shown
-->

## Cross-Screen Relationships

### `Accounting Topics` → `Portfolio Properties` → `Global Accounts`: the topic-to-GL mapping chain `[confirmed: DB + repo]`

Resolved via later screenshots (Portfolio Property → Topic → GLTA mapping) plus the existing DB-level evidence
already in this repo. The chain:

```text
T_BOX_ACCT_PORT_PROP_S.PK   → T_BOX_ACCT_LIST_TOPIC_S.FK_PARENT
T_BOX_ACCT_TOPICS_S.PK      → T_BOX_ACCT_LIST_TOPIC_S.FK_TOPIC
T_BOX_ACCT_GLTA_S.PK        → T_BOX_ACCT_LIST_TOPIC_S.FK_GLTA
```

In plain English: **Portfolio Property + Topic → selected GLTA (GL) account.** `T_BOX_ACCT_LIST_TOPIC_S` is
the mapping/junction table — it does not carry meaning of its own, it just selects which GL account applies
for a given Portfolio Property once you know which accounting Topic you're looking at. This is why
`Accounting Topics` (this screen) and `Global Accounts` are separate, siloed reference lists: neither one
encodes the mapping by itself, and mapping only exists as rows in `T_BOX_ACCT_LIST_TOPIC_S`.

This independently matches `../reference/branch-config/branch-config-surface.md`'s own documented Tier-1
findings about `T_BOX_ACCT_LIST_TOPIC_S` — same `FK_PARENT`/`FK_TOPIC`/`FK_GLTA` structure, confirmed there
from a different angle (DB queries rather than SIGOM screenshots). Two independent paths landing on the same
FK structure is strong confirmation this is the right model, not a guess.

`[open-question]` Does `T_BOX_ACCT_LIST_TOPIC_S` have its own SIGOM screen (not yet seen in any screenshot),
or is it only reachable as a child/drill-down grid inside `Portfolio Properties` — mirroring the
record-detail-with-sub-tabs pattern already documented above for `Fixing Curve` and `MIS`? Not confirmed
either way yet.

## Open Questions

- What does each toolbar icon do, specifically? Only visual guesses are possible from the icon shapes (e.g. green triangle = "run/execute", red icon = "stop/cancel").
- What does the environment badge `IGBOMD (copia 23-Dec-17)` fully mean — is `IGBOMD` the Tier 1 database/environment name, and what does "copia 23-Dec-17" indicate (a copy/snapshot date, and of what year)? **Strongly supported (not just circumstantial):** `Balance Report` showed suspiciously round balance figures and placeholder account values, and — more directly — the user explicitly confirmed on `Days Matured` that row values there "might be wrong" and don't need to be accurate. Together these strongly suggest this SIGOM instance is a test/copy environment where row-level data is not authoritative; the "copia" (copy) wording in the badge is consistent with that. Exact provenance/purpose of the copy still not confirmed.
- What is under each top-level Work View Explorer node other than `GBO` (`<ADMIN>`, `<PROJECTS>`, `<Security>`, `<TOOLS>`, `AFM`, `BOX`, `BOX - Accounting`, `BOX - Financial Engine`, `BOX - Migration`, `BOX - Settlement`, `Document Status Monitor`, `General Loader PT`, `Madrid`, `Mantenimiento`, `Master Product Catalogue`, `MDR Adapter`, `Settlement Interface`, `Spain`)? Not yet expanded.
- Under `GBO`, what is inside its second-level children other than `Accounting` and `Financial Engine` (i.e. `Agreement`, `Catalog`, `Collaterals`, `Conciliation`, `Confirmation`, `Documentation`, `File System`, `Financial Engine G1`, `GBO - Msg Service`, `General`, `Interfaces`, `Market Data`, `Portfolio Reconciliation`, `Process`, `Regulatory`, `Replic`, `Settlement`, `Static Data`, `STP`, `Swift`, `SYS`, `Trading`)? Not yet expanded. (`Financial Engine`'s own second-level folders — Control, Financial Status, OBB Module, Process Management, Static MIS Data — are known, but not yet expanded further to leaf screens.)
- Exact full names for tree items whose labels appeared visually truncated: "Grouped Accounting Conf[...]", "Grouped Accounting Move[...]" (under Accounting > Grouped Movements), and "SwapAgent Cpty Br Conf" (under Accounting > Settle to Market).
- What does each leaf screen under `Accounting` actually do/contain once opened (e.g. `Check Documents`, `Global Accounts`, `Manual Movements`, the various Reports)? Only one leaf screen (`Assign Instrument Type`) has been opened so far.
- Is the 3-part layout (filter header / vertical icon toolbar / data grid) universal across *all* SIGOM leaf screens, or just Config-type ones? Confirmed so far on 3 of 3 Config screens (`Assign Instrument Type`, `Condition Port Properties`, `Config. Local Properties`) — not yet checked against a Data or Reports screen.
- What do the eye icons (next to Branch/Instrument/Counterparty/Field/Branch Group fields) and the vertical toolbar icons (+, delete, edit, copy, search, filter) actually do? Inferred from icon shape/position only, not confirmed by interaction.
- Is `Current auth-code` truly a global/session-level value (carried over from whichever branch was last selected on any screen), rather than a per-screen setting? Suggested by `Condition Port Properties` and `Config. Local Properties` both showing the same auth-code as the first screen despite having no Branch field of their own — not fully confirmed.
- Is `Current auth-code` a fixed numeric code per branch (e.g. Madrid = 21)? What are the codes for other branches (SLB, and Tier 2's NY/Brazil/Mexico)?
- ~~What does the `Internal Id` two-part number format represent~~ — **Largely resolved:** `MBJ Config`'s `Group Id` column shows clearly European-formatted decimals (period = thousands separator, comma = decimal separator, e.g. `2.755,65`), strongly suggesting `Internal Id` values like `895,21` or `4,65` are single decimal numbers in that same format, not two separate joined codes. Still open: why the decimal portion so often repeats a small set of values (21, 65, etc.) across many rows/screens — possibly meaningful (e.g. a version or category encoded in the decimal part) or possibly coincidental; not confirmed either way.
- Why does the `Sel: n / Count: n` status-bar segment appear in full on some screens (`Assign Instrument Type`, `Condition Port Properties`) but show only `Sel: n` with no count on others (`Cross Account Config`, `Portfolio Properties`), and not appear at all on `Config. Local Properties`? Not yet understood — possibly tied to whether/how a search was executed, or to row selection state.
- What conditionally enables the greyed-out-looking `Entity` and `Account` fields on `Cross Account Config`? Not confirmed by interaction.
- What is the full set of `Status` values on `Portfolio Properties` beyond `Valid`/`InValid`? Only these two seen so far.
- What do the additional (undisplayed/off-screen) columns on `MBJ Config`'s data grid contain? Confirmed by the user that more columns exist beyond `Group Name`/`Label`.
- Is `AUKI` the only value the `Instanze` (likely "Instance") column on `MBJ Config` can take, or just the value in this particular filtered/sorted view? Not confirmed.
- What does the horizontal scrollbar-like element under `MBJ Config`'s filter header indicate — does the filter header itself scroll to reveal more fields? Not confirmed.
- What do the `Last Maint Source` values on `Accounting Topics` represent exactly (which upstream systems feed vs. directly-maintained BOX reference data)? Not confirmed beyond there being at least two distinct sources.
- On `Documents`, what does the filter's `Code:` field search against, given the grid has no `Code` column? And does `User:` in the filter correspond to the grid's `Owner` column? Not confirmed.
- What do the different short prefixes seen in `Documents`' `Name` column values represent (likely a document/movement type code)? Not confirmed.
- Why is `Global Accounts`' first grid column labeled `PK` while every other screen so far uses `Internal Id`/`Internal ID`? Is `PK` meaningfully different (e.g. a true database primary key vs. a business-facing sequence number), or just an inconsistent label for the same concept?
- What does the green row/cell highlighting on `Net Contract` indicate? Possibly system- vs. user-entered records, but not confirmed.
- Which fields are conditionally disabled/greyed-out, and what enables them? Seen on `Cross Account Config` (Entity, Account), `Net Contract` (Portfolio), and — most strongly — `Movements Report` (Entity, Port.Properties, Deal Id, Account, Security, Settle. Account, Folder — 7 fields at once). A recurring, clearly deliberate UI pattern, but the triggering condition (perhaps selecting an Instrument first) is not confirmed.
- ~~Is the vertical toolbar difference between Config/Data screens and Reports screens a general distinction~~ — **Refined:** `Balance Report` also showed only the filter icon (2/2 Reports screens), and `Days Matured` (under `Control > Configuration`, not Reports) showed the full CRUD icon set — supporting the idea that the filter-only toolbar is specifically a `Reports`-folder trait, not tied to anything else (like which top-level branch or sub-folder name a screen sits under).
- Is `Movements Report`'s default date range (1st of current month → today) a general "month-to-date" default, or coincidental to when this screenshot was taken? Only one observation.
- Why does `Movements Report`'s `Internal Id` use large negative European-formatted numbers, unlike the small positive values on Config/Data screens? Possibly a different/larger sequence generator, possibly negative = reversal/contra entries — not confirmed.
- What does the trailing `_S` suffix mean in the `BOX_FE.T_BOX_*_S` table names (e.g. `T_BOX_DEAL_DATA_S`)? Not confirmed.
- Exactly what does Ctrl+Shift+Click target (the whole screen, a specific field/column, a specific row?) when activating the Trace view, and what does the Trace view's output look like? Not yet screenshotted.
- ~~Do flat-grid list screens also support opening a record into a multi-sub-tab detail view~~ — **Resolved:** `MIS` also opens into a multi-sub-tab record-detail view (8 tabs), confirming this is a general SIGOM pattern for structurally complex config objects, not specific to `Fixing Curve`. Still open: whether the simpler flat-grid screens seen earlier (`Assign Instrument Type`, `Condition Port Properties`, `Cross Account Config`, etc.) also support this, or whether it's specific to more structurally complex config types like Fixing Curve/MIS.
- What table (if any) backs `Fixing Curve`'s `Array of Quotes` sub-tab, and what does `Array of Yield Curve` (not yet opened) contain? Similarly, what do `MIS`'s `Yield Curve`, `Fixing Exceptions`, and `Currency Basis` sub-tabs contain (not yet shown)?
- What do the truncated column headers on `MIS > Accrual` represent exactly (visually resembling something like InCurrency/Dea.../Co.../Dea.../TriggerI...)? Not confirmed.
- On the record-detail view, does clicking an entry in the right-hand "Navigation Tree" panel actually drive the same content as clicking the top sub-tabs? They appear to mirror each other and highlight in sync, but this hasn't been confirmed by interaction.
- What's inside the plain `BOX` top-level tree node (still unexpanded, sitting alongside `BOX - Accounting`)?
- ~~Is `BOX`'s internal structure organized like `GBO`...~~ — **Resolved:** `BOX - Accounting` is its own standalone top-level node with a structure genuinely different from `GBO > Accounting` (see Work View Explorer section above). Still open: what is inside the plain `BOX` top-level node itself, and does `BOX - Financial Engine` (and `BOX - Migration`, `BOX - Settlement`) follow the same standalone-top-level-node pattern as `BOX - Accounting`?
- Does each Start Page tile map 1:1 to a node/leaf in the Work View Explorer tree? — **Increasingly confirmed:** `MBJ Config` (Most Used Applications), `BOX Flow Data` and `BOX MarketValue & Risk` (History), and now `MIS` (Most Used Applications) all match tree leaves exactly. Not yet confirmed for `Global Accounts`, `Assign Instrument Type`, `Label Config`, `Branch Configuration`, `Deal Lite Query`, `BOX IRS/CCS/C&F Financial Data` — `Global Accounts` and `Assign Instrument Type` are plausible matches to leaves already seen, but not explicitly confirmed.
- Why are `<ADMIN>`, `<PROJECTS>`, `<Security>`, `<TOOLS>` shown with angle-bracket names while the rest aren't — is this a meaningful category distinction in SIGOM (e.g. system-level vs. functional/product areas)?
- Are there more tiles in "Most Used Applications" and "History" beyond what's visible (both sections appear cut off on the right edge, suggesting horizontal scrolling)?
- Does each Start Page tile map 1:1 to a node/leaf in the Work View Explorer tree, or are they a separate concept (e.g. bookmarked shortcuts)?
- What does `x700072` represent precisely (user ID / employee ID / login ID)?

## Changelog

- Doc created — skeleton only, no screenshots processed yet.
- Added Start Page screenshot: documented global UI chrome (window title, menu bar, toolbar, environment badge, Work View Explorer navigation tree, status bar) and the Start Page screen itself (Most Used Applications, History, Favorites).
- Added two screenshots showing the `GBO` node expanded, then `Accounting` and `Financial Engine` (both children of `GBO`) expanded. Documented GBO's full second-level child list and the third-level children of Accounting and Financial Engine. Documented tree expand/collapse behavior and the status-bar breadcrumb that shows the selected top-level node's name. Raised an open question about whether BOX's internal structure mirrors GBO's nesting.
- Added screenshots showing `GBO > Accounting` fully expanded down to leaf screens. Documented all leaf items under Documents, General, Grouped Movements, Interfaces, Manual Movements, Reports, and Settle to Market. Confirmed the tree uses two distinct icons — folder vs. leaf/launchable screen. Flagged two truncated labels as open questions.
- Added screenshot of `BOX - Accounting` (a separate top-level node from `GBO`) fully expanded. Documented its Config., Data, MBJ Config, and Reports sub-structure. Confirmed BOX's Accounting area is structurally distinct from GBO's, and confirmed the Start Page's `MBJ Config` tile maps directly to a tree leaf under `BOX - Accounting`.
- Added first screenshot of an actual leaf screen opened: `BOX - Accounting > Config. > Assign Instrument Type` (tab title "BOX Instrument Type"), filtered to branch MADRID REAL. Documented its filter header fields, vertical icon toolbar, data grid columns, and screen-specific status bar info (Sel/Count, Current auth-code). Per instruction, specific row data values were not transcribed — only screen structure.
- Added second leaf screen screenshot: `BOX - Accounting > Config. > Condition Port Properties` (tab title "Conditions Portfolio"). Confirmed the filter-header/toolbar/grid layout recurs across Config screens. Noted this screen has no Branch filter (unlike Assign Instrument Type), and that the status bar's "Current auth-code" persisted from the prior screen, suggesting it's a global/session value rather than per-screen.
- Added third leaf screen screenshot: `BOX - Accounting > Config. > Config. Local Properties` (tab title "Split Config. Local Prop"). Confirmed the trailing description column is consistently excluded from the filter header across all 3 Config screens seen. Noted a new "Branch Group" field distinct from "Branch", and that its values (Spain/London/Colombia) extend beyond the stated Tier 1 scope — raised as an open question. Also noted the `Sel/Count` status segment was absent here unlike the prior two screens, and that the earlier "Internal Id second component = branch code" hypothesis looks weaker now.
- Added fourth and fifth leaf screens: `BOX - Accounting > Config. > Cross Account Config` and `BOX - Accounting > Config. > Portfolio Properties`. Documented both screens' filter fields, grid columns, and toolbar (same recurring template). Noted a genuine UI label typo ("Intrument:") on Portfolio Properties, a naming inconsistency between its "Branch Group" filter and "Branch" grid column, a new `Status` (Valid/InValid) column, and two fields that look conditionally disabled on Cross Account Config. Also noted the tab bar revealed `FX Liquid Config` and `Grouped Accounting Config` had been opened too, though their content hasn't been shown yet.
- Added sixth leaf screen: `BOX - Accounting > MBJ Config` (the leaf sitting directly under BOX - Accounting, matching the Start Page's MBJ Config tile). Documented its filter header, grid columns (noting a second UI typo, "Instanze"), and that more grid columns exist off-screen per the user. Used a clear European-decimal-format example in this screen's `Group Id` column to substantially revise the earlier `Internal Id` two-part-number hypothesis — now understood as most likely a single decimal number in Spanish/European notation, not two joined codes.
- Added seventh and eighth leaf screens, the first two from the `Data` folder: `BOX - Accounting > Data > Accounting Topics` (tab "Topics") and `BOX - Accounting > Data > Documents` (tab "Documents(All Movements)"). Noted Accounting Topics breaks the earlier "trailing description column has no filter field" pattern, and introduced new maintenance/audit columns (Last Maint Date/User/Source). Noted Documents has filter/grid field-name mismatches (Code, User) and a date-defaulted filter field. Also reconfirmed BOX - Financial Engine, BOX - Migration, and BOX - Settlement as separate top-level tree nodes alongside BOX - Accounting.
- Added ninth and tenth leaf screens: `BOX - Accounting > Data > Global Accounts` (tab "Split for Glta Acct") and `BOX - Accounting > Data > Net Contract` (tab "Net Contract"). Noted Global Accounts uses "PK" instead of "Internal Id" for its first column (a new naming inconsistency), and its Account Type/Direction/FX Adjust controlled vocabularies. Noted Net Contract shows unexplained green row/cell highlighting, and reinforced the recurring "some filter fields appear disabled" pattern first seen on Cross Account Config.
- Added eleventh leaf screen and first from the `Reports` folder: `BOX - Accounting > Reports > Movements Report` (tab "Movem. between Two Dates"). Documented its rich two-column filter (including the first checkbox field, "Manual Only") and strong evidence of the disabled-field pattern (7 fields at once). Noted its toolbar shows only the filter icon — unlike every Config/Data screen's full add/edit/delete/copy/search/filter set — suggesting Reports screens may be read-only. Also flagged its unusual large-negative European-formatted `Internal Id` values as an open question. Actual monetary debit/credit/balance figures were not transcribed.
- Added twelfth leaf screen: `BOX - Accounting > Reports > Balance Report` (tab "Balance Consulting"), second Reports-folder screen. Confirmed the filter-only toolbar pattern now on 2/2 Reports screens. Contrasted its single-date "point in time" filter with Movements Report's date-range filter. Noted a second checkbox field ("View zero values"). Flagged suspiciously round balance figures and placeholder account values as supporting (not conclusive) evidence for the earlier "test/copy environment" open question about the IGBOMD badge.
- Added `BOX - Financial Engine` tree expansion (a separate top-level node from `BOX - Accounting`). Documented its 4 direct leaf screens and 4 unexpanded folders. Confirmed two Start Page "History" tiles (BOX Flow Data, BOX MarketValue & Risk) map directly to leaves here, extending the earlier tile-to-tree-leaf confirmation beyond "Most Used Applications". Compared its structure to GBO's Financial Engine branch, noting differences (no OBB Module equivalent; "Static IT Data" vs. "Static MIS Data").
- Added a new "Screen → Database Table Mapping" section, recording the first 4 screen-to-Oracle-table mappings provided directly by the user (all under the `BOX_FE` schema, `T_BOX_<NAME>_S` naming convention) for the 4 `BOX - Financial Engine` leaf screens.
- Expanded `BOX - Financial Engine > Control` fully: documented its Configuration, Historical Data, and Tools sub-folders and all their leaves. Confirmed the Start Page's `MIS` tile maps to `Control > Configuration > MIS`. Noted "Fixing Curve" appears as a leaf under both Configuration and Historical Data.
- Added thirteenth leaf screen and first from `BOX - Financial Engine`: `Control > Configuration > Days Matured`. Noted a fourth naming variant for the ID column (`Internal_ID`), confirmed the Reports-only filter toolbar pattern is specific to the Reports folder (this Control-folder screen has the full CRUD toolset), and — per the user's explicit note that row values here may be wrong — substantially strengthened the "test/copy environment" open question from circumstantial to directly supported.
- Added fourteenth leaf screen: `BOX - Financial Engine > Control > Configuration > FE Parameters` — the first screen with no filter header at all, and an EAV-style generic parameters table (Parameter name + typed Date/Number/String value columns). Noted a fifth naming variant for the ID column (`InternalID`). Added two new rows to the Database Table Mapping section (`Days Matured` → `T_BOX_ENGDAYS_MATURED_S`, `FE Parameters` → `T_BOX_ENGSETUP_S`, both user-provided), and noted an `ENG` infix sub-pattern distinguishing Control/Configuration tables from the core Financial Engine data tables.
- Added fifteenth leaf screen: `BOX - Financial Engine > Control > Configuration > Fixing Curve` (DB table `BOX_FE.T_BOX_ENGFCURVE_S`, user-provided). Strengthened the `ENG` infix naming sub-pattern to 3/3 Control > Configuration tables. Cross-referenced its two rows' "(ESP)"/"(SLB)" naming with the Tier 1 Madrid/SLB branch scope stated at the start of this document.
- Documented a new UI pattern: opening a specific record from the `Fixing Curve` list opens a separate record-detail tab with its own sub-tabs (Generic, Array of Quotes, Array of Yield Curve) plus a mirrored right-hand "Navigation Tree" panel. Documented the Generic and Array of Quotes sub-tabs (Array of Yield Curve not yet shown). Raised open questions about whether this drill-down pattern exists on other list screens, and what backs the Array of Quotes sub-tab in the database.
- Added sixteenth leaf screen: `BOX - Financial Engine > Control > Configuration > MIS` (tab "ENG Config Selection"; DB table `BOX_FE.T_BOX_ENGCONF_S`, user-provided). Strengthened the `ENG` infix naming pattern to 4/4 Control > Configuration tables. Reinforced the Tier 1 ESP/SLB cross-reference via this screen's two rows, and noted a new `Calendar` column (e.g. TARGET Settlement Day).
- Documented the MIS record-detail view (opening "Configuracion -SCH (ESP)"), which has 8 sub-tabs — resolving the earlier open question about whether Fixing Curve's multi-tab drill-down pattern is general (it is). Documented Generic (discovering a real cross-reference: MIS's Man./Acc. Fixing fields point to Fixing Curve records by name, plus Source Front/Back systems-integration fields), Accrual, Accrual Exceptions, Branch (confirming a literal "TEST" branch code alongside MADRID, both under legal entity Banco Santander S.A.), and Book sub-tabs. Yield Curve, Fixing Exceptions, and Currency Basis were not shown.
- Expanded `BOX - Financial Engine > Financial Status`: per the user, this branch holds financial data per product, with one sub-folder per product family (BRS, C&F, CCS, CDS, CES, CFM, Depo, FRA, FX, OTC, Swap). CCS and CDS were expanded, each showing the same 3-leaf pattern (Deal Data / Financial Data / MtM Data). Recorded the user-stated general DB table naming rule for these: Deal Data always maps to one shared table (`T_BOX_DATADEAL_S`) across all products, while Financial Data (`T_BOX_<PRODUCT>FINANCST_S`) and MtM Data (`V_BOX_ENG<PRODUCT>DATAMIS_S`, a view) are product-specific — confirmed explicitly for CCS, with CDS and other products' names derived from the stated rule but not individually confirmed.
- Expanded `BOX - Financial Engine > Process Management` (Allowed Errors, Log, Monitor, Process Queues) and `BOX - Financial Engine > Static IT Data` (Deal Status, Event, Event Parameter, Exec Direction, Fee Type, Procedures, Process, Process Status, Processed Instruments) fully — both previously unexpanded folders now fully documented.
- Added 13 more user-provided DB table mappings, all for `BOX - Accounting` screens (schema `BOX_ACC`). This confirmed a solid pattern: the Oracle schema name matches the top-level SIGOM tree branch (`BOX - Financial Engine` → `BOX_FE`, `BOX - Accounting` → `BOX_ACC`). Also found the first exception to the `_S` suffix convention: `T_BOX_ACCT_HISTSTD` (Standard Historic) has no trailing `_S`.
- Documented the "Trace" element in the status bar: per the user, Ctrl+Shift+Click or View > Trace View activates a Trace view that reveals a screen's underlying database table(s) — very likely the in-app source of the Screen → Database Table Mapping data the user has been supplying manually.
- Reconciled several open questions against other documents already in this repo, rather than waiting on further screenshots: removed the Branch-vs-Branch-Group open question (resolved via `branch-config-surface.md`'s `FK_LOCALGROUP` dual-keying proof — Branch Group is a bank-wide accounting-config dimension, independent of the Tier 1/Tier 2 split) and folded the resolution into the `Config. Local Properties` entry; confirmed the `T_BOX_ACCT_HISTSTD` naming exception is real (independently listed the same way in `box-data-model.md`, not a transcription artifact); corroborated the shared-table claim for `T_BOX_DATADEAL_S` using `fe-raw-data-stage.md`'s direct DB sample (both IRS and CCS rows present at once). Rewrote the `Accounting Topics` screen's Purpose bullet from a speculative guess to the confirmed model (a catalogue of reusable accounting concepts, explicitly not GL accounts) and filled in the previously-empty `Cross-Screen Relationships` section with the confirmed `T_BOX_ACCT_PORT_PROP_S` / `T_BOX_ACCT_TOPICS_S` / `T_BOX_ACCT_GLTA_S` → `T_BOX_ACCT_LIST_TOPIC_S` mapping chain, cross-checked against `branch-config-surface.md`'s independent Tier-1 findings on the same table.
