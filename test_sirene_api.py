"""
Test Script pour l'API Sirene
Diagnostique et valide la connectivité et les réponses de l'API Sirene
"""

import requests
import time
from datetime import datetime

# Exemples de SIRET à tester (entreprises agricoles connues)
TEST_SIRETS = [
    "31252693800047",  # Exemple d'entreprise
    "44306184100047",  # Exemple d'entreprise
    "89207591800018",  # Exemple d'entreprise
    "INVALID_SIRET",   # Test d'erreur
]

def test_sirene_direct(siret, timeout=5):
    """Test direct de l'API Sirene sans retry"""
    url = f"https://entreprise.data.gouv.fr/api/sirene/v3/unites_legales/{siret}"
    
    print(f"\n{'='*80}")
    print(f"Test SIRET: {siret}")
    print(f"URL: {url}")
    print(f"Timeout: {timeout}s")
    
    start_time = time.time()
    
    try:
        response = requests.get(url, timeout=timeout)
        elapsed = time.time() - start_time
        
        print(f"✓ Statut HTTP: {response.status_code}")
        print(f"✓ Temps de réponse: {elapsed:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            if 'unite_legale' in data:
                ul = data['unite_legale']
                print(f"✓ Dénomination: {ul.get('denomination', ul.get('nom_raison_sociale', 'N/A'))}")
                print(f"✓ Activité principale: {ul.get('activite_principale', 'N/A')}")
                print(f"✓ État: {ul.get('etat_administratif', 'N/A')}")
                return True, elapsed, data
            else:
                print(f"⚠ Réponse valide mais structure inattendue")
                return True, elapsed, data
        elif response.status_code == 404:
            print(f"⚠ SIRET non trouvé (404)")
            return False, elapsed, None
        else:
            print(f"✗ Erreur HTTP: {response.status_code}")
            return False, elapsed, None
            
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"✗ TIMEOUT après {elapsed:.2f}s")
        return False, elapsed, None
        
    except requests.exceptions.ConnectionError as e:
        elapsed = time.time() - start_time
        print(f"✗ ERREUR DE CONNEXION: {str(e)[:100]}")
        return False, elapsed, None
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"✗ ERREUR: {type(e).__name__}: {str(e)[:100]}")
        return False, elapsed, None

def test_sirene_with_retry(siret, max_retries=2, timeout=3):
    """Test avec retry et backoff comme dans fetch_sirene_info"""
    print(f"\n{'='*80}")
    print(f"Test avec RETRY - SIRET: {siret}")
    print(f"Max retries: {max_retries}, Timeout: {timeout}s")
    
    url = f"https://entreprise.data.gouv.fr/api/sirene/v3/unites_legales/{siret}"
    
    for attempt in range(max_retries + 1):
        if attempt > 0:
            wait_time = 0.5 * (2 ** (attempt - 1))  # 0.5s, 1s
            print(f"  → Retry {attempt}/{max_retries} après {wait_time}s...")
            time.sleep(wait_time)
        
        start_time = time.time()
        try:
            response = requests.get(url, timeout=timeout)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if 'unite_legale' in data:
                    ul = data['unite_legale']
                    print(f"✓ SUCCÈS (tentative {attempt + 1}) - {elapsed:.2f}s")
                    print(f"  Dénomination: {ul.get('denomination', ul.get('nom_raison_sociale', 'N/A'))}")
                    return True, attempt + 1, elapsed, data
            elif response.status_code == 404:
                print(f"⚠ SIRET non trouvé (404) - abandon")
                return False, attempt + 1, elapsed, None
            else:
                print(f"  Tentative {attempt + 1}: HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            elapsed = time.time() - start_time
            print(f"  Tentative {attempt + 1}: TIMEOUT après {elapsed:.2f}s")
            
        except requests.exceptions.ConnectionError as e:
            elapsed = time.time() - start_time
            print(f"  Tentative {attempt + 1}: ERREUR CONNEXION")
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  Tentative {attempt + 1}: {type(e).__name__}")
    
    print(f"✗ ÉCHEC après {max_retries + 1} tentatives")
    return False, max_retries + 1, 0, None

def test_api_availability():
    """Test la disponibilité générale de l'API"""
    print(f"\n{'#'*80}")
    print(f"# TEST DE DISPONIBILITÉ DE L'API SIRENE")
    print(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*80}")
    
    url = "https://entreprise.data.gouv.fr/api/sirene/v3/"
    
    try:
        response = requests.get(url, timeout=5)
        print(f"✓ API accessible (HTTP {response.status_code})")
        return True
    except Exception as e:
        print(f"✗ API inaccessible: {e}")
        return False

def main():
    print("="*80)
    print("TEST COMPLET DE L'API SIRENE")
    print("="*80)
    
    # 1. Test de disponibilité
    available = test_api_availability()
    
    if not available:
        print("\n⚠ L'API Sirene semble inaccessible. Tests abandonnés.")
        return
    
    # 2. Tests directs
    print("\n" + "#"*80)
    print("# PARTIE 1: TESTS DIRECTS (sans retry)")
    print("#"*80)
    
    results_direct = []
    for siret in TEST_SIRETS[:3]:  # Skip invalid
        success, elapsed, data = test_sirene_direct(siret, timeout=5)
        results_direct.append({
            'siret': siret,
            'success': success,
            'elapsed': elapsed
        })
        time.sleep(0.5)  # Pause entre requêtes
    
    # 3. Tests avec retry
    print("\n" + "#"*80)
    print("# PARTIE 2: TESTS AVEC RETRY")
    print("#"*80)
    
    results_retry = []
    for siret in TEST_SIRETS[:3]:
        success, attempts, elapsed, data = test_sirene_with_retry(siret, max_retries=2, timeout=3)
        results_retry.append({
            'siret': siret,
            'success': success,
            'attempts': attempts,
            'elapsed': elapsed
        })
        time.sleep(0.5)
    
    # 4. Test du SIRET invalide
    print("\n" + "#"*80)
    print("# PARTIE 3: TEST SIRET INVALIDE")
    print("#"*80)
    test_sirene_direct(TEST_SIRETS[3], timeout=3)
    
    # 5. Résumé
    print("\n" + "="*80)
    print("RÉSUMÉ DES TESTS")
    print("="*80)
    
    print("\nTests directs:")
    success_count = sum(1 for r in results_direct if r['success'])
    avg_time = sum(r['elapsed'] for r in results_direct if r['success']) / max(success_count, 1)
    print(f"  Succès: {success_count}/{len(results_direct)}")
    print(f"  Temps moyen: {avg_time:.2f}s")
    
    print("\nTests avec retry:")
    success_count = sum(1 for r in results_retry if r['success'])
    avg_attempts = sum(r['attempts'] for r in results_retry) / len(results_retry)
    avg_time = sum(r['elapsed'] for r in results_retry if r['success']) / max(success_count, 1)
    print(f"  Succès: {success_count}/{len(results_retry)}")
    print(f"  Tentatives moyennes: {avg_attempts:.1f}")
    print(f"  Temps moyen: {avg_time:.2f}s")
    
    print("\n" + "="*80)
    print("RECOMMANDATIONS:")
    print("="*80)
    
    if success_count == len(results_retry):
        print("✓ API Sirene fonctionne correctement")
        print("✓ Les timeouts et retry actuels semblent appropriés")
    elif success_count > 0:
        print("⚠ API Sirene instable - réussites partielles")
        print("→ Le cache et le retry sont essentiels")
        print("→ Limiter le nombre d'appels simultanés (max 10)")
    else:
        print("✗ API Sirene ne répond pas")
        print("→ Vérifier la connectivité réseau")
        print("→ Vérifier si l'API est en maintenance")
        print("→ Envisager de désactiver temporairement l'enrichissement")

if __name__ == "__main__":
    main()
