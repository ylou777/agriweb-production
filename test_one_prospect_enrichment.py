import psycopg2
import os
import json
import requests

conn = psycopg2.connect(os.environ['DATABASE_PUBLIC_URL'])
cur = conn.cursor()

print("TEST D'ENRICHISSEMENT MANUEL D'UN PROSPECT")
print("="*70)

# Prendre un prospect récent
cur.execute("""
    SELECT id, commune, parcelles_cadastrales, nom_prospect
    FROM agriweb_prospects
    WHERE parcelles_cadastrales IS NOT NULL 
      AND parcelles_cadastrales != ''
      AND parcelles_cadastrales != '[]'
      AND proprietaire_siren IS NULL
    ORDER BY id DESC
    LIMIT 1;
""")

prospect = cur.fetchone()
if not prospect:
    print("Aucun prospect à tester!")
    exit()

prospect_id, commune, parcelles_json, nom = prospect

print(f"\nProspect testé: ID {prospect_id}")
print(f"Nom: {nom or '(sans nom)'}")
print(f"Commune: {commune}")
print(f"Parcelles JSON: {parcelles_json[:100]}...")

# Parser les parcelles
try:
    parcelles = json.loads(parcelles_json)
    if parcelles and len(parcelles) > 0:
        parcelle = parcelles[0]
        section = parcelle.get('section', '')
        numero = parcelle.get('numero', '').zfill(4)
        
        print(f"\nParcelle parsée:")
        print(f"  Section: {section}")
        print(f"  Numéro: {numero}")
        
        # Obtenir le code INSEE
        print(f"\nRecherche code INSEE pour '{commune}'...")
        response = requests.get(f"https://geo.api.gouv.fr/communes?nom={commune}&fields=code,nom&limit=1", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                code_insee = data[0]['code']
                nom_commune = data[0]['nom']
                print(f"  ✓ Code INSEE trouvé: {code_insee} ({nom_commune})")
                
                # Chercher dans proprietaires_parcelles
                print(f"\nRecherche propriétaire pour {code_insee}-{section}-{numero}...")
                cur.execute("""
                    SELECT siren, denomination, forme_juridique
                    FROM proprietaires_parcelles
                    WHERE code_commune = %s
                      AND section = %s
                      AND numero = %s
                    LIMIT 1;
                """, (code_insee, section, numero))
                
                result = cur.fetchone()
                if result:
                    print(f"  ✓ PROPRIETAIRE TROUVE!")
                    print(f"    SIREN: {result[0]}")
                    print(f"    Dénomination: {result[1]}")
                    print(f"    Forme juridique: {result[2]}")
                    
                    print(f"\n💡 Le trigger DEVRAIT enrichir ce prospect automatiquement")
                    print(f"   Testons en forçant une mise à jour...")
                    
                    # Forcer le trigger en faisant un UPDATE
                    cur.execute("""
                        UPDATE agriweb_prospects
                        SET parcelles_cadastrales = parcelles_cadastrales
                        WHERE id = %s
                        RETURNING proprietaire_siren, proprietaire_denomination;
                    """, (prospect_id,))
                    
                    updated = cur.fetchone()
                    conn.commit()
                    
                    if updated and updated[0]:
                        print(f"  ✅ ENRICHISSEMENT REUSSI!")
                        print(f"     SIREN: {updated[0]}")
                        print(f"     Dénomination: {updated[1]}")
                    else:
                        print(f"  ❌ Le trigger n'a PAS enrichi le prospect")
                        print(f"     Le trigger a peut-être un bug de parsing")
                else:
                    print(f"  ✗ Propriétaire NON TROUVE dans la base")
                    print(f"    Cette parcelle n'existe pas dans proprietaires_parcelles")
                    
                    # Chercher des parcelles similaires
                    print(f"\n  Recherche de parcelles similaires pour {code_insee}-{section}...")
                    cur.execute("""
                        SELECT section, numero, siren, denomination
                        FROM proprietaires_parcelles
                        WHERE code_commune = %s
                          AND section = %s
                        LIMIT 5;
                    """, (code_insee, section))
                    
                    similaires = cur.fetchall()
                    if similaires:
                        print(f"    Parcelles trouvées dans cette section:")
                        for s in similaires:
                            print(f"      {code_insee}-{s[0]}-{s[1]} | SIREN: {s[2]} | {s[3][:40]}")
                    else:
                        print(f"    Aucune parcelle section {section} pour commune {code_insee}")
            else:
                print(f"  ✗ Commune '{commune}' non trouvée via API Geo")
        else:
            print(f"  ✗ Erreur API Geo: {response.status_code}")
            
except Exception as e:
    print(f"\nERREUR: {e}")
    import traceback
    traceback.print_exc()

cur.close()
conn.close()
