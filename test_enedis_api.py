"""
Test de l'API Enedis Open Data pour consommation électrique
"""
import requests
import json

def test_enedis_api(lat, lon, radius_m=500):
    """Test de l'API Enedis avec coordonnées GPS"""
    
    print(f"🔍 Test API Enedis Open Data")
    print(f"📍 Coordonnées: lat={lat}, lon={lon}")
    print(f"📏 Rayon: {radius_m}m\n")
    
    url = "https://opendata.enedis.fr/data-fair/api/v1/datasets/consommation-annuelle-entreprise-par-adresse"
    
    # Test plusieurs syntaxes possibles
    params_variants = [
        {
            'name': 'Syntaxe 1: _geopoint avec distance',
            'params': {
                'size': 100,
                'select': 'adresse,code_postal,pdl,consommation_annuelle_mwh,nb_sites,code_commune',
                'qs': f'_geopoint:{lat},{lon},{radius_m}'
            }
        },
        {
            'name': 'Syntaxe 2: geo_distance',
            'params': {
                'size': 100,
                'select': 'adresse,code_postal,pdl,consommation_annuelle_mwh,nb_sites,code_commune',
                'geo_distance': f'{radius_m}m',
                'geo_point': f'{lat},{lon}'
            }
        },
        {
            'name': 'Syntaxe 3: Sans filtre géographique (tous les résultats)',
            'params': {
                'size': 10,
                'select': 'adresse,code_postal,pdl,consommation_annuelle_mwh,nb_sites,code_commune'
            }
        }
    ]
    
    for variant in params_variants:
        params = variant['params']
        print(f"\n{'='*60}")
        print(f"🧪 {variant['name']}")
        print(f"{'='*60}")
    
        print(f"📊 Paramètres: {json.dumps(params, indent=2)}\n")
        
        try:
            response = requests.get(url, params=params, timeout=10)
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"🔗 URL finale: {response.url}\n")
        
        if response.status_code == 200:
            data = response.json()
            
            total = data.get('total', 0)
            results = data.get('results', [])
            
            print(f"✅ Réponse réussie!")
            print(f"📈 Total de résultats trouvés: {total}")
            print(f"📋 Résultats retournés: {len(results)}\n")
        
        print(f"📊 Paramètres: {json.dumps(params, indent=2)}\n")
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            print(f"📡 Status Code: {response.status_code}")
            print(f"🔗 URL finale: {response.url}\n")
            
            if response.status_code == 200:
                data = response.json()
                
                total = data.get('total', 0)
                results = data.get('results', [])
                
                print(f"✅ Réponse réussie!")
                print(f"📈 Total de résultats trouvés: {total}")
                print(f"📋 Résultats retournés: {len(results)}\n")
                
                if results:
                    print(f"🏢 Premiers résultats:")
                    for i, item in enumerate(results[:3], 1):
                        print(f"\n  {i}. Adresse: {item.get('adresse', 'N/A')}")
                        print(f"     Code postal: {item.get('code_postal', 'N/A')}")
                        print(f"     PDL: {item.get('pdl', 'N/A')}")
                        print(f"     Consommation: {item.get('consommation_annuelle_mwh', 'N/A')} MWh")
                        print(f"     Nb sites: {item.get('nb_sites', 'N/A')}")
                    
                    return data  # Succès, on retourne
                else:
                    print(f"⚠️ Aucun résultat avec cette syntaxe")
            else:
                print(f"❌ Erreur HTTP {response.status_code}")
                print(f"📄 Réponse: {response.text[:300]}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    # Aucune syntaxe n'a fonctionné
    return None


if __name__ == "__main__":
    # Test avec différentes coordonnées
    
    # Exemple 1: Paris (centre)
    print("="*70)
    print("TEST 1: Paris Centre")
    print("="*70)
    test_enedis_api(48.8566, 2.3522, 500)
    
    print("\n" + "="*70)
    print("TEST 2: Paris - Rayon plus grand (1km)")
    print("="*70)
    test_enedis_api(48.8566, 2.3522, 1000)
    
    # Si vous avez des coordonnées spécifiques de votre prospect
    print("\n" + "="*70)
    print("TEST 3: Coordonnées personnalisées (si disponibles)")
    print("="*70)
    print("💡 Remplacez les coordonnées ci-dessous par celles de votre prospect")
    # test_enedis_api(VOTRE_LAT, VOTRE_LON, 500)
