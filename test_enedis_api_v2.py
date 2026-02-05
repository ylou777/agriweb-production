"""
Test de l'API Enedis Open Data pour consommation électrique
"""
import requests
import json

def test_enedis_api(lat, lon, radius_m=500):
    """Test de l'API Enedis avec coordonnées GPS"""
    
    print(f"\n🔍 Test API Enedis Open Data")
    print(f"📍 Coordonnées: lat={lat}, lon={lon}")
    print(f"📏 Rayon: {radius_m}m\n")
    
    url = "https://opendata.enedis.fr/data-fair/api/v1/datasets/consommation-annuelle-entreprise-par-adresse"
    
    # Test plusieurs syntaxes possibles
    params_variants = [
        {
            'name': 'Syntaxe 1: _geopoint avec distance',
            'params': {
                'size': 100,
                'select': 'adresse,code_postal,pdl,consommation_annuelle_mwh,nb_sites,code_commune,_geopoint',
                'qs': f'_geopoint:{lat},{lon},{radius_m}'
            }
        },
        {
            'name': 'Syntaxe 2: geo_distance',
            'params': {
                'size': 100,
                'select': 'adresse,code_postal,pdl,consommation_annuelle_mwh,nb_sites,code_commune,_geopoint',
                'geo_distance': f'{radius_m}m',
                'geo_point': f'{lat},{lon}'
            }
        },
        {
            'name': 'Syntaxe 3: Sans filtre géographique (sample)',
            'params': {
                'size': 5,
                'select': 'adresse,code_postal,pdl,consommation_annuelle_mwh,nb_sites,code_commune,_geopoint'
            }
        }
    ]
    
    for variant in params_variants:
        params = variant['params']
        print(f"{'='*70}")
        print(f"🧪 {variant['name']}")
        print(f"{'='*70}")
        print(f"📊 Paramètres: {json.dumps(params, indent=2)}\n")
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            print(f"📡 Status Code: {response.status_code}")
            print(f"🔗 URL: {response.url[:120]}...\n")
            
            if response.status_code == 200:
                data = response.json()
                
                total = data.get('total', 0)
                results = data.get('results', [])
                
                print(f"✅ Réponse réussie!")
                print(f"📈 Total de résultats: {total}")
                print(f"📋 Retournés: {len(results)}\n")
                
                if results:
                    print(f"🏢 Premiers résultats:")
                    for i, item in enumerate(results[:3], 1):
                        print(f"\n  {i}. {item.get('adresse', 'N/A')}")
                        print(f"     CP: {item.get('code_postal', 'N/A')}")
                        print(f"     Conso: {item.get('consommation_annuelle_mwh', 'N/A')} MWh")
                        print(f"     Sites: {item.get('nb_sites', 'N/A')}")
                        if '_geopoint' in item:
                            print(f"     GPS: {item['_geopoint']}")
                    
                    print(f"\n✅ SUCCÈS avec {variant['name']}")
                    return data
                else:
                    print(f"⚠️ Aucun résultat\n")
            else:
                print(f"❌ Erreur HTTP {response.status_code}")
                print(f"📄 {response.text[:200]}\n")
                
        except Exception as e:
            print(f"❌ Erreur: {e}\n")
    
    return None


if __name__ == "__main__":
    # Test 1: Paris
    print("="*70)
    print("TEST 1: Paris Centre (500m)")
    print("="*70)
    data = test_enedis_api(48.8566, 2.3522, 500)
    
    if not data or data.get('total', 0) == 0:
        print("\n" + "="*70)
        print("TEST 2: Paris Centre (rayon 2000m)")
        print("="*70)
        data = test_enedis_api(48.8566, 2.3522, 2000)
    
    # Vérifier la structure des données
    print("\n" + "="*70)
    print("📋 ANALYSE DE LA STRUCTURE DE L'API")
    print("="*70)
    
    if data:
        print(f"✅ L'API fonctionne!")
        print(f"\nClés disponibles dans la réponse:")
        for key in data.keys():
            print(f"  - {key}: {type(data[key])}")
        
        if 'results' in data and len(data['results']) > 0:
            print(f"\nChamps disponibles par résultat:")
            sample = data['results'][0]
            for key in sample.keys():
                print(f"  - {key}: {sample[key]}")
    else:
        print("❌ Aucune donnée récupérée")
        print("\n💡 Possibilités:")
        print("   1. L'API ne contient que des données d'entreprises")
        print("   2. Les données peuvent être limitées géographiquement")
        print("   3. Le dataset peut être vide ou incomplet")
