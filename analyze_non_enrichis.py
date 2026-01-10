import os, psycopg2, json

conn = psycopg2.connect(os.environ.get('DATABASE_PUBLIC_URL'))
cur = conn.cursor()

# Analyser 30 prospects non enrichis
cur.execute("""
    SELECT id, commune, parcelles_cadastrales
    FROM agriweb_prospects
    WHERE parcelles_cadastrales LIKE '[%'
      AND parcelles_cadastrales != '[]'
      AND proprietaire_siren IS NULL
      AND id NOT IN (1348, 1350)
    LIMIT 30
""")

prospects = cur.fetchall()

commune_manquante = 0
parcelle_manquante = 0
siren_null = 0
json_vide = 0
section_manquante = 0

for pid, commune, parcelles_json in prospects:
    try:
        parcelles = json.loads(parcelles_json)
        if not parcelles:
            json_vide += 1
            continue
        
        p1 = parcelles[0]
        section = p1.get('section')
        numero = p1.get('numero', '').zfill(4)
        
        if not section:
            section_manquante += 1
            continue
        
        # Commune
        cur.execute("SELECT get_code_insee_from_commune(%s)", (commune,))
        result = cur.fetchone()
        if not result or not result[0]:
            commune_manquante += 1
            print(f"  {pid}: Commune '{commune}' non trouvee")
            continue
        
        code_insee = result[0]
        
        # Parcelle
        cur.execute("""
            SELECT siren, denomination
            FROM proprietaires_parcelles
            WHERE (code_commune = %s OR code_insee = %s)
              AND section = %s
              AND numero = %s
            LIMIT 1
        """, (code_insee, code_insee, section, numero))
        
        prop = cur.fetchone()
        if not prop:
            parcelle_manquante += 1
        elif not prop[0]:
            siren_null += 1
        
    except Exception as e:
        print(f"  {pid}: Erreur {e}")

print(f"\n ANALYSE 30 PROSPECTS:")
print(f"  JSON vide: {json_vide}")
print(f"  Section manquante: {section_manquante}")
print(f"  Commune non trouvee: {commune_manquante}")
print(f"  Parcelle introuvable: {parcelle_manquante}")
print(f"  Parcelle sans SIREN: {siren_null}")
print(f"  Total: {json_vide + section_manquante + commune_manquante + parcelle_manquante + siren_null}/30")

conn.close()
