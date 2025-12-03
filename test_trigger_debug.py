#!/usr/bin/env python3
"""Debug du trigger avec les logs NOTICE"""
import os
import sys
import psycopg2

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

database_url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')

conn = psycopg2.connect(database_url)
# Activer les NOTICE
conn.set_session(autocommit=False)
cursor = conn.cursor()

# Récupérer les notices PostgreSQL
notices = []
def notice_receiver(notice):
    notices.append(notice.pgerror)

conn.notices = []

# Tester UPDATE sur prospect existant avec parcelle connue
print("[*] Test UPDATE sur prospect 158 (Saint-Étienne, 42218-CI-0101)...")
print("    Parcelle devrait avoir SIREN 214202186 (COMMUNE DE SAINT ETIENNE)\n")

cursor.execute("""
    UPDATE agriweb_prospects
    SET commune = commune  -- Déclencher le trigger
    WHERE id = 158
    RETURNING id, commune, parcelles_cadastrales::text, 
              proprietaire_siren, proprietaire_denomination;
""")

result = cursor.fetchone()
conn.commit()

# Afficher les notices
if conn.notices:
    print("\n[LOGS TRIGGER]:")
    for notice in conn.notices:
        print(f"  {notice.strip()}")

if result:
    pid, commune, parcelles, siren, denom = result
    print(f"\n[OK] Prospect {pid} ({commune}):")
    print(f"     Parcelles: {parcelles[:100]}...")
    print(f"     SIREN: {siren}")
    print(f"     Denomination: {denom}")
    
    if siren:
        print("\n[SUCCESS] ENRICHISSEMENT FONCTIONNE!")
    else:
        print("\n[!] Pas d'enrichissement - vérifier les logs ci-dessus")

cursor.close()
conn.close()
