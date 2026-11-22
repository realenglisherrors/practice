# Usage: python3 fixfile_restyle.py in.html out.html  (adds the site look to a Fix File or an Error Bank; run after fill.py)
import sys,re,base64,importlib.util
spec=importlib.util.spec_from_file_location("r","/Users/bianca/Desktop/HACKING/practice/restyle.py")
# reuse the block text from restyle.py without running its loop
src=open("/Users/bianca/Desktop/HACKING/practice/restyle.py").read()
ns={}
exec(src.split("LEN_START, LEN_END")[0].replace("import glob, re, sys",""),{"re":re},ns)
blk=ns["BLOCK"][:-len(ns["END"])]+ns["FIXCSS"]+ns["END"]
EB=open("/Users/bianca/Desktop/HACKING/practice/errorbank_look.css").read()
f=sys.argv[1]; s=open(f,encoding="utf-8").read()
s=re.sub(re.escape(ns["START"])+r".*?"+re.escape(ns["END"])+r"\n?","",s,flags=re.S)
# swap the wide logo for the vertical one (all Fix Files)
vb="data:image/png;base64,"+base64.b64encode(open("/Users/bianca/Desktop/HACKING/practice/logo-vertical-transparent.png","rb").read()).decode()
s=re.sub(r'(<img[^>]*class="logo"[^>]*src=")(data:image/[^"]+)(")',lambda m:m.group(1)+vb+m.group(3),s)
if "Error Bank" in s[:3000]:  # Error Banks: soft cards, and Yes / Filmed keep their colour once borders are gone
    blk=blk.replace(ns["END"],EB+ns["END"])
k=s.rfind("</body>"); s=s[:k]+blk+"\n"+s[k:]
open(sys.argv[2],"w",encoding="utf-8").write(s); print("ok",len(s))
