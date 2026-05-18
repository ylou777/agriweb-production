"""Vérification des templates Jinja dans newssolar_demo.py"""
with open('newssolar_demo.py', encoding='utf-8') as f:
    lines = f.readlines()

total = len(lines)
print(f"Total lignes: {total}")

# Chercher les {% set %} avec apostrophes potentiellement problématiques
issues = []
for i, l in enumerate(lines, 1):
    if '{%' in l and 'set' in l and "'" in l:
        issues.append((i, l.rstrip()))

if issues:
    print("Tuples Jinja avec apostrophes:")
    for n, line in issues[:20]:
        print(f"  L{n}: {line[:130]}")
else:
    print("Aucun probleme detecte dans les tuples Jinja")

# Chercher les occurrences de ' dans des valeurs de tuples
import re
# look for pattern like ('...') ou ("...'...") dans les lignes de templates
apos_in_strings = []
for i, l in enumerate(lines, 1):
    # tuple items with apostrophes in single-quoted strings
    if re.search(r"\('.*?'.*?,", l):
        apos_in_strings.append((i, l.rstrip()))

if apos_in_strings:
    print("\nPossibles apostrophes dans strings Jinja:")
    for n, line in apos_in_strings[:10]:
        print(f"  L{n}: {line[:130]}")

print("\nVerification terminee")
