"""
Fonction pour géocoder les adresses Enedis et remplir les coordonnées GPS
Utilise l'API Adresse (data.gouv.fr) - gratuite et sans limite
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import time
import os

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

def geocode_address(adresse, code_commune):
    """
    Géocode une adresse via l'API Adresse (data.gouv.fr)
    """
    if not adresse or adresse.strip() == '':
        return None, None
    
    try:
        # API Adresse data.gouv.fr
        url = "https://api-adresse.data.gouv.fr/search/"
        params = {
            'q': adresse,
            'citycode': code_commune,
            'limit': 1
        }
        
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        if data['features'] and len(data['features']) > 0:
            coords = data['features'][0]['geometry']['coordinates']
            return coords[1], coords[0]  # latitude, longitude
        
    except Exception as e:
        print(f"⚠️  Erreur géocodage '{adresse}': {e}")
    
    return None, None

# Connexion
print("🔌 Connexion à PostgreSQL Railway...")
conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
cur = conn.cursor()

# Compter les adresses à géocoder
cur.execute("""
    SELECT COUNT(*) as total 
    FROM consommation_enedis 
    WHERE geocoded = FALSE AND adresse IS NOT NULL AND adresse != ''
    LIMIT 10000
""")
total = cur.fetchone()['total']
print(f"📍 {total:,} adresses à géocoder (max 10000 pour ce batch)")

if total == 0:
    print("✅ Toutes les adresses sont déjà géocodées!")
    exit(0)

# Récupérer les adresses à géocoder (batch de 10000 max)
cur.execute("""
    SELECT id, adresse, code_commune, nom_commune
    FROM consommation_enedis
    WHERE geocoded = FALSE AND adresse IS NOT NULL AND adresse != ''
    LIMIT 10000
""")

rows = cur.fetchall()
print(f"🚀 Démarrage du géocodage...")

success_count = 0
fail_count = 0

for i, row in enumerate(rows):
    lat, lon = geocode_address(row['adresse'], row['code_commune'])
    
    if lat and lon:
        cur.execute("""
            UPDATE consommation_enedis
            SET latitude = %s, longitude = %s, geocoded = TRUE
            WHERE id = %s
        """, (lat, lon, row['id']))
        success_count += 1
    else:
        # Marquer comme géocodé même si échec pour ne pas réessayer
        cur.execute("""
            UPDATE consommation_enedis
            SET geocoded = TRUE
            WHERE id = %s
        """, (row['id'],))
        fail_count += 1
    
    # Commit tous les 100
    if (i + 1) % 100 == 0:
        conn.commit()
        print(f"✅ {i+1:,}/{total:,} | Succès: {success_count:,} | Échecs: {fail_count:,}")
        time.sleep(0.5)  # Ralentir pour ne pas surcharger l'API

# Commit final
conn.commit()

print(f"\n📊 RÉSULTAT:")
print(f"   Total traité: {len(rows):,}")
print(f"   Géocodées avec succès: {success_count:,} ({success_count/len(rows)*100:.1f}%)")
print(f"   Échecs: {fail_count:,} ({fail_count/len(rows)*100:.1f}%)")

# Statistiques finales
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE latitude IS NOT NULL) as geocoded
    FROM consommation_enedis
""")
stats = cur.fetchone()
print(f"\n📍 GLOBAL:")
print(f"   Total adresses: {stats['total']:,}")
print(f"   Géocodées: {stats['geocoded']:,} ({stats['geocoded']/stats['total']*100:.1f}%)")

cur.close()
conn.close()

print("\n💡 Pour géocoder plus d'adresses, relancer ce script plusieurs fois")
print("   (batch de 10000 à chaque fois)")
