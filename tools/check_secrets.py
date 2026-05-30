#!/usr/bin/env python3
"""Garde-fou secrets (ISO 27001 A.8.24 / A.8.25) : echoue si un fichier secret connu
redevient suivi par git, ou si un secret haute-confiance est committe.

Complement leger : pour un scan complet, brancher gitleaks/detect-secrets en CI.
Usage : python tools/check_secrets.py   (exit 1 si infraction)
"""
import re
import subprocess
import sys

# Fichiers secrets retires du suivi (ne doivent jamais revenir)
FORBIDDEN_FILES = {
    "stripe_config.py", "stripe_config.env", "users.json",
    "production_users.json", "production_licenses.json",
}

# Secrets haute-confiance (faux positifs tres rares)
SECRET_PATTERNS = [
    (re.compile(r"sk_live_[0-9A-Za-z]{16,}"), "cle Stripe live"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "cle privee"),
    (re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}"), "token Slack"),
]

def tracked_files():
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout
    return [f for f in out.splitlines() if f.strip()]

def main():
    violations = []
    files = tracked_files()

    for f in files:
        name = f.rsplit("/", 1)[-1]
        if name in FORBIDDEN_FILES:
            violations.append(f"Fichier secret de nouveau suivi : {f}")

    for f in files:
        if f.startswith("tools/check_secrets.py") or f.endswith(("_template.env",)):
            continue
        try:
            content = open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for pat, label in SECRET_PATTERNS:
            if pat.search(content):
                violations.append(f"{label} detecte(e) dans {f}")

    if violations:
        print("ERREUR : secret(s) ou fichier(s) sensible(s) detecte(s) dans le suivi git :\n")
        for v in violations:
            print(f"  - {v}")
        print("\nUtilise des variables d'environnement ; ne committe jamais de secret.")
        return 1
    print("OK : aucun fichier secret connu ni secret haute-confiance dans le suivi git.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
