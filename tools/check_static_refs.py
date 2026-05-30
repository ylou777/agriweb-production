#!/usr/bin/env python3
"""Garde-fou : echoue si un template Jinja reference un asset en chemin /static absolu.

Toute ressource statique DOIT passer par {{ url_for('static', filename='...') }}.
Les chemins '/static/...' en dur cassent silencieusement derriere un prefixe d'URL,
un reverse-proxy ou un CDN (cf. bug des vignettes homepage, mai 2026).

Usage : python tools/check_static_refs.py   (exit 1 si infraction)
"""
import re
import sys
import glob

PATTERN = re.compile(r"""\b(?:src|href)\s*=\s*["']/static/""")

def main():
    violations = []
    for path in glob.glob("templates/**/*.html", recursive=True):
        with open(path, encoding="utf-8", errors="ignore") as fh:
            for n, line in enumerate(fh, 1):
                if PATTERN.search(line):
                    violations.append((path, n, line.strip()[:100]))

    if violations:
        print("ERREUR : references /static absolues interdites dans les templates.")
        print("Utilise {{ url_for('static', filename='...') }} a la place.\n")
        for path, n, snippet in violations:
            print(f"  {path}:{n}: {snippet}")
        print(f"\n{len(violations)} infraction(s).")
        return 1
    print("OK : aucune reference /static absolue dans les templates.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
