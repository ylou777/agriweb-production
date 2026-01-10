import os
import psycopg2

# Connexion à la base de données
DATABASE_URL = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Vérifier les 10 premiers prospects et leurs coordonnées
cur.execute("""
    SELECT id, commune, adresse, latitude, longitude, type
    FROM agriweb_prospects
    ORDER BY id
    LIMIT 20
""")

prospects = cur.fetchall()

print("=" * 100)
print(f"{'ID':<5} {'Type':<12} {'Commune':<20} {'Latitude':<12} {'Longitude':<12} {'Carte?':<10}")
print("=" * 100)

with_carte = 0
without_carte = 0

for p in prospects:
    id, commune, adresse, lat, lon, type_p = p
    has_coords = "✅ OUI" if (lat and lon) else "❌ NON"
    
    if lat and lon:
        with_carte += 1
    else:
        without_carte += 1
    
    print(f"{id:<5} {type_p:<12} {commune[:20]:<20} {str(lat)[:12]:<12} {str(lon)[:12]:<12} {has_coords:<10}")

print("=" * 100)
print(f"Prospects AVEC coordonnées GPS: {with_carte}")
print(f"Prospects SANS coordonnées GPS: {without_carte}")

# Compter le total
cur.execute("SELECT COUNT(*) FROM agriweb_prospects WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
total_with_coords = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM agriweb_prospects")
total = cur.fetchone()[0]

print(f"\nTotal dans la base: {total} prospects")
print(f"Avec coordonnées: {total_with_coords} ({100*total_with_coords/total:.1f}%)")
print(f"Sans coordonnées: {total - total_with_coords} ({100*(total-total_with_coords)/total:.1f}%)")

cur.close()
conn.close()
