from pathlib import Path
import re
p = Path(__file__).resolve().parents[1] / 'templates' / 'rapport_commune_complet.html'
s = p.read_text(encoding='utf-8')
ifs = re.findall(r"\{\%\s*if\b", s)
endifs = re.findall(r"\{\%\s*endif\s*\%\}", s)
elifs = re.findall(r"\{\%\s*elif\b", s)
elses = re.findall(r"\{\%\s*else\b", s)
print('ifs:', len(ifs))
print('endifs:', len(endifs))
print('elifs:', len(elifs))
print('elses:', len(elses))
# dump line numbers of if openings and endifs
lines = s.splitlines()
for i,l in enumerate(lines, start=1):
    if re.search(r"\{\%\s*if\b", l):
        print(f"IF at {i}: {l.strip()}")
    if re.search(r"\{\%\s*endif\s*\%\}", l):
        print(f"ENDIF at {i}: {l.strip()}")
