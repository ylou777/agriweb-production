"""
Script pour enrichir les prospects existants avec les données Enedis
Croise les adresses/communes des prospects avec la table consommation_enedis
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import sqlite3
from geopy.distance import geodesic

# Railway PostgreSQL (Enedis data)
DATABASE_URL = os.getenv('DATABASE_URL') or (sys.argv[1] if len(sys.argv) > 1 else None)

# SQLite CRM (prospects)
CRM_DB_PATH = r'C:\Users\Public\kpi_sunstice.db'

def enrich_prospects_with_enedis():
    """
    Enrichit les prospects AgriWeb avec les consommations Enedis
    
    Méthode:
    1. Pour chaque prospect avec lat/lon
    2. Chercher les sites Enedis dans un rayon de 500m
    3. Ajouter la consommation du site le plus proche
    """
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL non définie")
        print("Usage: python enrich_prospects_enedis.py 'postgresql://...'")
        return
    
    # Convertir postgres:// en postgresql://
    db_url = DATABASE_URL
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    print("=" * 60)
    print("ENRICHISSEMENT PROSPECTS AVEC DONNÉES ENEDIS")
    print("=" * 60)
    print()
    
    # Connexion PostgreSQL (Enedis)
    print("🔌 Connexion PostgreSQL Railway...")
    pg_conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
    pg_cur = pg_conn.cursor()
    
    # Connexion SQLite (CRM)
    print("🔌 Connexion SQLite CRM...")
    sqlite_conn = sqlite3.connect(CRM_DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()
    
    # Récupérer les prospects avec coordonnées
    print("\n📊 Récupération des prospects avec coordonnées...")
    sqlite_cur.execute("""
        SELECT id, commune, adresse, latitude, longitude, 
               consommation_enedis_mwh, secteur_enedis
        FROM agriweb_prospects
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """)
    
    prospects = sqlite_cur.fetchall()
    print(f"✅ {len(prospects)} prospects à enrichir")
    
    enriched = 0
    already_enriched = 0
    not_found = 0
    
    for prospect in prospects:
        prospect_id = prospect['id']
        lat = prospect['latitude']
        lon = prospect['longitude']
        commune = prospect['commune']
        
        # Si déjà enrichi, passer
        if prospect['consommation_enedis_mwh']:
            already_enriched += 1
            continue
        
        # Chercher les sites Enedis proches (dans un carré de ~1km)
        # 0.01 degré ≈ 1 km
        lat_range = 0.01
        lon_range = 0.01
        
        pg_cur.execute("""
            SELECT latitude, longitude, adresse,
                   consommation_annuelle_totale_mwh,
                   code_grand_secteur,
                   nombre_de_sites
            FROM consommation_enedis
            WHERE latitude BETWEEN %s AND %s
              AND longitude BETWEEN %s AND %s
              AND geocoded = TRUE
            ORDER BY consommation_annuelle_totale_mwh DESC
            LIMIT 10
        """, (lat - lat_range, lat + lat_range, 
              lon - lon_range, lon + lon_range))
        
        sites_proches = pg_cur.fetchall()
        
        if not sites_proches:
            not_found += 1
            continue
        
        # Trouver le site le plus proche
        min_distance = float('inf')
        closest_site = None
        
        for site in sites_proches:
            site_lat = float(site['latitude'])
            site_lon = float(site['longitude'])
            distance = geodesic((lat, lon), (site_lat, site_lon)).meters
            
            if distance < min_distance and distance < 500:  # Max 500m
                min_distance = distance
                closest_site = site
        
        if closest_site:
            # Enrichir le prospect
            sqlite_cur.execute("""
                UPDATE agriweb_prospects
                SET consommation_enedis_mwh = ?,
                    secteur_enedis = ?,
                    nb_sites_enedis = ?,
                    date_modification = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                float(closest_site['consommation_annuelle_totale_mwh']),
                closest_site['code_grand_secteur'],
                int(closest_site['nombre_de_sites']),
                prospect_id
            ))
            
            enriched += 1
            
            if enriched % 100 == 0:
                print(f"  ✅ {enriched} prospects enrichis...")
                sqlite_conn.commit()
        else:
            not_found += 1
    
    # Commit final
    sqlite_conn.commit()
    
    print("\n" + "=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print(f"✅ Prospects enrichis: {enriched}")
    print(f"ℹ️  Déjà enrichis: {already_enriched}")
    print(f"⚠️  Aucune consommation trouvée: {not_found}")
    print(f"📊 Total: {len(prospects)}")
    
    # Stats par secteur
    print("\n📈 Répartition par secteur:")
    sqlite_cur.execute("""
        SELECT secteur_enedis, COUNT(*) as nb, 
               ROUND(AVG(consommation_enedis_mwh), 2) as moy_mwh,
               ROUND(SUM(consommation_enedis_mwh), 2) as total_mwh
        FROM agriweb_prospects
        WHERE secteur_enedis IS NOT NULL
        GROUP BY secteur_enedis
        ORDER BY total_mwh DESC
    """)
    
    stats = sqlite_cur.fetchall()
    for row in stats:
        print(f"  {row['secteur_enedis']:<15} {row['nb']:>5} prospects | "
              f"Moy: {row['moy_mwh']:>8} MWh | Total: {row['total_mwh']:>10} MWh")
    
    # Fermeture connexions
    pg_cur.close()
    pg_conn.close()
    sqlite_cur.close()
    sqlite_conn.close()
    
    print("\n✅ Enrichissement terminé!")

if __name__ == "__main__":
    enrich_prospects_with_enedis()
