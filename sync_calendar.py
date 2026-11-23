#!/usr/bin/env python3
"""sync_calendar.py: make each student page's "Next class" match Bianca's Google Calendar.
Usage: python3 sync_calendar.py events.json [--apply]
events.json = list of {"summary": "<calendar title>", "start": "2026-11-23T12:00:00-07:00"} (Claude pulls these from Google Calendar).
For every student found in the calendar, next_class = the earliest event that has not started yet. Students not in the list are left alone.
Those students get calendar_sync=true, so sync_board.py stops overwriting their next_class from the board (the calendar wins)."""
import json, os, sys, datetime, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
# calendar title -> site student id(s). Anything not listed here is skipped (e.g. "Dan (visit)", "Romanian Class").
TITLES = {"h&m": ["hm"]}  # Beatriz & Oscar are left out on purpose: their page shows no next class (alternating cycle)


def norm(t):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", t.lower().strip()) if not unicodedata.combining(c)).replace("ı", "i")


def raw_day(start):
    return start[:10]  # the lesson's date in Bianca's calendar


def main():
    events = json.load(open(sys.argv[1])); apply = "--apply" in sys.argv
    if isinstance(events, dict):  # the raw Google Calendar export (what the calendar tool saves): keep title + start of live events
        events = [{"summary": e.get("summary", ""), "start": e["start"].get("dateTime") or e["start"].get("date")}
                  for e in events["events"] if e.get("status") != "cancelled"]
    students = json.load(open(f"{ROOT}/private/students.json"))
    by_id = {s["id"]: s for s in students}
    # Preply students are not scheduled in this calendar (their times come from the board), so never touch them
    by_name = {norm(s["name"]): s["id"] for s in students if not s.get("members") and "preply" not in (s.get("payment") or {}).get("via", "").lower()}
    now = datetime.datetime.now(datetime.timezone.utc)
    best, booked = {}, {}
    horizon = now + datetime.timedelta(days=28)
    for e in events:
        key = norm(e["summary"]); ids = TITLES.get(key) or ([by_name[key]] if key in by_name else [])
        if not ids:
            print(f"  (skipped calendar event '{e['summary']}': no matching student)"); continue
        when = datetime.datetime.fromisoformat(e["start"])
        if when <= now:
            continue
        for i in ids:
            if when <= horizon:
                booked.setdefault(i, set()).add(raw_day(e["start"]))
            if i not in best or when < best[i][0]:
                best[i] = (when, e["start"])
    n = 0
    for i, (when, raw) in sorted(best.items()):
        targets = [by_id[i]] + [by_id[m] for m in by_id[i].get("members", [])]
        for t in targets:
            if t.get("next_class") != raw:
                print(f"  {t['name']}: {t.get('next_class')}  ->  {raw}"); n += 1
                t["next_class"] = raw
            t["calendar_sync"] = True
        for t in targets:
            new = sorted(booked.get(i, ()))
            if t.get("booked_dates") != new:
                t["booked_dates"] = new; n += 1
    if not n:
        print("  site already matches the calendar")
    if not apply:
        print("(dry run: add --apply to write and rebuild)"); return
    json.dump(students, open(f"{ROOT}/private/students.json", "w"), indent=2, ensure_ascii=False)
    open(f"{ROOT}/private/students.json", "a").write("\n")
    subprocess.run([sys.executable, f"{ROOT}/build_site.py"], check=True)


if __name__ == "__main__":
    main()
