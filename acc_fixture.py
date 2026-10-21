"""Synthetic SLB-like reference ACC chain for build_acc_jobs.py tests (placeholder books BOOK_A / BOOK_B).

acc_fixture(**over) -> the run folder (inputs written). Two instruments: depos (Initial Accounting old-named
GMBOX0028D01, D07 -> D08 -> D12 per book, old-named ruler update GMBOX0028D04, D13 MIC end of day) and IRS
(GMBX3LB00D02 Initial Accounting, D07 -> D09 per book, ruler update GMBX3LB00D03 waiting a GBO event too).
"""
from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

CALL = ("PGT_ES.Pkg_GMBatchprocess.f_ExecuteGroup({g}, PGT_ES.PKG_GMBATCHPROCESS.CST_PK_BRANC_LND, "
        "to_date('$ODATE','YYYYMMDD'), PGT_ES.PKG_GMBATCHPROCESS.{i}, PGT_ES.PKG_GMBATCHPROCESS.CST_PK_DINAMIC);")
MBJ_COLS = ["PK", "BRANCH_PK", "INSTANZE", "JOB_NAME", "INSTR_PK", "INSTRUMENT", "GROUP_PK", "GROUPDESCRIP", "LABEL_PK",
            "LABEL_CODE", "SUBLABEL_PK", "SUBLABEL_CODE", "CONCURRENT_EVENTS", "CONCURRENT_EVENTS_DEPENDENCY", "WORKERS",
            "TASKS_PER_WORKER", "WORKERS_BY_EVENTS", "MIC_SENDER_TYPE", "MIC_FILE_TYPE", "MIC_EOD", "MIC_FLOW_MODE",
            "MONITOR_TYPES", "MONITOR_FILE_MAX_DAYS", "MONITOR_FILE_PATTERN", "FK_PARENT", "FK_OWNER_OBJ",
            "FK_EXTENSION", "RETURN_DATA", "RECOVER_MANUAL_MOVS", "RECOVER_RECLASSIFICATION_MOVS",
            "RECOVER_REGULARIZATION_MOVS", "FK_CALENDAR"]


def job(name, desc, waits=(), adds=None):
    o = {"Type": "Job:Script", "SubApplication": "ACCOUNTING", "FileName": name, "Host": "ref-acc-host",
         "FilePath": "/appl/gm/scripts", "CreatedBy": "devid0", "Description": desc, "RunAs": "gm",
         "Application": "REF-ACC-APP", "When": {"WeekDays": ["NONE"], "MonthDays": ["ALL"],
                                                 "MonthDaysCalendar": "REFCAL", "DaysRelation": "OR"}}
    if waits:
        o["eventsToWaitFor"] = {"Type": "WaitForEvents", "Events": [{"Event": w} for w in waits]}
    o["eventsToAdd"] = {"Type": "AddEvents", "Events": [{"Event": e} for e in (adds or [name + "-OK"])]}
    return o


def mbj_row(job_name, instr, group, label, eod="0", sender="lastly", wbe="{1, 8}"):
    return {"PK": "1.21", "BRANCH_PK": "20087.4", "INSTANZE": "AUKI", "JOB_NAME": job_name, "INSTR_PK": instr,
            "INSTRUMENT": "x", "GROUP_PK": group, "GROUPDESCRIP": "g", "LABEL_PK": "", "LABEL_CODE": label,
            "SUBLABEL_PK": "", "SUBLABEL_CODE": "", "CONCURRENT_EVENTS": "0", "CONCURRENT_EVENTS_DEPENDENCY": "",
            "WORKERS": "8", "TASKS_PER_WORKER": "1", "WORKERS_BY_EVENTS": wbe, "MIC_SENDER_TYPE": sender,
            "MIC_FILE_TYPE": "Accounting", "MIC_EOD": eod, "MIC_FLOW_MODE": "File", "MONITOR_TYPES": "FILE",
            "MONITOR_FILE_MAX_DAYS": "100", "MONITOR_FILE_PATTERN": "./logs/${job}-${date}.json", "FK_PARENT": "",
            "FK_OWNER_OBJ": "35000182.65", "FK_EXTENSION": "", "RETURN_DATA": "1", "RECOVER_MANUAL_MOVS": "0",
            "RECOVER_RECLASSIFICATION_MOVS": "0", "RECOVER_REGULARIZATION_MOVS": "0", "FK_CALENDAR": "1.21"}


def acc_fixture(fe_instruments=("depos", "irs"), **over) -> Path:
    root = Path(tempfile.mkdtemp())
    env, cm, run = root / "ref", root / "cm", root / "runs/NY_SCH/tier2-pre/acc-jobs/all_20261021_1"
    fe = root / "runs/NY_SCH/tier2-pre/fe-jobs/all_20261020_1"
    for d in (env, cm, run, root / "runs/NY_SCH/tier2-pre/books", fe / "out"):
        d.mkdir(parents=True, exist_ok=True)
    db = ["########## BOX - ACC ##########",
          "GMBOX0028D01:T:F:" + CALL.format(g="2409.65", i="CST_PK_DEP"),
          "GMBOX0028D04:T:F:" + CALL.format(g="2855.65", i="CST_PK_DEP"),
          "GMBX3LB00D02:T:F:" + CALL.format(g="2409.65", i="CST_PK_SWAP"),
          "GMBX3LB00D03:T:F:" + CALL.format(g="2855.65", i="CST_PK_SWAP"),
          "GMBX3LB14D07:T:F:" + CALL.format(g="2735.65", i="CST_PK_SWAP").replace(");", ",'XLB14');")]
    sh = ["# configuracoes do shell conf"]
    jobs = {"GMBOX0028D01": job("GMBOX0028D01", "BOX - Initial accounting - SLB", (),
                                ["GMBOX0028D01-OK", "G010014-GMBOX0028D01-OK"])}
    for b, bd in (("14", "SLB BOOK_B"), ("15", "SLB BOOK_A")):
        for s, w in (("07", ["GMBOX0028D01-OK", f"GMBX1LB{b}D06-OK"]), ("08", [f"GMBX1LB{b}D04-OK", f"GMBX1LB{b}D07-OK"]),
                     ("12", [f"GMBX1LB{b}D08-OK"])):
            jobs[f"GMBX1LB{b}D{s}"] = job(f"GMBX1LB{b}D{s}", f"Depos step {s} - {bd}", w)
            sh.append(f"GMBX1LB{b}D{s}:Y:bin:mbjbox.sh GMBX1LB{b}D{s} $ODATE 0000")
        jobs[f"GMBX3LB{b}D07"] = job(f"GMBX3LB{b}D07", f"IRS accounting - {bd}", ["GMBX3LB00D02-OK", f"GMBX3LB{b}D06-OK"])
        jobs[f"GMBX3LB{b}D09"] = job(f"GMBX3LB{b}D09", f"IRS reval - {bd}", [f"GMBX3LB{b}D04-OK", f"GMBX3LB{b}D07-OK"])
    sh += ["GMBX1LB00D13:Y:bin:mbjbox.sh GMBX1LB00D13 $ODATE 0000",
           "GMBX3LB14D07:Y:bin:mbjbox.sh GMBX3LB14D07 $ODATE 0000",
           "GMBX3LB14D09:Y:bin:mbjbox.sh GMBX3LB14D09 $ODATE 0000",
           "GMBX3LB15D07:Y:bin:mbjbox.sh GMBX3LB15D07 $ODATE 0000"]          # GMBX3LB15D09: db.conf only below
    db.append("GMBX3LB15D09:T:F:" + CALL.format(g="2755.65", i="CST_PK_SWAP").replace(");", ",'XLB15');"))
    jobs["GMBOX0028D04"] = job("GMBOX0028D04", "BOX MBJ Update Ruler Group", ["GMBX1LB14D12-OK", "GMBX1LB15D12-OK"])
    jobs["GMBX1LB00D13"] = job("GMBX1LB00D13", "Depos EOD reval - SLB", ["GMBOX0028D04-OK"])
    jobs["GMBX3LB00D02"] = job("GMBX3LB00D02", "IRS Initial accounting - SLB", (),
                               ["GMBX3LB00D02-OK", "G010014-GMBX3LB00D02-OK"])
    jobs["GMBX3LB00D03"] = job("GMBX3LB00D03", "IRS ruler update - SLB", ["GMBX3LB14D09-OK", "GMBX3LB15D09-OK",
                                                                       "GMGB9999D01-OK"])
    (env / "db.conf").write_text("\n".join(db) + "\n")
    (env / "shell.conf").write_text("\n".join(sh) + "\n")
    (cm / "acc.json").write_text(json.dumps({"JACD-REF-BOXAC-1": dict({"Type": "SimpleFolder", "ControlmServer": "REF-SRV",
                                 "SiteStandard": "REF-SITE", "OrderMethod": "Manual"}, **jobs)}, indent=2))
    rows = [mbj_row("GMBOX0028D01", "2.4", "2409.65", "")]
    for b in ("14", "15"):
        rows += [mbj_row(f"GMBX1LB{b}D07", "2.4", "2407.65", f"XLB{b}"),
                 mbj_row(f"GMBX1LB{b}D08", "2.4", "2408.65", f"XLB{b}"),
                 mbj_row(f"GMBX1LB{b}D12", "2.4", "", "XLB14", eod="1")]        # 15's D12 carries XLB14 (defect)
    rows += [mbj_row("GMBX1LB00D13", "2.4", "", "", eod="1"),
             mbj_row("GMBX3LB15D07", "20092.4", "2735.65", "XLB15", sender="none", wbe="{1, 8, 8, 1}"),
             mbj_row("GMBX3LB14D09", "20092.4", "2755.65", "XLB14", sender="lastly")]   # no row for 15's D09
    with (root / "mbj.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MBJ_COLS)
        w.writeheader()
        w.writerows(rows)
    (root / "ref-books.csv").write_text("CODE,DESCRIPTION\nXLB14,SLB BOOK_B\nXLB15,SLB BOOK_A\n")
    (root / "runs/NY_SCH/tier2-pre/books/books-register.csv").write_text(
        "kind,seq,code,description,pk,status,origin,evidence\n"
        "book,1,XNY01,NY BOOK ONE,1.44,exists,existing,Q-10f\nbook,2,XNY02,NY BOOK TWO,,to_create,,Q-10f\n")
    fe_folder = {"JACD-NY-BOXFE-9": {"Type": "SimpleFolder", **{f"GMBX{n}NY{b}D{s}": {"Type": "Job:Script"}
                                                                 for n in "13" for b in ("01", "02") for s in ("04", "06")}}}
    (fe / "out/JACD-NY-BOXFE-9.json").write_text(json.dumps(fe_folder))
    (fe / "fe-jobs-inputs.json").write_text(json.dumps({"instrument": list(fe_instruments)}))   # what the FE run built
    (fe / ".frozen").write_text("frozen\n")
    draft = job("GMBX1NY00D02", "BOX - Initial accounting - NY", (), ["GMBX1NY00D02-OK", "G010014-GMBX1NY00D02-OK"])
    (fe / "out/acc-handoff.json").write_text(json.dumps({"for": "box-acc-jobs-agent", "branch": "NY_SCH",
        "initial_accounting": [
            {"target_job": "GMBX1NY00D02", "instrument": "depos", "reference_job": "GMBOX0028D01", "group": "2409.65",
             "acc_folder": "JACD-NY-BOXAC-9", "draft_job": draft},
            {"target_job": "GMBX3NY00D02", "instrument": "irs", "reference_job": "GMBX3LB00D02", "group": "2409.65",
             "acc_folder": "JACD-NY-BOXAC-9", "draft_job": None}]}))
    cfg = {"reference": {"env_folder": str(env), "controlm_json": str(cm / "acc.json"), "token": "LB",
                         "branch_const": "CST_PK_BRANC_LND", "wrapper_owner": "PGT_ES", "display": "SLB",
                         "books_csv": str(root / "ref-books.csv"), "mbj_csv": str(root / "mbj.csv"),
                         "template_book": {"depos": "15", "irs": "15"}},
           "instrument": ["depos", "irs"],
           "target": {"branch_code": "NY_SCH", "token": "NY", "display": "NY", "branch_pk": "20007.4",
                      "wrapper_owner": "PGT_NY", "books_register": "runs/NY_SCH/tier2-pre/books/books-register.csv",
                      "fe_run": "runs/NY_SCH/tier2-pre/fe-jobs/all_20261020_1",
                      "constants": {"CST_PK_DEP": "SAME", "CST_PK_SWAP": "SAME"},
                      "constant_values": {"CST_PK_DINAMIC": "0"}},
           "controlm": {"folder_name": "JACD-NY-BOXAC-9", "ControlmServer": "T2-SRV", "SiteStandard": "T2-SITE",
                        "OrderMethod": "Manual", "Host": "t2-acc-host", "FilePath": "/t2/scripts", "RunAs": "gmny",
                        "Application": "T2-ACC-APP", "MonthDaysCalendar": "NYCAL", "CreatedBy": "omit"},
           "renames": {"GMBOX0028D04": "GMBX1NY00D03"},
           "external_events": {"GMGB9999D01-OK": "DROP-REVIEW"},
           "mic": {"depos": {"eod_steps": "keep", "sender_type": "reference"},
                   "irs": {"eod_steps": "none", "sender_type": "none"}},
           "mbj": {"calendar": "83.4", "pk_call": "BOX_ACC.F_GetPK('{table}')", "auth_code": "4"},
           "readiness": {"mbj_engine": "not deployed"},
           "unix": {"etc_dir": "/t2/etc"}}
    for k, v in over.items():
        cfg[k] = v(cfg[k]) if callable(v) else v
    (run / "acc-jobs-inputs.json").write_text(json.dumps(cfg, indent=2))
    return run
