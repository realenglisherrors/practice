#!/usr/bin/env python3
"""refresh_fixfile.py: put a student's latest Fix File on their student page.

Usage:  python3 refresh_fixfile.py <student id or name> <Fix File html> [--no-push]

<Fix File html> is the page saved from the student's Fix File artifact (Artifact read, path index.html).
During the cycle it hosts a STUDY COPY: every card, example and note, but none of Bianca's Production Push
(no Easy / Tricky / Forgot buttons, ratings or results box, no booking box). Once the Fix File is in final
mode ("const FINAL=true") it hosts the file as it is (that is also what "Download my work" gives at hand-over).

It then: writes src/exercises/<name>.html + exercises/<name>.counts.json (the card numbers on the student
page), locks the copy with the student's homework password (staticrypt, same look as build.sh), adds the
encrypt line to build.sh and sets "fixfile" in private/students.json if this is the student's first one,
rebuilds the site, checks that no student page folder (= link) changed, and commits + pushes.
A new cycle gets a new file (<id>fixfile2, ...); the old cycle's Fix File moves to the archive (fixfile_prev).
"""
import json, os, re, subprocess, sys, unicodedata

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
STUDY_CSS = '<style id="ree-study-copy">.prate,.undo,.last,.pushsum,.pushchip,.book{display:none!important}</style>'
STAMP = "<!-- student study copy: no Push ratings or buttons (refresh_fixfile.py) -->"


def die(msg):
    sys.exit("STOPPED, nothing was changed: " + msg)


def norm(s):
    s = unicodedata.normalize("NFD", s)
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if not unicodedata.combining(c)).lower().replace("ı", "i"))


def study_copy(s):
    if re.search(r"const FINAL\s*=\s*true", s):
        return s, "final"
    if STAMP in s or 'id="ree-study-copy"' in s:
        return s, "study"
    k = s.find("const SEED=")
    if k >= 0:
        _, end = json.JSONDecoder().raw_decode(s, k + len("const SEED="))
        s = s[:k] + "const SEED={}" + s[end:]
    if s.count("const HASPUSH=!FINAL;") != 1 or s.count('window.claude?.use?.("db")') != 1:
        die("this Fix File doesn't look like the in-cycle template (HASPUSH / db lines not found). Ask Claude to check it.")
    s = s.replace("const HASPUSH=!FINAL;", "const HASPUSH=false;").replace('window.claude?.use?.("db")', "null")
    j = s.rfind("</body>")
    return s[:j] + STAMP + STUDY_CSS + "\n" + s[j:], "study"


def counts(s):
    m = re.search(r"(?:const|let|var)\s+GROUPS\s*=\s*(\[.*?\]);\s*\n", s, re.S)
    if not m:
        die("no card data (const GROUPS=) in the Fix File.")
    by, ses = {}, {}
    for g in json.loads(m.group(1)):
        for it in g["items"]:
            if len(it) > 6 and it[6]:
                continue
            by[g["id"]] = by.get(g["id"], 0) + 1
            try:
                n = int(it[5]); ses[n] = ses.get(n, 0) + 1
            except Exception:
                pass
    return {"total": sum(by.values()), "by": by, "ses": {str(k): ses[k] for k in sorted(ses)}}


def week_cycle(c):
    if "week" in c:
        return int(c.get("cycle", 1))
    m = re.match(r"^[A-Za-z]*?(\d*)W(\d+)$", c["title"], re.I)
    return int(m.group(1) or 1) if m and c.get("tag") == "Homework" else None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    push = "--no-push" not in sys.argv
    if len(args) != 2:
        sys.exit(__doc__)
    who, src = args
    if not os.path.exists(src):
        die(f"{src} not found.")
    students = json.load(open("private/students.json"))
    cards = json.load(open("private/cards.json"))
    hits = [s for s in students if s["id"] == who or norm(s["name"]) == norm(who)]
    if len(hits) != 1:
        die(f"no single student matches '{who}'. Use their id from private/students.json.")
    st = hits[0]
    if st.get("offboarded"):
        die(f"{st['name']} is offboarded.")

    cyc = [week_cycle(c) for c in cards if c["student"] in ([st["id"]] + st.get("members", []))]
    cycle = max([c for c in cyc if c] or [1])
    fix = st.get("fixfile", "")
    if fix and int(st.get("fixfile_cycle", 1)) == cycle:
        href = fix
    else:
        href = f"exercises/{st['id']}fixfile{cycle if cycle > 1 else ''}.html"
    name = href[len("exercises/"):-len(".html")]

    s, mode = study_copy(open(src, encoding="utf-8").read())
    cnt = counts(s)

    # password: the one build.sh already uses for this file, else the student's homework password
    bs = open("build.sh", encoding="utf-8").read()
    enc = dict((a, b) for a, b in re.findall(r'^encrypt "([^"]+)"\s+"([^"]+)"\s*$', bs, re.M))
    pw = enc.get(name)
    if not pw:
        own = [os.path.basename(c["href"])[:-5].replace("%20", " ") for c in cards if c["student"] in ([st["id"]] + st.get("members", []))]
        pw = next((enc[o] for o in own if o in enc), None) or st["name"]
    secret = pw
    if os.path.exists("private/codes.txt"):
        for line in open("private/codes.txt"):
            if line.lower().startswith(pw.lower() + "="):
                secret = line.split("=", 1)[1].strip()

    before = sorted(os.listdir("s"))
    open(f"src/exercises/{name}.html", "w", encoding="utf-8").write(s)
    json.dump(cnt, open(f"exercises/{name}.counts.json", "w"), indent=1)
    open(f"exercises/{name}.counts.json", "a").write("\n")
    instr, ph, err = (("Type your 4-digit code to start.", "4-digit code", "Not quite. Check your code and try again.") if secret != pw
                      else ("Type your password to start.", "Password", "Not quite. Check the spelling and the capital letter."))
    subprocess.run(["npx", "staticrypt", f"src/exercises/{name}.html", "--password", secret, "-d", "exercises/", "--remember", "0", "--short", "--template-remember", "Remember me on this device",
                    "-t", "src/password-template.html", "--template-title", "Let's knock out these errors!", "--template-instructions", instr,
                    "--template-button", "Start training", "--template-placeholder", ph, "--template-error", err],
                   check=True, stdout=subprocess.DEVNULL)
    if name not in enc:
        lines = bs.split("\n")
        last = max(i for i, l in enumerate(lines) if l.startswith("encrypt "))
        lines.insert(last + 1, f'encrypt "{name}"                        "{pw}"')
        open("build.sh", "w", encoding="utf-8").write("\n".join(lines))

    if st.get("fixfile") != href:
        if fix and int(st.get("fixfile_cycle", 1)) < cycle:
            st["fixfile_prev"] = {"href": fix, "cycle": int(st.get("fixfile_cycle", 1))}
        st["fixfile"], st["fixfile_cycle"] = href, cycle
        json.dump(students, open("private/students.json", "w"), indent=2, ensure_ascii=False)
        open("private/students.json", "a").write("\n")

    subprocess.run([sys.executable, "build_site.py"], check=True)
    after = sorted(os.listdir("s"))
    if after != before:
        sys.exit(f"STOPPED before committing: the student page folders changed (links would break).\n removed: {sorted(set(before) - set(after))}\n added: {sorted(set(after) - set(before))}")

    latest = max([int(k) for k in cnt["ses"]] or [0])
    print(f"{st['name']}: {mode} copy at {href} (password: {pw}{', code' if secret != pw else ''}) · {cnt['total']} cards, "
          f"+{cnt['ses'].get(str(latest), 0)} from Session {latest} · {cnt['by']}")
    if not push:
        print("Not committed (--no-push).")
        return
    files = ["index.html", "s", f"exercises/{name}.html", f"exercises/{name}.counts.json"]
    subprocess.run(["git", "add", "--"] + files, check=True)
    if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode == 0:
        print("Nothing changed on the site (the Fix File was already up to date).")
        return
    subprocess.run(["git", "commit", "-q", "-m", f"Refresh {st['name']}'s Fix File on their page\n\nCo-Authored-By: Claude <noreply@anthropic.com>"], check=True)
    subprocess.run(["git", "pull", "-q", "--rebase"], check=True)
    subprocess.run(["git", "push", "-q"], check=True)
    print("Committed and pushed.")


if __name__ == "__main__":
    main()
