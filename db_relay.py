#!/usr/bin/env python3
r"""
db_relay.py - run an agent's read-only queries on the operator's machine and hand the CSVs back through git
[operator, 2026-10-28 - ADR 0021, PROPOSED: not used by any agent until the operator approves it].

The agent (in the cloud) cannot reach the bank's databases; the operator's PC can. The agent writes each query as a
file in a run folder and pushes it; this script, on the operator's PC, pulls, runs every new query READ-ONLY through
the PC's own SQL*Plus and pushes the CSV back. Nothing connects into the bank network; every query and result is in
the git history. **No package to install**: Python's standard library, git and SQL*Plus (12.2+, CSV output) only.

    python scripts/db_relay.py --save-passwords tier2-dev        # once: each account's password, checked, kept in
                                                                 #   Windows Credential Manager (never in git)
    python scripts/db_relay.py --check tier2-dev                 # smoke test: each account of the env
    python scripts/db_relay.py --once                            # run the pending requests of this checkout
    python scripts/db_relay.py --watch --branches "devin/*"      # every 10 s: a branch the agent pushed to ->
                                                                 #   pull, run, push the CSVs back (--review: ask first)
    python scripts/db_relay.py --forget tier2-dev                # remove the stored passwords

Run it in a clone of its own (e.g. C:\db-relay\cib-box-aukinbranch), never in the clone you work in: it checks out
the agent's branches and commits its results there. The agent side is scripts/relay_ask.py.

A request: `runs/**/relay/<NNN>-<name>.sql`, first line the header, then ONE statement:

    -- relay: env=tier2-dev system=BOX_ACC out=01-evidence/A-01-TGT.csv
    SELECT ...

`env` and `system` pick the account from docs/reference/db-routes.csv (never the agent); `out` is relative to the run
folder (the parent of relay/) and must be a .csv under 01-evidence/. Done when `<NNN>-<name>.log.json` exists (status
ok / refused / error, rows, truncated, seconds, the SQL's sha256) - delete the log to run it again.

Read-only, enforced here (check_sql), not trusted to the agent: one statement, SELECT or WITH only; no DML / DDL /
PL/SQL / FOR UPDATE / INTO / database link; no function but the SQL built-ins listed (a package function can write
even inside a SELECT); no unsubstituted `&` value; forbidden tables refused. Every SQL*Plus session: SET TRANSACTION
READ ONLY before the query, ROLLBACK after, exit on the first error; a row cap and a time limit. Only the
environments with relay_allowed=yes.

Passwords: from Windows Credential Manager when saved there (--save-passwords: asked, checked against the database,
then stored as generic credentials "box-db-relay:<alias>:<account>", encrypted with the Windows login - visible and
removable in Control Panel > Credential Manager), else asked once per session and kept in memory. Never in the repo, a
file, a log, git, the chat or the SQL*Plus command line (sent on its standard input). A rejected password (ORA-01017)
is dropped from memory and from the store, and asked again. Numbers exact (NUMWIDTH 40, '.' decimal),
dates ISO, UTF-8 (NLS_LANG set for the session). Exit: 0 done · 1 a request refused or failed · 2 bad invocation.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import getpass
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROUTES = ROOT / "docs/reference/db-routes.csv"
HEADER = re.compile(r"^--\s*relay:\s*(.*)$")
MAX_ROWS = 50000
TIMEOUT_S = 300
FORBIDDEN_TABLES = {"T_PGT_USAENTPROP_S"}                       # never read (operator, hard rule of the ACC agent)
FORBIDDEN_WORDS = {"INSERT", "UPDATE", "DELETE", "MERGE", "CREATE", "ALTER", "DROP", "TRUNCATE", "GRANT", "REVOKE",
                   "BEGIN", "DECLARE", "EXEC", "EXECUTE", "CALL", "COMMIT", "ROLLBACK", "SAVEPOINT", "LOCK", "INTO",
                   "RENAME", "AUDIT", "PURGE", "FLASHBACK", "ANALYZE"}
KEYWORDS = {"SELECT", "WITH", "FROM", "WHERE", "JOIN", "ON", "AND", "OR", "NOT", "IN", "EXISTS", "AS", "OVER",
            "PARTITION", "BY", "ORDER", "GROUP", "WITHIN", "HAVING", "UNION", "ALL", "MINUS", "INTERSECT", "ANY",
            "SOME", "THEN", "ELSE", "WHEN", "CASE", "IS", "LIKE", "BETWEEN", "KEEP", "VALUES", "USING", "DISTINCT",
            "LEFT", "RIGHT", "INNER", "OUTER", "FULL", "CROSS", "NULL", "END", "ROWS", "RANGE", "PRECEDING", "FOLLOWING"}
BUILTINS = {"COUNT", "SUM", "MIN", "MAX", "AVG", "NVL", "NVL2", "COALESCE", "NULLIF", "DECODE", "TO_CHAR", "TO_DATE",
            "TO_NUMBER", "TO_TIMESTAMP", "CAST", "TRUNC", "ROUND", "UPPER", "LOWER", "INITCAP", "TRIM", "LTRIM", "RTRIM",
            "LPAD", "RPAD", "SUBSTR", "INSTR", "LENGTH", "REPLACE", "CONCAT", "ABS", "MOD", "SIGN", "FLOOR", "CEIL",
            "GREATEST", "LEAST", "ADD_MONTHS", "MONTHS_BETWEEN", "LAST_DAY", "EXTRACT", "REGEXP_LIKE", "REGEXP_SUBSTR",
            "REGEXP_REPLACE", "REGEXP_INSTR", "REGEXP_COUNT", "ORA_HASH", "STANDARD_HASH", "ROW_NUMBER", "RANK",
            "DENSE_RANK", "LAG", "LEAD", "FIRST_VALUE", "LAST_VALUE", "LISTAGG", "STDDEV", "VARIANCE", "MEDIAN", "CHR",
            "ASCII", "NUMTODSINTERVAL",
            "VARCHAR2", "NVARCHAR2", "CHAR", "NCHAR", "NUMBER", "RAW", "TIMESTAMP", "FLOAT"}   # types: CAST(x AS VARCHAR2(n))


# --- the guard ------------------------------------------------------------------------------------------------------
class Result:
    """Refusals, each "<message> [<code>]" - the codes are the ones skill run-db-queries lists."""

    def __init__(self):
        self.errors: list[str] = []

    def err(self, code: str, where: str, msg: str):
        self.errors.append(f"{where + ': ' if where else ''}{msg} [{code}]")


def _strip(sql: str) -> str:
    """The SQL with comments removed and string literals emptied ('...' -> '')."""
    out, i, n = [], 0, len(sql)
    while i < n:
        if sql.startswith("--", i):
            j = sql.find("\n", i)
            i = n if j < 0 else j
        elif sql.startswith("/*", i):
            j = sql.find("*/", i + 2)
            i = n if j < 0 else j + 2
            out.append(" ")
        elif sql[i] == "'":
            j = i + 1
            while j < n:
                if sql[j] == "'" and j + 1 < n and sql[j + 1] == "'":
                    j += 2
                elif sql[j] == "'":
                    break
                else:
                    j += 1
            out.append("''")
            i = j + 1
        else:
            out.append(sql[i])
            i += 1
    return "".join(out)


def check_sql(sql: str) -> list[str]:
    """Why this statement may not run read-only through the relay ([] = it may)."""
    res = Result()
    s = _strip(sql)
    if "&" in s:
        res.err("sql-unsubstituted", "", "an unsubstituted & value - the agent fills every value before the request")
    parts = [p for p in s.split(";") if p.strip()]
    if len(parts) != 1:
        res.err("sql-statements", "", f"{len(parts)} statements - one per request")
    body = parts[0] if parts else ""
    first = re.match(r"\s*\(*\s*([A-Za-z]+)", body)
    if not first or first.group(1).upper() not in ("SELECT", "WITH"):
        res.err("sql-not-select", "", "not a SELECT / WITH")
    up = body.upper()
    for w in sorted(FORBIDDEN_WORDS):
        if re.search(rf"(?<![\w$#]){w}(?![\w$#])", up):
            res.err("sql-forbidden-word", "", f"forbidden word {w}")
    if "@" in body:
        res.err("sql-db-link", "", "a database link (@)")
    for name in re.findall(r"([A-Za-z_][\w$#]*(?:\s*\.\s*[A-Za-z_][\w$#]*)*)\s*\((?!\s*\+\s*\))", body):
        nm = re.sub(r"\s+", "", name).upper()
        if "." in nm:
            res.err("sql-package-call", "", f"a call to {nm}() - packages / schema functions may write; not run by "
                    "the relay")
        elif nm not in KEYWORDS and nm not in BUILTINS:
            res.err("sql-unknown-function", "", f"function {nm}() not in the relay's built-ins")
    for t in FORBIDDEN_TABLES:
        if re.search(rf"(?<![\w$#]){t}(?![\w$#])", up):
            res.err("sql-forbidden-table", "", f"forbidden table {t}")
    return sorted(set(res.errors))


# --- routes, requests -----------------------------------------------------------------------------------------------
def load_routes(path: Path = ROUTES) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        return [r for r in csv.DictReader(f) if (r.get("env") or "").strip() and not r["env"].startswith("#")]


def route_for(routes: list[dict], env: str, system: str):
    return next((r for r in routes if r["env"] == env and r["system"].upper() == system.upper()), None)


def parse_request(path: Path):
    text = path.read_text(encoding="utf-8")
    first, _, sql = text.partition("\n")
    m = HEADER.match(first.strip())
    if not m:
        return None, text, "no '-- relay: env=... system=... out=...' header on the first line"
    hdr = dict(kv.split("=", 1) for kv in m.group(1).split() if "=" in kv)
    miss = [k for k in ("env", "system", "out") if not hdr.get(k)]
    return hdr, sql, (f"header without {', '.join(miss)}" if miss else None)


def out_path(req: Path, out: str):
    run = req.parent.parent
    p = (run / out).resolve()
    ok = p.suffix == ".csv" and (run / "01-evidence").resolve() in p.parents and ".." not in Path(out).parts
    return p if ok else None


def pending(root: Path) -> list[Path]:
    return sorted(p for p in root.glob("runs/**/relay/*.sql") if not p.with_suffix(".log.json").exists())


# --- passwords: Windows Credential Manager (standard library only), else memory -------------------------------------
CRED_PREFIX = "box-db-relay"


class WinCredStore:
    """Generic credentials of the Windows Credential Manager, through advapi32 (ctypes - nothing to install)."""

    def __init__(self):
        import ctypes
        from ctypes import wintypes

        class CREDENTIAL(ctypes.Structure):
            _fields_ = [("Flags", wintypes.DWORD), ("Type", wintypes.DWORD), ("TargetName", wintypes.LPWSTR),
                        ("Comment", wintypes.LPWSTR), ("LastWritten", wintypes.FILETIME),
                        ("CredentialBlobSize", wintypes.DWORD), ("CredentialBlob", ctypes.POINTER(ctypes.c_char)),
                        ("Persist", wintypes.DWORD), ("AttributeCount", wintypes.DWORD),
                        ("Attributes", ctypes.c_void_p), ("TargetAlias", wintypes.LPWSTR),
                        ("UserName", wintypes.LPWSTR)]

        self.ct, self.CREDENTIAL = ctypes, CREDENTIAL
        self.api = ctypes.WinDLL("advapi32", use_last_error=True)

    def read(self, target: str):
        ct = self.ct
        p = ct.POINTER(self.CREDENTIAL)()
        if not self.api.CredReadW(target, 1, 0, ct.byref(p)):          # 1 = CRED_TYPE_GENERIC
            return None
        try:
            c = p.contents
            return ct.string_at(c.CredentialBlob, c.CredentialBlobSize).decode("utf-16-le")
        finally:
            self.api.CredFree(p)

    def write(self, target: str, user: str, pw: str):
        ct = self.ct
        blob = pw.encode("utf-16-le")
        buf = ct.create_string_buffer(blob, len(blob))
        c = self.CREDENTIAL(Type=1, TargetName=target, UserName=user, CredentialBlobSize=len(blob),
                            CredentialBlob=ct.cast(buf, ct.POINTER(ct.c_char)), Persist=2)   # 2 = this machine
        if not self.api.CredWriteW(ct.byref(c), 0):
            raise OSError(f"Credential Manager refused to store {target}")

    def delete(self, target: str):
        self.api.CredDeleteW(target, 1, 0)


def default_store():
    if sys.platform != "win32":
        return None
    try:
        return WinCredStore()
    except (OSError, AttributeError):
        return None


class Session:
    """The passwords of this run: memory, then the store (if any), then asked."""

    def __init__(self, ask=getpass.getpass, store=None):
        self.ask, self.store, self._pw = ask, store, {}

    @staticmethod
    def target(route: dict) -> str:
        return f"{CRED_PREFIX}:{route['alias']}:{route['account']}"

    def password(self, route: dict) -> str:
        key = self.target(route)
        if key not in self._pw:
            pw = self.store.read(key) if self.store else None
            self._pw[key] = pw or self.ask(f"Password for {route['account']}@{route['alias']} "
                                           f"({'not saved yet' if self.store else 'memory only, this session'}): ")
        return self._pw[key]

    def forget(self, route: dict):
        self._pw.pop(self.target(route), None)
        if self.store:
            self.store.delete(self.target(route))

    def save(self, route: dict):
        if self.store and self.target(route) in self._pw:
            self.store.write(self.target(route), route["account"], self._pw[self.target(route)])


def descriptor(route: dict) -> str:
    target = f"(SID={route['sid']})" if route.get("sid") else f"(SERVICE_NAME={route['service_name']})"
    return f"(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST={route['host']})(PORT={route['port']}))(CONNECT_DATA={target}))"


def sqlplus_stdin(route: dict, pw: str, script: Path) -> str:
    """SQL*Plus's standard input: exit on any error, connect (the password never on the command line), run the script."""
    return "\n".join(["WHENEVER OSERROR EXIT 9", "WHENEVER SQLERROR EXIT FAILURE ROLLBACK", "SET ECHO OFF",
                      f'CONNECT {route["account"]}/"{pw}"@{descriptor(route)}', f'@"{script}"', "EXIT 0", ""])


def query_script(sql: str, spool: Path) -> str:
    """The script file (no password): '.' decimal, read-only transaction, the query spooled as CSV, rollback. TERMOUT
    OFF - the rows go to the spool only, so a value that looks like an error message is never read as one."""
    return "\n".join([
        "SET TERMOUT OFF", "SET VERIFY OFF", "SET DEFINE OFF", "SET SQLBLANKLINES ON", "SET FEEDBACK OFF",
        "ALTER SESSION SET NLS_NUMERIC_CHARACTERS = '.,';",
        "ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS';",
        "SET TRANSACTION READ ONLY;",
        "SET MARKUP CSV ON QUOTE ON", "SET HEADING ON", "SET PAGESIZE 50000", "SET NUMWIDTH 40", "SET LONG 1000000",
        "SET LINESIZE 32767", "SET TRIMSPOOL ON",
        f'SPOOL "{spool}"', sql, "/", "SPOOL OFF",
        "ROLLBACK;", "EXIT 0", ""])


ERR_LINE = re.compile(r"\s*(ORA|SP2|TNS)-\d+")


def run_sqlplus(route: dict, pw: str, sql: str, spool: Path, timeout_s: int, sqlplus: str = "sqlplus"):
    """Run one query; the CSV lands in spool. Returns None (ok) or the error line (never the password)."""
    if '"' in pw:
        return 'a password containing " cannot be passed to SQL*Plus - not run'
    script = spool.with_suffix(".sql")
    script.write_text(query_script(sql, spool), encoding="utf-8")
    env = dict(os.environ, NLS_LANG="AMERICAN_AMERICA.AL32UTF8", NLS_DATE_FORMAT="YYYY-MM-DD HH24:MI:SS")
    try:
        cp = subprocess.run([sqlplus, "-S", "-L", "/nolog"], input=sqlplus_stdin(route, pw, script), text=True,
                            capture_output=True, timeout=timeout_s, env=env, encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return f"SQL*Plus not found ({sqlplus}) - --sqlplus <path>"
    except subprocess.TimeoutExpired:
        return f"time limit ({timeout_s} s) reached - the query was stopped"
    finally:
        script.unlink(missing_ok=True)
    said = [ln.strip() for ln in ((cp.stdout or "") + "\n" + (cp.stderr or "")).splitlines() if ERR_LINE.match(ln)]
    spooled = spool.read_text(encoding="utf-8", errors="replace").splitlines() if spool.exists() else []
    first = next((ln for ln in spooled if ln.strip()), "")
    if cp.returncode != 0 or said or ERR_LINE.match(first):
        in_spool = [ln.strip() for ln in spooled if ERR_LINE.match(ln)]
        msg = (said or in_spool[-1:] or [f"SQL*Plus exit {cp.returncode}"])[0]
        spool.unlink(missing_ok=True)
        return msg.replace(pw, "***") if pw else msg
    return None


def read_spool(spool: Path) -> list[list[str]]:
    """SQL*Plus's CSV: blank lines and repeated headings dropped."""
    if not spool.exists():
        return []
    rows = [r for r in csv.reader(spool.read_text(encoding="utf-8", errors="replace").splitlines()) if any(c.strip() for c in r)]
    return [rows[0]] + [r for r in rows[1:] if r != rows[0]] if rows else []


# --- one request ----------------------------------------------------------------------------------------------------
def run_request(req: Path, routes: list[dict], runner, session: Session, review=None,
                max_rows: int = MAX_ROWS, timeout_s: int = TIMEOUT_S) -> dict:
    log = {"request": req.name, "at": datetime.datetime.now().isoformat(timespec="seconds")}
    hdr, sql, err = parse_request(req)
    res = Result()
    if err:
        res.err("request-header", "", err)
    route = None
    if hdr:
        route = route_for(routes, hdr["env"], hdr["system"])
        if not route:
            res.err("route-unknown", "", f"no route for env {hdr['env']} system {hdr['system']} in db-routes.csv")
        elif (route.get("relay_allowed") or "").lower() != "yes":
            res.err("env-not-allowed", "", f"env {hdr['env']} not allowed for the relay (relay_allowed)")
        if out_path(req, hdr["out"]) is None:
            res.err("out-outside-evidence", "", f"out {hdr['out']!r} is not a .csv under the run's 01-evidence/")
    probs = res.errors + check_sql(sql)
    sql_run = sql.strip().rstrip(";").strip()
    log["sql_sha256"] = hashlib.sha256(sql_run.encode()).hexdigest()
    if hdr:
        log.update(env=hdr["env"], system=hdr["system"], out=hdr["out"])
    if route:
        log["account"] = route["account"]
    if probs:
        log.update(status="refused", problems=probs)
        return log
    if review and not review(req, hdr, route, sql_run):
        res.err("review-declined", "", "declined by the operator (review)")
        log.update(status="refused", problems=res.errors)
        return log
    t0 = time.time()
    dest = out_path(req, hdr["out"])
    with tempfile.TemporaryDirectory() as td:
        spool = Path(td) / "result.csv"
        error = runner(route, session.password(route), sql_run, spool, timeout_s)
        if error:
            if re.search(r"ORA-01017|ORA-01005", error):       # wrong password: dropped, asked again next time
                session.forget(route)
            log.update(status="error", error=error[:300])
        else:
            rows = read_spool(spool)
            truncated = len(rows) - 1 > max_rows
            rows = rows[: max_rows + 1]
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open("w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerows(rows)
            log.update(status="ok", rows=max(len(rows) - 1, 0), truncated=truncated, columns=len(rows[0]) if rows else 0)
            if not rows:
                log["note"] = "no rows (SQL*Plus writes no heading for an empty result)"
    log["seconds"] = round(time.time() - t0, 2)
    return log


def process(root: Path, routes: list[dict], runner, session, **kw) -> list[tuple[Path, dict]]:
    done = []
    for req in pending(root):
        log = run_request(req, routes, runner, session, **kw)
        req.with_suffix(".log.json").write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")
        print(f"{log['status']:8} {req.relative_to(root)}  {log.get('rows', '')} {'; '.join(log.get('problems', [])) or log.get('error', '')}")
        done.append((req, log))
    return done


# --- git ------------------------------------------------------------------------------------------------------------
def git(*args, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def git_cycle(root: Path, branch: str, routes, runner, session, **kw) -> int:
    top = Path(git("rev-parse", "--show-toplevel", cwd=root).stdout.strip() or root)
    if git("status", "--porcelain", "--untracked-files=no", cwd=top).stdout.strip():
        print("REFUSED: tracked files changed in this checkout - the relay commits only its own results", file=sys.stderr)
        return 2
    git("fetch", "origin", branch, cwd=top)                   # a branch the agent just created is known locally
    if git("checkout", branch, cwd=top).returncode or git("pull", "--rebase", "origin", branch, cwd=top).returncode:
        print(f"REFUSED: cannot check out / pull {branch}", file=sys.stderr)
        return 2
    done = process(root, routes, runner, session, **kw)
    if not done:
        return 0
    paths = []
    for req, log in done:
        paths.append(req.with_suffix(".log.json"))
        if log["status"] == "ok":
            paths.append(out_path(req, log["out"]))
    git("add", *[str(p) for p in paths], cwd=top)
    git("commit", "-m", f"db-relay: {len(done)} request(s) - "
        + ", ".join(f"{r.stem} {lg['status']}" for r, lg in done[:5]), cwd=top)
    for _ in range(3):
        if git("push", "origin", f"HEAD:{branch}", cwd=top).returncode == 0:
            return 1 if any(lg["status"] != "ok" for _, lg in done) else 0
        git("pull", "--rebase", "origin", branch, cwd=top)
    print("REFUSED: push failed 3 times", file=sys.stderr)
    return 2



def remote_heads(top: Path, patterns: list[str]) -> dict:
    """{branch: sha} on origin for the branch names / patterns given - one cheap call, nothing pulled."""
    out = git("ls-remote", "--heads", "origin", *[f"refs/heads/{p}" for p in patterns], cwd=top).stdout
    return {ln.split("\t")[1].removeprefix("refs/heads/"): ln.split("\t")[0] for ln in out.splitlines() if "\t" in ln}


def watch_once(root: Path, patterns: list[str], seen: dict, routes, runner, session, **kw) -> int:
    """One look at origin: every watched branch that moved since the last look is pulled and its requests run."""
    top = Path(git("rev-parse", "--show-toplevel", cwd=root).stdout.strip() or root)
    rc = 0
    for branch, sha in sorted(remote_heads(top, patterns).items()):
        if seen.get(branch) == sha:
            continue
        r = git_cycle(root, branch, routes, runner, session, **kw)
        if r == 2:
            return 2
        rc = max(rc, r)
        seen[branch] = remote_heads(top, [branch]).get(branch, sha)    # our own push is not a new request
    return rc


# --- smoke test -----------------------------------------------------------------------------------------------------
def check_env(env: str, routes, runner, session: Session, save: bool = False) -> int:
    rows = [r for r in routes if r["env"] == env]
    if not rows:
        print(f"no route for {env}", file=sys.stderr)
        return 2
    bad = 0
    for r in rows:
        with tempfile.TemporaryDirectory() as td:
            spool = Path(td) / "check.csv"
            err = runner(r, session.password(r), "SELECT USER AS db_user, SYS_CONTEXT('USERENV', 'DB_NAME') AS db_name "
                         "FROM DUAL", spool, 60)
            got = read_spool(spool)
        if err or len(got) < 2:
            bad += 1
            if err and re.search(r"ORA-01017|ORA-01005", err):
                session.forget(r)
            print(f"FAILED {r['system']:8} {r['account']:10} {err or 'no row'}")
        else:
            if save:
                session.save(r)
            print(f"OK     {r['system']:8} {r['account']:10} connected as {got[1][0]} to {got[1][1]} (read-only transaction)"
                  + (" - password saved in Credential Manager" if save and session.store else ""))
    return 1 if bad else 0


def ask_review(req, hdr, route, sql) -> bool:
    print(f"\n--- {req}\n    env {hdr['env']} · system {hdr['system']} · account {route['account']} · out {hdr['out']}\n{sql}\n")
    return input("Run it read-only? [y/N] ").strip().lower() == "y"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--save-passwords", metavar="ENV", help="ask each account's password, check it, keep it in Windows "
                   "Credential Manager")
    g.add_argument("--check", metavar="ENV", help="each account of ENV: SELECT USER (read-only)")
    g.add_argument("--once", action="store_true", help="run the pending requests of this checkout (no git)")
    g.add_argument("--watch", action="store_true", help="loop: a watched branch moved -> pull, run, push the results")
    g.add_argument("--forget", metavar="ENV", help="remove the stored passwords of ENV")
    ap.add_argument("--branches", nargs="+", metavar="BRANCH", help="branch names or patterns to watch, e.g. \"devin/*\"")
    ap.add_argument("--branch", help=argparse.SUPPRESS)                       # one branch (same as --branches B)
    ap.add_argument("--interval", type=int, default=10, help="seconds between two looks at origin (default 10)")
    ap.add_argument("--review", action="store_true", help="show each request and ask before running it")
    ap.add_argument("--sqlplus", default="sqlplus", help="SQL*Plus executable (default: the one on PATH)")
    ap.add_argument("--max-rows", type=int, default=MAX_ROWS)
    ap.add_argument("--timeout", type=int, default=TIMEOUT_S, help="seconds per query")
    ap.add_argument("--routes", default=str(ROUTES))
    ap.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    routes = load_routes(Path(a.routes))
    root, session = Path(a.root), Session(store=default_store())

    def runner(route, pw, sql, spool, timeout_s):
        return run_sqlplus(route, pw, sql, spool, timeout_s, a.sqlplus)

    kw = {"review": ask_review if a.review else None, "max_rows": a.max_rows, "timeout_s": a.timeout}
    if a.save_passwords:
        if not session.store:
            print("Windows Credential Manager not available here - passwords stay in memory, per session", file=sys.stderr)
            return 2
        return check_env(a.save_passwords, routes, runner, session, save=True)
    if a.forget:
        for r in (r for r in routes if r["env"] == a.forget):
            session.forget(r)
            print(f"forgotten {Session.target(r)}")
        return 0
    if a.check:
        return check_env(a.check, routes, runner, session)
    if a.once:
        return 1 if any(lg["status"] != "ok" for _, lg in process(root, routes, runner, session, **kw)) else 0
    patterns = a.branches or ([a.branch] if a.branch else None)
    if not patterns:
        ap.error('--watch needs --branches, e.g. --branches "devin/*"')
    print(f"watching {', '.join(patterns)} every {a.interval} s - Ctrl+C to stop")
    seen: dict = {}
    try:
        while True:
            if watch_once(root, patterns, seen, routes, runner, session, **kw) == 2:
                return 2
            time.sleep(a.interval)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
