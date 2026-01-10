#!/usr/bin/env python3
"""Test simple de l'enrichissement sur un prospect existant"""
import os
import sys
import psycopg2

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

database_url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')

conn = psycopg2.connect(database_url)
cursor = conn.cursor()

# Tester UPDATE sur prospect existant
print("[*] Test UPDATE sur prospect 1280 (Poitiers, 86194-IT-0060)...")

cursor.execute("""
    UPDATE agriweb_prospects
    SET commune = 'Poitiers'
    WHERE id = 1280
    RETURNING id, proprietaire_siren, proprietaire_denomination;
""")

result = cursor.fetchone()
conn.commit()

if result:
    pid, siren, denom = result
    print(f"[OK] Prospect {pid} mis à jour:")
    print(f"     SIREN: {siren}")
    print(f"     Denomination: {denom}")
    
    if siren:
        print("\n[SUCCESS] ENRICHISSEMENT FONCTIONNE!")
    else:
        print("\n[!] Pas d'enrichissement")
else:
    print("[X] Prospect non trouvé")

cursor.close()
conn.close()
