#!/usr/bin/env python3
"""Script pour vérifier la structure de la table agriweb_prospects dans Railway"""

import os
import psycopg2
from urllib.parse import urlparse

# URL de connexion Railway
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/agriweb")

print(f"\n🔍 Vérification de la structure de la table agriweb_prospects")
print(f"="*80)

try:
    # Parse l'URL PostgreSQL
    result = urlparse(DATABASE_URL)
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port
    
    print(f"📡 Connexion à: {hostname}:{port}/{database}")
    
    # Connexion
    conn = psycopg2.connect(
        database=database,
        user=username,
        password=password,
        host=hostname,
        port=port
    )
    
    cur = conn.cursor()
    
    # Vérifier les colonnes de la table
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'agriweb_prospects'
        ORDER BY ordinal_position;
    """)
    
    colonnes = cur.fetchall()
    
    print(f"\n✅ Table 'agriweb_prospects' trouvée avec {len(colonnes)} colonnes:")
    print(f"\n{'Colonne':<40} {'Type':<20} {'Taille':<10}")
    print("="*70)
    
    colonnes_postes_bt = []
    colonnes_postes_hta = []
    
    for col_name, data_type, max_length in colonnes:
        taille = str(max_length) if max_length else "-"
        print(f"{col_name:<40} {data_type:<20} {taille:<10}")
        
        if col_name.startswith('poste_bt_'):
            colonnes_postes_bt.append(col_name)
        elif col_name.startswith('poste_hta_'):
            colonnes_postes_hta.append(col_name)
    
    print(f"\n📊 Colonnes postes BT ({len(colonnes_postes_bt)}):")
    for col in colonnes_postes_bt:
        print(f"   ✓ {col}")
    
    print(f"\n📊 Colonnes postes HTA ({len(colonnes_postes_hta)}):")
    for col in colonnes_postes_hta:
        print(f"   ✓ {col}")
    
    # Vérifier si des données existent
    cur.execute("SELECT COUNT(*) FROM agriweb_prospects;")
    count = cur.fetchone()[0]
    print(f"\n📈 Nombre de prospects dans la table: {count}")
    
    if count > 0:
        # Vérifier un échantillon
        cur.execute("""
            SELECT 
                id, type, commune, 
                poste_bt_nom, poste_bt_commune, poste_bt_puissance,
                poste_hta_nom, poste_hta_commune
            FROM agriweb_prospects 
            LIMIT 3;
        """)
        
        echantillon = cur.fetchall()
        print(f"\n🔍 Échantillon de 3 premiers prospects:")
        print(f"="*80)
        
        for row in echantillon:
            id, type_p, commune, bt_nom, bt_comm, bt_pui, hta_nom, hta_comm = row
            print(f"\n  ID: {id} | Type: {type_p} | Commune: {commune}")
            print(f"  BT: nom='{bt_nom}', commune='{bt_comm}', puissance='{bt_pui}'")
            print(f"  HTA: nom='{hta_nom}', commune='{hta_comm}'")
    
    cur.close()
    conn.close()
    
    print(f"\n{'='*80}")
    print(f"✅ Vérification terminée avec succès")
    
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
