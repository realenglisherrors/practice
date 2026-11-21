# Usage: python3 fixfile_restyle.py in.html out.html  (adds the site look to a Fix File; run after fill.py)
import sys,re,importlib.util
spec=importlib.util.spec_from_file_location("r","/Users/bianca/Desktop/HACKING/practice/restyle.py")
# reuse the block text from restyle.py without running its loop
src=open("/Users/bianca/Desktop/HACKING/practice/restyle.py").read()
ns={}
exec(src.split("LEN_START, LEN_END")[0].replace("import glob, re, sys",""),{"re":re},ns)
blk=ns["BLOCK"][:-len(ns["END"])]+ns["FIXCSS"]+ns["END"]
f=sys.argv[1]; s=open(f,encoding="utf-8").read()
s=re.sub(re.escape(ns["START"])+r".*?"+re.escape(ns["END"])+r"\n?","",s,flags=re.S)
k=s.rfind("</body>"); s=s[:k]+blk+"\n"+s[k:]
open(sys.argv[2],"w",encoding="utf-8").write(s); print("ok",len(s))
