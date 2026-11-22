#!/usr/bin/env python3
"""Take a student who has finished (and downloaded their work) off the student site.

Hand-over (last class, Claude runs it with the final Fix File):
  python3 offboard.py "Masha" --handover  -> switches on the "Keep your work" download on their page, rebuilds
Usage (Claude runs this when Bianca says "offboard [Name]", about a week after hand-over):
  python3 offboard.py "Masha"            -> lists what would be removed
  python3 offboard.py "Masha" --apply    -> removes it, then rebuilds the site

What it does:
  - deletes the student's locked pages from exercises/ (homework, Fix File, Meet link page)
  - moves their cards from private/cards.json to private/offboarded_cards.json
  - comments out their encrypt lines in build.sh
  - marks them "offboarded": <date> in private/students.json (their record and src/ files stay, so they can come back)
  - rebuilds the site, so their private page and download disappear
Then commit the deletions + s/ + index.html with explicit paths and push.
The old locked pages stay in git history (still password-protected); the live site no longer serves them.
"""
import datetime, json, os, re, subprocess, sys, unicodedata

ROOT = os.path.dirname(os.path.abspath(__file__))


def norm(s):
    s = unicodedata.normalize("NFD", s)
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if not unicodedata.combining(c)).lower().replace("ı", "i"))


def main():
    who, apply = sys.argv[1], "--apply" in sys.argv
    students = json.load(open(f"{ROOT}/private/students.json"))
    cards = json.load(open(f"{ROOT}/private/cards.json"))
    st = next((s for s in students if norm(s["name"]) == norm(who) or s["id"] == who), None)
    if not st:
        sys.exit(f"No student called {who!r} in private/students.json")
    group = [st] + [s for s in students if s["id"] in st.get("members", [])]
    if "--handover" in sys.argv:
        st["handover"] = datetime.date.today().isoformat()
        json.dump(students, open(f"{ROOT}/private/students.json", "w"), indent=2, ensure_ascii=False)
        open(f"{ROOT}/private/students.json", "a").write("\n")
        subprocess.run([sys.executable, f"{ROOT}/build_site.py"], check=True)
        print(f"{st['name']}'s download is on. Commit s/ and push; offboard about a week from now.")
        return
    host = next((s for s in students if st["id"] in s.get("members", [])), None)
    if host:
        print(f"! {st['name']} shares a page with {host['name']}: offboard \"{host['name']}\" to remove both")
    ids = {s["id"] for s in group}
    mine = [c for c in cards if c["student"] in ids]
    files = {c["href"].replace("%20", " ") for c in mine if c["href"].startswith("exercises/")}
    for s in group:
        if s.get("fixfile"):
            files.add(s["fixfile"])
        files.add(f"exercises/meet-{s['id']}.html")
    files = sorted(f for f in files if os.path.exists(f"{ROOT}/{f}"))
    names = {os.path.basename(f)[:-5] for f in files}

    print(f"Offboarding {', '.join(s['name'] for s in group)}:")
    print(f"  {len(mine)} cards → private/offboarded_cards.json")
    for f in files:
        print(f"  delete {f}")
    if not apply:
        print("\n(dry run: add --apply to do it)")
        return

    for f in files:
        os.remove(f"{ROOT}/{f}")
    old = json.load(open(f"{ROOT}/private/offboarded_cards.json")) if os.path.exists(f"{ROOT}/private/offboarded_cards.json") else []
    json.dump(old + mine, open(f"{ROOT}/private/offboarded_cards.json", "w"), indent=2, ensure_ascii=False)
    json.dump([c for c in cards if c["student"] not in ids], open(f"{ROOT}/private/cards.json", "w"), indent=2, ensure_ascii=False)
    bs = open(f"{ROOT}/build.sh").read().split("\n")
    bs = [("# offboarded: " + l) if (m := re.match(r'^encrypt\s+"([^"]+)"', l)) and m.group(1) in names else l for l in bs]
    open(f"{ROOT}/build.sh", "w").write("\n".join(bs))
    today = datetime.date.today().isoformat()
    for s in group:
        s["offboarded"] = today
        s.pop("handover", None)
    json.dump(students, open(f"{ROOT}/private/students.json", "w"), indent=2, ensure_ascii=False)
    open(f"{ROOT}/private/students.json", "a").write("\n")
    subprocess.run([sys.executable, f"{ROOT}/build_site.py"], check=True)
    print("\nDone. Commit with: git add -A exercises s index.html && git commit && git push")


if __name__ == "__main__":
    main()
