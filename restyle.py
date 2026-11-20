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
.lenswitch{display:flex;gap:6px;margin-top:9px}.lenswitch button{flex:1;border:1.5px solid var(--line);background:transparent;color:var(--muted);border-radius:999px;padding:7px 10px;font:700 12.5px "Montserrat",sans-serif;cursor:pointer}.lenswitch button[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}
.hw-logo{border-radius:0!important;box-shadow:none!important}
.btn{border-radius:999px!important;font-weight:700}
@media (prefers-color-scheme: light){:root:not([data-theme="dark"]){--paper:#FFFFFF;--card:#F5F6FA;--line:#E3E7F0;--accent:#3C518A;--accent-soft:#E6EAF4;--mark:#DDE5F8;--pc-goldbg:#EAEEF6;--pc-goldtrack:#D3DAEA}}
:root[data-theme="light"]{--paper:#FFFFFF;--card:#F5F6FA;--line:#E3E7F0;--accent:#3C518A;--accent-soft:#E6EAF4;--mark:#DDE5F8;--pc-goldbg:#EAEEF6;--pc-goldtrack:#D3DAEA}
</style>
""" + END
FIX = START.replace("-->","-fix-->")  # unused marker kept simple
FIXCSS = """<style>
:root{--display:"Montserrat","Helvetica Neue",Arial,sans-serif;--body:"Montserrat","Helvetica Neue",Arial,sans-serif}
.logo,.hero .logo{border-radius:0!important;box-shadow:none!important}
.hero .logo{max-width:300px!important}
.hint{font-style:normal!important}
.rev,.tier,.pushsum,.send,.gift,.msg{border:0!important;border-radius:20px!important;background:var(--tint)!important}
.card{background:var(--surface)!important}
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
n = 0
for f in sorted(glob.glob("src/exercises/*.html")+glob.glob("private/meet/*.html")):
    s = open(f, encoding="utf-8").read()
    if "</head>" not in s : continue
    s2 = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", s, flags=re.S)
    if "--display:" in s2:  # Fix File: styles live in <body>, so go last
        blk = BLOCK[:-len(END)] + FIXCSS + END
        k = s2.rfind("</body>")
        s2 = (s2[:k] + blk + "\n" + s2[k:]) if k != -1 else s2 + blk
    else:
        s2 = s2.replace("</head>", BLOCK + "\n</head>", 1)
        s2 = re.sub(re.escape(LEN_START) + r".*?" + re.escape(LEN_END) + r"\n?", "", s2, flags=re.S)
        m = re.search(r"const DATA = \{.*?\};\n", s2, flags=re.S)
        if m and "config" in m.group(0)[:40]:
            s2 = s2[:m.end()] + LEN_JS + "\n" + s2[m.end():]
    if s2 != s:
        open(f, "w", encoding="utf-8").write(s2); n += 1
print(f"restyled {n} pages")
