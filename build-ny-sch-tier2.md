# Devin kickoff — `box-fe-jobs-agent` — NY_SCH BOX FE jobs, from SLB (Tier 1) to Tier 2

> **How to start — nothing to paste.** Open a Devin session with the repos in the table below attached, and type:
> **`Run automation/agents/box-fe-jobs-agent/prompts/build-ny-sch-tier2.md`**
> Devin reads this file and asks you for anything it needs, one question at a time (with a default you can accept).

**This is NY's kickoff: the procedure is [`build-tier2.md`](build-tier2.md)** (generic). Everything NY-specific is
here and in NY's files below; a new branch copies this file and changes the table.

## Before you start — NY_SCH

| | |
|---|---|
| **Branch** | `<BRANCH>` = **`NY_SCH`** (token `NY`), environment folder **`tier2-pre`** (default; DEV = `tier2-dev`) |
| **Inputs file** | `runs/NY_SCH/tier2-pre/fe-jobs/fe-jobs-inputs.NY_SCH.json` — NY's known values and answers (Control-M folders, hosts, calendar `CALC-USA`, `/gmny/scripts`, renames, GBO events with their exact spellings, template / shared-jobs book 15…) |
| **NY's values, decisions, history** | [`runs/NY_SCH/tier2-pre/fe-jobs/README.md`](../../../runs/NY_SCH/tier2-pre/fe-jobs/README.md) (section "NY values and decisions"); questions: `runs/NY_SCH/tier2-pre/jobs/99-open-items.md` |
| **Reference** | **SLB** first (else Madrid) — facts: [`docs/reference/job-chains/reference-slb-fe.md`](../../../docs/reference/job-chains/reference-slb-fe.md) |
| **Repos** | this automation repo `cib-box-aukinbranch` (**read/write**); **read-only**: `cib-boxfin-t1mdslbfe` (SLB FE; Madrid `cib-boxfin-t1mdesfe`), `cib-boxacc-t1mdslbac` (SLB ACC; Madrid `cib-boxacc-t1mdesac`), `cib-boxfin-t1mdloadprices`, `cib-boxfin-mdschedulmonitor`, `cib-boxfin-dbboxfe`, `cib-boxacc-dbboxacc` |
| **Target repos** (Step 7 only) | `cib-boxfin-t2usnyfe`, `cib-boxfin-t2nyloadprices` — PR of `projects/<repo>.json` only after your yes (ADR 0012) |
| **Not attachable (other organisation)** | `cib-auki-aukicnfgsrvc` (descriptors) and `cib-auki-aukictrlmcntrm` (Data Lake jobs per book): **copies in this repo**, `runs/_reference/external/` — check they are there |
| **NY's GBO folder** (optional) | `runs/_reference/external/gbo-ny/P-GBO-NY-TIER2.json` — **PRODUCTION only** (no PRE one exists): PRO waits are checked against it, PRE-only waits are reported "not checked" |
| **Already there** | `runs/_reference/tier1-prod/` (Madrid + SLB `db.conf`, `jobs-inventory.csv`); `runs/_reference/tier2-pre/` (NY's Tier 2 `db.conf` / `shell.conf`); `runs/NY_SCH/tier2-pre/books/books-register.csv` (22 books, 4 excluded in `books-excluded.csv`); NY's instruments in `docs/reference/branch-registry.csv` |
| ✏️ **Devin asks** | the environment, which instruments to build (from NY's plan), confirms the reference, then the renames, external events, Data Lake books and constants the script asks for — one at a time, each with a suggestion |

## NY-specific checks during the run

- **Step 2:** every NY instrument not deployed yet in one run (`depos irs ccs otc cap`; CDS `skip`). The folders
  `depos/`, `depos-v2/`, `all/` are runs from before versioning — history, never written again.
- **Step 5:** pre-answered GBO events — `GMGB1420D01-OK` → `GMNY0011D01_PR-OK`, `GMGB1420D02-OK` →
  `GMNY0012D01-OK_PR`, `GMGB1575D01-OK` / SwapAgent `GMGB4436D02-OK` / `GMGB4465D02-OK` → `DROP-REVIEW`. NY's PRO
  `ControlmServer` is proposed (`GCB.GCB-P-D012`, to confirm); PRE is asked.
- **Step 5b:** NY's ACC folder `JACD-T2USNYAC-BOXAC-100068125` (confirm); `unix.etc_dir` `/gmny/etc`; OrderMethod PRE
  `ON DEMAND`, PRO `JAC1400`.
- **Step 6a:** no job of NY's excluded books: `grep -c 'NY07\|NY09\|NY18\|NY19' out/*.json out/db.conf.proposal` = 0.
- **Step 7:** `python3 scripts/stage_target_pr.py <run folder>/ --checkout cib-boxfin-t2usnyfe=<its clone>
  cib-boxfin-t2nyloadprices=<its clone>`; branch `box-fe-jobs/NY_SCH-<date>`.

---

**If you were pointed at this file**, it is your task prompt: skip the table above, check the repos are attached
(say which are missing), then **follow [`build-tier2.md`](build-tier2.md) from Step 0** with `<BRANCH>` = `NY_SCH`,
`<tier>-<env>` = `tier2-pre` (unless the operator chooses another), the inputs file and the checks above.
