#!/usr/bin/env python3
import os, sys, psycopg2, json, time

url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')
conn = psycopg2.connect(url)
cur = conn.cursor()

print("Enrichissement continu jusqu'a epuisement...")
sys.stdout.flush()

total_enriched = 0
total_batches = 0
no_progress_count = 0

while no_progress_count < 3:  # Arrêter après 3 lots vides consécutifs
    total_batches += 1
    
    # Récupérer 20 prospects
    cur.execute("""
        SELECT id, commune, parcelles_cadastrales
        FROM agriweb_prospects
        WHERE parcelles_cadastrales IS NOT NULL
          AND parcelles_cadastrales NOT IN ('', '[]')
          AND proprietaire_siren IS NULL
          AND id NOT IN (1348, 1350)
        LIMIT 20
    """)
    
    prospects = cur.fetchall()
    if not prospects:
        print(f"\nPlus de prospects a traiter!")
        break
    
    batch_enriched = 0
    for pid, commune, parcelles_json in prospects:
        try:
            parcelles = json.loads(parcelles_json)
            if not parcelles:
                continue
            
            p1 = parcelles[0]
            section = p1.get('section')
            numero = p1.get('numero', '').zfill(4)
            
            if not section or not numero:
                continue
            
            # Code INSEE
            cur.execute("SELECT get_code_insee_from_commune(%s)", (commune,))
            result = cur.fetchone()
            if not result or not result[0]:
                continue
            code_insee = result[0]
            
            # Proprietaire
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
            
            # UPDATE
            cur.execute("""
                UPDATE agriweb_prospects
                SET proprietaire_siren = %s,
                    proprietaire_denomination = %s,
                    proprietaire_forme_juridique = %s,
                    proprietaire_enrichi_date = NOW()
                WHERE id = %s
            """, (siren, denom, forme, pid))
            
            batch_enriched += 1
            total_enriched += 1
            
        except Exception:
            pass
    
    conn.commit()
    
    if batch_enriched > 0:
        print(f"Lot {total_batches}: +{batch_enriched} (total: {total_enriched})")
        sys.stdout.flush()
        no_progress_count = 0
    else:
        no_progress_count += 1
        if no_progress_count == 1:
            print(f"Lot {total_batches}: 0 enrichi, verification...")
            sys.stdout.flush()

print(f"\n=== TERMINE ===")
print(f"Total enrichis: {total_enriched}")
print(f"Lots traites: {total_batches}")
sys.stdout.flush()

# Stats finales
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(proprietaire_siren) as avec_siren
    FROM agriweb_prospects
    WHERE parcelles_cadastrales IS NOT NULL 
      AND parcelles_cadastrales NOT IN ('', '[]')
""")
r = cur.fetchone()
if r:
    print(f"Base totale: {r[0]} prospects, {r[1]} avec SIREN ({r[1]/r[0]*100:.1f}%)")
    sys.stdout.flush()

conn.close()
