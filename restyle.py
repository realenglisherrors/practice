#!/usr/bin/env python3
"""Gives every src/exercises/*.html (and the Meet pages) the realenglisherrors.com look; homework pages also get
the Short / Long switch. Run by build.sh. All the look lives in site_look.py (the same script the homework skill runs)."""
import glob
from site_look import site_look

n = 0
for f in sorted(glob.glob("src/exercises/*.html") + glob.glob("private/meet/*.html")):
    s = open(f, encoding="utf-8").read()
    s2 = site_look(s)
    if s2 != s:
        open(f, "w", encoding="utf-8").write(s2); n += 1
print(f"restyled {n} pages")
