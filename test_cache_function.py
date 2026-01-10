#!/usr/bin/env python3
"""Test de la fonction get_code_insee_from_commune"""
import os
import sys
import psycopg2

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

database_url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')

conn = psycopg2.connect(database_url)
cursor = conn.cursor()

# Test 1: Fonction existe ?
print("[*] Vérification de la fonction get_code_insee_from_commune...")
cursor.execute("""
    SELECT proname FROM pg_proc WHERE proname = 'get_code_insee_from_commune';
""")
result = cursor.fetchone()
if result:
    print("[OK] Fonction existe")
else:
    print("[X] Fonction manquante!")
    sys.exit(1)

# Test 2: Test de la fonction
communes_test = ['Saint-Étienne', 'Poitiers', 'Limoges', 'Guéret']

print("\n[*] Test de la fonction:")
for commune in communes_test:
    cursor.execute("""
        SELECT get_code_insee_from_commune(%s);
    """, (commune,))
    
    code = cursor.fetchone()[0]
    print(f"  {commune:20} -> {code or 'NON TROUVÉ'}")

# Test 3: Chercher parcelle manuellement
print("\n[*] Test recherche parcelle 42218-CI-0101:")
cursor.execute("""
    SELECT code_commune, code_insee, section, numero, siren, denomination
    FROM proprietaires_parcelles
    WHERE (code_commune = '42218' OR code_insee = '42218')
      AND section = 'CI'
      AND numero = '0101'
      AND siren IS NOT NULL
    LIMIT 1;
""")

parcelle = cursor.fetchone()
if parcelle:
    print(f"  [OK] Parcelle trouvée:")
    print(f"       code_commune: {parcelle[0]}")
    print(f"       code_insee: {parcelle[1]}")
    print(f"       section: {parcelle[2]}")
    print(f"       numero: {parcelle[3]}")
    print(f"       siren: {parcelle[4]}")
    print(f"       denomination: {parcelle[5]}")
else:
    print("  [X] Parcelle non trouvée")

# Test 4: Simuler exactement ce que fait le trigger
print("\n[*] Simulation du trigger pour prospect 158:")
cursor.execute("""
    SELECT id, commune, parcelles_cadastrales
    FROM agriweb_prospects
    WHERE id = 158;
""")

prospect = cursor.fetchone()
if prospect:
    pid, commune, parcelles_json = prospect
    print(f"  Prospect: {pid}")
    print(f"  Commune: {commune}")
    print(f"  Parcelles JSON: {str(parcelles_json)[:100]}...")
    
    # Parser la première parcelle
    import json
    parcelles = json.loads(parcelles_json)
    p1 = parcelles[0]
    
    print(f"\n  Première parcelle:")
    print(f"    code_commune (JSON): '{p1.get('commune', '')}'")
    print(f"    section: {p1.get('section')}")
    print(f"    numero: {p1.get('numero')}")
    
    # Appeler la fonction de cache
    cursor.execute("SELECT get_code_insee_from_commune(%s);", (commune,))
    code_insee = cursor.fetchone()[0]
    print(f"\n  get_code_insee_from_commune('{commune}') = {code_insee}")
    
    # Chercher la parcelle avec ce code
    numero_padded = p1.get('numero', '').zfill(4)
    cursor.execute("""
        SELECT siren, denomination
        FROM proprietaires_parcelles
        WHERE (code_commune = %s OR code_insee = %s)
          AND section = %s
          AND numero = %s
          AND siren IS NOT NULL
        LIMIT 1;
    """, (code_insee, code_insee, p1.get('section'), numero_padded))
    
    prop = cursor.fetchone()
    if prop:
        print(f"\n  [OK] Propriétaire trouvé:")
        print(f"       SIREN: {prop[0]}")
        print(f"       Denomination: {prop[1]}")
    else:
        print(f"\n  [X] Propriétaire non trouvé pour {code_insee}-{p1.get('section')}-{numero_padded}")

cursor.close()
conn.close()
