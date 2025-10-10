"""
Test de la nouvelle API Recherche Entreprises
https://recherche-entreprises.api.gouv.fr
"""

import requests
import time

def test_new_api_siret(siret):
    """Test avec la nouvelle API"""
    # Essayons différents endpoints possibles
    
    endpoints = [
        f"https://recherche-entreprises.api.gouv.fr/search?siret={siret}",
        f"https://recherche-entreprises.api.gouv.fr/siret/{siret}",
        f"https://recherche-entreprises.api.gouv.fr/entreprises/{siret}",
    ]
    
    print(f"\nTest SIRET: {siret}")
    print("="*80)
    
    for url in endpoints:
        print(f"\nTest endpoint: {url}")
        try:
            start = time.time()
            response = requests.get(url, timeout=5)
            elapsed = time.time() - start
            
            print(f"  Statut: {response.status_code}")
            print(f"  Temps: {elapsed:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✓ Réponse JSON reçue")
                print(f"  Clés: {list(data.keys())}")
                
                # Afficher un aperçu des données
                if 'results' in data and len(data['results']) > 0:
                    result = data['results'][0]
                    print(f"\n  Données entreprise:")
                    print(f"    - Nom: {result.get('nom_complet', result.get('nom_raison_sociale', 'N/A'))}")
                    print(f"    - SIRET: {result.get('siret', 'N/A')}")
                    print(f"    - Activité: {result.get('activite_principale', 'N/A')}")
                elif 'nom_complet' in data:
                    print(f"\n  Données entreprise:")
                    print(f"    - Nom: {data.get('nom_complet', 'N/A')}")
                    print(f"    - SIRET: {data.get('siret', 'N/A')}")
                    print(f"    - Activité: {data.get('activite_principale', 'N/A')}")
                
                return True, data
            elif response.status_code == 404:
                print(f"  ⚠ SIRET non trouvé (404)")
            else:
                print(f"  ⚠ Erreur HTTP {response.status_code}")
                print(f"  Réponse: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"  ✗ Timeout après 5s")
        except Exception as e:
            print(f"  ✗ Erreur: {type(e).__name__}: {str(e)[:100]}")
    
    return False, None

def test_search_endpoint():
    """Test l'endpoint de recherche"""
    print("\n" + "="*80)
    print("TEST DE RECHERCHE PAR MOT-CLÉ")
    print("="*80)
    
    url = "https://recherche-entreprises.api.gouv.fr/search?q=agriculture"
    print(f"\nURL: {url}")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"Statut: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ API accessible !")
            print(f"Clés réponse: {list(data.keys())}")
            
            if 'results' in data:
                print(f"Nombre de résultats: {len(data['results'])}")
                if data['results']:
                    print(f"\nPremier résultat:")
                    result = data['results'][0]
                    for key, value in list(result.items())[:10]:
                        print(f"  {key}: {value}")
            
            return True, data
    except Exception as e:
        print(f"✗ Erreur: {e}")
    
    return False, None

def main():
    print("="*80)
    print("TEST NOUVELLE API RECHERCHE ENTREPRISES")
    print("https://recherche-entreprises.api.gouv.fr")
    print("="*80)
    
    # Test 1: Endpoint de recherche général
    search_ok, search_data = test_search_endpoint()
    
    time.sleep(1)
    
    # Test 2: SIRET spécifique
    test_sirets = [
        "31252693800047",
        "44306184100047",
        "89207591800018"
    ]
    
    for siret in test_sirets:
        success, data = test_new_api_siret(siret)
        if success:
            print(f"\n✓ API fonctionne avec SIRET {siret}")
            break
        time.sleep(0.5)
    
    # Recommandations
    print("\n" + "="*80)
    print("RECOMMANDATIONS")
    print("="*80)
    
    if search_ok:
        print("\n✓ La nouvelle API recherche-entreprises.api.gouv.fr fonctionne !")
        print("\nÉtapes pour migrer:")
        print("  1. Identifier l'endpoint correct pour SIRET")
        print("  2. Adapter fetch_sirene_info() pour utiliser la nouvelle API")
        print("  3. Mapper les champs de réponse (structure différente)")
        print("  4. Tester avec timeout court (0.5s)")
    else:
        print("\n⚠ Besoin de voir la documentation complète")
        print("  → Consulter https://recherche-entreprises.api.gouv.fr/docs/")

if __name__ == "__main__":
    main()
