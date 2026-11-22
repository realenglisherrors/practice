#!/usr/bin/env python3
"""Generates index.html and one page per student (s/<slug>/index.html).

Sources of truth:
  private/students.json  - id, name, slug, meet (Google Meet link), fixfile (e.g. exercises/mkfixfilefinal.html); "" = hidden
  private/cards.json     - one entry per exercise card (append new ones at the end)

Run:  python3 build_site.py
"""
import datetime, json, re, html, os, shutil, hashlib, secrets, unicodedata

ROOT = os.path.dirname(os.path.abspath(__file__))
students = json.load(open(f"{ROOT}/private/students.json"))
cards = json.load(open(f"{ROOT}/private/cards.json"))

CSS = """
:root{--bg:#fff;--card:#F5F6FA;--navy:#1F2A4D;--navy2:#3C518A;--gold:#D9AE4A;--gold-soft:#E6EAF4;--dim:#5A6378;--border:#DCE1EB;
--shadow:0 1px 2px rgba(31,42,77,.05),0 8px 24px rgba(31,42,77,.08);}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:'Montserrat',system-ui,-apple-system,'Segoe UI',sans-serif;background:var(--bg);color:var(--navy);min-height:100vh;line-height:1.5;-webkit-font-smoothing:antialiased}
.band{background:linear-gradient(135deg,#1F2A4D 0%,#3C518A 62%,#6F81A8 100%);color:#fff;padding:40px 20px 76px;position:relative;overflow:hidden}
.band:after{content:"";position:absolute;right:-90px;top:-90px;width:300px;height:300px;border-radius:50%;background:radial-gradient(circle,rgba(217,174,74,.28),rgba(217,174,74,0) 68%)}
.band-in{max-width:860px;margin:0 auto;display:flex;align-items:center;gap:34px;position:relative;z-index:1}
.band img{width:168px;height:auto;border-radius:14px;box-shadow:0 10px 30px rgba(0,0,0,.28);flex-shrink:0}
.eyebrow,.btn,.cta,.enter button,a.tl-btn,.now,.badge{font-family:'Montserrat',system-ui,sans-serif}
.eyebrow{font-size:.7rem;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:var(--gold);margin-bottom:10px}
.band h1{font-family:'Montserrat',system-ui,sans-serif;font-weight:800;letter-spacing:-.02em;font-size:clamp(2.2rem,6.5vw,3.3rem);font-weight:600;line-height:1.05;letter-spacing:.005em}
.band h1.hi:after{content:"";display:block;width:54px;height:3px;border-radius:3px;background:var(--gold);margin:12px 0 0}
@media(max-width:600px){.band h1.hi:after{margin-left:auto;margin-right:auto}}
.nextc{position:absolute;top:-16px;right:0;display:none;text-align:right;font-size:.72rem;letter-spacing:.06em;color:rgba(255,255,255,.78);line-height:1.35}
.nextc b{display:block;font-size:.95rem;letter-spacing:0;color:#fff;font-weight:600}
.nextc i{font-style:normal;font-size:.62rem;letter-spacing:.2em;text-transform:uppercase;color:var(--gold);font-weight:600;display:block}
@media(max-width:600px){.nextc{top:-22px;font-size:.66rem}.nextc b{font-size:.85rem}}
.pay{display:flex;align-items:center;gap:12px;background:var(--card);border:1px solid var(--border);border-radius:14px;padding:12px 16px;margin:0 0 18px;box-shadow:var(--shadow);font-size:.95rem}
.pay i{font-style:normal;width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;background:#e3f3e7;color:#1f7a3a;flex-shrink:0}
.pay.due i{background:var(--gold-soft);color:#3C518A}
.pay small{color:var(--dim);display:block;font-size:.8rem}
.pstrip{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.pstrip span{min-width:46px;height:26px;padding:0 8px;border-radius:13px;border:2px solid var(--border);display:inline-flex;align-items:center;justify-content:center;font-size:.72rem;color:var(--dim);box-sizing:border-box}
.pstrip .p{background:#2f7d4f;border-color:#2f7d4f;color:#fff;font-weight:700}
.pstrip .h{box-shadow:0 0 0 2px #fff,0 0 0 4px var(--navy)}
.paybar{position:fixed;left:0;right:0;bottom:0;z-index:20;background:var(--card);border-top:1px solid var(--border);box-shadow:0 -4px 18px rgba(31,42,77,.08);padding-bottom:env(safe-area-inset-bottom)}
.paybar details{max-width:860px;margin:0 auto}
.paybar summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:10px;padding:9px 20px;font-size:.84rem}
.paybar summary::-webkit-details-marker{display:none}
.paybar summary i{font-style:normal;width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.72rem;background:#e3f3e7;color:#1f7a3a;flex-shrink:0}
.paybar.due summary i{background:var(--gold-soft);color:#3C518A}
.paybar summary small{color:var(--dim);margin-left:auto;font-size:.74rem}
.paybar .more{padding:0 20px 12px;font-size:.8rem;color:var(--dim)}
body:has(.paybar){padding-bottom:56px}
.pay .legend{font-size:.72rem;color:var(--dim);margin-top:6px}
.main:has(.duo){max-width:1040px}
.duo{display:grid;grid-template-columns:1fr 1fr;gap:22px;align-items:start}
@media(max-width:700px){.duo{grid-template-columns:1fr}}
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
.sec h2{font-family:'Montserrat',system-ui,sans-serif;font-weight:800;letter-spacing:-.02em;font-size:1.65rem;font-weight:600}
.sec small{font-size:.74rem;color:var(--dim);letter-spacing:.04em}
a.hero-card{display:block;text-decoration:none;color:inherit;background:var(--card);border-radius:16px;padding:22px 24px 20px;box-shadow:var(--shadow);border:1px solid var(--border);border-left:5px solid var(--gold);transition:box-shadow .15s,transform .15s}
a.hero-card:hover,a.hero-card:focus{outline:none;transform:translateY(-2px);box-shadow:0 2px 6px rgba(31,42,77,.08),0 14px 34px rgba(31,42,77,.14)}
.now{display:inline-block;font-size:.64rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#3C518A;background:var(--gold-soft);border-radius:999px;padding:3px 10px;margin-bottom:10px}
.hero-card .title{font-variant-numeric:lining-nums;font-family:'Montserrat',system-ui,sans-serif;font-weight:800;letter-spacing:-.02em;font-size:1.9rem;font-weight:600;line-height:1.1}
.subtitle{font-size:.82rem;color:var(--dim);font-style:italic;margin-top:2px}
.desc{font-size:.86rem;color:#4b5b70;line-height:1.6;margin-top:12px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:14px}
.chip{font-size:.68rem;color:#52627a;padding:3px 10px;border-radius:999px;background:#E7EBF3;font-weight:500}
.cta{display:inline-flex;align-items:center;gap:8px;margin-top:18px;padding:11px 22px;border-radius:999px;background:var(--navy);color:#fff;font-weight:600;font-size:.9rem}
.hero-card:hover .cta{background:var(--navy2)}
details.arch{margin-top:36px}
details.arch summary{list-style:none;cursor:pointer;display:flex;align-items:baseline;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-bottom:12px;padding:2px 0}
details.arch summary::-webkit-details-marker{display:none}
details.arch summary h2{font-family:'Montserrat',system-ui,sans-serif;font-weight:800;letter-spacing:-.02em;font-size:1.65rem;font-weight:600}
details.arch summary small{font-size:.74rem;color:var(--dim);letter-spacing:.04em;margin-left:auto}
.chev{width:9px;height:9px;border-right:2px solid var(--dim);border-bottom:2px solid var(--dim);transform:rotate(45deg);transition:transform .2s;align-self:center;margin-left:4px;position:relative;top:-2px}
details.arch[open] .chev{transform:rotate(-135deg);top:2px}
details.arch summary:focus-visible{outline:2px solid var(--gold);outline-offset:4px;border-radius:6px}
.hl{list-style:none;margin:14px 0 0;padding:0;display:flex;flex-direction:column;gap:9px}
.hl li{position:relative;padding-left:22px;font-size:.88rem;color:#3f4f66;line-height:1.5}
.hl li:before{content:"";position:absolute;left:3px;top:.55em;width:8px;height:8px;border-radius:50%;background:var(--gold)}
.hl li b{color:var(--navy);margin-right:4px}
.promo{margin-top:40px;background:linear-gradient(135deg,#1F2A4D,#3C518A);color:#fff;border-radius:18px;padding:26px 26px 24px;box-shadow:var(--shadow);position:relative;overflow:hidden}
.promo h2{font-family:'Montserrat',system-ui,sans-serif;font-weight:800;letter-spacing:-.02em;font-size:1.9rem;font-weight:600;line-height:1.1;margin-top:2px}
.promo .pl{color:rgba(255,255,255,.82);margin-top:10px;font-size:.95rem}
.promo .pl em{color:var(--gold);font-style:italic}
.promo .hl li{color:rgba(255,255,255,.9)}
.promo .hl li b{color:#fff}
.promo .cta{background:var(--gold);color:var(--navy);text-decoration:none;margin-top:20px}
.promo .cta:hover{background:#E4BC5E}
.rows{display:flex;flex-direction:column;gap:8px}
a.row{display:flex;align-items:center;gap:14px;text-decoration:none;color:inherit;background:var(--card);border:1px solid var(--border);border-radius:12px;padding:11px 16px;transition:border-color .15s,transform .15s}
a.row:hover,a.row:focus{border-color:var(--gold);outline:none;transform:translateX(2px)}
.badge{width:38px;height:38px;border-radius:50%;background:var(--navy);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:600;font-size:.8rem;flex-shrink:0}
.badge.alt{background:var(--gold-soft);color:#3C518A}
.row .wk{font-weight:600;font-size:.92rem}
.row .sub{font-size:.74rem;color:var(--dim);flex:1}
.row .go{color:var(--gold);font-weight:700;font-size:1.1rem}
.enter-card{background:var(--card);border-radius:18px;box-shadow:var(--shadow);border:1px solid var(--border);padding:24px 24px 22px}
.enter-card label{display:block;font-family:'Montserrat',system-ui,sans-serif;font-weight:800;letter-spacing:-.02em;font-size:1.5rem;font-weight:600}
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
.feat .n{display:inline-flex;width:26px;height:26px;border-radius:50%;background:var(--gold-soft);color:#3C518A;font-weight:700;font-size:.78rem;align-items:center;justify-content:center;margin-bottom:8px}
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
.tl .fixnode .dot{border-color:var(--gold);color:#3C518A;background:var(--gold-soft)}
.tl .fixnode .lbl{color:#8a6d1c;font-weight:600}
footer{text-align:center;padding:8px 20px 40px;font-size:.72rem;color:#9aa4b2;letter-spacing:.12em;text-transform:uppercase}

h1,h2,.band h1,.sec h2,.hero-card .title,details.arch summary h2,.promo h2,.enter-card label{font-family:'Montserrat',system-ui,sans-serif!important;font-weight:800!important;letter-spacing:-.02em!important}
.pay,a.hero-card,.enter-card,.feat,.paybar{border:0!important}
a.hero-card{border-left:5px solid var(--gold)!important;border-radius:24px}
.enter-card,.promo,.pay{border-radius:24px}
a.row{border:0;background:var(--card);border-radius:16px}
.feat{background:var(--card)}
.shadow-none,.pay,a.hero-card,.enter-card{box-shadow:none}
.enter input{background:#fff;border-color:var(--border)}
.dot{background:#fff}

em,i,.subtitle,.band h1 em,.promo .pl em{font-style:normal!important}
.band h1 em{color:var(--gold)}
.band{padding:22px 20px 56px!important}
.band img{width:96px!important;border-radius:10px;box-shadow:0 6px 18px rgba(0,0,0,.25)}
.band-in{gap:22px!important}
.band h1{font-size:clamp(1.6rem,5vw,2.2rem)!important}
.lede{font-size:.9rem;margin-top:8px}
.btns{margin-top:14px}
.main{margin-top:-24px}
@media(max-width:600px){.band{padding:20px 20px 52px!important}.band img{width:80px!important}.band-in{gap:12px!important}}
.band img{border-radius:0!important;box-shadow:none!important}
.nextc{top:10px!important;right:20px!important}
@media(max-width:600px){.nextc{top:8px!important;right:14px!important}}
"""

HEAD = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{robots}<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,600;0,9..144,700;1,9..144,600&family=Inter:wght@400;500;600&family=Montserrat:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>{css}</style></head><body>
"""
DEMO_NB = """<style>
.nbov{position:fixed;inset:0;z-index:100;background:#fffdf8;display:none;flex-direction:column;font-family:'Montserrat',system-ui,sans-serif}
.nbov.on{display:flex}
.nbov .nbh{background:#3C518A;color:#fff;padding:16px clamp(16px,4vw,40px);display:flex;justify-content:space-between;align-items:center;gap:12px}
.nbov .nbh p{margin:0;font-size:.7rem;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:#D9AE4A}
.nbov .nbh h2{margin:2px 0 0;font-size:clamp(1.4rem,3vw,2.2rem);font-weight:800;letter-spacing:-.02em}
.nbov .nbh button{border:1.5px solid rgba(255,255,255,.55);background:transparent;color:#fff;border-radius:999px;padding:8px 18px;font:700 .85rem 'Montserrat',sans-serif;cursor:pointer}
.nbov .nbk{display:flex;flex-wrap:wrap;gap:6px 18px;padding:10px clamp(16px,4vw,40px);border-bottom:1px solid #E3E7F0;font-size:.82rem;color:#5A6378}
.nbov .pp{flex:1;overflow:auto;padding:clamp(18px,3vw,32px) clamp(20px,7vw,96px);font-size:clamp(1.05rem,1.9vw,1.35rem);line-height:1.75;color:#1a1a1a}
.nbov h3{margin:1.2em 0 .3em;font-size:1.1em;font-weight:800;color:#1155CC}.nbov h3:first-child{margin-top:0}
.nbov .bad{color:#9aa0ab;font-weight:800}.nbov .ok{color:#1A7A4B;font-weight:800}.nbov .gap{color:#1155CC;font-weight:700}.nbov .pron{color:#A44879;font-weight:700}
.nbov ul{margin:.2em 0;padding-left:1.3em}
</style>
<div class="nbov" id="nbov" role="dialog" aria-label="Sample's notebook"><div class="nbh"><div><p>Real English Errors</p><h2>Sample's notebook</h2></div><button type="button" id="nbx">Close</button></div>
<div class="nbk"><span><b class="bad">grey</b> what you said</span><span><b class="ok">green</b> the fix</span><span><b class="gap">blue</b> a gap</span><span><b class="pron">purple</b> pronunciation</span></div>
<div class="pp">
<h3>Class 1 · Nov 20</h3><ul>
<li>Last weekend, <span class="bad">we go</span> &rarr; <span class="ok">we went</span> to the lake.</li>
<li>I <span class="bad">don't wear</span> a coat yesterday &rarr; I <span class="ok">didn't wear</span> a coat yesterday.</li>
<li>My brother <span class="bad">want get</span> a dog &rarr; my brother <span class="ok">wants to get</span> a dog.</li>
<li>My grandparents live <span class="gap">in the lower part of</span> Poland.</li>
<li>People there speak a different <span class="gap">dialect</span>.</li>
<li><span class="pron">comfortable</span> &nbsp; [KUMF-ter-bul]</li></ul>
<h3>Class 2 · Nov 27</h3><ul>
<li>If <span class="bad">will be</span> good weather &rarr; <span class="ok">if the weather is good</span>, we will go to the beach.</li>
<li>I'm <span class="bad">tired about</span> the noise &rarr; I'm <span class="ok">tired of</span> the noise.</li>
<li>She cooks and talks <span class="gap">at the same time</span>.</li>
<li><span class="pron">vegetable</span> &nbsp; [VEJ-tuh-bul]</li></ul>
</div></div>
<script>(function(){var h=document.querySelector(".btns");if(!h){h=document.createElement("div");h.className="btns";(document.querySelector(".band-in>div")||document.querySelector(".band")).appendChild(h)}
var a=document.createElement("button");a.type="button";a.className="btn gold";a.innerHTML="<i></i>Present notebook";h.appendChild(a);
var o=document.getElementById("nbov");a.onclick=function(){o.classList.add("on")};document.getElementById("nbx").onclick=function(){o.classList.remove("on")};
document.addEventListener("keydown",function(e){if(e.key==="Escape")o.classList.remove("on")})})()</script>"""
def present_js(st):
    return DEMO_NB if st["id"] == "sm" else ""
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


_stale = any(_st.get("slug") != slug_for(_st["name"]) for _st in students)
for _st in students:
    _st["slug"] = slug_for(_st["name"])
ACTIVE = [x for x in students if not x.get("offboarded")]  # offboard.py sets "offboarded": date; their pages are gone
if _stale:  # keep the stored slugs honest, so a page's folder can be found from students.json
    json.dump(students, open(f"{ROOT}/private/students.json", "w"), indent=2, ensure_ascii=False)
    open(f"{ROOT}/private/students.json", "a").write("\n")
assert len({s["slug"] for s in students}) == len(students), "two students normalise to the same name"

MEET_PAGE = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Your class</title><style>body{font-family:system-ui,sans-serif;background:#1F2A4D;color:#fff;min-height:100vh;display:flex;align-items:center;justify-content:center;margin:0;text-align:center;padding:24px}
a{display:inline-block;margin-top:18px;padding:14px 26px;border-radius:999px;background:#D9AE4A;color:#1F2A4D;font-weight:700;text-decoration:none;font-size:1.05rem}</style></head>
<body><div><h1 style="font-weight:600;margin:0 0 6px">Joining your class&hellip;</h1><p style="opacity:.8;margin:0">If nothing happens, tap the button.</p>
<a id="go" href="__URL__">Open Google Meet</a></div>
<script>setTimeout(function(){location.replace(document.getElementById("go").href)},400)</script></body></html>"""
os.makedirs(f"{ROOT}/private/meet", exist_ok=True)
for _f in os.listdir(f"{ROOT}/private/meet"):
    os.remove(f"{ROOT}/private/meet/{_f}")
_lines = []
_members = {m for x in students for m in x.get("members", [])}
for _st in ACTIVE:
    if _st["meet"] and _st["id"] not in _members:
        open(f"{ROOT}/private/meet/meet-{_st['id']}.html", "w").write(MEET_PAGE.replace("__URL__", html.escape(_st["meet"], quote=True)))
        _lines.append(f"meet-{_st['id']}|{_st.get('meet_pw', _st['name'])}")
open(f"{ROOT}/private/meet/list.txt", "w").write("\n".join(_lines) + ("\n" if _lines else ""))

NEXT_JS = """<script>(function(){var e=document.querySelector(".nextc");if(!e)return;var d=new Date(e.getAttribute("data-t"));if(isNaN(d)||d<new Date())return;
var z=e.getAttribute("data-z"),o={weekday:"short",month:"short",day:"numeric"},t={hour:"numeric",minute:"2-digit"};if(z){o.timeZone=z;t.timeZone=z;}
e.querySelector("b").textContent=d.toLocaleDateString("en-US",o)+" \u00b7 "+d.toLocaleTimeString("en-US",t);e.style.display="block";})()</script>"""


def next_chip(st):
    nc = st.get("next_class")
    if not nc:
        return ""
    z = f' data-z="{html.escape(st["tz"])}"' if st.get("tz") else ""
    return f'<div class="nextc" data-t="{html.escape(nc)}"{z}><i>Next class</i><b></b></div>'


def pay_bar(pay):
    """Same content as pay_html, but as a slim bar pinned to the bottom (tap to expand)."""
    e = html.escape
    if pay.get("status") == "paid":
        head, sub = f'Paid through {e(pay["through"])}', "Thank you!"
    elif pay.get("status") == "via":
        head, sub = f'Payments go through {e(pay["via"])}', ""
    elif pay.get("status") == "info":
        head, sub = e(pay["head"]), ""
    else:
        head, sub = "Payments", e(pay.get("detail", "")) + ". Message Bianca if you have any questions."
    strip = ""
    pd_, od_ = pay.get("paid_dates", []), pay.get("owed_dates", [])
    if pd_ or od_:
        td = datetime.date.today().isoformat()
        chips = "".join(
            f'<span class="{"p" if d in pd_ else ""}{" h" if d <= td else ""}" title="{d}: {"paid" if d in pd_ else "not paid yet"}">'
            f'{d[5:].replace("-", "/")}</span>' for d in sorted(set(pd_) | set(od_)))
        strip = (f'<div class="pstrip">{chips}</div>'
                 '<div class="legend">Each circle is a class. Filled = paid. Outline = not paid yet. Ring = class already held.</div>')
    due = pay.get("status") == "due"
    more = f'<div class="more">{sub if due else ""}{strip}</div>' if (strip or due) else ""
    tip = "<small>Details &#9652;</small>" if more else ""
    return (f'<div class="paybar{" due" if due else ""}"><details><summary><i>{"!" if due else "&#10003;"}</i>'
            f'<b>{head}</b>{tip}</summary>{more}</details></div>')


def pay_html(pay):
    e = html.escape
    strip = ""
    pd_, od_ = pay.get("paid_dates", []), pay.get("owed_dates", [])
    if pd_ or od_:
        td = datetime.date.today().isoformat()
        chips = "".join(
            f'<span class="{"p" if d in pd_ else ""}{" h" if d <= td else ""}" title="{d}: {"paid" if d in pd_ else "not paid yet"}">'
            f'{d[5:].replace("-", "/")}</span>' for d in sorted(set(pd_) | set(od_)))
        strip = (f'<div class="pstrip">{chips}</div>'
                 '<div class="legend">Each circle is a class. Filled = paid. Outline = not paid yet. Ring = class already held.</div>')
    if pay.get("status") == "paid":
        head = f'<b>Paid through {e(pay["through"])}</b><small>Thank you!</small>'
    elif pay.get("status") == "via":
        head = f'<b>Payments go through {e(pay["via"])}</b>'
    elif pay.get("status") == "info":
        head = f'<b>{e(pay["head"])}</b>'
    else:
        head = f'<b>Payments</b><small>{e(pay.get("detail", ""))}. Message Bianca if you have any questions.</small>'
    cls = "pay due" if pay.get("status") == "due" else "pay"
    return f'<div class="{cls}"><i>{"!" if cls.endswith("due") else "&#10003;"}</i><div>{head}{strip}</div></div>'


import zipfile


def keep_pack(st, members=None):
    """One zip with the student's Fix File and every homework as a blank copy (the locked pages: no unlocked copy ever goes into the public repo)."""
    if not st.get("handover"):  # only from hand-over until offboarding (keeps the public repo small)
        return ""
    ids = [m["id"] for m in members] if members else [st["id"]]
    files = []
    for c in cards:
        if c["student"] in ids and c["href"] != st.get("fixfile") and os.path.exists(f"{ROOT}/{c['href']}".replace("%20", " ")):
            k = week_key(c)
            who = next((m["name"] for m in members if m["id"] == c["student"]), "") if members else ""
            nm = (f"Cycle {k[0]} " if k and k[0] > 1 else "") + (f"Session {k[1]} Homework" if k else c["title"])
            files.append((f"{ROOT}/{c['href']}".replace("%20", " "), f"Homework/{(who + ' - ') if who else ''}{nm}.html"))
    if st.get("fixfile") and os.path.exists(f"{ROOT}/{st['fixfile']}"):
        files.append((f"{ROOT}/{st['fixfile']}", f"{st['name']} - Fix File.html"))
    if not files:
        return ""
    name = f"{re.sub(r'[^A-Za-z0-9]+', '-', unicodedata.normalize('NFD', st['name']).encode('ascii', 'ignore').decode()).strip('-')}-Real-English-Errors.zip"
    readme = (f"Real English Errors: {st['name']}'s work\n\nOpen any file in your browser. Type your first name to unlock it.\n"
              "Every homework starts blank, so you can do it again as often as you like.\n")
    with zipfile.ZipFile(f"{ROOT}/s/{st['slug']}/{name}", "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(zipfile.ZipInfo("Read me.txt", (2026, 1, 1, 0, 0, 0)), readme)
        for src, arc in sorted(set(files), key=lambda x: x[1]):
            zi = zipfile.ZipInfo(arc, (2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zi, open(src, "rb").read())
    n_hw = sum(1 for _, a in files if a.startswith("Homework/"))
    what = ("your Fix File and " if st.get("fixfile") else "") + (f"all {n_hw} homework pages" if n_hw != 1 else "your homework page")
    return (f'<div class="sec"><h2>Keep your work</h2></div><p class="desc" style="margin-top:0">Download {what} to your computer. '
            'Each homework opens blank, so you can do it again whenever you like.</p>'
            f'<div class="btns" style="margin-top:14px"><a class="btn" href="{html.escape(name)}" download><i></i>Download my work</a></div>')


shutil.rmtree(f"{ROOT}/s", ignore_errors=True)
for st in ACTIVE:
    if st.get("members"):
        names = [next(x for x in students if x["id"] == m) for m in st["members"]]
        out = HEAD.format(robots='<meta name="robots" content="noindex">\n', title=f"{html.escape(st['name'])} · Real English Errors", css=CSS)
        btn = (f'<div class="btns"><a class="btn" href="../../exercises/meet-{st["id"]}.html"><i></i>Join our class on Google Meet</a></div>' if st["meet"] else "")
        out += ('<header class="band"><div class="band-in"><img src="../../logo-vertical.png" alt="Real English Errors">'
                f'<div><p class="eyebrow">Your shared page</p><h1 class="hi">Hi, {html.escape(st["name"])}</h1>'
                '<p class="lede">One page for your shared class: payments for everyone, and a homework column each.</p>'
                f'{btn}</div>{next_chip(st)}</div></header><main class="main">')
        out += '<div class="duo">'
        for m in names:
            wk = sorted(((week_key(c), c) for c in cards if c["student"] == m["id"] and week_key(c)), key=lambda x: x[0], reverse=True)
            out += f'<section class="col"><div class="sec"><h2>{html.escape(m["name"])}</h2></div>'
            if wk:
                cyc = max(k[0] for k, _ in wk)
                out += card_html(wk[0][1], "../../")
                bywk = {k[1]: c for k, c in wk if k[0] == cyc}
                latest = max(bywk)
                total = int(m.get("homeworks", 10))
                out += '<div class="sec"><h2>12 sessions</h2></div><ol class="tl">'
                for n in range(1, total + 1):
                    c = bywk.get(n)
                    if c:
                        cur_ = n == latest
                        out += (f'<li class="{"cur" if cur_ else "done"}"><span class="dot">{str(n) if cur_ else "&#10003;"}</span>'
                                f'<a class="tl-btn{" cur" if cur_ else ""}" href="../../{c["href"]}">Session {n} Homework &rarr;</a></li>')
                    elif n < latest:
                        out += f'<li class="done"><span class="dot">&#10003;</span><span class="lbl">Session {n} Homework</span><span class="soon">done in class</span></li>'
                    else:
                        out += f'<li><span class="dot">{n}</span><span class="lbl">Session {n} Homework</span></li>'
                out += "</ol>"
            else:
                out += '<p class="desc">Homework appears here when it is ready.</p>'
            out += "</section>"
        out += "</div>"
        ielts = [c for c in cards if c["student"] == st["id"] and not week_key(c)]
        if ielts:
            out += (f'<details class="arch"><summary><h2>IELTS Materials</h2>'
                    f'<small>{len(ielts)} item{"s" if len(ielts) != 1 else ""}</small>'
                    f'<span class="chev" aria-hidden="true"></span></summary><div class="rows">')
            out += "".join(row_html(c, None, "../../") for c in ielts)
            out += "</div></details>"
        if st["fixfile"]:
            out += f'<div class="btns" style="margin-top:22px"><a class="btn gold" href="../../{html.escape(st["fixfile"])}">Open our shared Fix File</a></div>'
        else:
            out += '<p class="desc" style="margin-top:22px;text-align:center">Your shared Fix File opens after session 11.</p>'
        os.makedirs(f"{ROOT}/s/{st['slug']}", exist_ok=True)
        out += keep_pack(st, names)
        out += "</main>" + TAIL.replace("</body>", NEXT_JS + (pay_bar(st["payment"]) if st.get("payment") else "") + present_js(st) + "</body>")
        # the pair's own name AND each member's first name open this same page
        for sl in {st["slug"]} | {m["slug"] for m in names}:
            os.makedirs(f"{ROOT}/s/{sl}", exist_ok=True)
            open(f"{ROOT}/s/{sl}/index.html", "w").write(out)
        continue
    if st["id"] in {m for x in students for m in x.get("members", [])}:
        continue  # members of a shared page have no individual page
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
            f'{btns}</div>{next_chip(st)}</div></header><main class="main">')
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
    os.makedirs(f"{ROOT}/s/{st['slug']}", exist_ok=True)
    out += keep_pack(st)
    out += "</main>" + TAIL.replace("</body>", NEXT_JS + (pay_bar(st["payment"]) if st.get("payment") else "") + present_js(st) + "</body>")
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
# every student's page and current homework, for the Students board (read by sync_board.py; private, never committed)
SITE = "https://realenglisherrors.github.io/practice/"
_links = {}
for st in ACTIVE:
    host = next((x for x in students if st["id"] in x.get("members", [])), st)  # pair members share the pair's page
    wk = sorted(((week_key(c), c) for c in cards if c["student"] == st["id"] and week_key(c)), key=lambda x: x[0], reverse=True)
    _links[st["id"]] = {"page": f"{SITE}s/{host['slug']}/",
                        "hw": (SITE + wk[0][1]["href"]) if wk else "",
                        "hw_title": wk[0][1]["title"] if wk else ""}
json.dump(_links, open(f"{ROOT}/private/site_links.json", "w"), indent=1, ensure_ascii=False)

idx = HEAD.format(robots='<meta name="robots" content="noindex">\n', title="Real English Errors", css=CSS)
idx += LANDING.replace("__SALT__", SALT) + TAIL
open(f"{ROOT}/index.html", "w").write(idx)
print(f"Built index + {len(students)} student pages, {len(cards)} cards")
