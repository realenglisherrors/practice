#!/usr/bin/env python3
"""Injects the realenglisherrors.com look (Montserrat, pale borderless cards, site blue)
into every src/exercises/*.html. Idempotent: replaces its own block. Run by build.sh."""
import glob, re, sys
START, END = "<!--ree-site-look-->", "<!--/ree-site-look-->"
BLOCK = START + """
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
body,button,input,textarea,select{font-family:"Montserrat","Helvetica Neue",Arial,sans-serif}
h1,h2,h3,.term,.grp-term,.pc-h,.edit .now,.hw-title{font-family:"Montserrat","Helvetica Neue",Arial,sans-serif!important;font-weight:800!important;letter-spacing:-.02em!important}
.pc-h{font-size:23px!important;line-height:1.2!important}
.card{border:0!important;border-radius:24px!important;box-shadow:none!important}
.pp-row{grid-template-columns:4.6em 1fr 5.8em!important}.pp-n{white-space:nowrap}
.hw-logo{border-radius:0!important;box-shadow:none!important}
.btn{border-radius:999px!important;font-weight:700}
@media (prefers-color-scheme: light){:root:not([data-theme="dark"]){--paper:#FFFFFF;--card:#F5F6FA;--line:#E3E7F0;--accent:#3C518A;--accent-soft:#E6EAF4;--mark:#DDE5F8;--pc-goldbg:#EAEEF6;--pc-goldtrack:#D3DAEA}}
:root[data-theme="light"]{--paper:#FFFFFF;--card:#F5F6FA;--line:#E3E7F0;--accent:#3C518A;--accent-soft:#E6EAF4;--mark:#DDE5F8;--pc-goldbg:#EAEEF6;--pc-goldtrack:#D3DAEA}
</style>
""" + END
n = 0
for f in sorted(glob.glob("src/exercises/*.html")+glob.glob("private/meet/*.html")):
    s = open(f, encoding="utf-8").read()
    if "</head>" not in s: continue
    s2 = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", s, flags=re.S)
    s2 = s2.replace("</head>", BLOCK + "\n</head>", 1)
    if s2 != s:
        open(f, "w", encoding="utf-8").write(s2); n += 1
print(f"restyled {n} pages")
