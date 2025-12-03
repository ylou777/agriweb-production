"""
Script pour créer les colonnes OSM dans Railway PostgreSQL
Exécutez ce script pour ajouter les colonnes manquantes
"""

import os
import psycopg2

# URL de connexion Railway - À REMPLACER par votre DATABASE_URL depuis Railway
DATABASE_URL = os.getenv('DATABASE_URL') or input("Collez votre DATABASE_URL Railway (postgresql://...): ")

print("🔄 Connexion à Railway PostgreSQL...")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    print("✅ Connecté à la base de données")
    
    osm_columns = [
        'osm_amenity', 'osm_shop', 'osm_building', 
        'osm_landuse', 'osm_office', 'osm_industrial'
    ]
    
    print("\n🔄 Ajout des colonnes OSM...")
    for col in osm_columns:
        try:
            cur.execute(f"ALTER TABLE agriweb_prospects ADD COLUMN {col} TEXT")
            conn.commit()
            print(f"✅ Colonne {col} créée avec succès")
        except Exception as e:
            conn.rollback()
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print(f"ℹ️  Colonne {col} existe déjà")
            else:
                print(f"❌ Erreur {col}: {e}")
    
    # Vérifier les colonnes
    print("\n📊 Vérification des colonnes OSM dans la base:")
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'agriweb_prospects' 
        AND column_name LIKE 'osm_%'
        ORDER BY column_name
    """)
    
    columns = cur.fetchall()
    if columns:
        for col_name, col_type in columns:
            print(f"  ✅ {col_name} ({col_type})")
    else:
        print("  ⚠️ Aucune colonne OSM trouvée")
    
    cur.close()
    conn.close()
    print("\n✅ Migration terminée avec succès!")
    
except Exception as e:
    print(f"\n❌ Erreur de connexion: {e}")
    print("\n💡 Pour obtenir votre DATABASE_URL:")
    print("   1. Allez sur railway.app")
    print("   2. Cliquez sur votre projet")
    print("   3. Cliquez sur le service PostgreSQL")
    print("   4. Onglet 'Variables' → copiez DATABASE_URL")
