"""
Test de comparaison entre les deux APIs Sirene disponibles
"""

import requests
import time

def test_api_entreprise():
    """Test de l'API publique entreprise.data.gouv.fr"""
    print("\n" + "="*80)
    print("TEST 1: API Entreprise (data.gouv.fr) - PUBLIQUE")
    print("="*80)
    
    siret = "31252693800047"
    url = f"https://entreprise.data.gouv.fr/api/sirene/v3/etablissements/{siret}"
    
    print(f"URL: {url}")
    print(f"Authentification: NON")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"✓ Statut: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ SUCCÈS - Données reçues")
            return True
    except requests.exceptions.ConnectionError as e:
        error_str = str(e)
        if "10061" in error_str:
            print(f"✗ Connexion refusée (10061)")
        elif "10054" in error_str:
            print(f"✗ Connexion fermée par l'hôte (10054)")
        else:
            print(f"✗ Erreur connexion: {type(e).__name__}")
    except requests.exceptions.Timeout:
        print(f"✗ Timeout après 5s")
    except Exception as e:
        print(f"✗ Erreur: {type(e).__name__}")
    
    return False

def test_api_insee_sans_auth():
    """Test de l'API INSEE officielle SANS authentification (devrait échouer)"""
    print("\n" + "="*80)
    print("TEST 2: API INSEE (api.insee.fr) - SANS TOKEN")
    print("="*80)
    
    siret = "31252693800047"
    url = f"https://api.insee.fr/entreprises/sirene/V3/siret/{siret}"
    
    print(f"URL: {url}")
    print(f"Authentification: NON (devrait échouer)")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"✓ Statut: {response.status_code}")
        
        if response.status_code == 401:
            print(f"✓ Comportement attendu: 401 Unauthorized")
            print(f"  → L'API INSEE nécessite un token Bearer")
            return True
        elif response.status_code == 200:
            print(f"⚠ Inattendu: API accessible sans token!")
            return True
        else:
            print(f"⚠ Statut inattendu: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print(f"✗ Erreur connexion")
    except requests.exceptions.Timeout:
        print(f"✗ Timeout")
    except Exception as e:
        print(f"✗ Erreur: {type(e).__name__}")
    
    return False

def test_api_insee_endpoint_accessible():
    """Test si l'endpoint API INSEE est accessible (base URL)"""
    print("\n" + "="*80)
    print("TEST 3: API INSEE - Accessibilité du domaine")
    print("="*80)
    
    url = "https://api.insee.fr/"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"✓ Domaine accessible - Statut: {response.status_code}")
        return True
    except Exception as e:
        print(f"✗ Domaine inaccessible: {type(e).__name__}")
        return False

def test_recherche_multicriteres():
    """Test endpoint de recherche avec critères"""
    print("\n" + "="*80)
    print("TEST 4: Endpoint de recherche multi-critères")
    print("="*80)
    
    url = "https://entreprise.data.gouv.fr/api/sirene/v3/siret?q=activitePrincipaleUniteLegale:01*&nombre=1"
    
    print(f"URL: {url}")
    print(f"Recherche: Activité agricole (01*)")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"✓ Statut: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Nombre de résultats: {data.get('header', {}).get('total', 0)}")
            return True
            
    except Exception as e:
        print(f"✗ Erreur: {type(e).__name__}")
    
    return False

def main():
    print("="*80)
    print("COMPARAISON DES APIs SIRENE DISPONIBLES")
    print("="*80)
    
    results = {
        'entreprise_api': test_api_entreprise(),
        'insee_sans_auth': test_api_insee_sans_auth(),
        'insee_domaine': test_api_insee_endpoint_accessible(),
        'recherche': test_recherche_multicriteres()
    }
    
    time.sleep(1)
    
    # Résumé
    print("\n" + "="*80)
    print("RÉSUMÉ ET RECOMMANDATIONS")
    print("="*80)
    
    if results['entreprise_api']:
        print("\n✅ API Entreprise (data.gouv.fr) fonctionne")
        print("   → Continuer à l'utiliser")
        print("   → Garder le cache et les retry actuels")
    else:
        print("\n❌ API Entreprise (data.gouv.fr) inaccessible")
        print("   Causes possibles:")
        print("   1. Maintenance temporaire")
        print("   2. Rate limiting (trop de requêtes)")
        print("   3. Blocage réseau/pare-feu")
        
    if results['insee_domaine']:
        print("\n✅ API INSEE (api.insee.fr) est accessible")
        print("   → Option de migration disponible")
        print("   → Nécessite:")
        print("      1. Créer un compte sur api.insee.fr")
        print("      2. Obtenir client_id et client_secret")
        print("      3. Implémenter gestion OAuth2 token")
        print("      4. Avantages: 30 req/min, plus stable")
    else:
        print("\n❌ API INSEE inaccessible")
        print("   → Problème réseau global")
        
    print("\n" + "-"*80)
    print("STRATÉGIE RECOMMANDÉE:")
    print("-"*80)
    
    if not results['entreprise_api'] and not results['insee_domaine']:
        print("\n⚠️ Aucune API Sirene accessible actuellement")
        print("   → Attendre 1-2 heures et réessayer")
        print("   → Vérifier pare-feu/proxy d'entreprise")
        print("   → L'application fonctionne en mode dégradé")
    elif not results['entreprise_api'] and results['insee_domaine']:
        print("\n💡 Migrer vers API INSEE officielle")
        print("   Étapes:")
        print("   1. S'inscrire sur https://api.insee.fr/")
        print("   2. Créer une application")
        print("   3. Récupérer les credentials")
        print("   4. Implémenter fetch_sirene_info_insee() avec OAuth2")
    else:
        print("\n✅ API Entreprise fonctionne - Aucune action requise")
        print("   → Les corrections actuelles sont suffisantes")

if __name__ == "__main__":
    main()
