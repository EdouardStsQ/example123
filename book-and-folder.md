# Book and Folder — two dimensions that both travel with a trade

**One page, one job:** stop these being confused, and record the one thing that is missing between
them.

`[stated: Edouard, 2026-09-21]` unless marked otherwise.

## ⚠️ First, three things called "label" and two called "book"

`[confirmed: source via Devin, 2026-09-21]` An earlier version of this page treated **Book** and
**Label** as the same word for one thing. **They are not.** The load code distinguishes them, and
conflating them is the mistake this page now exists to prevent.

| Name | What it actually is | Where |
|---|---|---|
| **Process LABEL** | **The BOX configuration concept — what this page calls the desk.** What `T_BOX_CONF_BY_BOOK_S.FK_LABEL` and `T_BOX_DATADEAL_S.FK_LABEL` hold, and what batch procedures take as the `P_Label` parameter | `PGT_SYS.PGT_DOMAINS` where `FK_OWNER_OBJ = 17910.4` |
| **BOOK (raw)** | **The trading-book identifier string** carried on every datalake row. A real business key — part of `IU_BOX_RAW_MARKET_DATA_S` = (PROCESSDATE, SOURCESYSTEM, FRONT_ID, CURRENCY, DIRECTION, **BOOK**, DATA_EXECUTION_TYPE, CURRENT_CONTRACT) | a column on `T_BOX_RAW_*` |
| **raw LABEL / DEAL_LABEL** | Datalake-sourced attributes carried through on the raw row. **Not** the process label, and not used to drive loads | columns on `T_BOX_RAW_*` |

**The bridge between the first two is a function:**

```
process LABEL (config, P_Label)
      │  BOX_SYS.PKG_BOXUTILITY.f_GetBookByLabel(P_Label)
      ▼
BOOK (a string)
      │  filter: upper(BOOK) = upper(str_book)
      ▼
raw datalake rows
```

Every load and import procedure does exactly this — `PKG_FE_MTM_CALCULATION`, `p_Import_Deal_Data`,
the datadeal-load packages. The process label's own PK is stored separately as `FK_LABEL` on
`T_BOX_DATADEAL_S` via `f_getPKByLabel(P_Label)`, **independent of the raw `DEAL_LABEL` column.**

`[open-question]` `f_GetBookByLabel` lives in the external `BOX_SYS` schema and its body was not
readable, so **whether one label resolves to one book or several is unconfirmed.** That matters: if one
label maps to many books, the process label sits a level *above* the trading book, and "the desk" is
the label rather than the book.

**Folder has the same duality**: a datalake-sourced `FOLDER` string on the raw row, and the SIGOM
master `PGT_STC.T_PGT_FOLDER_S` that `FK_FOLDER` resolves to. They presumably correspond; nothing
confirms it.

## The two dimensions, as configuration

| | **BOOK / Process LABEL** *(Libro)* | **FOLDER** |
|---|---|---|
| What it is | **The desk.** Contains many folders | **An aggregation of trades / Murex portfolios** |
| Who owns it | Configured in GBO | **GER** — an external system that owns folders and distributes them to consuming systems including BOX |
| SIGOM screen | `GBO > SYS > Process > Batch > Label Config > Label Config` | `GBO > Static Data > Environment > Folders` |
| Table | `PGT_SYS.PGT_DOMAINS` **where `FK_OWNER_OBJ = 17910.4`** | `PGT_STC.T_PGT_FOLDER_S` |
| SIGOM object | `PGT - Label Config` (`17910.4`) | `PGT - Folders` |
| Schema | `PGT_SYS` — **shared**, identical in every environment | `PGT_STC` — **shared**, and **branch-keyed** via `FK_BRANCH` |

**Book lives in `PGT_DOMAINS`, which is one physical table holding many unrelated enumerations**,
separated by `FK_OWNER_OBJ`. So `FK_OWNER_OBJ = 17910.4` is not an optional refinement of a book query
— without it you are reading across every enumeration in the system. See
[`sigom-metamodel.md`](sigom-metamodel.md) §2.

**SIGOM itself treats Folder and portfolio as the same thing.** `[confirmed: DB, 2026-09-21]` The
`BOX - Migration Criteria` and `BOX - Auki Criteria` objects each declare a field literally named
**`apPortfolio`** whose declared target is `PGT - Folders → PGT_STC.T_PGT_FOLDER_S`. The screen says
portfolio; the metadata says folder. That settles what had been an inference in
[`box-data-model.md`](box-data-model.md) ("Folder ≈ the Murex portfolio context").

## Why it matters: processing runs by (BOOK, INSTRUMENT, BRANCH)

**Both BOX FE and BOX ACC partition their batch work on that triple** — for parallelisation and batch
performance. That is the reason the dimension exists in the configuration at all, and it is what these
two tables are:

| Side | Table | Object | Declared fields |
|---|---|---|---|
| **FE** | `T_BOX_CONF_BY_BOOK_S` | `BOX - MIS Config by Book` (`35000302.65`) | `pBranch`, `pInstrument`, `pLabel` |
| **ACC** | `T_BOX_MBJ_PROPERTIES_S` | `BOX - MBJ Properties` (`35000182.65`) | `pBranch`, `pInstrument`, `pLabel`, `pSubLabel`, `pGroup`, plus `Concurrence`, `Workers`, `Task_per_worker`, `Workers_by_events`, `Instanze` |

MBJ Properties' field list is the proof: `Workers`, `Task_per_worker` and `Concurrence` are
parallelisation parameters, sitting on the same row as the (branch, instrument, book) key.

### Proven from source, 2026-09-21

`[confirmed: source via Devin]` **`PKG_ENGGNCP_OPTZ.p_create_process_queues_optz`** reads
`T_BOX_CONF_BY_BOOK_S` joined to `T_BOX_ENGCONF_X`, filtered by `(FK_BRANCH, FK_INSTRUMENT)`, selecting
`FK_LABEL` — and **for each distinct `FK_LABEL` inserts a queue row into
`T_BOX_BRPROCCAL_QUEUE_S_OPTZ`, using the label as the `QUEUE` value.** One book, one processing queue.

The change history settles any doubt: **`CIBAUKI-4704` replaced a generic `PGT_DOMAINS` lookup with
this cursor in r0.0.27, specifically so queue creation is driven by the book configuration.** The table
exists *for* queue creation.

**Two consequences.** The join to `T_BOX_ENGCONF_X` means the branch-association row (FE walk step 5)
is a **runtime prerequisite** — without it, nothing is queued at all. And the unique index
`(FK_BRANCH, FK_INSTRUMENT, FK_LABEL)` `[confirmed: DDL, 2026-09-21]` confirms the partitioning triple
is the table's natural key.

### This resolves walk step 11's standing open question

`fe-branch-configuration.md` and the FE charter record that a BOX FE Developer confirmed *"the books
which are created there for X branch and X instrument are the ones that are executed"* — and then that
**the table's exact purpose was not fully understood, by the developer either**.

It is now. **`T_BOX_CONF_BY_BOOK_S` is a batch-partitioning table, not business configuration.** A row
declares a unit of parallel work. That reframes the developer's two rules:

- *"At least one row per instrument is required, hence the `0 - EMPTY` Book/Label rows"* → an instrument
  with no real book still needs **a partition**, or it is never processed. `0 - EMPTY` is a partition
  placeholder, not a data gap.
- *"A missing row means that combination is never processed, silently"* → a missing **partition**, which
  is why the failure is silent: nothing errors, the work simply is not scheduled.

`[inferred]` from the two declared field sets above plus the developer's statements. Worth confirming
with him in one sentence, but every piece of evidence points the same way.

## The gap: no BOOK ↔ FOLDER mapping exists in BOX

**There is nowhere in BOX to look up which folders sit inside which book.** The team wants one in
future; it does not exist today.

This is an absence, so it is evidenced rather than asserted — three independent passes over the
metamodel, per hard rule 8:

| Pass | Result |
|---|---|
| Every field of the 31 ACC configuration objects (269 rows) | Folder on `Acct Movements`, `Acct Key`, `Net Contract`, `Grouped Movements`. Book only on `MBJ Properties`. **No object declares both** |
| Every field of the 9 objects sharing `T_BOX_LINK_ARRAY_X` (129 rows) | Folder 3×, Book 0× |
| The FE walk's 68 declared fields | Book on `MIS Config by Book`; Folder nowhere |

Stronger than "nobody built the screen": the two dimensions attach to **different kinds of object** —
Folder to accounting movements and keys, Book to job configuration. They are not two attributes of one
thing that someone forgot to relate.

### What this costs the onboarding, concretely

Walk step 11 asks an SME which books a branch needs. **There is no query that checks the answer was
complete.** You cannot enumerate the folders under a book, so you cannot prove a branch's Book rows
cover all of its trades — and a missing row means that work is silently never scheduled.

Gate 0c gets the *instrument* scope signed off in writing. **There is no equivalent gate for book
scope, and no query that could produce one from configuration alone.** Treat that as a named risk on
step 11, not a footnote.

## But the mapping is *derivable* from trade data

`[confirmed: DB, 2026-09-21]` **41 tables carry both dimensions** — and every one of them is a deal,
RAW or MIS-view table, not a configuration table. That is the same finding from the other side, and it
opens a workaround:

| Table family | Columns | What it is |
|---|---|---|
| `T_BOX_DATADEAL_S` and its per-product twins (`T_BOX_IRDATADEAL_S`, `T_BOX_MMDATADEAL_S`, `T_BOX_CESDATADEAL_S`, …) | `FK_FOLDER`, `FK_LABEL` | **Resolved FKs** — `FK_LABEL` is the *process label's* PK, `FK_FOLDER` the folder master's |
| `V_BOX_ENG*DATAMIS_S` (per-product MIS views) | `FK_FOLDER`, `FK_LABEL` | Resolved, as above |
| `T_BOX_RAW_DEAL_DATA_S`, `T_BOX_RAW_MARKET_DATA_S`, `T_BOX_DEAL_DATA_S` | `BOOK`, `FOLDER`, `LABEL` / `DEAL_LABEL` | **Datalake strings**, all four populated by the external feed — see the three-labels warning above |
| `DEVENG.T_PGT_MTM_DATALAKE_S` | `FOLDER`, `LABEL` | The GBO side |

**Use the `DATADEAL` family, not the RAW family.** `[confirmed: source, 2026-09-21]` The RAW columns are
datalake attributes carried through verbatim; the load code neither writes them nor treats
`LABEL`/`DEAL_LABEL` as the process label. It is the **DATADEAL** tables that carry the resolved pair —
the process label's PK in `FK_LABEL` (via `f_getPKByLabel`) alongside `FK_FOLDER` — and that pair is
exactly the configuration-level relationship no configuration table declares.

### The coverage check this makes possible

```sql
-- Observed book ↔ folder pairs for a branch, from actual deals
SELECT lbl.CODE  AS book_code,  lbl.DESCRIPTION AS book,
       f.CODE    AS folder_code, f.DESCRIPTION  AS folder,
       COUNT(*)  AS deals
FROM        BOX_FE.T_BOX_DATADEAL_S    d
JOIN        PGT_SYS.PGT_DOMAINS        lbl ON lbl.PK = d.FK_LABEL
JOIN        PGT_STC.T_PGT_FOLDER_S     f   ON f.PK   = d.FK_FOLDER
WHERE       d.FK_BRANCH = &&BRANCH_PK
GROUP  BY   lbl.CODE, lbl.DESCRIPTION, f.CODE, f.DESCRIPTION
ORDER  BY   1, 3;
```

Then diff the distinct books it returns against `T_BOX_CONF_BY_BOOK_S` for the same branch: **any book
appearing on deals with no partition row is a silent processing gap.** That is the check step 11 has
never had.

⚠️ **Observed, not authoritative.** It shows which pairs *have traded*, not which are *permitted*. It
cannot reveal a folder that has never traded under a book, so it is a coverage check on a live branch,
not a completeness guarantee for a new one. For NY_SCH — not yet live in BOX — it can only be run
against a **reference** branch, to size the problem and validate the method.

It is also the most promising starting point for the mapping the team wants in future: the data to
build it already exists.

## Open questions

| Question | Why it matters |
|---|---|
| Does a BOOK↔FOLDER mapping exist **outside** BOX — in GER, or derivable from the Data Lake? | "No mapping in BOX" and "no mapping anywhere" are different risks. Only the second is unfixable today `[open-question]` |
| Is the book catalogue **global or branch-scoped**? | `PGT_DOMAINS` is in shared `PGT_SYS`, so the working read is that books are global and `T_BOX_CONF_BY_BOOK_S` assigns them per branch. Unconfirmed `[open-question]` |
| Where does **GER** sit relative to Murex — upstream, beside, downstream? | It owns a dimension that reaches BOX; it belongs in [`system-overview.md`](system-overview.md) once placed `[open-question]` |
| ~~RAW carries `BOOK` *and* `LABEL` as separate columns~~ | ✅ **Answered 2026-09-21** — they are different things. `BOOK` is the trading-book identifier and part of the raw unique key; `LABEL`/`DEAL_LABEL` are datalake attributes; and the *process* label is a third concept that resolves to a book via `f_GetBookByLabel`. See the warning at the top of this page |
| **Does one process label resolve to one book or many?** | `f_GetBookByLabel`'s body is in the external `BOX_SYS` schema and was not readable. If many, the process label sits above the trading book and "the desk" is the label `[open-question]` |
| Does the raw `FOLDER` string correspond 1:1 to `PGT_STC.T_PGT_FOLDER_S`? | Presumed, unconfirmed `[open-question]` |
| What is `pSubLabel` (`PGT - SubLabel Config`)? | A second level below Book on MBJ Properties, absent from the FE side entirely `[open-question]` |

## Related

- [`sigom-metamodel.md`](sigom-metamodel.md) — how these objects and fields were read, and the
  `FK_OWNER_OBJ` discriminator rule that makes a `PGT_DOMAINS` query correct.
- [`box-data-model.md`](box-data-model.md#folders--branch-keyed-gbo-static-data) — the Folder query,
  its outer-join caveat, and Folder's branch-keying.
- [`fe-raw-data-stage.md`](fe-raw-data-stage.md) — how both dimensions arrive from Murex into RAW.
- [`job-chains/control-m-batch-layer.md`](job-chains/control-m-batch-layer.md) — `<BOOK-ABBREV>` in job
  naming. Book = desk makes an entry like `XLB01 - HPE FIXED INCOME SLB` read as a desk name, which
  bears on that document's open question about where its abbreviation list comes from.
