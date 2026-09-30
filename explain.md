# Devin kickoff — `box-batch-jobs-agent`, EXPLAIN mode

Paste this, then your question. Branch-agnostic: it works for any job, group or event, in any
environment.

## Before you paste

| | |
|---|---|
| **Repos** | this automation repo (read/write, for the trace file only); `cib-boxacc-dbboxacc`, `cib-boxfin-dbboxfe` and the Control-M folder repos (**read-only**) |
| ⛔ **Write protection** | No commit, branch, push, PR, draft PR or local edit on any repo except this automation repo, ever |
| **Database** | Devin gets no connection. You run each query it asks for and export the result (CSV) |
| ✏️ **Fill in** | `QUESTION` and `ENV` below |

---

You are running as the `box-batch-jobs-agent`, mode **EXPLAIN**.

**Step 0 — find the repo root.** This automation repo is the `automation/` subfolder of the checkout.
Search case-insensitively (the charter may arrive as `agent.md`):

```bash
find / -ipath '*/automation/agents/box-batch-jobs-agent/agent.md' -not -path '*/archive/*' 2>/dev/null | head -5
```

`cd` into the folder containing `agents/`. Every path below is relative to it. Nothing found → say so
and stop; never recreate the charter.

**Step 1 — read, in full:** `agents/box-batch-jobs-agent/AGENT.md`,
`docs/reference/job-chains/box-batch-chain.md`, `docs/reference/queries/box-jobs-queries.md`, and the
reference answer `docs/examples/gmbx3es02d07-trace.md`.

**Step 2 — the question**

```text
QUESTION : <job name, group PK/name, event PK/name, or a plain question>
ENV      : <Tier 1 | Tier 2 | ...>
```

**Step 3 — answer it** following the charter's *EXPLAIN* procedure:

- Ask for **one query at a time** (by J-ID, with the placeholders filled), and wait for its CSV. If the
  environment's owners are not yet known, start with J-E1 and J-E2 — never assume `PGT_ES`.
- For code, read the repo's **highest `r` folder** containing the object and say it is the committed
  copy; ask for J-X1 when the deployed copy matters.
- Answer in the shape of the worked example: a summary paragraph, one row per level with the key used
  and the evidence, each claim **CONFIRMED** or **INFERRED**, then the open points.
- Describe events as **entries** (deals selected, values calculated, accounts debited and credited;
  `MC_DRCR` 1 = debit).
- If the answer took more than three levels, also write it to
  `docs/examples/<question-slug>-trace.md` with placeholders for any book or portfolio code, and say so.
