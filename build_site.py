#!/usr/bin/env python3
"""Generates index.html and one page per student (s/<slug>/index.html).

Sources of truth:
  private/students.json  - id, name, slug, meet (Google Meet link), fixfile (e.g. exercises/mkfixfilefinal.html); "" = hidden
  private/cards.json     - one entry per exercise card (append new ones at the end)

Run:  python3 build_site.py
"""
import json, re, html, os, shutil, hashlib, secrets, unicodedata

ROOT = os.path.dirname(os.path.abspath(__file__))
students = json.load(open(f"{ROOT}/private/students.json"))
cards = json.load(open(f"{ROOT}/private/cards.json"))

CSS = """
:root{--bg:#F5F3EE;--card:#fff;--navy:#1A2E48;--navy2:#2c4a7c;--gold:#C9A84C;--gold-soft:#f6efd9;--dim:#5f6f84;--border:#E6E2D8;
--shadow:0 1px 2px rgba(26,46,72,.05),0 8px 24px rgba(26,46,72,.08);}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:'DM Sans',system-ui,sans-serif;background:var(--bg);color:var(--navy);min-height:100vh;line-height:1.5;-webkit-font-smoothing:antialiased}
.band{background:linear-gradient(135deg,#1A2E48 0%,#2c4a7c 62%,#5473a8 100%);color:#fff;padding:40px 20px 76px;position:relative;overflow:hidden}
.band:after{content:"";position:absolute;right:-90px;top:-90px;width:300px;height:300px;border-radius:50%;background:radial-gradient(circle,rgba(201,168,76,.28),rgba(201,168,76,0) 68%)}
.band-in{max-width:860px;margin:0 auto;display:flex;align-items:center;gap:34px;position:relative;z-index:1}
.band img{width:168px;height:auto;border-radius:14px;box-shadow:0 10px 30px rgba(0,0,0,.28);flex-shrink:0}
.eyebrow{font-size:.7rem;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:var(--gold);margin-bottom:10px}
.band h1{font-family:'Cormorant Garamond',Georgia,serif;font-size:clamp(2.2rem,6.5vw,3.3rem);font-weight:600;line-height:1.05;letter-spacing:.005em}
.band h1.hi:after{content:"";display:block;width:54px;height:3px;border-radius:3px;background:var(--gold);margin:12px 0 0}
@media(max-width:600px){.band h1.hi:after{margin-left:auto;margin-right:auto}}
.pay{display:flex;align-items:center;gap:12px;background:var(--card);border:1px solid var(--border);border-radius:14px;padding:12px 16px;margin:0 0 18px;box-shadow:var(--shadow);font-size:.95rem}
.pay i{font-style:normal;width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;background:#e3f3e7;color:#1f7a3a;flex-shrink:0}
.pay.due i{background:var(--gold-soft);color:#9a7a1c}
.pay small{color:var(--dim);display:block;font-size:.8rem}
.band h1 em{font-style:italic;color:var(--gold)}
.lede{font-size:.98rem;color:rgba(255,255,255,.82);margin-top:12px;max-width:34em}
.btns{display:flex;flex-wrap:wrap;gap:10px;margin-top:20px}
.btn{display:inline-flex;align-items:center;gap:9px;padding:11px 20px;border-radius:999px;text-decoration:none;font-weight:600;font-size:.88rem;
background:#fff;color:var(--navy);box-shadow:0 2px 10px rgba(0,0,0,.18);transition:transform .12s}
.btn:hover,.btn:focus{transform:translateY(-1px);outline:none}
.btn i{width:9px;height:9px;border-radius:50%;background:#2fa36b;display:inline-block}
.btn.gold{background:var(--gold)}.btn.gold i{background:var(--navy)}
@media(max-width:600px){.band{padding:30px 20px 70px}.band-in{flex-direction:column;text-align:center;gap:22px}.band img{width:132px}.btns{justify-content:center}.lede{margin-left:auto;margin-right:auto}}
.main{max-width:860px;margin:-30px auto 0;padding:0 20px 56px;position:relative;z-index:2}
.sec{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:10px;margin:36px 0 12px}
.main>.sec:first-child{margin-top:46px}
.sec h2{font-family:'Cormorant Garamond',Georgia,serif;font-size:1.65rem;font-weight:600}
.sec small{font-size:.74rem;color:var(--dim);letter-spacing:.04em}
a.hero-card{display:block;text-decoration:none;color:inherit;background:var(--card);border-radius:16px;padding:22px 24px 20px;box-shadow:var(--shadow);border:1px solid var(--border);border-left:5px solid var(--gold);transition:box-shadow .15s,transform .15s}
a.hero-card:hover,a.hero-card:focus{outline:none;transform:translateY(-2px);box-shadow:0 2px 6px rgba(26,46,72,.08),0 14px 34px rgba(26,46,72,.14)}
.now{display:inline-block;font-size:.64rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#7a5f14;background:var(--gold-soft);border-radius:999px;padding:3px 10px;margin-bottom:10px}
.hero-card .title{font-variant-numeric:lining-nums;font-family:'Cormorant Garamond',Georgia,serif;font-size:1.9rem;font-weight:600;line-height:1.1}
.subtitle{font-size:.82rem;color:var(--dim);font-style:italic;margin-top:2px}
.desc{font-size:.86rem;color:#4b5b70;line-height:1.6;margin-top:12px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:14px}
.chip{font-size:.68rem;color:#52627a;padding:3px 10px;border-radius:999px;background:#f1efe8;font-weight:500}
.cta{display:inline-flex;align-items:center;gap:8px;margin-top:18px;padding:11px 22px;border-radius:999px;background:var(--navy);color:#fff;font-weight:600;font-size:.9rem}
.hero-card:hover .cta{background:var(--navy2)}
details.arch{margin-top:36px}
details.arch summary{list-style:none;cursor:pointer;display:flex;align-items:baseline;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-bottom:12px;padding:2px 0}
details.arch summary::-webkit-details-marker{display:none}
details.arch summary h2{font-family:'Cormorant Garamond',Georgia,serif;font-size:1.65rem;font-weight:600}
details.arch summary small{font-size:.74rem;color:var(--dim);letter-spacing:.04em;margin-left:auto}
.chev{width:9px;height:9px;border-right:2px solid var(--dim);border-bottom:2px solid var(--dim);transform:rotate(45deg);transition:transform .2s;align-self:center;margin-left:4px;position:relative;top:-2px}
details.arch[open] .chev{transform:rotate(-135deg);top:2px}
details.arch summary:focus-visible{outline:2px solid var(--gold);outline-offset:4px;border-radius:6px}
.hl{list-style:none;margin:14px 0 0;padding:0;display:flex;flex-direction:column;gap:9px}
.hl li{position:relative;padding-left:22px;font-size:.88rem;color:#3f4f66;line-height:1.5}
.hl li:before{content:"";position:absolute;left:3px;top:.55em;width:8px;height:8px;border-radius:50%;background:var(--gold)}
.hl li b{color:var(--navy);margin-right:4px}
.promo{margin-top:40px;background:linear-gradient(135deg,#1A2E48,#2c4a7c);color:#fff;border-radius:18px;padding:26px 26px 24px;box-shadow:var(--shadow);position:relative;overflow:hidden}
.promo h2{font-family:'Cormorant Garamond',Georgia,serif;font-size:1.9rem;font-weight:600;line-height:1.1;margin-top:2px}
.promo .pl{color:rgba(255,255,255,.82);margin-top:10px;font-size:.95rem}
.promo .pl em{color:var(--gold);font-style:italic}
.promo .hl li{color:rgba(255,255,255,.9)}
.promo .hl li b{color:#fff}
.promo .cta{background:var(--gold);color:var(--navy);text-decoration:none;margin-top:20px}
.promo .cta:hover{background:#d6b65a}
.rows{display:flex;flex-direction:column;gap:8px}
a.row{display:flex;align-items:center;gap:14px;text-decoration:none;color:inherit;background:var(--card);border:1px solid var(--border);border-radius:12px;padding:11px 16px;transition:border-color .15s,transform .15s}
a.row:hover,a.row:focus{border-color:var(--gold);outline:none;transform:translateX(2px)}
.badge{width:38px;height:38px;border-radius:50%;background:var(--navy);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:600;font-size:.8rem;flex-shrink:0}
.badge.alt{background:var(--gold-soft);color:#7a5f14}
.row .wk{font-weight:600;font-size:.92rem}
.row .sub{font-size:.74rem;color:var(--dim);flex:1}
.row .go{color:var(--gold);font-weight:700;font-size:1.1rem}
.enter-card{background:var(--card);border-radius:18px;box-shadow:var(--shadow);border:1px solid var(--border);padding:24px 24px 22px}
.enter-card label{display:block;font-family:'Cormorant Garamond',Georgia,serif;font-size:1.5rem;font-weight:600}
.enter-card p.hint{font-size:.84rem;color:var(--dim);margin-top:2px}
.enter{display:flex;gap:10px;margin-top:16px;flex-wrap:wrap}
.enter input{flex:1;min-width:190px;font:inherit;font-size:1.05rem;padding:13px 20px;border:2px solid var(--border);border-radius:999px;background:#fff;color:var(--navy)}
.enter input:focus{outline:none;border-color:var(--gold)}
.enter button{font:inherit;font-weight:600;font-size:.95rem;padding:13px 26px;border:0;border-radius:999px;background:var(--navy);color:#fff;cursor:pointer}
.enter button:hover{background:var(--navy2)}
.msg{min-height:1.3em;margin-top:10px;font-size:.84rem;color:#b0413e}
.feats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:22px}
@media(max-width:640px){.feats{grid-template-columns:1fr}}
.feat{background:transparent;border:1px solid var(--border);border-radius:14px;padding:16px 18px}
.feat b{display:block;font-size:.9rem;margin-bottom:3px}
.feat span{font-size:.8rem;color:var(--dim)}
.feat .n{display:inline-flex;width:26px;height:26px;border-radius:50%;background:var(--gold-soft);color:#7a5f14;font-weight:700;font-size:.78rem;align-items:center;justify-content:center;margin-bottom:8px}
.tl{position:relative;list-style:none;margin:6px 0 0 6px;padding:0}
.tl:before{content:"";position:absolute;left:15px;top:14px;bottom:14px;width:2px;background:linear-gradient(var(--gold),var(--border))}
.tl li{position:relative;display:flex;align-items:center;gap:14px;padding:7px 0}
.dot{width:32px;height:32px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:.78rem;font-weight:700;background:var(--bg);border:2px solid var(--border);color:#9aa4b2;z-index:1}
.tl .done .dot{background:var(--navy);border-color:var(--navy);color:#fff}
.tl .cur .dot{background:var(--gold);border-color:var(--gold);color:var(--navy);box-shadow:0 0 0 5px var(--gold-soft)}
.tl .lbl{font-size:.88rem;color:#8b97a8}
.tl .done .lbl{color:var(--dim)}
a.tl-btn{display:inline-flex;align-items:center;gap:8px;text-decoration:none;font-weight:600;font-size:.88rem;padding:9px 18px;border-radius:999px;background:var(--navy);color:#fff;transition:transform .12s}
a.tl-btn:hover,a.tl-btn:focus{transform:translateX(2px);outline:none;background:var(--navy2)}
a.tl-btn.cur{background:var(--gold);color:var(--navy)}
.tl .soon{font-size:.7rem;color:#aab3c0;margin-left:2px}
.tl .note{padding-top:0}.tl .note .dot{visibility:hidden;height:0}.tl .note .soon{margin-left:0;max-width:30em;line-height:1.4}
.tl .fixnode .dot{border-color:var(--gold);color:#9a7a1c;background:var(--gold-soft)}
.tl .fixnode .lbl{color:#8a6d1c;font-weight:600}
footer{text-align:center;padding:8px 20px 40px;font-size:.72rem;color:#9aa4b2;letter-spacing:.12em;text-transform:uppercase}
"""

HEAD = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{robots}<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>{css}</style></head><body>
"""
TAIL = '<footer>Real students. Real errors. Real fixes.</footer></body></html>\n'


def week_key(card):
    if "week" in card:
        return (int(card.get("cycle", 1)), int(card["week"]))
    m = re.match(r"^[A-Za-z]*?(\d*)W(\d+)$", card["title"], re.I)
    if not m or card["tag"] != "Homework":
        return None
    return (int(m.group(1) or 1), int(m.group(2)))


def week_label(k):
    cycle, wk = k
    return f"Week {wk}" if cycle == 1 else f"Cycle {cycle} · Week {wk}"


def highlights(desc):
    """Turn the prose description into a few bullets; fall back to the paragraph."""
    t = html.unescape(re.sub(r"<[^>]+>", "", desc))
    m = re.search(r"then practise with (.+?)(?:,? and send| ?\. Then send|\.$)", t, re.I)
    practice = m.group(1).strip().rstrip(".") if m else ""
    head = t[: m.start()] if m else t
    items = []
    for g in re.finditer(r"\b(vocabulary and expressions|vocabulary|grammar|pronunciation|numbers)\b(?:\s*\(([^)]*)\))?", head, re.I):
        label = g.group(1).capitalize()
        body = re.sub(r",?\s*and more\b", "", g.group(2) or "").strip()
        items.append((label, body))
    # "vocabulary and grammar" (no brackets) -> two bullets
    if not items and not practice:
        return f'<p class="desc">{desc}</p>'
    if items and not any(x for _, x in items):
        names = " and ".join(l.lower() for l, _ in items)
        lis = f"<li><b>Review</b> this week&rsquo;s {names}</li>"
    else:
        lis = "".join(f'<li><b>{html.escape(l)}</b>{(" " + html.escape(x)) if x else ""}</li>' for l, x in items)
    if practice:
        lis += f'<li><b>Practise</b> {html.escape(practice)}</li>'
    lis += '<li><b>Finish</b> by sending your results to Bianca by email and WhatsApp</li>'
    return f'<ul class="hl">{lis}</ul>'


PROMO = """<section class="promo"><p class="eyebrow">The 12-session program</p>
<h2>Ready to fix your errors for good?</h2>
<p class="pl">Practice helps. The program goes further, because everything is built from <em>your</em> own mistakes.</p>
<ul class="hl"><li><b>12 one-to-one sessions</b> of 50 minutes each</li>
<li><b>Your own homework page</b> after every class, made from your errors</li>
<li><b>A take-home Fix File</b> with guided repetition, so the corrections stay</li></ul>
<a class="cta" href="https://www.realenglisherrors.com">See how the program works &rarr;</a></section>"""


def display_title(c):
    k = week_key(c)
    return f"Session {k[1]} Homework" if k else c["title"]


def card_html(c, href_prefix):
    chips = "".join(f'<span class="chip">{x}</span>' for x in c["chips"])
    return (f'<a class="hero-card" href="{href_prefix}{c["href"]}"><span class="now">This week</span>'
            f'<div class="title">{display_title(c)}</div><div class="subtitle">{c["subtitle"]}</div>'
            f'{highlights(c["desc"])}'
            f'<span class="cta">Start this week&rsquo;s homework &rarr;</span></a>')


def row_html(c, k, href_prefix):
    # k: (cycle, week) or None for extra practice
    if k:
        badge = f'<span class="badge">{k[1]}</span>' if k[0] == 1 else f'<span class="badge alt">{k[0]}&middot;{k[1]}</span>'
        label = f"Session {k[1]}" if k[0] == 1 else f"Cycle {k[0]} &middot; Session {k[1]}"
    else:
        badge = '<span class="badge alt">&#9733;</span>'
        label = c["title"]
    sub = "Homework" if k else c["tag"]
    return (f'<a class="row" href="{href_prefix}{c["href"]}">{badge}<span class="wk">{label}</span>'
            f'<span class="sub">{sub}</span><span class="go">&rarr;</span></a>')


SALT_FILE = f"{ROOT}/private/salt.txt"
if not os.path.exists(SALT_FILE):
    open(SALT_FILE, "w").write(secrets.token_hex(16))
SALT = open(SALT_FILE).read().strip()


def norm(name):
    # must match the JS normalisation on the landing page
    n = unicodedata.normalize("NFD", name)
    n = "".join(ch for ch in n if not unicodedata.combining(ch)).lower().replace("\u0131", "i")
    return re.sub(r"[^a-z0-9]", "", n)


def slug_for(name):
    return hashlib.sha256((SALT + ":" + norm(name)).encode()).hexdigest()[:16]


for _st in students:
    _st["slug"] = slug_for(_st["name"])
assert len({s["slug"] for s in students}) == len(students), "two students normalise to the same name"

MEET_PAGE = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Your class</title><style>body{font-family:system-ui,sans-serif;background:#1A2E48;color:#fff;min-height:100vh;display:flex;align-items:center;justify-content:center;margin:0;text-align:center;padding:24px}
a{display:inline-block;margin-top:18px;padding:14px 26px;border-radius:999px;background:#C9A84C;color:#1A2E48;font-weight:700;text-decoration:none;font-size:1.05rem}</style></head>
<body><div><h1 style="font-weight:600;margin:0 0 6px">Joining your class&hellip;</h1><p style="opacity:.8;margin:0">If nothing happens, tap the button.</p>
<a id="go" href="__URL__">Open Google Meet</a></div>
<script>setTimeout(function(){location.replace(document.getElementById("go").href)},400)</script></body></html>"""
os.makedirs(f"{ROOT}/private/meet", exist_ok=True)
for _f in os.listdir(f"{ROOT}/private/meet"):
    os.remove(f"{ROOT}/private/meet/{_f}")
_lines = []
for _st in students:
    if _st["meet"]:
        open(f"{ROOT}/private/meet/meet-{_st['id']}.html", "w").write(MEET_PAGE.replace("__URL__", html.escape(_st["meet"], quote=True)))
        _lines.append(f"meet-{_st['id']}|{_st['name']}")
open(f"{ROOT}/private/meet/list.txt", "w").write("\n".join(_lines) + ("\n" if _lines else ""))

shutil.rmtree(f"{ROOT}/s", ignore_errors=True)
for st in students:
    mine = [c for c in cards if c["student"] == st["id"]]
    weekly = sorted(((week_key(c), c) for c in mine if week_key(c)), key=lambda x: x[0], reverse=True)
    fix = st.get("fixfile", "")
    extra = [c for c in mine if not week_key(c) and c["href"] != fix]
    esc = html.escape(st["name"])
    out = HEAD.format(robots='<meta name="robots" content="noindex">\n', title=f"{esc} · Real English Errors", css=CSS)
    btns = ""
    if st["meet"]:
        btns += f'<a class="btn" href="../../exercises/meet-{st["id"]}.html"><i></i>Join my class on Google Meet</a>'
    fix_is_old = bool(fix) and bool(weekly) and int(st.get("fixfile_cycle", 1)) < max(k[0] for k, _ in weekly)
    if fix and not fix_is_old:
        btns += f'<a class="btn gold" href="../../{html.escape(fix)}">Open my Fix File</a>'
    btns = f'<div class="btns">{btns}</div>' if btns else ""
    on_cycle = bool(weekly)
    lede = (("This week&rsquo;s homework, every week before it, and your class link: everything you need between lessons, in one place."
             if st["meet"] else "This week&rsquo;s homework and every week before it: everything you need between lessons, in one place.")
            if on_cycle else "Your practice exercises, all in one place.")
    out += ('<header class="band"><div class="band-in"><img src="../../logo-vertical.png" alt="Real English Errors">'
            f'<div><p class="eyebrow">Your personal page</p><h1 class="hi">Hi, {esc}</h1>'
            f'<p class="lede">{lede}</p>'
            f'{btns}</div></div></header><main class="main">')
    pay = st.get("payment")
    if pay:
        if pay.get("status") == "paid":
            msg = "Paid" + (f" through {html.escape(pay['through'])}" if pay.get("through") else "")
            out += f'<div class="pay"><i>&#10003;</i><div><b>{msg}</b><small>Thank you!</small></div></div>'
        else:
            msg = "Payment due" + (f" {html.escape(pay['due'])}" if pay.get("due") else "")
            out += f'<div class="pay due"><i>!</i><div><b>{msg}</b><small>Message Bianca if you have any questions.</small></div></div>'
    if weekly:
        cur_cycle = max(k[0] for k, _ in weekly)
        this = weekly[0]
        out += f'<div class="sec"><h2>This week</h2></div>{card_html(this[1], "../../")}'
        total = int(st.get("homeworks", 10))
        bywk = {k[1]: c for k, c in weekly if k[0] == cur_cycle}
        latest = max(bywk)
        out += f'<div class="sec"><h2>Your 12 sessions</h2><small>Each homework appears here when it&rsquo;s ready</small></div><ol class="tl">'
        for n in range(1, total + 1):
            c = bywk.get(n)
            if c:
                is_cur = (n == latest)
                cls = "cur" if is_cur else "done"
                inner = (f'<a class="tl-btn{" cur" if is_cur else ""}" href="../../{c["href"]}">Session {n} Homework &rarr;</a>')
                mark = "&#10003;" if not is_cur else str(n)
            elif n < latest:
                cls, inner, mark = "done", f'<span class="lbl">Session {n} Homework</span><span class="soon">done in class</span>', "&#10003;"
            else:
                cls, inner, mark = "", f'<span class="lbl">Session {n} Homework</span>', str(n)
            out += f'<li class="{cls}"><span class="dot">{mark}</span>{inner}</li>'
        fix_old = bool(fix) and int(st.get("fixfile_cycle", cur_cycle)) < cur_cycle
        if fix and not fix_old:
            out += (f'<li class="fixnode"><span class="dot">&#9733;</span><a class="tl-btn cur" href="../../{html.escape(fix)}">Sessions 11 &amp; 12: Your Fix File &rarr;</a></li>'
                    '<li class="note"><span class="dot"></span><span class="soon">Our final production push: no new homework, just your Fix File.</span></li>')
        else:
            out += ('<li class="fixnode"><span class="dot">&#9733;</span><span class="lbl">Sessions 11 &amp; 12: Your Fix File</span></li>'
                    '<li class="note"><span class="dot"></span><span class="soon">Opens after session 11. We use it in class as a final production push of all your errors, with no new homework.</span></li>')
        out += "</ol>"
        older = [(k, c) for k, c in weekly if k[0] < cur_cycle]
        if older or fix_old:
            n_old = len(older) + (1 if fix_old else 0)
            out += (f'<details class="arch"><summary><h2>Your archive</h2>'
                    f'<small>Previous cycle{"s" if cur_cycle > 2 else ""} &middot; {n_old} item{"s" if n_old != 1 else ""}</small>'
                    f'<span class="chev" aria-hidden="true"></span></summary><div class="rows">')
            if fix_old:
                out += (f'<a class="row" href="../../{html.escape(fix)}"><span class="badge alt">&#9733;</span>'
                        f'<span class="wk">Cycle {st["fixfile_cycle"]} Fix File</span><span class="sub">Final review</span><span class="go">&rarr;</span></a>')
            out += "".join(row_html(c, k, "../../") for k, c in older)
            out += "</div></details>"
    if extra and (not on_cycle or st.get("show_practice")):
        out += '<div class="sec"><h2>Practice</h2></div><div class="rows">'
        out += "".join(row_html(c, None, "../../") for c in extra)
        out += "</div>"
    if not on_cycle:
        out += PROMO
    out += "</main>" + TAIL
    os.makedirs(f"{ROOT}/s/{st['slug']}", exist_ok=True)
    open(f"{ROOT}/s/{st['slug']}/index.html", "w").write(out)

LANDING = """<header class="band"><div class="band-in"><img src="logo-vertical.png" alt="Real English Errors: Real students. Real errors. Real fixes.">
<div><p class="eyebrow">Student page</p><h1>Your homework, <em>all in one place</em></h1>
<p class="lede">Open your personal page to find this week&rsquo;s exercises, and every week before it.</p></div></div></header>
<main class="main"><div class="enter-card"><form id="f" autocomplete="off"><label for="n">What&rsquo;s your name?</label>
<div class="enter"><input id="n" type="text" placeholder="Your name" autocapitalize="words" required><button type="submit">Open my page</button></div>
<p id="msg" class="msg" role="alert"></p></form></div>
<div class="feats"><div class="feat"><span class="n">1</span><b>This week&rsquo;s homework</b><span>New homework is added here when it&rsquo;s ready, made for your errors.</span></div>
<div class="feat"><span class="n">2</span><b>Every past week</b><span>Come back to any lesson to review it again.</span></div>
<div class="feat"><span class="n">3</span><b>Your class link</b><span>If we meet on Google Meet, join your lessons from the same page.</span></div></div></main>
<script>
var SALT="__SALT__";
function norm(s){return s.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/\u0131/g,"i").replace(/[^a-z0-9]/g,"");}
async function slug(s){var d=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(SALT+":"+norm(s)));
return Array.from(new Uint8Array(d)).map(function(x){return x.toString(16).padStart(2,"0")}).join("").slice(0,16);}
document.getElementById("f").addEventListener("submit",async function(e){
e.preventDefault();var msg=document.getElementById("msg");msg.textContent="";
var v=document.getElementById("n").value;if(!norm(v)){return;}
try{var u="s/"+await slug(v)+"/";var r=await fetch(u,{cache:"no-store"});
if(r.ok){location.href=u;}else{msg.textContent="We couldn\u2019t find that name. Check the spelling, or message Bianca.";}}
catch(x){msg.textContent="Something went wrong. Please try again.";}});
</script>"""
idx = HEAD.format(robots='<meta name="robots" content="noindex">\n', title="Real English Errors", css=CSS)
idx += LANDING.replace("__SALT__", SALT) + TAIL
open(f"{ROOT}/index.html", "w").write(idx)
print(f"Built index + {len(students)} student pages, {len(cards)} cards")
