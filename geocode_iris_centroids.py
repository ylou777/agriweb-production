"""
Geocode Enedis addresses using IRIS centroids
Fast bulk geocoding using INSEE IRIS district centers
"""
import psycopg2
import requests
import json
from urllib.parse import urlparse
import os
import sys

# Railway PostgreSQL connection from environment or command-line
DATABASE_URL = os.getenv('DATABASE_URL') or (sys.argv[1] if len(sys.argv) > 1 else None)

def download_iris_geometries():
    """Download IRIS geometries from INSEE open data"""
    print("📥 Downloading IRIS geometries from INSEE...")
    
    # INSEE IRIS contours 2024 (GeoJSON format)
    # Alternative: https://data.geopf.fr/wfs for IGN data
    url = "https://wxs.ign.fr/administratif/geoportail/wfs"
    
    # Use simplified approach: download pre-computed IRIS centroids from data.gouv.fr
    # This is faster than downloading full geometries
    centroid_url = "https://www.data.gouv.fr/fr/datasets/r/05f3e53e-df8f-4f8e-9e2f-8817d7b8e9c4"
    
    print(f"⚠️  Full IRIS geometries are large (>500 MB)")
    print(f"Alternative: Using INSEE commune centers as fallback")
    
    return None

def get_iris_centroids_from_csv():
    """
    Alternative: Calculate centroids from Enedis data itself
    Group by code_iris, take mean of first few geocoded addresses
    """
    print("🔄 Using alternative approach: commune centroids")
    
    # Download INSEE communes with coordinates
    url = "https://geo.api.gouv.fr/communes?fields=code,nom,centre&format=json"
    
    print(f"📥 Downloading commune centers from geo.api.gouv.fr...")
    response = requests.get(url, timeout=30)
    
    if response.status_code != 200:
        print(f"❌ Error downloading communes: {response.status_code}")
        return {}
    
    communes = response.json()
    commune_coords = {}
    
    for commune in communes:
        code = commune['code']
        if 'centre' in commune and commune['centre']:
            coords = commune['centre']['coordinates']
            commune_coords[code] = {
                'longitude': coords[0],
                'latitude': coords[1]
            }
    
    print(f"✅ Downloaded {len(commune_coords)} commune centers")
    return commune_coords

def update_enedis_with_commune_centroids():
    """Update Enedis table using commune centroids as approximation"""
    
    # Get commune coordinates
    commune_coords = get_iris_centroids_from_csv()
    
    if not commune_coords:
        print("❌ Could not get commune coordinates")
        return
    
    # Connect to database
    database_url = DATABASE_URL
    if not database_url:
        print("❌ DATABASE_URL not set")
        return
    
    # Convert postgres:// to postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print(f"\n🔌 Connecting to Railway PostgreSQL...")
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    
    # Count rows to update
    cur.execute("""
        SELECT COUNT(*) 
        FROM consommation_enedis 
        WHERE latitude IS NULL AND code_commune IN %s
    """, (tuple(commune_coords.keys()),))
    
    total_to_update = cur.fetchone()[0]
    print(f"📊 Found {total_to_update:,} rows to geocode")
    
    # Update in batches
    batch_size = 10000
    updated = 0
    
    print(f"\n🔄 Updating coordinates (batch size: {batch_size:,})...")
    
    for code_commune, coords in commune_coords.items():
        try:
            cur.execute("""
                UPDATE consommation_enedis
                SET 
                    latitude = %s,
                    longitude = %s,
                    geocoded = TRUE
                WHERE code_commune = %s AND latitude IS NULL
            """, (coords['latitude'], coords['longitude'], code_commune))
            
            rows_updated = cur.rowcount
            updated += rows_updated
            
            if updated % 50000 == 0:
                print(f"  ✅ {updated:,}/{total_to_update:,} rows updated...")
                conn.commit()
        
        except Exception as e:
            print(f"  ⚠️  Error updating commune {code_commune}: {e}")
            continue
    
    # Final commit
    conn.commit()
    
    print(f"\n✅ Geocoding complete!")
    print(f"📊 Total rows updated: {updated:,}")
    
    # Verify results
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE geocoded = TRUE) as geocoded,
            COUNT(DISTINCT code_commune) as communes
        FROM consommation_enedis
    """)
    
    stats = cur.fetchone()
    print(f"\n📈 Final statistics:")
    print(f"  Total rows: {stats[0]:,}")
    print(f"  Geocoded: {stats[1]:,} ({stats[1]/stats[0]*100:.1f}%)")
    print(f"  Communes: {stats[2]:,}")
    
    cur.close()
    conn.close()

def main():
    print("=" * 60)
    print("ENEDIS GEOCODING - IRIS/COMMUNE CENTROIDS")
    print("=" * 60)
    print()
    print("⚠️  Note: Using commune centroids as approximation")
    print("   Precision: ~1-5 km (commune center)")
    print("   Speed: Instant (API call only)")
    print()
    
    update_enedis_with_commune_centroids()
    
    print("\n" + "=" * 60)
    print("✅ GEOCODING COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Refresh your map to see Enedis markers")
    print("2. Markers show at commune centers (approximate)")
    print("3. For precise geocoding, use batch API later")

if __name__ == "__main__":
    main()
