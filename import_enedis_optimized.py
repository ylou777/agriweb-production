"""
Script optimisé pour importer les données Enedis dans PostgreSQL Railway
Import progressif par batch pour gérer les gros fichiers
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import os

# Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL non définie")
    exit(1)

if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

CSV_PATH = r"c:\Users\Public\Documents\conso sup36KW\consommation-annuelle-entreprise-par-adresse.csv"

if not os.path.exists(CSV_PATH):
    print(f"❌ Fichier CSV introuvable: {CSV_PATH}")
    exit(1)

print(f"📂 Fichier: {CSV_PATH} ({os.path.getsize(CSV_PATH) / 1024 / 1024:.2f} MB)")

# Connexion PostgreSQL
print("🔌 Connexion à PostgreSQL Railway...")
try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Créer la table
    print("📋 Création de la table...")
    with open('create_enedis_table.sql', 'r', encoding='utf-8') as f:
        sql_create = f.read()
        cur.execute(sql_create)
        conn.commit()
    print("✅ Table créée")
    
    # Vider la table
    print("🗑️  Vidage de la table...")
    cur.execute("TRUNCATE TABLE consommation_enedis RESTART IDENTITY;")
    conn.commit()
    
except Exception as e:
    print(f"❌ Erreur PostgreSQL: {e}")
    exit(1)

# Import par chunks
print("\n💾 Import des données par batch...")
chunk_size = 50000  # 50k lignes par batch
total_inserted = 0

try:
    for i, chunk in enumerate(pd.read_csv(CSV_PATH, delimiter=',', encoding='utf-8', 
                                          quotechar='"', chunksize=chunk_size)):
        # Normaliser les colonnes
        chunk.columns = chunk.columns.str.lower().str.strip()
        chunk.columns = chunk.columns.str.replace('é', 'e').str.replace('è', 'e').str.replace('ê', 'e')
        chunk.columns = chunk.columns.str.replace(' ', '_').str.replace("'", '_')
        chunk.columns = chunk.columns.str.replace('(', '').str.replace(')', '')
        
        # Nettoyer les données
        chunk = chunk.fillna({
            'numero_de_voie': '',
            'indice_de_repetition': '',
            'type_de_voie': '',
            'libelle_de_voie': '',
            'adresse': '',
            'code_secteur_naf2': ''
        })
        
        # Convertir consommation en numérique
        chunk['consommation_annuelle_totale_de_l_adresse_mwh'] = pd.to_numeric(
            chunk['consommation_annuelle_totale_de_l_adresse_mwh'], 
            errors='coerce'
        )
        
        # Filtrer les lignes valides
        chunk = chunk[chunk['consommation_annuelle_totale_de_l_adresse_mwh'] > 0]
        
        if len(chunk) == 0:
            continue
        
        # Préparer les données
        insert_query = """
            INSERT INTO consommation_enedis (
                annee, code_iris, nom_iris, numero_de_voie, indice_de_repetition,
                type_de_voie, libelle_de_voie, adresse, nombre_de_sites,
                consommation_annuelle_totale_mwh, code_grand_secteur,
                code_categorie_consommation, code_secteur_naf2, code_commune,
                nom_commune, code_epci, code_departement, code_region, tri_des_adresses
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        data = [
            (
                row['annee'], row['code_iris'], row['nom_iris'], row['numero_de_voie'],
                row['indice_de_repetition'], row['type_de_voie'], row['libelle_de_voie'],
                row['adresse'], row['nombre_de_sites'],
                row['consommation_annuelle_totale_de_l_adresse_mwh'],
                row['code_grand_secteur'], row['code_categorie_consommation'],
                row['code_secteur_naf2'], row['code_commune'], row['nom_commune'],
                row['code_epci'], row['code_departement'], row['code_region'],
                row['tri_des_adresses']
            )
            for _, row in chunk.iterrows()
        ]
        
        # Insertion
        execute_batch(cur, insert_query, data, page_size=1000)
        conn.commit()
        
        total_inserted += len(data)
        print(f"✅ Batch {i+1}: {len(data):,} lignes | Total: {total_inserted:,}")
        
except Exception as e:
    print(f"❌ Erreur import: {e}")
    conn.rollback()
    exit(1)

# Statistiques finales
print("\n📊 STATISTIQUES FINALES:")
cur.execute("SELECT COUNT(*) FROM consommation_enedis;")
total = cur.fetchone()[0]
print(f"   Total lignes: {total:,}")

cur.execute("SELECT SUM(consommation_annuelle_totale_mwh) FROM consommation_enedis;")
total_conso = cur.fetchone()[0]
print(f"   Consommation totale: {total_conso:,.2f} MWh")

cur.execute("""
    SELECT code_grand_secteur, COUNT(*), ROUND(SUM(consommation_annuelle_totale_mwh)::numeric, 2)
    FROM consommation_enedis
    GROUP BY code_grand_secteur
    ORDER BY SUM(consommation_annuelle_totale_mwh) DESC;
""")
stats = cur.fetchall()
print("\n   Par secteur:")
for secteur, count, conso in stats:
    print(f"   - {secteur}: {count:,} sites, {float(conso):,.2f} MWh")

cur.close()
conn.close()
print("\n✅ Import terminé avec succès!")
