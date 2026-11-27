#!/usr/bin/env python3
"""site_look.py: give one page the realenglisherrors.com look, and a homework page its Short / Long switch.
Usage: python3 site_look.py page.html [more.html ...]   (works anywhere: repo, Cowork, claude.ai sandbox)
Generated from restyle.py (the repo runs restyle.py over src/exercises on every build.sh)."""

import glob, re, sys
START, END = "<!--ree-site-look-->", "<!--/ree-site-look-->"
BLOCK = START + """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Montserrat:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
body,button,input,textarea,select{font-family:"Inter","Helvetica Neue",Arial,sans-serif}
h1,h2,h3,.hw-title{font-family:"Montserrat","Helvetica Neue",Arial,sans-serif!important;font-weight:800!important;letter-spacing:-.02em!important}
.term,.grp-term,.pc-h,.edit .now,.dlab,.pp-h,.step b,.verb{font-family:"Inter","Helvetica Neue",Arial,sans-serif!important;font-weight:700!important;letter-spacing:-.01em!important}
.pc-h{font-size:23px!important;line-height:1.2!important}
.card{border:0!important;border-radius:24px!important;box-shadow:none!important}
.pp-row{grid-template-columns:4.6em 1fr 5.8em!important}.pp-n{white-space:nowrap}
.lenswitch{display:flex;gap:6px;margin-top:9px}.lenswitch button{flex:1;border:1.5px solid var(--line);background:transparent;color:var(--muted);border-radius:999px;padding:7px 10px;font:700 12.5px "Montserrat",sans-serif;cursor:pointer}.lenswitch button[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}
.hw-logo{border-radius:0!important;box-shadow:none!important}
.btn{border-radius:999px!important;font-weight:700}
@media (prefers-color-scheme: light){:root:not([data-theme="dark"]){--paper:#FFFFFF;--card:#F5F6FA;--line:#E3E7F0;--accent:#3C518A;--accent-soft:#E6EAF4;--mark:#DDE5F8;--pc-goldbg:#EAEEF6;--pc-goldtrack:#D3DAEA}}
:root[data-theme="light"]{--paper:#FFFFFF;--card:#F5F6FA;--line:#E3E7F0;--accent:#3C518A;--accent-soft:#E6EAF4;--mark:#DDE5F8;--pc-goldbg:#EAEEF6;--pc-goldtrack:#D3DAEA}
</style>
""" + END
FIX = START.replace("-->","-fix-->")  # unused marker kept simple
FIXCSS = """<style>
:root{--display:"Montserrat","Helvetica Neue",Arial,sans-serif;--body:"Inter","Helvetica Neue",Arial,sans-serif}
.logo,.hero .logo{border-radius:0!important;box-shadow:none!important}
.hero .logo{width:auto!important;max-width:150px!important;max-height:210px!important;opacity:.38}
@media(max-width:600px){.hero .logo{max-width:84px!important;max-height:116px!important}}
.hint{font-style:normal!important}
.rev,.tier,.pushsum,.send,.gift,.msg{border:0!important;border-radius:20px!important;background:var(--tint)!important}
.card{background:var(--surface)!important}
.card.easy,.card.g{background:#e6f4ea!important;box-shadow:inset 0 0 0 2px #2f8a4e!important}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .card.easy,:root:not([data-theme="light"]) .card.g{background:#1d3a28!important}}
@media (prefers-color-scheme: light){:root:not([data-theme="dark"]){--gold-soft:#E6EAF4}}
:root[data-theme="light"]{--gold-soft:#E6EAF4}
</style>
"""
SKIP = ()
LEN_START, LEN_END = "/*ree-len*/", "/*/ree-len*/"
LEN_JS = LEN_START + r"""
(function(){
  var key="ree-len-"+(DATA.config.storageKey||"x"), mode="long";
  var cardPages=DATA.pages.filter(function(p){return p.type==="lessons"&&!/^your sentences/i.test(p.title);});
  var hasLong=cardPages.some(function(p){return (p.blocks||[]).some(function(b){return b.kind!=="pron"&&b.tasks&&b.tasks.length;});})
    ||cardPages.some(function(p){return (p.blocks||[]).some(function(b){return b.kind==="pron"&&((b.examples||[]).length>2||(b.items||[]).some(function(i){return (i.examples||[]).length>2;}));});});
  if(!hasLong) return;
  try{mode=localStorage.getItem(key)||"long";}catch(e){}
  if(mode==="short"){
    cardPages.forEach(function(p){
      (p.blocks||[]).forEach(function(b){
        if(b.kind==="pron"){ if(b.examples) b.examples=b.examples.slice(0,2); (b.items||[]).forEach(function(i){ if(i.examples) i.examples=i.examples.slice(0,2); }); }
        else { delete b.practice; delete b.tasks; }
      });
      if(/^grammar/i.test(p.title)&&p.lede) p.lede="Read the correction and the rule. You'll practice them in the next pages.";
      else if(/^vocab/i.test(p.title)&&p.lede) p.lede="Read each card. You'll practice every one of them in the next pages.";
    });
  }
  var host=document.querySelector(".top-inner"); if(!host) return;
  var w=document.createElement("div"); w.className="lenswitch"; w.setAttribute("role","group"); w.setAttribute("aria-label","Homework length");
  [["short","Short · ~25 min"],["long","Long · ~45 min"]].forEach(function(o){
    var b=document.createElement("button"); b.type="button"; b.textContent=o[1]; b.setAttribute("aria-pressed",String(mode===o[0]));
    b.onclick=function(){ if(mode===o[0]) return; try{localStorage.setItem(key,o[0]);}catch(e){} location.reload(); };
    w.appendChild(b);
  });
  host.appendChild(w);
})();
""" + LEN_END

# the transparent vertical logo (logo-vertical-transparent.png), so the homework header matches the site and Fix Files.
# Read from the repo when it's there, otherwise from the live site (so this script also works in the skill sandbox).
def _logo():
    import base64, os, urllib.request
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo-vertical-transparent.png")
    try:
        data = open(here, "rb").read()
    except OSError:
        data = urllib.request.urlopen("https://realenglisherrors.github.io/practice/logo-vertical-transparent.png", timeout=20).read()
    return "data:image/png;base64," + base64.b64encode(data).decode()


LOGO = None


def _get_logo():
    global LOGO
    LOGO = LOGO or _logo()
    return LOGO


# Older homework pages opened with a bare logo picture (the "sticker"), a date and a heading. Give them the same blue header band
# (transparent logo, eyebrow, heading, date) as the newer pages. No "Due" pill: these are past weeks. Safe to run twice.
HERO_START, HERO_END = "/*hw-hero-legacy*/", "/*end hw-hero-legacy*/"
HERO_CSS = HERO_START + """
.hw-hero{position:relative;overflow:hidden;background:#3C518A;color:#fff;border-radius:16px;margin:0 0 18px;display:grid;grid-template-columns:minmax(0,118px) minmax(0,1fr);gap:16px;align-items:center;padding:16px}
.hw-hero::before{content:"";position:absolute;right:-180px;top:-200px;width:460px;height:460px;border-radius:50%;background:radial-gradient(circle,rgba(217,174,74,.28),rgba(217,174,74,0) 65%);pointer-events:none}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .hw-hero{background:#24305A}}
:root[data-theme="dark"] .hw-hero{background:#24305A}
.hw-logo{position:relative;display:block;width:100%;height:auto;border-radius:0;box-shadow:none}
.hw-text{position:relative;min-width:0}
.hw-eye{margin:0 0 6px;font-family:"Montserrat","Helvetica Neue",Arial,sans-serif;font-weight:700;font-size:11.5px;letter-spacing:.15em;color:#D9AE4A}
.hw-hero h1{position:relative;color:#fff;font-size:26px;line-height:1.12;margin:0 0 10px}
.hw-hero .date{position:relative;color:#DFE4F4;font-size:14.5px;margin:0}
@media (max-width:360px){.hw-hero{grid-template-columns:minmax(0,92px) minmax(0,1fr);gap:12px;padding:14px}.hw-hero h1{font-size:23px}}
""" + HERO_END
_OLD_HERO = re.compile(r'<img class="brand-logo" src="data:image/png;base64,[A-Za-z0-9+/=]+" alt="([^"]*)">\s*<p class="date">Week \$\{C\.week\}, \$\{C\.date\}</p>\s*<h1>Your homework, \$\{C\.student\}</h1>')


def upgrade_header(s):
    if ".hw-hero{" in s:  # already has the band styles (newer pages carry their own; upgraded pages carry ours)
        return s
    if _OLD_HERO.search(s):
        s = _OLD_HERO.sub(lambda m: ('<header class="hw-hero"><img class="hw-logo" src="' + _get_logo() + '" alt="' + m.group(1) + '">'
                     '<div class="hw-text"><p class="hw-eye">${C.student.toUpperCase()}\'S HOMEWORK</p>'
                     '<h1>Your homework, ${C.student}</h1><p class="date">Week ${C.week}, ${C.date}</p></div></header>'), s, count=1)
    if 'class="hw-hero"' in s:
        s = s.replace("</head>", "<style>" + HERO_CSS + "</style>\n</head>", 1)
    return s


# --- fix-marks: highlight the changed words in correction cards (Bianca, Nov 26, 2026) ---
FX_JS = r'''
/* fix-marks: highlight the words that changed in a correction (was -> now) */
function fxMark(was,now){
  if(!was||!now||/[<>]/.test(now)) return now||"";
  const norm=w=>w.toLowerCase().replace(/[^a-z0-9'’]/g,"");
  const a=String(was).replace(/<[^>]*>/g,"").split(/\s+/).filter(Boolean).map(norm), bw=String(now).split(/(\s+)/);
  const b=bw.filter(t=>!/^\s+$/.test(t)&&t!==""), bn=b.map(norm);
  const n=a.length,m=b.length,L=Array.from({length:n+1},()=>new Array(m+1).fill(0));
  for(let i=n-1;i>=0;i--)for(let j=m-1;j>=0;j--)L[i][j]=a[i]&&a[i]===bn[j]?L[i+1][j+1]+1:Math.max(L[i+1][j],L[i][j+1]);
  const keep=new Array(m).fill(false);let i=0,j=0;
  while(i<n&&j<m){ if(a[i]&&a[i]===bn[j]){keep[j]=true;i++;j++;} else if(L[i+1][j]>=L[i][j+1]) i++; else j++; }
  const wasW=String(was).replace(/<[^>]*>/g,"").split(/\s+/).filter(Boolean);
  let k=0; return bw.map(t=>{ if(/^\s+$/.test(t)||t==="") return t; const idx=k++;
    if(keep[idx]||/^\[|\]$/.test(t)||!bn[idx]) return t;
    const ap=t.search(/['’]/);   /* contraction: it'll -> it'd marks only 'd */
    if(ap>0&&wasW.some(w=>w.toLowerCase().slice(0,ap+1).replace("’","'")===t.toLowerCase().slice(0,ap+1).replace("’","'")))
      return t.slice(0,ap)+`<mark class="fx">${t.slice(ap)}</mark>`;
    return `<mark class="fx">${t}</mark>`; }).join("");
}
'''
FX_CSS = '<style id="fix-marks">.edit .now mark.fx{background:#FFF1B8;color:inherit;padding:0 3px;margin:0 -1px;border-radius:4px;-webkit-box-decoration-break:clone;box-decoration-break:clone}</style>'
OLD = '<span class="now">${b.now}</span>'
NEW = '<span class="now">${fxMark(b.was,b.now)}</span>'


def fix_marks(s):
    """Homework pages: highlight the changed words in every correction card. Safe to run twice."""
    if OLD not in s or 'function fxMark' in s:
        return s
    s = s.replace(OLD, NEW)
    i = s.find('const DATA = {')
    s = s[:i] + FX_JS.strip() + '\n' + s[i:]
    return s.replace('</head>', FX_CSS + '</head>', 1)


def site_look(s):
    """Return the page with the realenglisherrors.com look (and, for homework pages, the Short / Long switch). Safe to run twice."""
    s2 = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", s, flags=re.S)
    if "--display:" in s2:  # Fix File / Error Bank: styles live in <body>, so go last
        blk = BLOCK[:-len(END)] + FIXCSS + END
        k = s2.rfind("</body>")
        return (s2[:k] + blk + "\n" + s2[k:]) if k != -1 else s2 + blk
    if "</head>" not in s2:
        return s2
    s2 = upgrade_header(s2)
    s2 = re.sub(r'(<img[^>]*class="hw-logo"[^>]*src=")(data:image/[^"]+)(")', lambda m: m.group(1) + _get_logo() + m.group(3), s2)
    s2 = fix_marks(s2)
    s2 = s2.replace("</head>", BLOCK + "\n</head>", 1)
    s2 = re.sub(re.escape(LEN_START) + r".*?" + re.escape(LEN_END) + r"\n?", "", s2, flags=re.S)
    m = re.search(r"const DATA = \{.*?\};\n", s2, flags=re.S)
    if m and "config" in m.group(0)[:40]:
        s2 = s2[:m.end()] + LEN_JS + "\n" + s2[m.end():]
    return s2


if __name__ == "__main__":
    for f in sys.argv[1:]:
        s = open(f, encoding="utf-8").read(); s2 = site_look(s)
        if s2 != s:
            open(f, "w", encoding="utf-8").write(s2)
        print(("styled " if s2 != s else "already styled ") + f, "· Short/Long switch:", "yes" if "ree-len" in s2 else "no (not a homework page)")
