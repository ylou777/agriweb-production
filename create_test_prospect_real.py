import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_PUBLIC_URL'])
cur = conn.cursor()

print("CREATION D'UN PROSPECT TEST AVEC PARCELLE REELLE")
print("="*70)

# 1. Trouver une parcelle réelle dans la base
print("\n1. Recherche d'une parcelle réelle avec propriétaire...")
cur.execute("""
    SELECT code_commune, section, numero, siren, denomination, forme_juridique
    FROM proprietaires_parcelles
    WHERE siren IS NOT NULL
      AND denomination IS NOT NULL
      AND code_commune IS NOT NULL
    ORDER BY RANDOM()
    LIMIT 1;
""")

parcelle_real = cur.fetchone()
if not parcelle_real:
    print("❌ Aucune parcelle trouvée!")
    exit()

code_commune, section, numero, siren, denomination, forme_jur = parcelle_real

print(f"✓ Parcelle trouvée:")
print(f"  Code commune: {code_commune}")
print(f"  Section: {section}")
print(f"  Numéro: {numero}")
print(f"  SIREN: {siren}")
print(f"  Propriétaire: {denomination}")

# 2. Obtenir le nom de la commune
import requests
try:
    response = requests.get(f"https://geo.api.gouv.fr/communes/{code_commune}", timeout=5)
    if response.status_code == 200:
        commune_name = response.json().get('nom', f'Commune {code_commune}')
    else:
        commune_name = f"Commune {code_commune}"
except:
    commune_name = f"Commune {code_commune}"

print(f"\n2. Nom de la commune: {commune_name}")

# 3. Créer le prospect avec cette parcelle
parcelles_json = f'[{{"commune": "", "numero": "{numero}", "section": "{section}", "ref": "{section}{numero}"}}]'

print(f"\n3. Création du prospect test...")
print(f"   Parcelles JSON: {parcelles_json}")

cur.execute("""
    INSERT INTO agriweb_prospects (
        type,
        commune,
        parcelles_cadastrales,
        nom_prospect,
        statut
    ) VALUES (
        'test',
        %s,
        %s,
        'PROSPECT TEST ENRICHISSEMENT AUTO',
        'test'
    ) RETURNING 
        id,
        proprietaire_siren,
        proprietaire_denomination,
        proprietaire_forme_juridique,
        proprietaire_enrichi_date;
""", (commune_name, parcelles_json))

result = cur.fetchone()
conn.commit()

print(f"\n4. Résultat de l'insertion:")
print(f"   ID prospect créé: {result[0]}")
print(f"   SIREN enrichi: {result[1] or '❌ NON ENRICHI'}")
print(f"   Dénomination: {result[2] or '❌ NON ENRICHI'}")
print(f"   Forme juridique: {result[3] or '❌ NON ENRICHI'}")
print(f"   Date enrichissement: {result[4] or '❌ NON ENRICHI'}")

print("\n" + "="*70)
if result[1]:  # Si SIREN rempli
    print("✅ ENRICHISSEMENT AUTOMATIQUE FONCTIONNE!")
    print(f"\n💡 Le trigger a bien enrichi le prospect avec:")
    print(f"   - SIREN attendu: {siren}")
    print(f"   - SIREN obtenu: {result[1]}")
    print(f"   - Match: {'✅ OUI' if result[1] == siren else '❌ NON'}")
else:
    print("❌ ENRICHISSEMENT AUTOMATIQUE NE FONCTIONNE PAS")
    print("\n🔍 Déboggage nécessaire du trigger...")
    
    # Test manuel pour voir si la recherche fonctionne
    cur.execute("""
        SELECT siren, denomination
        FROM proprietaires_parcelles
        WHERE code_commune = %s
          AND section = %s
          AND numero = %s
        LIMIT 1;
    """, (code_commune, section, numero))
    
    check = cur.fetchone()
    if check:
        print(f"   ✓ La requête manuelle TROUVE le propriétaire: {check[0]}")
        print(f"   ⚠️  Le problème est dans le parsing du trigger")
    else:
        print(f"   ✗ Même la requête manuelle ne trouve pas la parcelle")

cur.close()
conn.close()
