"""
Détail des 29 prospects enrichis de Guéret
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Connexion Railway
DATABASE_URL = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')

if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

print("🏢 Détail des 29 prospects enrichis de Guéret\n")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

cursor.execute("""
    SELECT 
        id,
        type,
        adresse,
        surface_m2,
        proprietaire_denomination,
        proprietaire_siren,
        proprietaire_forme_juridique,
        parcelles_cadastrales
    FROM agriweb_prospects
    WHERE commune = 'Guéret' 
      AND proprietaire_siren IS NOT NULL
    ORDER BY id
""")

results = cursor.fetchall()

print(f"{'ID':<6} {'Type':<10} {'Adresse':<50} {'Surface':<12} {'Propriétaire (SIREN)'}")
print("=" * 150)

for i, row in enumerate(results, 1):
    id_prospect = row['id']
    type_p = row['type'] or 'N/A'
    adresse = (row['adresse'] or 'N/A')[:48]
    surface = f"{int(row['surface_m2'])} m²" if row['surface_m2'] else 'N/A'
    proprio = (row['proprietaire_denomination'] or 'N/A')[:50]
    siren = row['proprietaire_siren'] or 'N/A'
    forme = row['proprietaire_forme_juridique'] or ''
    
    print(f"{id_prospect:<6} {type_p:<10} {adresse:<50} {surface:<12} {proprio}")
    print(f"{'':6} {'':10} {'':50} {'':12} SIREN: {siren} | Forme: {forme}")
    
    # Afficher les parcelles
    parcelles = row['parcelles_cadastrales']
    if parcelles:
        if isinstance(parcelles, str):
            parcelles_str = parcelles
        else:
            try:
                import json
                parcelles_list = json.loads(parcelles) if isinstance(parcelles, str) else parcelles
                parcelles_str = ', '.join(parcelles_list[:3])
                if len(parcelles_list) > 3:
                    parcelles_str += f' (+{len(parcelles_list)-3} autres)'
            except:
                parcelles_str = str(parcelles)[:50]
        
        print(f"{'':6} {'':10} 📍 Parcelles: {parcelles_str}")
    
    print()

print("=" * 150)
print(f"Total: {len(results)} prospects enrichis à Guéret")

# Statistiques sur les propriétaires
cursor.execute("""
    SELECT 
        proprietaire_denomination,
        proprietaire_forme_juridique,
        COUNT(*) as nb_prospects
    FROM agriweb_prospects
    WHERE commune = 'Guéret' 
      AND proprietaire_siren IS NOT NULL
    GROUP BY proprietaire_denomination, proprietaire_forme_juridique
    ORDER BY nb_prospects DESC
""")

proprios = cursor.fetchall()

print("\n📊 Top propriétaires à Guéret:")
print(f"{'Propriétaire':<60} {'Forme juridique':<25} {'Nb prospects'}")
print("=" * 100)

for p in proprios:
    nom = (p['proprietaire_denomination'] or 'N/A')[:58]
    forme = (p['proprietaire_forme_juridique'] or 'N/A')[:23]
    nb = p['nb_prospects']
    print(f"{nom:<60} {forme:<25} {nb}")

cursor.close()
conn.close()
