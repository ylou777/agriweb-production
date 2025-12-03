#!/usr/bin/env python3
import os, sys, psycopg2, json, time

url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')
conn = psycopg2.connect(url)
cur = conn.cursor()

print("Enrichissement par petits lots de 10...")
sys.stdout.flush()

total_enriched = 0
batch_num = 0

while batch_num < 10:
    batch_num += 1
    
    # Récupérer 10 prospects
    cur.execute("""
        SELECT id, commune, parcelles_cadastrales
        FROM agriweb_prospects
        WHERE parcelles_cadastrales IS NOT NULL
          AND parcelles_cadastrales NOT IN ('', '[]')
          AND proprietaire_siren IS NULL
        LIMIT 10
    """)
    
    prospects = cur.fetchall()
    if not prospects:
        print(f"\nLot {batch_num}: Plus de prospects")
        break
    
    print(f"\nLot {batch_num}: {len(prospects)} prospects")
    sys.stdout.flush()
    
    batch_enriched = 0
    for pid, commune, parcelles_json in prospects:
        try:
            # Parser parcelles (JSON ou texte)
            try:
                parcelles = json.loads(parcelles_json)
                if not parcelles:
                    continue
                p1 = parcelles[0]
                section = p1.get('section')
                numero = p1.get('numero', '').zfill(4)
            except (json.JSONDecodeError, ValueError):
                # Format texte: "CODE-SECTION-NUMERO"
                parts = parcelles_json.split('-')
                if len(parts) >= 3:
                    section = parts[1]
                    numero = parts[2].zfill(4)
                else:
                    continue
            
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
            print(f"  {pid}: {siren} - {denom[:30]}")
            sys.stdout.flush()
            
        except Exception as e:
            print(f"  Erreur {pid}: {str(e)[:40]}")
            sys.stdout.flush()
    
    conn.commit()
    print(f"  --> {batch_enriched} enrichis dans ce lot")
    sys.stdout.flush()
    time.sleep(0.5)

print(f"\n\nTOTAL ENRICHIS: {total_enriched}")
sys.stdout.flush()

conn.close()
