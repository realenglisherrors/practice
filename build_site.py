#!/usr/bin/env python3
"""Generates index.html and one page per student (s/<slug>/index.html).

Sources of truth:
  private/students.json  - id, name, slug, meet (Google Meet link), fixfile (e.g. exercises/mkfixfilefinal.html); "" = hidden
  private/cards.json     - one entry per exercise card (append new ones at the end)

Run:  python3 build_site.py
"""
import json, re, html, os, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
students = json.load(open(f"{ROOT}/private/students.json"))
cards = json.load(open(f"{ROOT}/private/cards.json"))

CSS = """
:root{--bg:#F2F4F7;--card:#fff;--navy:#1A2E48;--gold:#C9A84C;--dim:#6B7A8D;--border:#E4E8EF;
--shadow:0 1px 3px rgba(26,46,72,.06),0 4px 16px rgba(26,46,72,.07);}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:'DM Sans',system-ui,sans-serif;background:var(--bg);color:var(--navy);min-height:100vh;
display:flex;flex-direction:column;align-items:center;padding:32px 20px 64px}
.wrap{width:100%;max-width:860px}
.hero{display:flex;align-items:center;gap:28px;margin-bottom:34px}
.hero img{width:190px;height:auto;border-radius:14px;box-shadow:var(--shadow);flex-shrink:0}
.hero h1{font-family:'Cormorant Garamond',Georgia,serif;font-size:clamp(1.8rem,5vw,2.6rem);font-weight:600;line-height:1.1;letter-spacing:.01em}
.hero h1 em{font-style:italic;color:var(--gold)}
.hero p{font-size:.78rem;color:var(--dim);letter-spacing:.1em;text-transform:uppercase;margin-top:10px}
.meet{display:inline-flex;align-items:center;gap:8px;margin-top:16px;padding:10px 18px;border-radius:999px;background:var(--navy);
color:#fff;text-decoration:none;font-weight:600;font-size:.85rem;letter-spacing:.02em}
.meet.fix{margin-left:8px;background:var(--gold);color:var(--navy)}
.meet.fix i{background:var(--navy)}
.meet:hover,.meet:focus{background:#25406a;outline:none}
.meet i{width:9px;height:9px;border-radius:50%;background:var(--gold);display:inline-block}
@media(max-width:560px){.hero{flex-direction:column;text-align:center;gap:18px}.hero img{width:150px}}
h2.sec{font-family:'Cormorant Garamond',Georgia,serif;font-size:1.4rem;font-weight:600;letter-spacing:.05em;
padding-bottom:6px;margin:30px 0 12px;border-bottom:2px solid var(--gold)}
.tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
@media(max-width:620px){.tiles{grid-template-columns:repeat(2,1fr)}}
a.tile,a.card{display:flex;flex-direction:column;text-decoration:none;color:inherit;background:var(--card);border-radius:12px;
padding:14px 16px 12px;box-shadow:var(--shadow);border:1px solid var(--border);transition:border-color .15s,box-shadow .15s}
a.tile:hover,a.card:hover,a.tile:focus,a.card:focus{border-color:#b0bcd4;outline:none;box-shadow:0 2px 6px rgba(26,46,72,.08),0 8px 28px rgba(26,46,72,.12)}
.tile .name{font-family:'Cormorant Garamond',Georgia,serif;font-size:1.3rem;font-weight:600}
.tile .meta{font-size:.7rem;color:var(--dim);margin-top:3px}
.card-top{display:flex;align-items:flex-start;justify-content:space-between;gap:8px;margin-bottom:5px}
.title{font-size:.95rem;font-weight:600;line-height:1.2;margin-bottom:2px}
.subtitle{font-size:.72rem;color:var(--dim);font-style:italic}
.tag{font-size:.55rem;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:var(--dim);white-space:nowrap;padding:2px 7px;border:1px solid var(--border);border-radius:999px;margin-top:2px}
.desc{font-size:.74rem;color:var(--dim);line-height:1.55}
.chips{display:flex;flex-wrap:wrap;gap:3px;margin-top:7px}
.chip{font-size:.58rem;color:#8a96a5;padding:2px 6px;border-radius:999px;border:1px solid var(--border);font-weight:500}
.now{display:inline-block;font-size:.6rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#8a6d1c;background:#f7efd6;border-radius:999px;padding:2px 8px;margin-bottom:6px}
.rows{display:flex;flex-direction:column;gap:6px}
a.row{display:flex;align-items:center;gap:12px;text-decoration:none;color:inherit;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:10px 14px}
a.row:hover,a.row:focus{border-color:#b0bcd4;outline:none}
.row .wk{font-weight:600;font-size:.85rem;min-width:84px}
.row .sub{font-size:.72rem;color:var(--dim);flex:1}
.row .go{color:var(--gold);font-weight:700}
.back{font-size:.75rem;color:var(--dim);text-decoration:none;display:inline-block;margin-bottom:14px}
.back:hover{color:var(--navy)}
footer{margin-top:44px;font-size:.7rem;color:#aab;text-align:center;letter-spacing:.05em}
"""

HEAD = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{robots}<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>{css}</style></head><body><div class="wrap">
"""
TAIL = '</div><footer>Real English Errors</footer></body></html>\n'


def week_key(card):
    m = re.match(r"^[A-Za-z]*?(\d*)W(\d+)$", card["title"], re.I)
    if not m or card["tag"] != "Homework":
        return None
    return (int(m.group(1) or 1), int(m.group(2)))


def week_label(k):
    cycle, wk = k
    return f"Week {wk}" if cycle == 1 else f"Cycle {cycle} · Week {wk}"


def card_html(c, href_prefix, now=False):
    chips = "".join(f'<span class="chip">{x}</span>' for x in c["chips"])
    badge = '<span class="now">This week</span>' if now else ""
    return (f'<a class="card" href="{href_prefix}{c["href"]}">{badge}<div class="card-top"><div>'
            f'<div class="title">{c["title"]}</div><div class="subtitle">{c["subtitle"]}</div></div>'
            f'<span class="tag">{c["tag"]}</span></div><p class="desc">{c["desc"]}</p>'
            f'<div class="chips">{chips}</div></a>')


def row_html(c, label, href_prefix):
    return (f'<a class="row" href="{href_prefix}{c["href"]}"><span class="wk">{label}</span>'
            f'<span class="sub">{c["title"]}</span><span class="go">→</span></a>')


shutil.rmtree(f"{ROOT}/s", ignore_errors=True)
tiles = []
for st in students:
    mine = [c for c in cards if c["student"] == st["id"]]
    weekly = sorted(((week_key(c), c) for c in mine if week_key(c)), key=lambda x: x[0], reverse=True)
    fix = st.get("fixfile", "")
    extra = [c for c in mine if not week_key(c) and c["href"] != fix]
    esc = html.escape(st["name"])
    out = HEAD.format(robots='<meta name="robots" content="noindex">\n', title=f"{esc} · Real English Errors", css=CSS)
    meet = (f'<a class="meet" href="{html.escape(st["meet"])}" target="_blank" rel="noopener"><i></i>Join our class on Google Meet</a>'
            if st["meet"] else "")
    if fix:
        meet += (f'<a class="meet fix" href="../../{html.escape(fix)}"><i></i>My Fix File</a>')
    out += (f'<div class="hero">'
            f'<img src="../../logo-vertical.png" alt="Real English Errors">'
            f'<div><h1>{esc}&rsquo;s <em>exercises</em></h1><p>Real students. Real errors. Real fixes.</p>{meet}</div></div>')
    if weekly:
        k, c = weekly[0]
        out += f'<h2 class="sec">This week</h2>{card_html(c, "../../", now=True)}'
        if len(weekly) > 1:
            out += '<h2 class="sec">Archive</h2><div class="rows">'
            out += "".join(row_html(c, week_label(k), "../../") for k, c in weekly[1:])
            out += "</div>"
    if extra:
        out += '<h2 class="sec">Extra practice</h2><div class="rows">'
        out += "".join(row_html(c, c["tag"], "../../") for c in extra)
        out += "</div>"
    out += TAIL
    os.makedirs(f"{ROOT}/s/{st['slug']}", exist_ok=True)
    open(f"{ROOT}/s/{st['slug']}/index.html", "w").write(out)
    last = week_label(weekly[0][0]) if weekly else "Practice"
    tiles.append(f'<a class="tile" href="s/{st["slug"]}/"><span class="name">{esc}</span>'
                 f'<span class="meta">{len(mine)} exercises · {last}</span></a>')

idx = HEAD.format(robots='<meta name="robots" content="noindex">\n', title="Real English Errors", css=CSS)
idx += ('<div class="hero"><img src="logo-vertical.png" alt="Real English Errors: Real students. Real errors. Real fixes.">'
        '<div><h1>Let&rsquo;s knock out <em>these errors</em></h1><p>Open the personal link your teacher sent you</p>'
        '<a class="meet" href="https://www.realenglisherrors.com">Go to realenglisherrors.com</a></div></div>' + TAIL)
open(f"{ROOT}/index.html", "w").write(idx)
print(f"Built index + {len(students)} student pages, {len(cards)} cards")
