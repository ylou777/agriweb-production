#!/usr/bin/env python3
"""Test du padding LPAD"""
import os
import sys
import psycopg2

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

database_url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')

conn = psycopg2.connect(database_url)
cursor = conn.cursor()

# Test LPAD sur "0101"
print("[*] Test LPAD sur différentes valeurs:")

tests = ["0101", "101", "1", "0024"]

for val in tests:
    cursor.execute("SELECT LPAD(%s, 4, '0');", (val,))
    result = cursor.fetchone()[0]
    print(f"  LPAD('{val}', 4, '0') = '{result}'")

print("\n[!] PROBLÈME: LPAD('0101', 4, '0') donne '0101', pas de problème")
print("[*] Vérifions le numero réel dans la base:")

cursor.execute("""
    SELECT DISTINCT numero
    FROM proprietaires_parcelles
    WHERE code_insee = '42218'
      AND section = 'CI'
      AND numero LIKE '%101%'
    LIMIT 10;
""")

numeros = cursor.fetchall()
print(f"\n[*] Numéros dans la base pour 42218-CI:")
for n in numeros:
    print(f"  '{n[0]}' (longueur: {len(n[0])})")

cursor.close()
conn.close()
