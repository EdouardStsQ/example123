# 0017. MIC end-of-day jobs for every instrument; label aliases for MIC created with the ACC configuration

Date: 2026-10-27
Status: accepted — refines ADR 0016 (the MIC decisions of `box-acc-jobs-agent`)

## Context

The BOX expert reviewed NY's ACC jobs run. The agent asked per instrument whether to keep the reference's MIC
end-of-day steps (D12 per book, 00D13) and which sender type to use, and gave none to an instrument the reference runs
without them (SLB's IRS and CCS). The expert also pointed at a prerequisite the agents did not know: MBJ sends
accounting to MIC by book, and each book label needs the GL's alias.

## Decision

`[BOX expert via operator, 2026-10-27]`

1. **D12 / D13 are mandatory for every instrument** of a new branch: D12 per branch, instrument and book
   (`MIC_FILE_TYPE` Accounting), 00D13 per branch and instrument (Revaluation), `MIC_EOD = 1`. They are "scanning"
   jobs: they send to MIC the movements no event grouping sends (cancelled trades, manual movements). Not asked.
   An instrument the reference runs without them gets them on the pattern of one that has them (the reference's
   chain: D12 after the book's last step, the ruler update after every D12, 00D13 after the ruler update).
2. **`MIC_SENDER_TYPE` is `lastly`** on every MBJ row `[operator, 2026-10-27]`. Not asked.
3. **Label aliases for MIC**: one per book label with ACC jobs, in `PGT_TRD.T_PGT_OBJ_SOURCE_S` (owner `17910.4`,
   extension `118615.4`), code given by the GL team (Equation), source = the GL source. **Not needed for the FE side**:
   the book labels skill creates labels without them (codes recorded if known); `sigom-box-acc-configs-agent`
   creates them (screen 14) `[operator, 2026-10-27]`.
4. The MBJ Java code (`cib-efapex-javagboclmbjbtch`) is a read-only source for what MBJ jobs do.

## Consequences

- `build_acc_jobs.py`: no `mic.<instrument>` question; `eod-steps-added` / `eod-template-missing` /
  `eod-row-unexpected`; every row `lastly`; the report lists the label aliases as a readiness item.
- `sigom-box-acc-configs-agent`: screen 14 (A-14a–c); the branch's `books/label-aliases.csv` and
  `label_aliases.source`.
- Open: the GL source of a new branch's label aliases (NY: `629.4` EQUATION_NY proposed); whether the reference's
  MBJ rows are complete in the environment J-R2 was read in.
