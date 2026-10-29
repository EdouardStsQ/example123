#!/usr/bin/env python3
"""Tests of scripts/db_relay.py - the guard, one request against a fake database, the git round trip.
No database and no network needed. Run: python3 scripts/tests/test_db_relay.py"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import db_relay as dr

FAILS = []


def report(ok, what, detail=""):
    print(("✓ " if ok else "✗ ") + what)
    if not ok:
        FAILS.append(what)
        if detail:
            print("    " + str(detail)[:600])


def fake_runner(rows, calls, error=None):
    """Stands for run_sqlplus: writes SQL*Plus-like CSV (quoted, a blank line, a repeated heading) to the spool."""
    def run(route, pw, sql, spool, timeout_s):
        calls.append((route["account"], pw, sql, timeout_s))
        if error:
            return error
        lines = ['"PK","CODE","D"'] + [",".join(f'"{c}"' if isinstance(c, str) else str(c) for c in r) for r in rows]
        if len(lines) > 3:
            lines.insert(3, "")
            lines.insert(4, '"PK","CODE","D"')
        spool.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return None
    return run


FAKE_SQLPLUS = r"""#!/usr/bin/env python3
import os, re, sys
stdin = sys.stdin.read()
script = open(re.search(r'@"([^"]+)"', stdin).group(1)).read()
open(os.environ["FAKE_LOG"], "w").write(stdin + "\n#SCRIPT\n" + script + "\n#ARGV " + " ".join(sys.argv[1:])
                                     + "\n#NLS " + os.environ.get("NLS_LANG", ""))
mode = os.environ.get("FAKE_MODE", "ok")
if mode == "badpw":
    print("ERROR:\nORA-01017: invalid username/password; logon denied")
    sys.exit(1)
spool = re.search(r'SPOOL "([^"]+)"', script).group(1)
if mode == "ora":
    open(spool, "w").write("SELECT a FROM missing\n*\nERROR at line 1:\nORA-00942: table or view does not exist\n")
    sys.exit(1)
if mode == "notconnected":
    open(spool, "w").write("SP2-0640: Not connected\n")
    sys.exit(0)
open(spool, "w").write('"PK","CODE"\n2485.35,"FXCONTROL"\n23205549.44,"A,B"\n2,"ORA-00001 in a value"\n')
"""
def run_folder(tmp: Path) -> Path:
    run = tmp / "runs/NY_SCH/tier2-dev/acc-configs/gap_20261028_1"
    (run / "relay").mkdir(parents=True)
    (run / "01-evidence").mkdir()
    return run


ROUTES = [{"env": "tier2-dev", "alias": "DGBOUS", "host": "h", "port": "1528", "sid": "dgbous", "service_name": "",
           "relay_allowed": "yes", "system": "BOX_ACC", "account": "box_acc"},
          {"env": "tier1-prod", "alias": "PROD", "host": "h", "port": "1521", "sid": "p", "service_name": "",
           "relay_allowed": "no", "system": "BOX_ACC", "account": "box_acc"}]


def main() -> int:
    # --- the guard
    ok_sql = ["SELECT COUNT(*) AS n FROM BOX_ACC.T_BOX_ACCT_PORT_PROP_S WHERE FK_OWNER_OBJ = 35000170.65",
              "WITH x AS (SELECT 1 AS a FROM dual) SELECT a FROM x",
              "SELECT T1.PK FROM A T1, B T2 WHERE T1.FK = T2.PK(+)",
              "SELECT 'DELETE; UPDATE' AS txt FROM dual -- DROP TABLE x;",
              "SELECT CASE WHEN c IN (1, 2) THEN 'H' || ORA_HASH(v) END AS h FROM t",
              "SELECT CAST(NULL AS VARCHAR2(128)) AS x FROM dual;"]
    bad_sql = {"UPDATE t SET a = 1": "UPDATE", "DELETE FROM t": "DELETE", "INSERT INTO t VALUES (1)": "INSERT",
               "SELECT * FROM t FOR UPDATE": "UPDATE", "SELECT a INTO b FROM t": "INTO",
               "BEGIN NULL; END;": "SELECT", "SELECT 1 FROM dual; SELECT 2 FROM dual": "statements",
               "SELECT PKG_X.F_WRITE(1) FROM dual": "PKG_X.F_WRITE", "SELECT MYFUNC(1) FROM dual": "MYFUNC",
               "SELECT * FROM t@remote": "@", "SELECT * FROM t WHERE PK = &&PK": "&",
               "SELECT * FROM PGT_SYS.T_PGT_USAENTPROP_S": "T_PGT_USAENTPROP_S",
               "MERGE INTO t USING s ON (1=1) WHEN MATCHED THEN UPDATE SET a=1": "SELECT"}
    report(all(not dr.check_sql(s) for s in ok_sql), "guard: SELECT / WITH, outer join (+), words inside strings and "
           "comments, built-ins and CAST types pass", [(s, dr.check_sql(s)) for s in ok_sql if dr.check_sql(s)])
    miss = {s: dr.check_sql(s) for s, w in bad_sql.items() if not any(w in p for p in dr.check_sql(s))}
    report(not miss, "guard refuses: DML, FOR UPDATE, SELECT INTO, PL/SQL, two statements, package / unknown "
           "functions, database link, unsubstituted &, forbidden table, MERGE", miss)
    # every catalogue query of the ACC configs agent passes once its values are filled in
    doc = (ROOT / "docs/reference/queries/acc-config-mining.md").read_text()
    stmts = [s for b in re.findall(r"```sql\n(.*?)```", doc, re.DOTALL) for s in re.split(r";\s*(?:--[^\n]*)?\n", b)
             if dr._strip(s).strip()]
    refused = [(dr._strip(s).strip()[:80], dr.check_sql(re.sub(r"&&\w+", "1", s))) for s in stmts
               if dr.check_sql(re.sub(r"&&\w+", "1", s))]
    report(len(stmts) > 50 and not refused, f"guard: every ACC configs catalogue query passes ({len(stmts)})", refused)

    # --- one request against a fake database
    tmp = Path(tempfile.mkdtemp())
    run = run_folder(tmp)
    req = run / "relay/001-a01.sql"
    req.write_text("-- relay: env=tier2-dev system=BOX_ACC out=01-evidence/A-01-TGT.csv\n"
                   "SELECT PK, CODE, D FROM BOX_ACC.T_BOX_ACCT_TOPICS_S;\n")
    calls, asked = [], []

    def ask(prompt):
        asked.append(prompt)
        return "s3cret-pw"

    sess = dr.Session(ask)
    rows3 = [(2485.35, "FXCONTROL", ""), (20111.4, "X,Y", ""), (23205549.44, "NIVELNET", "")]
    done = dr.process(tmp, ROUTES, fake_runner(rows3, calls), sess)
    log = json.loads(req.with_suffix(".log.json").read_text())
    out = (run / "01-evidence/A-01-TGT.csv").read_text() if (run / "01-evidence/A-01-TGT.csv").exists() else ""
    report(log["status"] == "ok" and log["rows"] == 3 and out.splitlines()[0] == "PK,CODE,D" and "2485.35" in out
           and "23205549.44" in out and '"X,Y"' in out and len(out.splitlines()) == 4 and len(done) == 1
           and calls[0][2].startswith("SELECT PK, CODE, D") and not calls[0][2].endswith(";"),
           "relay: the query handed to SQL*Plus without its ';'; the CSV in 01-evidence (blank lines and repeated "
           "headings dropped, exact numbers); the log says ok", (log, out))
    everything = json.dumps(log) + out + req.with_suffix(".log.json").read_text()
    report(calls[0][:2] == ("box_acc", "s3cret-pw") and len(asked) == 1 and "s3cret-pw" not in everything,
           "relay: the account comes from db-routes.csv (env + system); the password is asked once, used, never "
           "written", asked)
    report(dr.pending(tmp) == [], "relay: a request with a log is done (not run again)")

    # refusals never connect
    cases = {"002-prod.sql": ("-- relay: env=tier1-prod system=BOX_ACC out=01-evidence/x.csv\nSELECT 1 FROM dual\n",
                              "not allowed"),
             "003-escape.sql": ("-- relay: env=tier2-dev system=BOX_ACC out=../../x.csv\nSELECT 1 FROM dual\n", "01-evidence"),
             "004-dml.sql": ("-- relay: env=tier2-dev system=BOX_ACC out=01-evidence/y.csv\nDELETE FROM t\n", "DELETE"),
             "005-nohdr.sql": ("SELECT 1 FROM dual\n", "header"),
             "006-system.sql": ("-- relay: env=tier2-dev system=GBO out=01-evidence/z.csv\nSELECT 1 FROM dual\n", "no route")}
    for n, (t, _) in cases.items():
        (run / "relay" / n).write_text(t)
    calls.clear()
    dr.process(tmp, ROUTES, fake_runner(rows3, calls), sess)
    logs = {n: json.loads((run / "relay" / n).with_suffix(".log.json").read_text()) for n in cases}
    wrong = {n: lg for n, (_, w) in cases.items() for lg in [logs[n]]
             if lg["status"] != "refused" or not any(w in p for p in lg["problems"])}
    report(not wrong and not calls, "relay refuses without connecting: an env not allowed (relay_allowed), an output "
           "outside 01-evidence, DML, no header, a system with no route", wrong)

    # a database error: logged, rolled back, closed, no CSV
    (run / "relay/007-err.sql").write_text("-- relay: env=tier2-dev system=BOX_ACC out=01-evidence/e.csv\n"
                                           "SELECT a FROM missing_table\n")
    dr.process(tmp, ROUTES, fake_runner([], [], error="ORA-00942: table or view does not exist"), sess)
    el = json.loads((run / "relay/007-err.log.json").read_text())
    report(el["status"] == "error" and "ORA-00942" in el["error"] and not (run / "01-evidence/e.csv").exists(),
           "relay: a database error is logged (ORA code), no CSV", el)

    # the row cap
    (run / "relay/008-cap.sql").write_text("-- relay: env=tier2-dev system=BOX_ACC out=01-evidence/cap.csv\n"
                                           "SELECT PK, CODE, D FROM t\n")
    dr.process(tmp, ROUTES, fake_runner([(i, "c", "") for i in range(25)], []), sess, max_rows=10)
    cl = json.loads((run / "relay/008-cap.log.json").read_text())
    report(cl["status"] == "ok" and cl["rows"] == 10 and cl["truncated"] is True
           and len((run / "01-evidence/cap.csv").read_text().splitlines()) == 11, "relay: the row cap - first N rows, "
           "truncated: true in the log", cl)

    # review mode: declined -> refused, never connected
    (run / "relay/009-review.sql").write_text("-- relay: env=tier2-dev system=BOX_ACC out=01-evidence/r.csv\n"
                                              "SELECT 1 AS one FROM dual\n")
    rc_ = []
    dr.process(tmp, ROUTES, fake_runner([], rc_), sess, review=lambda *a: False)
    rl = json.loads((run / "relay/009-review.log.json").read_text())
    report(rl["status"] == "refused" and "declined" in rl["problems"][0] and not rc_,
           "relay --review: a request the operator declines is not run", rl)

    # --- run_sqlplus against a fake SQL*Plus: what it is sent, how errors come back
    fk = Path(tempfile.mkdtemp())
    exe = fk / "sqlplus"
    exe.write_text(FAKE_SQLPLUS)
    exe.chmod(0o755)
    import os
    os.environ["FAKE_LOG"] = str(fk / "stdin.txt")
    route = dict(ROUTES[0], host="dgbous.nngg.corp", sid="dgbous")
    os.environ["FAKE_MODE"] = "ok"
    sp = fk / "r.csv"
    e1 = dr.run_sqlplus(route, "p4ss-w0rd", "SELECT PK, CODE FROM t", sp, 30, str(exe))
    sent = (fk / "stdin.txt").read_text()
    stdin_, script_ = sent.split("#SCRIPT")[0], sent.split("#SCRIPT")[1].split("#ARGV")[0]
    order = [script_.find(x) for x in ("SET TERMOUT OFF", "NLS_NUMERIC_CHARACTERS = '.,'", "SET TRANSACTION READ ONLY;",
                                       "SET MARKUP CSV ON", "SPOOL ", "SELECT PK, CODE FROM t\n/", "SPOOL OFF",
                                       "ROLLBACK;", "EXIT 0")]
    report(e1 is None and dr.read_spool(sp) == [["PK", "CODE"], ["2485.35", "FXCONTROL"], ["23205549.44", "A,B"],
                                                ["2", "ORA-00001 in a value"]]
           and all(o >= 0 for o in order) and order == sorted(order) and "(SID=dgbous)" in stdin_
           and "PORT=1528" in stdin_ and stdin_.index("WHENEVER SQLERROR EXIT") < stdin_.index("CONNECT box_acc/")
           < stdin_.index('@"') and "p4ss-w0rd" not in script_ and "p4ss-w0rd" not in sent.split("#ARGV")[1]
           and "#ARGV -S -L /nolog" in sent and "#NLS AMERICAN_AMERICA.AL32UTF8" in sent and "SET NUMWIDTH 40" in script_
           and not list(fk.glob("*.sql")),
           "run_sqlplus: SQL*Plus -S -L /nolog; stdin: exit on any error, connect (SID descriptor), @script; the script "
           "(no password, deleted after): TERMOUT OFF, '.' decimal, SET TRANSACTION READ ONLY, CSV spool, the query + "
           "'/', ROLLBACK, EXIT; a value looking like an error is data; the password never on the command line; NLS_LANG "
           "UTF-8", (e1, order, sent[-300:]))
    os.environ["FAKE_MODE"] = "badpw"
    e2 = dr.run_sqlplus(route, "p4ss-w0rd", "SELECT 1 FROM dual", fk / "b.csv", 30, str(exe))
    os.environ["FAKE_MODE"] = "ora"
    e3 = dr.run_sqlplus(route, "p4ss-w0rd", "SELECT 1 FROM dual", fk / "c.csv", 30, str(exe))
    os.environ["FAKE_MODE"] = "notconnected"
    e6 = dr.run_sqlplus(route, "p4ss-w0rd", "SELECT 1 FROM dual", fk / "f.csv", 30, str(exe))
    e4 = dr.run_sqlplus(route, 'with"quote', "SELECT 1 FROM dual", fk / "d.csv", 30, str(exe))
    e5 = dr.run_sqlplus(route, "x", "SELECT 1 FROM dual", fk / "e.csv", 30, str(fk / "no-such-sqlplus"))
    report(e2 and e2.startswith("ORA-01017") and e3 and e3.startswith("ORA-00942") and e6 and e6.startswith("SP2-0640")
           and e4 and "not run" in e4 and e5 and "not found" in e5 and not (fk / "c.csv").exists(),
           "run_sqlplus: a connect error (stdout), a query error (spool, exit 1) and 'not connected' (exit 0) returned as "
           "their line, no CSV; a password with a quote refused; SQL*Plus missing said", (e2, e3, e6, e4, e5))
    asked2 = []
    s2 = dr.Session(lambda p: asked2.append(p) or "pw")
    reqb = run / "relay/010-badpw.sql"
    reqb.write_text("-- relay: env=tier2-dev system=BOX_ACC out=01-evidence/bp.csv\nSELECT 1 AS one FROM dual\n")
    dr.process(tmp, ROUTES, fake_runner([], [], error="ORA-01017: invalid username/password; logon denied"), s2)
    s2.password(ROUTES[0])
    report(len(asked2) == 2, "relay: a rejected password (ORA-01017) is forgotten and asked again next time", asked2)

    # --- the git round trip: the agent pushes a request, the relay answers through the same branch
    g = Path(tempfile.mkdtemp())
    sh = lambda *a, cwd: subprocess.run(a, cwd=cwd, capture_output=True, text=True)
    sh("git", "init", "--bare", "-b", "main", str(g / "origin.git"), cwd=g)
    for who in ("agent", "relay"):
        sh("git", "clone", str(g / "origin.git"), who, cwd=g)
        sh("git", "config", "user.email", f"{who}@test", cwd=g / who)
        sh("git", "config", "user.name", who, cwd=g / who)
    ag, rl_ = g / "agent", g / "relay"
    (ag / "README.md").write_text("x\n")
    sh("git", "add", "-A", cwd=ag)
    sh("git", "commit", "-m", "init", cwd=ag)
    sh("git", "push", "origin", "HEAD:main", cwd=ag)
    sh("git", "checkout", "-b", "db-relay", cwd=ag)
    arun = run_folder(ag)
    (arun / "relay/001-g.sql").write_text("-- relay: env=tier2-dev system=BOX_ACC out=01-evidence/G.csv\n"
                                          "SELECT PK, CODE, D FROM t\n")
    (arun / "01-evidence/.keep").write_text("")
    sh("git", "add", "-A", cwd=ag)
    sh("git", "commit", "-m", "agent: request", cwd=ag)
    sh("git", "push", "origin", "db-relay", cwd=ag)
    # the relay's checkout has never seen the branch: git_cycle fetches it
    grc = dr.git_cycle(rl_, "db-relay", ROUTES, fake_runner([(1, "a", "")], []), sess)
    sh("git", "pull", "origin", "db-relay", cwd=ag)
    got = (arun / "01-evidence/G.csv").exists() and json.loads((arun / "relay/001-g.log.json").read_text())["status"] == "ok"
    msg = sh("git", "log", "-1", "--format=%s", cwd=ag).stdout
    report(grc == 0 and got and msg.startswith("db-relay:"), "git round trip: the agent pushes a request on its branch, "
           "the relay pulls, runs, commits the CSV + log and pushes; the agent pulls the result", (grc, got, msg))
    (rl_ / "README.md").write_text("changed by hand\n")
    report(dr.git_cycle(rl_, "db-relay", ROUTES, fake_runner([], []), sess) == 2,
           "git: a checkout with tracked files changed by hand is refused (the relay commits only its own results)")

    # --- passwords: the store (Windows Credential Manager on the operator's PC; a fake here)
    class FakeStore:
        def __init__(self):
            self.d = {}

        def read(self, k):
            return self.d.get(k)

        def write(self, k, user, pw):
            self.d[k] = pw

        def delete(self, k):
            self.d.pop(k, None)

    st, asked3 = FakeStore(), []
    st.d["box-db-relay:DGBOUS:box_acc"] = "from-store"
    s3 = dr.Session(lambda p: asked3.append(p) or "typed", store=st)
    got1 = s3.password(ROUTES[0])
    s3.forget(ROUTES[0])
    got2 = s3.password(ROUTES[0])
    report(got1 == "from-store" and len(asked3) == 1 and got2 == "typed"
           and "box-db-relay:DGBOUS:box_acc" not in st.d,
           "passwords: a stored one is used without asking; forgetting it (a rejected password) removes it from the store "
           "and asks again", (got1, got2, asked3, st.d))
    st2 = FakeStore()
    s4 = dr.Session(lambda p: "pw-ok", store=st2)
    rc_ok = dr.check_env("tier2-dev", ROUTES, fake_runner([("BOX_ACC", "DGBOUS", "")], []), s4, save=True)
    st3 = FakeStore()
    s5 = dr.Session(lambda p: "pw-bad", store=st3)
    rc_bad = dr.check_env("tier2-dev", ROUTES, fake_runner([], [], error="ORA-01017: invalid username/password"), s5,
                          save=True)
    report(rc_ok == 0 and st2.d == {"box-db-relay:DGBOUS:box_acc": "pw-ok"} and rc_bad == 1 and st3.d == {},
           "--save-passwords: a password is stored only after the database accepted it", (st2.d, st3.d))

    # --- the agent's side: relay_ask.py - checks before sending, then one push, then the answers
    import relay_ask as ra
    rcsv = Path(tempfile.mkdtemp()) / "routes.csv"
    rcsv.write_text("env,alias,host,port,sid,service_name,relay_allowed,system,account,note\n"
                    "tier2-dev,DGBOUS,h,1528,dgbous,,yes,BOX_ACC,box_acc,\n"
                    "tier2-dev,DGBOUS,h,1528,dgbous,,yes,GBO,pgtadmin,\n")
    rroutes = dr.load_routes(rcsv)
    qd = Path(tempfile.mkdtemp())
    (qd / "ok.sql").write_text("SELECT PK, CODE, D FROM BOX_ACC.T_BOX_ACCT_TOPICS_S;\n")
    (qd / "dml.sql").write_text("DELETE FROM BOX_ACC.T_BOX_ACCT_TOPICS_S\n")
    prun = run_folder(Path(tempfile.mkdtemp()))
    (prun / "01-evidence/EXISTS.csv").write_text("x\n")
    _, pp = ra.prepare(prun, "tier2-dev", [f"BOX_ACC:A1={qd / 'dml.sql'}", f"BOX_STC:A2={qd / 'ok.sql'}",
                                           f"BOX_ACC:EXISTS={qd / 'ok.sql'}", f"BOX_ACC:A3={qd / 'ok.sql'}",
                                           f"BOX_ACC:A3={qd / 'ok.sql'}", "nonsense"], rroutes)
    want = ["A1: forbidden word DELETE", "A2: no route", "EXISTS: 01-evidence/EXISTS.csv exists", "A3: twice",
            "expected SYSTEM:NAME=FILE"]
    report(all(any(w in p for p in pp) for w in want) and not list((prun / "relay").glob("*.sql")),
           "relay_ask refuses before sending (nothing written): DML, a system with no route, an evidence file already "
           "there, a name twice, a bad spec", pp)

    g2 = Path(tempfile.mkdtemp())
    sh("git", "init", "--bare", "-b", "main", str(g2 / "origin.git"), cwd=g2)
    for who in ("agent", "relay"):
        sh("git", "clone", str(g2 / "origin.git"), who, cwd=g2)
        sh("git", "config", "user.email", f"{who}@test", cwd=g2 / who)
        sh("git", "config", "user.name", who, cwd=g2 / who)
    ag2, rl2 = g2 / "agent", g2 / "relay"
    (ag2 / "README.md").write_text("x\n")
    sh("git", "add", "-A", cwd=ag2)
    sh("git", "commit", "-m", "init", cwd=ag2)
    sh("git", "push", "origin", "HEAD:main", cwd=ag2)
    sh("git", "checkout", "-b", "devin/123-acc-configs", cwd=ag2)
    arun2 = run_folder(ag2)
    (arun2 / "01-evidence/.keep").write_text("")
    sh("git", "add", "-A", cwd=ag2)
    sh("git", "commit", "-m", "run folder", cwd=ag2)
    sh("git", "push", "origin", "devin/123-acc-configs", cwd=ag2)
    (qd / "gbo.sql").write_text("SELECT PK, CODE, D FROM PGT_ACT.T_PGT_ACCT_PORT_PROP_S\n")
    ask_p = subprocess.Popen([sys.executable, str(ROOT / "scripts/relay_ask.py"), str(arun2), "--env", "tier2-dev",
                              "--routes", str(rcsv), "--poll", "1", "--timeout", "60",
                              f"BOX_ACC:A-01-TGT={qd / 'ok.sql'}", f"GBO:A-04d-GBO={qd / 'gbo.sql'}"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    seen, calls_w, t0 = {}, [], time.time()
    while ask_p.poll() is None and time.time() - t0 < 60:
        dr.watch_once(rl2, ["devin/*"], seen, rroutes, fake_runner([(1, "a", "")], calls_w), sess)
        time.sleep(0.5)
    aout, aerr = ask_p.communicate(timeout=30)
    report(ask_p.returncode == 0 and "ok       001-A-01-TGT: 1 rows" in aout and "ok       002-A-04d-GBO: 1 rows" in aout
           and sorted(c[0] for c in calls_w) == ["box_acc", "pgtadmin"] and (arun2 / "01-evidence/A-04d-GBO.csv").exists(),
           "relay_ask + relay --watch \"devin/*\": two queries in one push, each run with its system's account, both "
           "answers pulled by the agent (exit 0)", (ask_p.returncode, aout, aerr[-400:]))
    report(all(v for v in seen.values()) and dr.watch_once(rl2, ["devin/*"], seen, rroutes,
                                                           fake_runner([], calls_w), sess) == 0
           and len(calls_w) == 2, "relay --watch: a branch that has not moved is not pulled again (one cheap ls-remote)")
    to = subprocess.run([sys.executable, str(ROOT / "scripts/relay_ask.py"), str(arun2), "--env", "tier2-dev",
                         "--routes", str(rcsv), "--poll", "1", "--timeout", "3", f"BOX_ACC:A-99-TGT={qd / 'ok.sql'}"],
                        capture_output=True, text=True, check=False)
    report(to.returncode == 3 and "NO ANSWER" in to.stdout and "manual mode" in to.stdout,
           "relay_ask: no relay answering within the timeout -> exit 3, 'go on in manual mode'", to.stdout + to.stderr)

    print("\nFAILURES\n" + "\n".join(FAILS) if FAILS else "\nall passed")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
