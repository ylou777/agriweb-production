"""
Script pour importer les données de consommation Enedis dans PostgreSQL Railway
Source: https://opendata.enedis.fr/datasets/consommation-annuelle-entreprise-par-adresse
"""

import requests
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import os
from urllib.parse import quote

# Configuration Railway - essayer plusieurs variables d'environnement
DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_PRIVATE_URL')

# Si pas de variable d'environnement, utiliser connexion locale Railway
if not DATABASE_URL:
    # Format pour Railway: postgresql://postgres:PASSWORD@HOST:PORT/railway
    print("⚠️  DATABASE_URL non définie dans l'environnement")
    print("💡 Veuillez définir DATABASE_URL avec votre connexion Railway PostgreSQL")
    print("   Exemple: $env:DATABASE_URL='postgresql://postgres:PASSWORD@HOST:PORT/railway'")
    exit(1)

print("📥 Lecture des données Enedis locales...")

# Fichier local fourni par l'utilisateur
CSV_PATH = r"c:\Users\Public\Documents\conso sup36KW\consommation-annuelle-entreprise-par-adresse.csv"

# Vérifier que le fichier existe
if not os.path.exists(CSV_PATH):
    print(f"❌ Fichier non trouvé: {CSV_PATH}")
    exit(1)

# Lire avec pandas
print(f"📊 Lecture CSV: {CSV_PATH}")
try:
    file_size = os.path.getsize(CSV_PATH) / 1024 / 1024
    print(f"📦 Taille fichier: {file_size:.2f} MB")
    
    # Lire avec encoding utf-8 - le CSV utilise "," comme séparateur avec guillemets
    df = pd.read_csv(CSV_PATH, delimiter=',', encoding='utf-8', low_memory=False, quotechar='"')
    
    # Debug: afficher les colonnes brutes
    print(f"📋 Colonnes détectées ({len(df.columns)} colonnes)")
    
    # Normaliser les noms de colonnes (minuscules, pas d'espaces, pas d'accents)
    df.columns = df.columns.str.lower().str.strip()
    df.columns = df.columns.str.replace('é', 'e').str.replace('è', 'e').str.replace('ê', 'e')
    df.columns = df.columns.str.replace(' ', '_').str.replace("'", '_').str.replace('(', '').str.replace(')', '')
    
    print(f"📋 Exemples colonnes: {', '.join(df.columns.tolist()[:5])}")
    
    # Vérifier qu'on a bien les colonnes attendues
    if 'annee' not in df.columns:
        print(f"⚠️  Colonne 'annee' non trouvée. Colonnes: {df.columns.tolist()}")
        exit(1)
    
    print(f"✅ {len(df):,} lignes chargées")
    print(f"📅 Années: {sorted(df['annee'].unique())}")
    print(f"🏢 Secteurs: {df['code_grand_secteur'].value_counts().to_dict()}")
    
except Exception as e:
    print(f"❌ Erreur lecture CSV: {e}")
    exit(1)

# Nettoyer les données
print("🧹 Nettoyage des données...")
df = df.fillna({
    'numero_de_voie': '',
    'indice_de_repetition': '',
    'type_de_voie': '',
    'libelle_de_voie': '',
    'adresse': '',
    'code_secteur_naf2': ''
})

# Convertir les types
df['consommation_annuelle_totale_mwh'] = pd.to_numeric(
    df['consommation_annuelle_totale_mwh'], 
    errors='coerce'
)

# Filtrer les lignes avec consommation valide
df = df[df['consommation_annuelle_totale_mwh'] > 0]
print(f"✅ {len(df):,} lignes après nettoyage")

# Connexion PostgreSQL
print("🔌 Connexion à PostgreSQL Railway...")
try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Créer la table si nécessaire
    print("📋 Création de la table...")
    with open('create_enedis_table.sql', 'r', encoding='utf-8') as f:
        sql_create = f.read()
        cur.execute(sql_create)
        conn.commit()
    print("✅ Table créée/vérifiée")
    
    # Vider la table (optionnel - commenter si on veut garder les anciennes données)
    print("🗑️  Vidage de la table...")
    cur.execute("TRUNCATE TABLE consommation_enedis RESTART IDENTITY;")
    conn.commit()
    
    # Préparer les données pour insertion
    print("💾 Insertion des données...")
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
    
    # Convertir DataFrame en liste de tuples
    data = [
        (
            row['annee'], row['code_iris'], row['nom_iris'], row['numero_de_voie'],
            row['indice_de_repetition'], row['type_de_voie'], row['libelle_de_voie'],
            row['adresse'], row['nombre_de_sites'],
            row['consommation_annuelle_totale_mwh'],
            row['code_grand_secteur'], row['code_categorie_consommation'],
            row['code_secteur_naf2'], row['code_commune'], row['nom_commune'],
            row['code_epci'], row['code_departement'], row['code_region'],
            row['tri_des_adresses']
        )
        for _, row in df.iterrows()
    ]
    
    # Insertion par batch (plus rapide)
    execute_batch(cur, insert_query, data, page_size=1000)
    conn.commit()
    
    print(f"✅ {len(data):,} lignes insérées")
    
    # Statistiques finales
    cur.execute("SELECT COUNT(*) FROM consommation_enedis;")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT SUM(consommation_annuelle_totale_mwh) FROM consommation_enedis;")
    total_conso = cur.fetchone()[0]
    
    cur.execute("""
        SELECT code_grand_secteur, COUNT(*), SUM(consommation_annuelle_totale_mwh)
        FROM consommation_enedis
        GROUP BY code_grand_secteur
        ORDER BY SUM(consommation_annuelle_totale_mwh) DESC;
    """)
    stats = cur.fetchall()
    
    print("\n📊 STATISTIQUES:")
    print(f"   Total lignes: {total:,}")
    print(f"   Consommation totale: {total_conso:,.2f} MWh")
    print(f"\n   Par secteur:")
    for secteur, count, conso in stats:
        print(f"   - {secteur}: {count:,} sites, {conso:,.2f} MWh")
    
    cur.close()
    conn.close()
    print("\n✅ Import terminé avec succès!")
    
except Exception as e:
    print(f"❌ Erreur PostgreSQL: {e}")
    if 'conn' in locals():
        conn.rollback()
    exit(1)

print("\n🎯 Prochaines étapes:")
print("   1. Géocoder les adresses pour remplir la colonne 'geom'")
print("   2. Créer fonction pour croiser avec toitures OSM")
print("   3. Intégrer dans les rapports commune")
