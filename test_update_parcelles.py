#!/usr/bin/env python3
"""Test UPDATE avec changement de parcelles"""
import os
import sys
import psycopg2

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

database_url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')

conn = psycopg2.connect(database_url)
cursor = conn.cursor()

# Récupérer les parcelles actuelles
cursor.execute("SELECT parcelles_cadastrales FROM agriweb_prospects WHERE id = 158;")
parcelles_actuelles = cursor.fetchone()[0]

print("[*] Test UPDATE en modifiant les parcelles (trigger UPDATE OF parcelles_cadastrales)...")
print(f"    Parcelles actuelles: {str(parcelles_actuelles)[:80]}...\n")

# Modifier légèrement pour déclencher le trigger
cursor.execute("""
    UPDATE agriweb_prospects
    SET parcelles_cadastrales = parcelles_cadastrales  -- Force trigger
    WHERE id = 158
    RETURNING id, proprietaire_siren, proprietaire_denomination;
""")

result = cursor.fetchone()
conn.commit()

if result:
    pid, siren, denom = result
    print(f"[OK] Prospect {pid}:")
    print(f"     SIREN: {siren}")
    print(f"     Denomination: {denom}")
    
    if siren:
        print("\n[SUCCESS] ENRICHISSEMENT FONCTIONNE!")
    else:
        print("\n[!] Toujours pas d'enrichissement")
        print("\n[DEBUG] Test manuel de la requête SQL du trigger:")
        
        import json
        parcelles = json.loads(parcelles_actuelles)
        p1 = parcelles[0]
        
        # Obtenir code INSEE
        cursor.execute("SELECT get_code_insee_from_commune('Saint-Étienne');")
        code_insee = cursor.fetchone()[0]
        
        section = p1.get('section')
        numero = p1.get('numero', '').zfill(4)
        
        print(f"\n     Recherche: code={code_insee}, section={section}, numero={numero}")
        
        cursor.execute("""
            SELECT siren, denomination
            FROM proprietaires_parcelles
            WHERE (code_commune = %s OR code_insee = %s)
              AND section = %s
              AND numero = %s
              AND siren IS NOT NULL
            LIMIT 1;
        """, (code_insee, code_insee, section, numero))
        
        prop = cursor.fetchone()
        if prop:
            print(f"     [OK] Requête manuelle trouve: SIREN {prop[0]}")
            print(f"     [!] Le trigger a un problème de logique")
        else:
            print(f"     [X] Requête manuelle ne trouve pas non plus")

cursor.close()
conn.close()
