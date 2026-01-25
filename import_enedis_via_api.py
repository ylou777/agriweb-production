"""
Script pour importer les données Enedis via l'API Flask Railway
Envoie le CSV au serveur qui l'importe directement dans PostgreSQL
"""

import requests
import os

CSV_PATH = r"C:\Users\Public\Documents\conso sup36KW\consommation-annuelle-entreprise-par-adresse.csv"
API_URL = "https://ample-manifestation-production-7b1a.up.railway.app/api/admin/import-enedis"

def upload_csv():
    """Upload le CSV Enedis vers Railway pour import"""
    
    if not os.path.exists(CSV_PATH):
        print(f"❌ Fichier CSV introuvable: {CSV_PATH}")
        return
    
    file_size = os.path.getsize(CSV_PATH) / (1024 * 1024)
    print(f"📁 Fichier CSV: {CSV_PATH}")
    print(f"📊 Taille: {file_size:.2f} MB")
    print(f"🚀 Upload vers {API_URL}...")
    
    with open(CSV_PATH, 'rb') as f:
        files = {'file': ('enedis.csv', f, 'text/csv')}
        
        # Timeout 30 minutes pour gros fichier
        response = requests.post(
            API_URL,
            files=files,
            timeout=1800
        )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Import réussi!")
        print(f"   - Table créée: {result.get('table_created')}")
        print(f"   - Lignes importées: {result.get('rows_imported')}")
        print(f"   - Lignes géocodées: {result.get('rows_geocoded')}")
        print(f"   - Temps: {result.get('duration_seconds'):.1f}s")
    else:
        print(f"❌ Erreur {response.status_code}: {response.text}")

if __name__ == "__main__":
    upload_csv()
