import psycopg2
import os
import json

conn = psycopg2.connect(os.environ['DATABASE_PUBLIC_URL'])
cur = conn.cursor()

print("DEBUG: TEST ENRICHISSEMENT D'UN PROSPECT REEL")
print("="*70)

# Prendre un prospect avec parcelle
cur.execute("""
    SELECT id, commune, parcelles_cadastrales
    FROM agriweb_prospects
    WHERE parcelles_cadastrales IS NOT NULL 
      AND parcelles_cadastrales != ''
      AND parcelles_cadastrales != '[]'
      AND proprietaire_siren IS NULL
      AND commune IS NOT NULL
      AND commune NOT LIKE 'Commune %'  -- Exclure les noms génériques
    ORDER BY RANDOM()
    LIMIT 1;
""")

prospect = cur.fetchone()
if not prospect:
    print("Aucun prospect à tester")
    exit()

prospect_id, commune, parcelles_json = prospect

print(f"\nProspect ID: {prospect_id}")
print(f"Commune: {commune}")
print(f"Parcelles JSON: {parcelles_json[:100]}")

# Parser les parcelles
parcelles = json.loads(parcelles_json)
if parcelles and len(parcelles) > 0:
    parcelle = parcelles[0]
    section = parcelle.get('section', '')
    numero = parcelle.get('numero', '').zfill(4)
    
    print(f"\nParcelle: {section}-{numero}")
    
    # 1. Vérifier que la commune est dans le cache
    print(f"\n1. Vérification du cache pour '{commune}':")
    cur.execute("""
        SELECT code_insee, nom_complet
        FROM communes_insee_cache
        WHERE nom_commune_lower = LOWER(%s);
    """, (commune,))
    
    cache_result = cur.fetchone()
    if cache_result:
        code_insee = cache_result[0]
        print(f"   ✓ Trouvé dans cache: {code_insee} - {cache_result[1]}")
        
        # 2. Chercher la parcelle avec ce code INSEE
        print(f"\n2. Recherche de la parcelle {code_insee}-{section}-{numero}:")
        cur.execute("""
            SELECT siren, denomination, forme_juridique
            FROM proprietaires_parcelles
            WHERE (code_commune = %s OR code_insee = %s)
              AND section = %s
              AND numero = %s
            LIMIT 1;
        """, (code_insee, code_insee, section, numero))
        
        prop_result = cur.fetchone()
        if prop_result:
            print(f"   ✓ PROPRIETAIRE TROUVE!")
            print(f"     SIREN: {prop_result[0]}")
            print(f"     Dénomination: {prop_result[1]}")
            print(f"     Forme juridique: {prop_result[2]}")
            
            # 3. Tester le trigger en faisant un UPDATE
            print(f"\n3. Test du trigger via UPDATE...")
            cur.execute("""
                UPDATE agriweb_prospects
                SET parcelles_cadastrales = parcelles_cadastrales
                WHERE id = %s
                RETURNING proprietaire_siren, proprietaire_denomination;
            """, (prospect_id,))
            
            update_result = cur.fetchone()
            conn.commit()
            
            if update_result and update_result[0]:
                print(f"   ✅ TRIGGER A ENRICHI LE PROSPECT!")
                print(f"      SIREN: {update_result[0]}")
                print(f"      Dénomination: {update_result[1]}")
            else:
                print(f"   ❌ Le trigger N'A PAS enrichi le prospect")
                print(f"      Il y a un problème dans la logique du trigger")
        else:
            print(f"   ✗ Propriétaire NON TROUVE pour {code_insee}-{section}-{numero}")
            
            # Chercher des parcelles similaires
            cur.execute("""
                SELECT code_commune, code_insee, section, numero, siren
                FROM proprietaires_parcelles
                WHERE (code_commune = %s OR code_insee = %s)
                  AND section = %s
                LIMIT 3;
            """, (code_insee, code_insee, section))
            
            similaires = cur.fetchall()
            if similaires:
                print(f"\n   Parcelles similaires trouvées dans cette section:")
                for s in similaires:
                    print(f"      {s[0] or s[1]}-{s[2]}-{s[3]} | SIREN: {s[4]}")
            else:
                print(f"\n   Aucune parcelle section {section} pour commune {code_insee}")
    else:
        print(f"   ✗ Commune '{commune}' NON TROUVEE dans le cache")
        print(f"      Le trigger ne pourra pas enrichir ce prospect")

cur.close()
conn.close()
