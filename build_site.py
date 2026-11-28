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
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%;text-size-adjust:100%}
body{font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif;background:var(--bg);color:var(--navy);min-height:100vh;line-height:1.5;-webkit-font-smoothing:antialiased}
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
.ptiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin:2px 0 12px}
.ptiles>div{background:var(--bg);border-radius:14px;padding:10px 12px;display:flex;flex-direction:column;gap:2px}
.ptiles small{font-size:.7rem;letter-spacing:.06em;text-transform:uppercase;color:var(--dim)}
.ptiles b{font-size:1.25rem;line-height:1.15;color:var(--navy);font-weight:800}
.ptiles span{font-size:.78rem;color:var(--dim)}
.ptiles .due{background:var(--gold-soft)}.ptiles .due b{color:#8a6d1c}
.pdetail h4{font-size:.74rem;letter-spacing:.08em;text-transform:uppercase;color:var(--dim);margin:14px 0 6px;font-weight:700}
.prow{background:var(--bg);border-radius:14px;padding:10px 12px;margin-bottom:6px}
.prow>div{display:flex;justify-content:space-between;gap:10px;align-items:baseline}
.prow b{font-size:1rem;color:var(--navy);font-weight:800}.prow span{font-size:.85rem;color:var(--navy);font-weight:600}
.prow small{display:block;margin-top:3px;font-size:.78rem;color:var(--dim);line-height:1.4}
.pnote{margin:10px 0 0}
.paybar .more{max-height:60vh;overflow:auto;padding:0 20px 12px;font-size:.8rem;color:var(--dim)}
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
div.hero-card{background:var(--card);border-radius:24px;padding:22px 24px 20px;border-left:5px solid var(--gold)}
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
/* like the Fix File and homework headers: logo on the left beside the text, never small and centred */
.band img{width:132px!important}
@media(max-width:600px){.band-in{flex-direction:row!important;text-align:left!important;align-items:center!important;gap:16px!important}.band img{width:104px!important}.band h1.hi:after{margin-left:0!important;margin-right:0!important}.btns{justify-content:flex-start!important}.lede{margin-left:0!important;margin-right:0!important}}
@media(max-width:360px){.band img{width:84px!important}.band-in{gap:12px!important}}
/* desktop: the Fix File hero: text on the left, the logo big and faded on the right */
@media(min-width:761px){.band-in{max-width:1088px!important}.band-in>div{flex:1 1 auto;min-width:0}.band img{order:2;margin-left:auto;width:190px!important;opacity:.38;margin-top:58px}}
.nextc{top:10px!important;right:20px!important}
@media(max-width:600px){.nextc{top:8px!important;right:14px!important}}
/* phones: nothing floats. Row 1 = small logo + next-class pill, row 2 = the text, full width, button full width */
@media(max-width:600px){
.band{padding:18px 18px 46px!important}
.band-in{display:grid!important;grid-template-columns:auto minmax(0,1fr);grid-template-areas:"logo next" "text text";align-items:center!important;gap:16px 12px!important}
.band-in>img{grid-area:logo;width:64px!important}
.band-in>div:not(.nextc){grid-area:text;min-width:0}
.band-in>.nextc{grid-area:next;position:static!important;justify-self:end;text-align:right!important;background:rgba(255,255,255,.12);border-radius:14px;padding:6px 12px;font-size:.7rem!important;line-height:1.3}
.band h1{font-size:clamp(1.9rem,9vw,2.4rem)!important}
.lede{font-size:.92rem!important;margin-top:10px!important}
.btns{margin-top:16px!important}
.btns .btn{width:100%;justify-content:center}
}
@media(max-width:340px){.band-in>.nextc i{display:none}}
/* phones: readable greys, thumb-sized taps, nothing hidden behind the bottom bar */
@media(max-width:600px){
.tl .lbl{color:#6b7689;font-size:.95rem}.tl .done .lbl{color:var(--dim)}
.tl .soon{color:#6b7689;font-size:.78rem}
.tl li{padding:5px 0;min-height:46px}
a.tl-btn{min-height:44px;font-size:.95rem;padding:10px 20px}
.sec small,.row .sub,.pay small,.pay .legend,.paybar .more,details.arch summary small{font-size:.82rem}
a.row{min-height:56px;padding:12px 16px}
.cta{width:100%;justify-content:center;min-height:48px;font-size:.98rem}
.hero-card .title{font-size:1.6rem}
a.hero-card{padding:20px 18px 18px}
.paybar summary{min-height:54px;font-size:.92rem;padding:10px 18px}
.paybar summary small{font-size:.82rem}
body:has(.paybar){padding-bottom:calc(72px + env(safe-area-inset-bottom))}
footer{color:#6b7689;font-size:.74rem;padding-bottom:calc(90px + env(safe-area-inset-bottom))}
.enter{flex-direction:column;align-items:stretch}
.enter input{min-width:0;font-size:1rem}
.enter button{min-height:50px;width:100%}
}
"""

HEAD = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{robots}<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,600;0,9..144,700;1,9..144,600&family=Inter:wght@400;500;600;700&family=Montserrat:wght@400;500;600;700;800&display=swap" rel="stylesheet">
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
    m = re.search(r"then practi[cs]e with (.+?)(?:,? and send| ?\. Then send|\.$)", t, re.I)
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
        # a label with no words (e.g. just "pronunciation") gets a generic line, never a blank bullet
        items = [(l, x or "the sounds and words from this week\u2019s class") for l, x in items]
        lis = "".join(f'<li><b>{html.escape(l)}</b> {html.escape(x)}</li>' for l, x in items)
    if practice:
        lis += f'<li><b>Practice</b> {html.escape(practice)}</li>'
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


def fix_counts(path):
    """Card counts from a Fix File's GROUPS data: total, per group, per session. None if the file can't be read (e.g. locked)."""
    side = f"{ROOT}/{path}".replace("%20", " ")
    side = side[:-5] + ".counts.json" if side.endswith(".html") else side + ".counts.json"
    if os.path.exists(side):  # written next to the Fix File by the fix-file skill (the hosted Fix File itself is locked)
        try:
            c = json.load(open(side))
            return {"total": int(c["total"]), "by": c.get("by", {}), "ses": {int(k): v for k, v in c.get("ses", {}).items()}}
        except Exception:
            pass
    try:
        t = open(f"{ROOT}/{path}".replace("%20", " "), encoding="utf-8").read()
        m = re.search(r"(?:const|let|var)\s+GROUPS\s*=\s*(\[.*?\]);\s*\n", t, re.S)
        G = json.loads(m.group(1))
    except Exception:
        return None
    by, ses = {}, {}
    for g in G:
        for it in g["items"]:
            if len(it) > 6 and it[6]:
                continue
            by[g["id"]] = by.get(g["id"], 0) + 1
            try:
                n = int(it[5])
                ses[n] = ses.get(n, 0) + 1
            except Exception:
                pass
    return {"total": sum(by.values()), "by": by, "ses": ses}


FIXCARD_CSS = """<style>
.fixcard{display:flex;flex-direction:column;gap:12px;background:#1F2A4D;color:#fff;border-radius:22px;padding:22px 22px 20px;margin-top:18px;box-shadow:var(--shadow)}
.fixcard .fc-top{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
.fixcard .fc-eye{margin:0;font-family:'Montserrat',system-ui,sans-serif;font-size:.72rem;font-weight:700;letter-spacing:.18em;color:var(--gold)}
.fixcard .fc-new{margin:0;background:var(--gold);color:#1F2A4D;border-radius:999px;padding:4px 12px;font-size:.74rem;font-weight:800;font-family:'Montserrat',system-ui,sans-serif}
.fixcard .fc-big{display:flex;align-items:baseline;gap:12px}
.fixcard .fc-big b{font-family:'Montserrat',system-ui,sans-serif;font-size:3.4rem;font-weight:800;line-height:1}
.fixcard .fc-big span{font-weight:600;color:#DFE4F4;line-height:1.35}
.fixcard .fc-split{display:flex;gap:6px}
.fixcard .fc-split p{margin:0;flex:1;background:rgba(255,255,255,.1);border-radius:12px;padding:8px 10px;font-size:.78rem;color:#DFE4F4}
.fixcard .fc-split b{display:block;font-size:1.1rem;color:#fff}
.fixcard .fc-note{margin:0;font-size:.86rem;line-height:1.5;color:#C9D1EC}
.fixcard a.fc-go{display:flex;align-items:center;justify-content:center;min-height:48px;border-radius:999px;background:var(--gold);color:#1F2A4D;font-family:'Montserrat',system-ui,sans-serif;font-weight:800;text-decoration:none}
.tl .fc-add{margin-left:8px;font-size:.74rem;font-weight:700;color:var(--navy2)}
</style>"""


def fix_card(href, counts, latest):
    """Option A (Nov 26 2026): the Fix File as a card under This week, during the cycle."""
    big = new = split = ""
    if counts:
        n_new = counts["ses"].get(latest, 0)
        new = f'<p class="fc-new">+{n_new} from Session {latest}</p>' if n_new else ""
        big = (f'<div class="fc-big"><b>{counts["total"]}</b><span>words, phrases and patterns so far</span></div>')
        by = counts["by"]
        split = ('<div class="fc-split">' + "".join(f'<p><b>{by.get(k, 0)}</b>{lbl}</p>' for k, lbl in
                 [("grammar", "grammar"), ("vocab", "vocabulary"), ("pron", "pronunciation")]) + "</div>")
    return (f'{FIXCARD_CSS}<section class="fixcard"><div class="fc-top"><p class="fc-eye">YOUR FIX FILE</p>{new}</div>{big}{split}'
            '<p class="fc-note">It grows after every class. At the end of the cycle it&rsquo;s yours to keep, with all your homework inside.</p>'
            f'<a class="fc-go" href="../../{html.escape(href)}">Open my Fix File &rarr;</a></section>')


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

NEXT_JS = """<script>(function(){var e=document.querySelector(".nextc");if(!e)return;var now=new Date(),L=((e.getAttribute("data-ts")||"")+" "+e.getAttribute("data-t")).split(" ").filter(Boolean).map(function(x){return new Date(x)}).filter(function(x){return !isNaN(x)&&x>now}).sort(function(a,b){return a-b}),d=L[0];if(!d)return;
var z=e.getAttribute("data-z"),o={weekday:"short",month:"short",day:"numeric"},t={hour:"numeric",minute:"2-digit"};if(z){o.timeZone=z;t.timeZone=z;}
e.querySelector("b").textContent=d.toLocaleDateString("en-US",o)+" \u00b7 "+d.toLocaleTimeString("en-US",t);e.style.display="block";})()</script>"""


def next_chip(st):
    nc = st.get("next_class") or ""
    if not nc and not st.get("upcoming_classes"):
        return ""
    z = f' data-z="{html.escape(st["tz"])}"' if st.get("tz") else ""
    ts = " ".join(st.get("upcoming_classes") or [])  # all upcoming classes: the page picks the next one, so it never goes blank after a class
    tsa = f' data-ts="{html.escape(ts)}"' if ts else ""
    return f'<div class="nextc" data-t="{html.escape(nc)}"{tsa}{z}><i>Next class</i><b></b></div>'


PAY_JS = """<script>(function(){var bar=document.querySelector(".paybar[data-pay]");if(!bar)return;var P;try{P=JSON.parse(bar.getAttribute("data-pay"))}catch(e){return}
var M=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],n=new Date(),td=n.getFullYear()+"-"+("0"+(n.getMonth()+1)).slice(-2)+"-"+("0"+n.getDate()).slice(-2);
function f(d){return M[+d.slice(5,7)-1]+" "+(+d.slice(8))}function fl(a){return a.map(f).join(", ")}function c(k){return k+(k==1?" class":" classes")}
var pays=(P.pays||[]).slice().sort(function(x,y){return x.date<y.date?1:-1}),paid=P.paid||[],owed=P.owed||[],cal=P.cal||[];
if(!(pays.length||paid.length||owed.length)){var m0=bar.querySelector(".more"),t0=bar.querySelector("summary small");if(m0)m0.remove();if(t0)t0.remove();return}
var due=owed.slice();cal.forEach(function(d){if(d<td&&paid.indexOf(d)<0&&due.indexOf(d)<0)due.push(d)});due.sort();
var pre=paid.filter(function(d){return d>=td}).sort(),cov={};
/* prepay students: once nothing is prepaid, the next block of N classes is due (oldest unpaid first, then upcoming calendar classes) */
var N=+P.prepay||0,blk=[];if(N&&!pre.length){blk=due.concat(cal.filter(function(d){return d>=td&&paid.indexOf(d)<0&&due.indexOf(d)<0})).sort().slice(0,N)}pays.forEach(function(p){(p.dates||[]).forEach(function(d){cov[d]=1})});
var earlier=paid.filter(function(d){return !cov[d]}).sort();
var h='<div class="ptiles">'+(blk.length?'<div class="due"><small>Next payment due</small><b>'+c(N)+'</b><span>'+(blk[0]<td?'Due now':'Due by '+f(blk[0]))+'. Covers '+f(blk[0])+' to '+f(blk[blk.length-1])+(due.length?' ('+due.length+' already held)':'')+'</span></div>':'<div class="'+(due.length?"due":"")+'"><small>You owe</small><b>'+(due.length?c(due.length):"Nothing")+'</b>'+(due.length?'<span>'+fl(due)+'</span>':'<span>All held classes are paid</span>')+'</div>')
+'<div><small>Prepaid</small><b>'+c(pre.length)+'</b>'+(pre.length?'<span>'+fl(pre)+'</span>':'<span>None left</span>')+'</div></div>';
if(pays.length||earlier.length){h+='<h4>Your payments</h4>';
pays.forEach(function(p){h+='<div class="prow"><div><b>'+f(p.date)+'</b><span>'+c(p.classes)+'</span></div>'+((p.dates&&p.dates.length)?'<small>Paid for: '+fl(p.dates)+'</small>':'')+'</div>'});
if(earlier.length)h+='<div class="prow"><div><b>Earlier</b><span>'+c(earlier.length)+'</span></div><small>Paid for: '+fl(earlier)+'</small></div>'}
bar.querySelector(".pdetail").innerHTML=h;
var hd=bar.querySelector(".pb-head");hd.textContent=blk.length?"Next payment due: "+c(N):due.length?"You owe "+c(due.length):(pre.length?c(pre.length)+" prepaid":"All your classes are paid");
bar.classList.toggle("due",due.length>0||blk.length>0);bar.querySelector("summary i").innerHTML=(due.length||blk.length)?"!":"&#10003;"})()</script>"""


def pay_bar(pay, booked=None):
    """The payment bar pinned to the bottom (tap to expand): what you owe, what is prepaid, and every payment with the classes it covered.
    Never shows prices. The numbers are worked out in the browser from today's date, so classes held since the last build count by themselves."""
    e = html.escape
    if pay.get("status") == "paid":
        head = f'Paid through {e(pay["through"])}'
    elif pay.get("status") == "via":
        head = f'Payments go through {e(pay["via"])}'
    elif pay.get("status") == "info":
        head = e(pay["head"])
    else:
        head = "Payments"
    pays = pay.get("payments") or []
    data = {"pays": pays, "paid": pay.get("paid_dates", []), "owed": pay.get("owed_dates", []), "cal": booked or [], "prepay": pay.get("prepay")}
    due = pay.get("status") == "due"
    show = pay.get("status") != "via" and (data["paid"] or data["owed"] or pays or (pay.get("status") == "info" and data["cal"]))
    more = '<div class="more"><div class="pdetail"></div><p class="pnote">Questions about your payments? Message Bianca.</p></div>' if show else ""
    tip = "<small>Details &#9652;</small>" if more else ""
    attr = f" data-pay='{html.escape(json.dumps(data), quote=True)}'" if show else ""
    bar = (f'<div class="paybar{" due" if due else ""}"{attr}><details><summary><i>{"!" if due else "&#10003;"}</i>'
           f'<b class="pb-head">{head}</b>{tip}</summary>{more}</details></div>')
    return bar + (PAY_JS if show else "")


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
    # Nov 26 2026: the final Fix File holds every homework page (embed_homework.py), so the student downloads ONE file.
    if st.get("fixfile") and os.path.exists(f"{ROOT}/{st['fixfile']}"):
        fname = f"{st['name']} - Fix File.html"
        return ('<div class="sec"><h2>Keep your work</h2></div><p class="desc" style="margin-top:0">Download your Fix File to your phone or computer. '
                'Every homework page from our cycle is saved inside it, so you can practice any week again, anytime.</p>'
                f'<div class="btns" style="margin-top:14px"><a class="btn" href="../../{html.escape(st["fixfile"])}" download="{html.escape(fname, quote=True)}"><i></i>Download my work</a></div>')
    ids = [m["id"] for m in members] if members else [st["id"]]
    files, seen = [], set()
    for c in cards:
        if c["student"] in ids and c["href"] != st.get("fixfile") and c["href"] not in seen and os.path.exists(f"{ROOT}/{c['href']}".replace("%20", " ")):
            k = week_key(c)
            who = next((m["name"] for m in members if m["id"] == c["student"]), "") if members else ""
            nm = (f"Cycle {k[0]} " if k and k[0] > 1 else "") + (f"Session {k[1]} Homework" if k else c["title"])
            seen.add(c["href"])
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


WHATSAPP, EMAIL = "16047354550", "biamtakacs@gmail.com"
TQ = [("start", "When we started, what did you want to change about your English?", ""),
      ("now", "What feels different now?", "A moment when you noticed it is perfect."),
      ("fix", "Is there a fix you catch yourself using?", "Your Fix File can jog your memory."),
      ("friend", "What would you tell someone who's thinking about doing a cycle?", ""),
      ("better", "Is there anything you'd change about the program?", "This one is just for me, and honest answers help the most.")]

TSTYLE = """<style>.tform .tq{display:block;margin:18px 0 0}.tform .tq b{display:block;font-weight:700;font-size:.95rem}.tform .tq small{display:block;color:var(--dim);font-size:.82rem;margin-top:2px}
.tform textarea{display:block;width:100%;margin-top:8px;font:inherit;font-size:.95rem;padding:12px 16px;border:0;border-radius:18px;background:var(--card);color:var(--navy);resize:vertical}
.tform textarea:focus{outline:2px solid var(--gold)}.tps{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}.tp{display:inline-flex;gap:6px;align-items:center;padding:7px 14px;border-radius:999px;background:var(--card);font-size:.86rem;cursor:pointer}</style>"""


def share_section(st):
    """Replaces the testimonial form: two sharing pictures (with a gift code, and a public one with no name on it) + the same fixed message for everyone.
    Pictures live in private/share/<id>/code.png and public.png (made with the sharing-image skill) and are copied next to the student's page."""
    if not st.get("handover"):
        return ""
    src = f"{ROOT}/private/share/{st['id']}"
    if not (os.path.exists(f"{src}/code.png") and os.path.exists(f"{src}/public.png")):
        return ""
    os.makedirs(f"{ROOT}/s/{st['slug']}", exist_ok=True)
    shutil.copy(f"{src}/code.png", f"{ROOT}/s/{st['slug']}/share-with-code.png")
    shutil.copy(f"{src}/public.png", f"{ROOT}/s/{st['slug']}/share-public.png")
    code = st.get("share_code") or "FROM" + re.sub(r"[^A-Z]", "", st["name"].upper())
    pub = st.get("public_code", "")
    t1 = ("I just finished 12 sessions with Bianca at Real English Errors and wanted to share. If you'd like to find your own real English errors, "
          "she's offering a free consultation to anyone I share this with:\n\U0001F4AC WhatsApp her: wa.me/16047354550\n"
          f"\U0001F4C5 Or book at realenglisherrors.com and use the code {code} at checkout")
    t2 = ("I just finished 12 sessions with Bianca at Real English Errors. If you'd like to find your own real English errors:\n"
          f"\U0001F4C5 Book at realenglisherrors.com and mention the code {pub}")
    def card(title, desc, img, text, name):
        return (f'<div class="sharec"><h3>{title}</h3><p>{desc}</p><img src="{img}" alt="Your results picture" loading="lazy">'
                f'<div class="shbtns"><a class="btn" href="{img}" download="{name}">Download</a>'
                f'<button type="button" class="btn ghost" data-copy="{html.escape(text, quote=True)}">Copy message</button></div></div>')
    return ('<div class="sec"><h2>Share what you learned</h2><small>Only if you want to. Neither picture shows your errors.</small></div>'
            + card("For people you know", "Your results, plus a free consultation for them with your code.", "share-with-code.png", t1, "my-results-with-code.png")
            + card("To post anywhere", "Your results with no name on it, for groups or social media.", "share-public.png", t2, "my-results.png")
            + SHARE_JS)


SHARE_JS = """<style>.sharec{background:var(--card);border-radius:24px;padding:18px;margin-bottom:14px}.sharec h3{font-weight:800;letter-spacing:-.02em;font-size:1.15rem}
.sharec p{color:var(--dim);font-size:.9rem;margin:4px 0 12px}.sharec img{display:block;width:100%;max-width:300px;max-height:420px;object-fit:cover;object-position:top;border-radius:14px;margin:0 auto 14px}
.shbtns{display:flex;gap:10px;flex-wrap:wrap}.shbtns .btn{flex:1;justify-content:center;min-height:48px;cursor:pointer;font-family:inherit}
.btn.ghost{background:transparent;border:2px solid var(--navy);color:var(--navy)}</style>
<script>document.addEventListener("click",function(e){var b=e.target.closest("[data-copy]");if(!b)return;var t=b.getAttribute("data-copy");
function ok(){var o=b.textContent;b.textContent="Copied!";setTimeout(function(){b.textContent=o},1800)}
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(ok,fb)}else fb();
function fb(){var a=document.createElement("textarea");a.value=t;a.style.position="fixed";a.style.opacity="0";document.body.appendChild(a);a.select();try{document.execCommand("copy");ok()}catch(x){}a.remove()}});</script>"""


def testimonial(st, n_hw):
    """Hand-over only: a short, open testimonial form. It sends to Bianca the same way the homework does (WhatsApp, email or copy)."""
    if not st.get("handover"):
        return ""
    e, first = html.escape, st["name"].split(" ")[0]
    facts = " · ".join(x for x in [f"{st.get('homeworks', 10) + 2} sessions", (f"{n_hw} homework pages" if n_hw != 1 else "1 homework page") if n_hw else "", "your Fix File"] if x)
    qs = "".join(f'<label class="tq"><b>{e(q)}</b>{f"<small>{e(h)}</small>" if h else ""}<textarea data-k="{k}" rows="3"></textarea></label>' for k, q, h in TQ)
    perm = "".join(f'<label class="tp"><input type="radio" name="perm" value="{e(v)}"{" checked" if i == 0 else ""}> {e(v)}</label>'
                   for i, v in enumerate([f"{first} and my country", "My initials only", "No name", "Please keep it private"]))
    return f"""<div class="sec"><h2>Share your experience</h2></div>
<div class="tform" id="tform"><p class="desc" style="margin-top:0">Looking back on our cycle: {e(facts)}. If you'd like to, tell me in your own words how it went.
Honest answers help other learners decide, and help me make the program better. Short answers are perfect, and you can skip any question.</p>
{qs}<p class="tq"><b>If I share your words, how should I sign them?</b></p><div class="tps">{perm}</div>
<div class="btns"><a class="btn gold" id="twa" href="#"><i></i>Send on WhatsApp</a><a class="btn" id="tem" href="#"><i></i>Send by email</a><a class="btn" id="tcp" href="#"><i></i>Copy</a></div>
<p class="desc" id="tmsg" role="status"></p></div>
{TSTYLE}
<script>(function(){{var K="ree-testimonial-{e(st['slug'])}",f=document.getElementById("tform"),T=f.querySelectorAll("textarea");
try{{var d=JSON.parse(localStorage.getItem(K)||"{{}}");T.forEach(function(t){{t.value=d[t.dataset.k]||""}})}}catch(x){{}}
f.addEventListener("input",function(){{var d={{}};T.forEach(function(t){{d[t.dataset.k]=t.value}});try{{localStorage.setItem(K,JSON.stringify(d))}}catch(x){{}}}});
function msg(){{var out=["Testimonial from {e(st['name'])}",""];T.forEach(function(t){{if(t.value.trim()){{out.push(t.closest(".tq").querySelector("b").textContent+(t.dataset.k==="better"?" (private)":""));out.push(t.value.trim());out.push("")}}}});
var p=f.querySelector("input[name=perm]:checked");out.push("Sign it: "+(p?p.value:""));return out.join("\\n")}}
function empty(){{return ![].some.call(T,function(t){{return t.value.trim()}})}}
function say(t){{document.getElementById("tmsg").textContent=t}}
document.getElementById("twa").onclick=function(ev){{ev.preventDefault();if(empty())return say("Write a few words first.");window.open("https://wa.me/{WHATSAPP}?text="+encodeURIComponent(msg()),"_blank");say("Thank you so much!")}};
document.getElementById("tem").onclick=function(ev){{ev.preventDefault();if(empty())return say("Write a few words first.");location.href="mailto:{EMAIL}?subject="+encodeURIComponent("My Real English Errors cycle")+"&body="+encodeURIComponent(msg());say("Thank you so much!")}};
document.getElementById("tcp").onclick=function(ev){{ev.preventDefault();if(empty())return say("Write a few words first.");navigator.clipboard.writeText(msg()).then(function(){{say("Copied. Paste it to me on WhatsApp or email. Thank you!")}},function(){{say("Copy didn't work here. Try WhatsApp or email.")}})}};
}})()</script>"""


shutil.rmtree(f"{ROOT}/s", ignore_errors=True)
for st in ACTIVE:
    if st.get("members"):
        names = [next(x for x in students if x["id"] == m) for m in st["members"]]
        out = HEAD.format(robots='<meta name="robots" content="noindex">\n', title=f"{html.escape(st['name'])} · Real English Errors", css=CSS)
        btn = (f'<div class="btns"><a class="btn" href="../../exercises/meet-{st["id"]}.html"><i></i>Join our class on Google Meet</a></div>' if st["meet"] else "")
        out += ('<header class="band"><div class="band-in"><img src="../../logo-vertical-transparent.png" alt="Real English Errors">'
                f'<div><p class="eyebrow">Your shared page</p><h1 class="hi">Hi, {html.escape(st["name"])}</h1>'
                + ('<p class="lede">One page for your shared class: payments and one shared homework each session.</p>' if st.get("shared_homework") else
                   '<p class="lede">One page for your shared class: payments for everyone, and a homework column each.</p>') +
                f'{btn}</div>{next_chip(st)}</div></header><main class="main">')
        # shared_homework: one homework page per session for the whole pair (cards use the pair's id), so one column
        cols = [dict(st, name="Your homework")] if st.get("shared_homework") else names
        out += '<div class="duo">' if len(cols) > 1 else '<div>'
        for m in cols:
            wk = sorted(((week_key(c), c) for c in cards if c["student"] == m["id"] and week_key(c)), key=lambda x: x[0], reverse=True)
            out += f'<section class="col"><div class="sec"><h2>{html.escape(m["name"])}</h2></div>'
            # the timeline shows from day one, like solo students' pages (no "appears here" placeholder)
            bywk, latest = {}, 0
            if wk:
                cyc = max(k[0] for k, _ in wk)
                out += card_html(wk[0][1], "../../")
                bywk = {k[1]: c for k, c in wk if k[0] == cyc}
                latest = max(bywk)
            total = int(m.get("homeworks", 10))
            out += '<div class="sec"><h2>Your 12 sessions</h2><small>Each homework appears here when it&rsquo;s ready</small></div><ol class="tl">'
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
            if st["fixfile"]:
                out += f'<li class="fixnode"><span class="dot">&#9733;</span><a class="tl-btn cur" href="../../{html.escape(st["fixfile"])}">Sessions 11 &amp; 12: complete Production Push &rarr;</a></li>'
            else:
                out += '<li class="fixnode"><span class="dot">&#9733;</span><span class="lbl">Sessions 11 &amp; 12: complete Production Push</span></li>'
            out += ('<li class="note"><span class="dot"></span><span class="soon">We use your Fix File in class for a complete Production Push of everything from the cycle. No new homework.</span></li>'
                    "</ol>")
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
        out += share_section(st)
        out += "</main>" + TAIL.replace("</body>", NEXT_JS + (pay_bar(st["payment"], st.get("booked_dates")) if st.get("payment") else "") + present_js(st) + "</body>")
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
    if fix and not fix_is_old and not weekly:
        btns += f'<a class="btn gold" href="../../{html.escape(fix)}">Open my Fix File</a>'
    btns = f'<div class="btns">{btns}</div>' if btns else ""
    on_cycle = bool(weekly)
    lede = (("This week&rsquo;s homework, every week before it, and your class link: everything you need between lessons, in one place."
             if st["meet"] else "This week&rsquo;s homework and every week before it: everything you need between lessons, in one place.")
            if on_cycle else ("Your homework, your Fix File and your next class: everything you need between lessons, in one place."
                              if st.get("start") else "Your practice exercises, all in one place."))
    out += ('<header class="band"><div class="band-in"><img src="../../logo-vertical-transparent.png" alt="Real English Errors">'
            f'<div><p class="eyebrow">Your personal page</p><h1 class="hi">Hi, {esc}</h1>'
            f'<p class="lede">{lede}</p>'
            f'{btns}</div>{next_chip(st)}</div></header><main class="main">')
    if weekly:
        cur_cycle = max(k[0] for k, _ in weekly)
        this = weekly[0]
        total = int(st.get("homeworks", 10))
        bywk = {k[1]: c for k, c in weekly if k[0] == cur_cycle}
        nohw = {int(n) for n in st.get("no_homework", []) if int(n) not in bywk}  # sessions held with no homework (this cycle)
        latest = max(set(bywk) | nohw)
        if latest in nohw:
            out += ('<div class="sec"><h2>This week</h2></div><div class="hero-card"><span class="now">This week</span>'
                    f'<div class="title">No homework this week</div><div class="subtitle">Session {latest} was a class-only session</div>'
                    '<p class="desc">Take a few minutes before our next class to look through your Fix File, or go back to any earlier homework below.</p></div>')
        else:
            out += f'<div class="sec"><h2>This week</h2></div>{card_html(this[1], "../../")}'
        fix_now = bool(fix) and int(st.get("fixfile_cycle", cur_cycle)) >= cur_cycle
        fixc = fix_counts(fix) if fix_now else None  # an old cycle's Fix File: its session counts don't belong on this cycle's sessions
        if fix_now:
            out += fix_card(fix, fixc, latest)
        out += f'<div class="sec"><h2>Your 12 sessions</h2><small>Each homework appears here when it&rsquo;s ready</small></div><ol class="tl">'
        for n in range(1, total + 1):
            c = bywk.get(n)
            if c:
                is_cur = (n == latest)
                cls = "cur" if is_cur else "done"
                add = (fixc or {}).get("ses", {}).get(n, 0)
                inner = (f'<a class="tl-btn{" cur" if is_cur else ""}" href="../../{c["href"]}">Session {n} Homework &rarr;</a>'
                         + (f'<span class="fc-add">+{add} cards</span>' if add else ""))
                mark = "&#10003;" if not is_cur else str(n)
            elif n in nohw:
                cls, inner, mark = ("cur" if n == latest else "done"), f'<span class="lbl">Session {n}</span><span class="soon">no homework</span>', ("&#10003;" if n < latest else str(n))
            elif n < latest:
                cls, inner, mark = "done", f'<span class="lbl">Session {n} Homework</span><span class="soon">done in class</span>', "&#10003;"
            else:
                cls, inner, mark = "", f'<span class="lbl">Session {n} Homework</span>', str(n)
            out += f'<li class="{cls}"><span class="dot">{mark}</span>{inner}</li>'
        fix_old = bool(fix) and int(st.get("fixfile_cycle", cur_cycle)) < cur_cycle
        if fix and not fix_old:
            out += (f'<li class="fixnode"><span class="dot">&#9733;</span><a class="tl-btn cur" href="../../{html.escape(fix)}">Sessions 11 &amp; 12: complete Production Push &rarr;</a></li>'
                    '<li class="note"><span class="dot"></span><span class="soon">We use your Fix File in class for a complete Production Push of everything from the cycle. No new homework.</span></li>')
        else:
            out += ('<li class="fixnode"><span class="dot">&#9733;</span><span class="lbl">Sessions 11 &amp; 12: complete Production Push</span></li>'
                    '<li class="note"><span class="dot"></span><span class="soon">We use your Fix File in class for a complete Production Push of everything from the cycle. No new homework.</span></li>')
        out += "</ol>"
        older = [(k, c) for k, c in weekly if k[0] < cur_cycle]
        prev = st.get("fixfile_prev") or {}  # a finished cycle's Fix File, once "fixfile" points at the current cycle's
        if older or fix_old or prev:
            n_old = len(older) + (1 if fix_old else 0) + (1 if prev else 0)
            out += (f'<details class="arch"><summary><h2>Your archive</h2>'
                    f'<small>Previous cycle{"s" if cur_cycle > 2 else ""} &middot; {n_old} item{"s" if n_old != 1 else ""}</small>'
                    f'<span class="chev" aria-hidden="true"></span></summary><div class="rows">')
            if prev:
                out += (f'<a class="row" href="../../{html.escape(prev["href"])}"><span class="badge alt">&#9733;</span>'
                        f'<span class="wk">Cycle {prev["cycle"]} Fix File</span><span class="sub">Final review</span><span class="go">&rarr;</span></a>')
            if fix_old:
                out += (f'<a class="row" href="../../{html.escape(fix)}"><span class="badge alt">&#9733;</span>'
                        f'<span class="wk">Cycle {st["fixfile_cycle"]} Fix File</span><span class="sub">Final review</span><span class="go">&rarr;</span></a>')
            out += "".join(row_html(c, k, "../../") for k, c in older)
            out += "</div></details>"
    if extra and (not on_cycle or st.get("show_practice")):
        out += '<div class="sec"><h2>Practice</h2></div><div class="rows">'
        out += "".join(row_html(c, None, "../../") for c in extra)
        out += "</div>"
    if not on_cycle and st.get("start"):  # enrolled, cycle not started yet: welcome them, never the sales box
        out += ('<div class="sec"><h2>Welcome</h2></div><div class="hero-card"><span class="now">Your 12-session cycle</span>'
                '<div class="title">We&rsquo;re about to start</div>'
                '<ul class="hl"><li><b>After every class</b> your homework appears here, made from your own errors</li>'
                '<li><b>Your Fix File</b> grows with every session, so the corrections stay</li>'
                '<li><b>Your next class</b> is always in the top corner of this page</li></ul></div>')
    elif not on_cycle:
        out += PROMO
    os.makedirs(f"{ROOT}/s/{st['slug']}", exist_ok=True)
    out += keep_pack(st)
    out += share_section(st)
    out += "</main>" + TAIL.replace("</body>", NEXT_JS + (pay_bar(st["payment"], st.get("booked_dates")) if st.get("payment") else "") + present_js(st) + "</body>")
    os.makedirs(f"{ROOT}/s/{st['slug']}", exist_ok=True)
    open(f"{ROOT}/s/{st['slug']}/index.html", "w").write(out)

LANDING = """<header class="band"><div class="band-in"><img src="logo-vertical-transparent.png" alt="Real English Errors: Real students. Real errors. Real fixes.">
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
