import requests
import time

print("⏳ Attente 10 secondes pour le serveur...")
time.sleep(10)

print("🔍 Test simple avec filtrage HTA souterrain")
url = "http://localhost:5000/generate_reports_by_dept_sse"
params = {
    'department': '90',
    'reseau_types': 'HTA',
    'min_area_ha': '10',
    'max_area_ha': '50',
    'hta_underground_max_distance': '0.5',
    'filter_hta_lines_underground': 'true'
}

try:
    response = requests.get(url, params=params, stream=True, timeout=20)
    ligne_count = 0
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            ligne_count += 1
            
            # Chercher les logs importants
            if any(keyword in line_str for keyword in [
                'Filtres HTA lignes', 
                'HTA UNDERGROUND', 
                'RPG REJECTED',
                'RPG filtré:',
                'Bbox réel commune'
            ]):
                print(f"📋 {line_str.strip()}")
            
            # Arrêter après 2 communes pour test
            if 'SSE COMMUNE 3/' in line_str:
                break
    
    print(f"✅ Test terminé - {ligne_count} lignes traitées")
    
except Exception as e:
    print(f"❌ Erreur: {e}")