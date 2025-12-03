#!/usr/bin/env python3
"""Enrichissement manuel prospect par prospect"""
import os, sys, psycopg2, json

url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')
conn = psycopg2.connect(url)
cur = conn.cursor()

print("Enrichissement manuel de 100 prospects...")

# Récupérer prospects à enrichir
cur.execute("""
    SELECT id, commune, parcelles_cadastrales
    FROM agriweb_prospects
    WHERE parcelles_cadastrales IS NOT NULL
      AND parcelles_cadastrales != ''
      AND parcelles_cadastrales != '[]'
      AND proprietaire_siren IS NULL
    LIMIT 1000
""")

prospects = cur.fetchall()
print(f"{len(prospects)} prospects a traiter")

enriched = 0

for pid, commune, parcelles_json in prospects:
    try:
        # Parser parcelles
        parcelles = json.loads(parcelles_json)
        if not parcelles or len(parcelles) == 0:
            continue
        p1 = parcelles[0]
        section = p1.get('section')
        numero = p1.get('numero', '').zfill(4)
        
        # Obtenir code INSEE
        cur.execute("SELECT get_code_insee_from_commune(%s)", (commune,))
        result = cur.fetchone()
        if not result or not result[0]:
            continue
        code_insee = result[0]
        
        # Chercher proprietaire
        cur.execute("""
            SELECT siren, denomination, forme_juridique
            FROM proprietaires_parcelles
            WHERE (code_commune = %s OR code_insee = %s)
              AND section = %s
              AND numero = %s
              AND siren IS NOT NULL
            LIMIT 1
        """, (code_insee, code_insee, section, numero))
        
        prop = cur.fetchone()
        if not prop:
            continue
        
        siren, denom, forme = prop
        
        # Enrichir
        cur.execute("""
            UPDATE agriweb_prospects
            SET proprietaire_siren = %s,
                proprietaire_denomination = %s,
                proprietaire_forme_juridique = %s,
                proprietaire_enrichi_date = NOW()
            WHERE id = %s
        """, (siren, denom, forme, pid))
        
        enriched += 1
        if enriched <= 20:
            print(f"  {enriched}. Prospect {pid}: {siren} - {denom[:40]}")
        
    except Exception as e:
        print(f"  Erreur prospect {pid}: {e}")
        continue

conn.commit()
print(f"\nEnrichis: {enriched}/{len(prospects)}")

# Stats finales
cur.execute("SELECT COUNT(*), COUNT(proprietaire_siren) FROM agriweb_prospects WHERE parcelles_cadastrales IS NOT NULL")
r = cur.fetchone()
print(f"Total: {r[0]}, SIREN: {r[1]} ({r[1]/r[0]*100:.1f}%)")

conn.close()
