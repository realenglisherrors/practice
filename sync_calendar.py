#!/usr/bin/env python3
"""sync_calendar.py: make each student page's "Next class" match Bianca's Google Calendar.
Usage: python3 sync_calendar.py events.json [preply.json ...] [--apply]
events.json = list of {"summary": "<calendar title>", "start": "2026-11-23T12:00:00-07:00"} (Claude pulls these from Google Calendar).
For every student found in the calendar, next_class = the earliest event that has not started yet. Students not in the list are left alone.
Those students get calendar_sync=true, so sync_board.py stops overwriting their next_class from the board (the calendar wins)."""
import json, os, sys, datetime, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
# calendar title -> site student id(s). Anything not listed here is skipped (e.g. "Dan (visit)", "Romanian Class").
TITLES = {"h&m": ["hm"], "oscar and beatriz": ["bo"], "beatriz and oscar": ["bo"]}
NO_NEXT = set()  # students whose page must not show a next class (none right now: Beatriz & Oscar do show theirs)


def norm(t):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", t.lower().strip()) if not unicodedata.combining(c)).replace("ı", "i")


def raw_day(start):
    return start[:10]  # the lesson's date in Bianca's calendar


def main():
    apply = "--apply" in sys.argv
    events = []  # one or more files: the main calendar AND the "Preply Schedule" calendar (Preply lessons live there)
    for path in [a for a in sys.argv[1:] if not a.startswith("--")]:
        ev = json.load(open(path))
        if isinstance(ev, dict):  # the raw Google Calendar export (what the calendar tool saves): keep title + start of live events
            ev = [{"summary": e.get("summary", ""), "start": e["start"].get("dateTime") or e["start"].get("date"),
                   "end": (e.get("end") or {}).get("dateTime")}
                  for e in ev["events"] if e.get("status") != "cancelled"]
        events += ev
    students = json.load(open(f"{ROOT}/private/students.json"))
    by_id = {s["id"]: s for s in students}
    # Bianca (Nov 27, 2026): ANY event with a student's name anywhere in its title counts ("Anton", "Preply: Roberto", "Class with Olga"),
    # Preply students included. Whole words only, so "Hannah" is not "Anna" and "Andreea" is not "Andre". A pair member's name = the pair's page.
    import re as _re
    pair_of = {m: s["id"] for s in students for m in s.get("members", [])}
    # "calendar_names": other names a student goes by in the calendar (Roberto is "Carlos" on Preply)
    # Days: "calendar_days" limits every match for that student, "calendar_names_days" only the matches on their other names.
    # Masha takes lessons on her brother Anton's Preply account: "Anton" on a weekday = Anton, on a weekend = Masha (Bianca, Nov 27, 2026).
    live = [s for s in students if not s.get("members") and not s.get("offboarded") and s["id"] != "sm"]
    pats = [(_re.compile(r"(?<![a-z0-9])" + _re.escape(norm(n)) + r"(?![a-z0-9])"), s, n != s["name"])
            for s in live for n in [s["name"]] + s.get("calendar_names", [])]

    def day_ok(rule, start):
        if not rule:
            return True
        wknd = datetime.date.fromisoformat(start[:10]).weekday() >= 5
        return wknd if rule == "weekend" else not wknd

    def match(title, start):
        key = norm(title)
        if key in TITLES:
            return TITLES[key]
        ids = [pair_of.get(s["id"], s["id"]) for pat, s, alias in pats if pat.search(key)
               and day_ok(s.get("calendar_days"), start) and (not alias or day_ok(s.get("calendar_names_days"), start))]
        return sorted(set(ids))
    now = datetime.datetime.now(datetime.timezone.utc)
    best, booked, upcoming = {}, {}, {}
    horizon = now + datetime.timedelta(days=28)
    for e in events:
        if "T" not in (e.get("start") or ""):
            continue  # all-day events (holidays, reminders) are never classes
        ids = match(e["summary"], e["start"])
        if not ids:
            print(f"  (skipped calendar event '{e['summary']}': no matching student)"); continue
        when = datetime.datetime.fromisoformat(e["start"])
        if when <= now:
            continue
        for i in ids:
            if when <= horizon:
                booked.setdefault(i, set()).add(raw_day(e["start"]))
                upcoming.setdefault(i, set()).add(e["start"])
            if i not in best or when < best[i][0]:
                best[i] = (when, e["start"], e.get("end"))
    n = 0
    for i, (when, raw, end) in sorted(best.items()):
        targets = [by_id[i]] + [by_id[m] for m in by_id[i].get("members", [])]
        for t in targets:
            if i in NO_NEXT:
                continue
            if t.get("next_class") != raw:
                print(f"  {t['name']}: {t.get('next_class')}  ->  {raw}"); n += 1
                t["next_class"] = raw
            t["calendar_sync"] = True
            if end:  # length of the next lesson in minutes, for the Add to calendar button
                mins = int((datetime.datetime.fromisoformat(end) - datetime.datetime.fromisoformat(raw)).total_seconds() // 60)
                if t.get("next_minutes") != mins:
                    t["next_minutes"] = mins; n += 1
        for t in targets:
            new = sorted(booked.get(i, ()))
            if t.get("booked_dates") != new:
                t["booked_dates"] = new; n += 1
            up = [] if i in NO_NEXT else sorted(upcoming.get(i, ()), key=datetime.datetime.fromisoformat)
            if t.get("upcoming_classes") != up:  # every class in the next 28 days: the page shows the next one by itself
                t["upcoming_classes"] = up; n += 1
    if not n:
        print("  site already matches the calendar")
    if not apply:
        print("(dry run: add --apply to write and rebuild)"); return
    json.dump(students, open(f"{ROOT}/private/students.json", "w"), indent=2, ensure_ascii=False)
    open(f"{ROOT}/private/students.json", "a").write("\n")
    subprocess.run([sys.executable, f"{ROOT}/build_site.py"], check=True)


if __name__ == "__main__":
    main()
