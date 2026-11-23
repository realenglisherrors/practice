#!/usr/bin/env python3
"""Two-way sync between the Students board (claude.ai artifact) and the student site.

The board is the source of truth for: next class, student time zone and payments.
The site is the source of truth for: each student's private page and current homework.

Usage (Claude runs this when Bianca says "sync board"):
  1. Export the board:  ArtifactData list  url=<board>  collection=students  out_dir=<dir>
     and save the listed versions as <dir>/students/_versions.json  {"anton": 37, ...}
  2. python3 sync_board.py <dir>/students            -> shows what would change
     python3 sync_board.py <dir>/students --apply    -> writes private/students.json,
        runs build_site.py, and writes private/board_writes.json (an ArtifactData batch
        that puts the page + homework links on the board)
  3. Send private/board_writes.json as ArtifactData batch, then commit + push the site.
"""
import datetime, glob, hashlib, json, os, re, subprocess, sys, unicodedata

ROOT = os.path.dirname(os.path.abspath(__file__))
OFFSET = "-07:00"  # BC is on permanent UTC-7 (the board stores "your time" with no offset)


def norm(s):
    s = unicodedata.normalize("NFD", s)
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if not unicodedata.combining(c)).lower().replace("ı", "i"))


def fmt_day(d):
    return datetime.date.fromisoformat(d).strftime("%b %-d")


def payment_from_board(b):
    """Same rules as the 'push payments' workflow. None = the board has no payment info (leave the site alone)."""
    if b.get("payVia"):
        return {"status": "via", "via": b["payVia"]}
    paid = sorted({d for p in b.get("payments", []) for d in p.get("dates", [])})
    owed = sorted(set(b.get("owed", [])) - set(paid))
    thru = max([x for x in paid + [b.get("paidThrough", "")] if x], default="")
    if not (paid or owed or thru):
        return None
    if owed:
        n = len(owed)
        out = {"status": "due", "detail": f"{n} class{'es' if n != 1 else ''}: " + ", ".join(fmt_day(d) for d in owed)}
    else:
        out = {"status": "paid", "through": fmt_day(thru)}
    if paid or owed:
        out["paid_dates"], out["owed_dates"] = paid, owed
    # when each payment was made and how many classes it bought. Never an amount: the site shows classes, not prices.
    recs = [{"date": p["date"], "classes": p.get("classes") or len(p.get("dates", []))} for p in b.get("payments", []) if p.get("date")]
    if recs:
        out["payments"] = sorted(recs, key=lambda r: r["date"])
    return out


def backwards(old, new):
    """True when a 'paid through' date would move earlier (e.g. 'Nov 19' -> 'Nov 15')."""
    try:
        p = lambda x: datetime.datetime.strptime(x, "%b %d").replace(year=2000)
        return p(new) < p(old)
    except ValueError:
        return False


def unlock_hash(password, salt):
    """StatiCrypt 3 auto-decrypt hash (same as `npx staticrypt --share`)."""
    h = hashlib.pbkdf2_hmac("sha1", password.encode(), salt.encode(), 1000, 32).hex()
    h = hashlib.pbkdf2_hmac("sha256", h.encode(), salt.encode(), 14000, 32).hex()
    return hashlib.pbkdf2_hmac("sha256", h.encode(), salt.encode(), 585000, 32).hex()


def homework_passwords():
    """exercise name -> password, read from build.sh (and private/codes.txt when a student has a code)."""
    pw = {}
    for name, who in re.findall(r'^encrypt\s+"([^"]+)"\s+"([^"]+)"', open(f"{ROOT}/build.sh").read(), re.M):
        pw[name] = who
    codes = {}
    if os.path.exists(f"{ROOT}/private/codes.txt"):
        for line in open(f"{ROOT}/private/codes.txt"):
            if "=" in line:
                k, v = line.split("=", 1)
                codes[k.strip().lower()] = v.strip()
    return {n: codes.get(w.lower(), w) for n, w in pw.items()}


def main():
    src, apply = sys.argv[1], "--apply" in sys.argv
    vfile = f"{src}/_versions.json"
    versions = json.load(open(vfile)) if os.path.exists(vfile) else {}
    board = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(f"{src}/*.json") if not f.endswith("/_versions.json")}
    students = json.load(open(f"{ROOT}/private/students.json"))
    by_id = {s["id"]: s for s in students}

    # match each board record to a site record: remembered link first, then full name, then first name
    match = {}
    for bid, b in board.items():
        s = next((x for x in students if x.get("board") == bid), None)
        s = s or next((x for x in students if norm(x["name"]) == norm(b["name"])), None)
        s = s or next((x for x in students if norm(x["name"]) == norm(b["name"].split()[0])), None)
        if s:
            match[bid] = s
        else:
            print(f"  ! board student '{b['name']}' has no site page (skipped)")

    changes = []
    for bid, s in match.items():
        b = board[bid]
        targets = [s] + [by_id[m] for m in s.get("members", [])]  # a pair's data goes to both members too
        new = {"board": bid}
        if b.get("nextClass") and not s.get("calendar_sync"):  # students synced from Google Calendar keep the calendar time
            new["next_class"] = b["nextClass"] + ":00" + OFFSET
        if b.get("tz"):
            new["tz"] = b["tz"]
        pay = payment_from_board(b)
        old = s.get("payment") or {}
        if pay and pay.get("status") == old.get("status") == "paid" and "paid_dates" not in pay and backwards(old["through"], pay["through"]):
            print(f"  ! {s['name']}: board says paid through {pay['through']}, the page says {old['through']}: kept the page (fix the board)")
            pay = None
        if pay:
            new["payment"] = pay
        for t in targets:
            for k, v in new.items():
                if k == "board" and t is not s:
                    continue
                if t.get(k) != v:
                    changes.append((t["name"], k, t.get(k), v))
                    t[k] = v

    for name, k, old, v in changes:
        if k == "board":
            continue
        print(f"  {name}: {k}  {json.dumps(old, ensure_ascii=False)}  ->  {json.dumps(v, ensure_ascii=False)}")
    if not [c for c in changes if c[1] != "board"]:
        print("  site data already matches the board")
    if not apply:
        print("\n(dry run: add --apply to write)")
        return

    json.dump(students, open(f"{ROOT}/private/students.json", "w"), indent=2, ensure_ascii=False)
    open(f"{ROOT}/private/students.json", "a").write("\n")
    subprocess.run([sys.executable, f"{ROOT}/build_site.py"], check=True)

    # links for the board: private page + this week's homework (opens unlocked, the board is private to Bianca)
    links = json.load(open(f"{ROOT}/private/site_links.json"))
    salt = json.load(open(f"{ROOT}/.staticrypt.json"))["salt"]
    pws = homework_passwords()
    writes = []
    for bid, s in match.items():
        b, l = board[bid], links.get(s["id"], {})
        cur = dict(b.get("links") or {})
        want = dict(cur)
        if l.get("page"):
            want["page"] = l["page"]
        if l.get("hw"):
            ex = l["hw"].rsplit("/", 1)[-1][:-5]
            want["hw"] = l["hw"] + (f"#staticrypt_pwd={unlock_hash(pws[ex], salt)}" if ex in pws else "")
        else:
            want.pop("hw", None)
        if want != cur:
            writes.append({"op": "update", "collection": "students", "doc_id": bid,
                           "data": {"links": want}, "if_version": versions.get(bid)})
    json.dump(writes, open(f"{ROOT}/private/board_writes.json", "w"), indent=1, ensure_ascii=False)
    print(f"\n{len(writes)} board link update(s) in private/board_writes.json")


if __name__ == "__main__":
    main()
