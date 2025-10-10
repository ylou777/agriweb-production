"""
Test simple et direct de l'API Sirene
"""

import requests
import time
from datetime import datetime

def test_basic_connectivity():
    """Test basique de connectivité"""
    print(f"\n{'='*80}")
    print("TEST 1: Connexion basique à entreprise.data.gouv.fr")
    print(f"{'='*80}")
    
    urls = [
        "https://entreprise.data.gouv.fr",
        "https://entreprise.data.gouv.fr/api/sirene/v3",
    ]
    
    for url in urls:
        print(f"\nTest: {url}")
        try:
            response = requests.get(url, timeout=10)
            print(f"  ✓ Statut: {response.status_code}")
            print(f"  ✓ Taille réponse: {len(response.content)} bytes")
        except requests.exceptions.Timeout:
            print(f"  ✗ TIMEOUT après 10s")
        except requests.exceptions.ConnectionError as e:
            print(f"  ✗ ERREUR CONNEXION: {type(e).__name__}")
            print(f"     {str(e)[:200]}")
        except Exception as e:
            print(f"  ✗ ERREUR: {type(e).__name__}: {str(e)[:100]}")

def test_simple_siret():
    """Test avec un SIRET simple et connu"""
    print(f"\n{'='*80}")
    print("TEST 2: Requête SIRET simple")
    print(f"{'='*80}")
    
    # SIRET de test - entreprise connue
    siret = "31252693800047"
    url = f"https://entreprise.data.gouv.fr/api/sirene/v3/etablissements/{siret}"
    
    print(f"\nSIRET: {siret}")
    print(f"URL: {url}")
    
    for attempt in range(3):
        print(f"\n  Tentative {attempt + 1}/3...")
        start = time.time()
        
        try:
            response = requests.get(url, timeout=10)
            elapsed = time.time() - start
            
            print(f"    ✓ Réponse reçue en {elapsed:.2f}s")
            print(f"    ✓ Statut: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'etablissement' in data:
                    etab = data['etablissement']
                    print(f"    ✓ Dénomination: {etab.get('unite_legale', {}).get('denomination', 'N/A')}")
                    print(f"    ✓ SUCCÈS!")
                    return True
            elif response.status_code == 404:
                print(f"    ⚠ SIRET non trouvé")
                return False
            else:
                print(f"    ⚠ Statut inattendu: {response.status_code}")
                
        except requests.exceptions.Timeout:
            elapsed = time.time() - start
            print(f"    ✗ TIMEOUT après {elapsed:.2f}s")
            
        except requests.exceptions.ConnectionError as e:
            elapsed = time.time() - start
            print(f"    ✗ ERREUR CONNEXION après {elapsed:.2f}s")
            print(f"       Type: {type(e).__name__}")
            error_str = str(e)
            if "10061" in error_str:
                print(f"       → Connexion refusée (10061)")
            elif "10054" in error_str:
                print(f"       → Connexion fermée par l'hôte (10054)")
            
        except Exception as e:
            elapsed = time.time() - start
            print(f"    ✗ ERREUR: {type(e).__name__}")
            print(f"       {str(e)[:150]}")
        
        if attempt < 2:
            wait = 2
            print(f"    → Attente {wait}s avant retry...")
            time.sleep(wait)
    
    print(f"\n  ✗ Échec après 3 tentatives")
    return False

def test_alternative_endpoint():
    """Test de l'endpoint unites_legales au lieu de etablissements"""
    print(f"\n{'='*80}")
    print("TEST 3: Endpoint alternatif (unites_legales)")
    print(f"{'='*80}")
    
    siret = "31252693800047"
    siren = siret[:9]  # Prendre les 9 premiers caractères
    url = f"https://entreprise.data.gouv.fr/api/sirene/v3/unites_legales/{siren}"
    
    print(f"\nSIREN: {siren}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"  ✓ Statut: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'unite_legale' in data:
                ul = data['unite_legale']
                print(f"  ✓ Dénomination: {ul.get('denomination', 'N/A')}")
                print(f"  ✓ SUCCÈS avec endpoint unites_legales!")
                return True
                
    except Exception as e:
        print(f"  ✗ ERREUR: {type(e).__name__}")
    
    return False

def main():
    print("="*80)
    print(f"DIAGNOSTIC SIRENE API - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Test 1: Connectivité basique
    test_basic_connectivity()
    time.sleep(2)
    
    # Test 2: Requête SIRET
    success_siret = test_simple_siret()
    time.sleep(2)
    
    # Test 3: Alternative
    success_alt = test_alternative_endpoint()
    
    # Résumé
    print(f"\n{'='*80}")
    print("RÉSUMÉ DU DIAGNOSTIC")
    print(f"{'='*80}")
    
    if success_siret or success_alt:
        print("\n✓ L'API Sirene fonctionne")
        print("  → Le problème dans l'application peut venir de:")
        print("     - Trop d'appels simultanés")
        print("     - Timeout trop court")
        print("     - Pas de retry")
        print("\n✓ Les corrections apportées (cache + retry) devraient résoudre le problème")
    else:
        print("\n✗ L'API Sirene est actuellement inaccessible depuis votre réseau")
        print("\nCauses possibles:")
        print("  1. L'API est en maintenance")
        print("  2. Votre pare-feu bloque les connexions HTTPS vers ce domaine")
        print("  3. Limitation du nombre de requêtes (rate limiting)")
        print("  4. Problème réseau temporaire")
        print("\nSolutions:")
        print("  → Réessayer dans quelques minutes")
        print("  → Vérifier les paramètres pare-feu")
        print("  → L'enrichissement Sirene est maintenant limité à 10 max")
        print("  → Le cache évitera les appels répétés")

if __name__ == "__main__":
    main()
