"""
Test de la fonction fetch_sirene_info mise à jour
avec la nouvelle API Recherche Entreprises
"""

import sys
sys.path.insert(0, '.')

# Mock des dépendances
import requests
class MockSession:
    def get(self, *args, **kwargs):
        return requests.get(*args, **kwargs)

http_session = MockSession()

# Import de la fonction modifiée
_sirene_cache = {}
_sirene_failures = set()

exec(open('agriweb_hebergement_gratuit.py', encoding='utf-8').read().split('def fetch_sirene_info')[0])

def fetch_sirene_info(siret, max_retries=0, timeout=0.5):
    """Version de test"""
    if siret in _sirene_cache:
        return _sirene_cache[siret]
    
    if siret in _sirene_failures:
        return None
    
    url = f"https://recherche-entreprises.api.gouv.fr/search?q={siret}"
    
    for attempt in range(max_retries + 1):
        try:
            response = http_session.get(url, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('total_results', 0) > 0 and data.get('results'):
                    result = data['results'][0]
                    
                    formatted_data = {
                        'etablissement': {
                            'siret': result.get('siege', {}).get('siret', siret),
                            'siren': result.get('siren', siret[:9] if len(siret) >= 9 else ''),
                            'uniteLegale': {
                                'denominationUniteLegale': result.get('nom_complet') or result.get('nom_raison_sociale'),
                                'activitePrincipaleUniteLegale': result.get('activite_principale'),
                                'categorieJuridiqueUniteLegale': result.get('nature_juridique'),
                            },
                            'adresseEtablissement': result.get('siege', {}).get('adresse', '')
                        }
                    }
                    
                    _sirene_cache[siret] = formatted_data
                    return formatted_data
                else:
                    _sirene_failures.add(siret)
                    return None
            else:
                _sirene_failures.add(siret)
                return None
                
        except Exception:
            _sirene_failures.add(siret)
            return None
    
    _sirene_failures.add(siret)
    return None

# Tests
print("="*80)
print("TEST FONCTION fetch_sirene_info() MISE À JOUR")
print("="*80)

# Test avec un SIREN connu (Google France)
test_cases = [
    ("44306184100047", "Google France LLC"),
    ("48126505600020", "AGRICULTURE Marseille"),
]

for siret, expected_name in test_cases:
    print(f"\nTest SIRET: {siret}")
    print(f"Attendu: {expected_name}")
    
    result = fetch_sirene_info(siret, timeout=2)
    
    if result:
        nom = result.get('etablissement', {}).get('uniteLegale', {}).get('denominationUniteLegale')
        print(f"✓ Résultat: {nom}")
        print(f"  SIREN: {result.get('etablissement', {}).get('siren')}")
        print(f"  Activité: {result.get('etablissement', {}).get('uniteLegale', {}).get('activitePrincipaleUniteLegale')}")
    else:
        print(f"✗ Aucun résultat (SIRET peut-être invalide ou API ne le trouve pas)")

print(f"\n{'='*80}")
print("STATISTIQUES")
print(f"{'='*80}")
print(f"Cache hits: {len(_sirene_cache)}")
print(f"Failures: {len(_sirene_failures)}")
