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

**Step 0 — find the repo root.** This automation repo is the `automation/` subfolder of the
`cib-box-auki-nbranch` checkout. Run both searches (case-insensitive; the first hit wins):

```bash
for d in ~/repos/cib-box-auki-nbranch/automation "$PWD" "$PWD/automation" \
         "$(git rev-parse --show-toplevel 2>/dev/null)/automation"; do
  if [ -f "$d/agents/box-batch-jobs-agent/AGENT.md" ] || [ -f "$d/agents/box-batch-jobs-agent/agent.md" ]; then echo "REPO_ROOT=$d"; break; fi
done
find / -path /proc -prune -o -type f -ipath '*/agents/box-batch-jobs-agent/agent.md' -not -path '*/archive/*' -print 2>/dev/null | head -5
```

**Nothing found → ask the operator for the path of the `cib-box-auki-nbranch` checkout** (do not stop, never
recreate the charter).

`cd` into the folder containing `agents/`. Every path below is relative to it.

**Step 1 — read, in full:** `agents/box-batch-jobs-agent/AGENT.md`,
`docs/reference/job-chains/box-batch-chain.md`, `docs/reference/queries/box-jobs-queries.md`, and the
reference answer `docs/examples/gmbx3es02d07-trace.md`.

**Step 2 — the question**

```text
QUESTION : <job name, group PK/name, event PK/name, a list ("all IRS jobs for Madrid and their order"), or a plain question>
ENV      : <Tier 1 | Tier 2 | ...>
DEPTH    : overview          # overview (default) | event <PK> | full
```

**Step 3 — answer it** following the charter's *EXPLAIN* procedure:

- **Respect `DEPTH` and its query budget** (charter, *EXPLAIN depth*): `overview` = binding + the group's events
  by name (J-C2), **≤ 3 queries**; `event <PK>` = that event only; `full` = group-wide J-C3g / J-C4g, never one
  query per event. End by offering the next depth. A **list** question is answered with
  `scripts/find_jobs.py` on `jobs-inventory.csv` — no query; "… and their order" adds `--controlm` with the
  Control-M repo dirs (charter, *LIST questions*).
- Ask for **one query at a time** (by J-ID, with the placeholders filled), and wait for its CSV. If the
  environment's owners are not yet known, start with J-E1 and J-E2 — never assume `PGT_ES`.
- For code, read the repo's **highest `r` folder** containing the object and say it is the committed
  copy; ask for J-X1 when the deployed copy matters.
- Answer in the shape of the worked example: a summary paragraph, one row per level with the key used
  and the evidence, each claim **CONFIRMED** or **INFERRED**, then the open points.
- At depth `event` / `full`, describe events as **entries** (deals selected, values calculated, accounts debited and credited;
  `MC_DRCR` 1 = debit).
- If the answer took more than three levels, also write it to
  `docs/examples/<question-slug>-trace.md` with placeholders for any book or portfolio code, and say so.
