"""
Script de vérification rapide de l'autocomplétion
Teste les cas les plus importants
"""

import requests
import sys

BASE_URL = "http://localhost:5000"

def test_endpoint(endpoint, query, expected_keyword):
    """Test un endpoint avec un mot-clé attendu dans les résultats"""
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", params={'q': query}, timeout=3)
        
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}"
        
        data = response.json()
        suggestions = data.get('suggestions', [])
        
        if not suggestions:
            return False, "Aucune suggestion"
        
        # Vérifier si le mot-clé est dans au moins une suggestion
        found = any(expected_keyword.lower() in str(sugg).lower() for sugg in suggestions)
        
        if not found:
            return False, f"'{expected_keyword}' non trouvé"
        
        return True, f"{len(suggestions)} suggestions"
        
    except Exception as e:
        return False, str(e)

def main():
    print("🔍 VÉRIFICATION RAPIDE DE L'AUTOCOMPLÉTION")
    print("="*60)
    
    tests = [
        # (endpoint, query, expected_keyword, description)
        ("/api/autocomplete/address", "montiers", "moutiers", "Adresse: faute typo"),
        ("/api/autocomplete/address", "verdun 55", "verdun", "Adresse: avec dept"),
        ("/api/autocomplete/address", "lyon", "lyon", "Adresse: ville simple"),
        ("/api/autocomplete/commune", "montiers", "moutiers", "Commune: faute typo"),
        ("/api/autocomplete/commune", "verdun", "verdun", "Commune: homonymes"),
        ("/api/autocomplete/commune", "23150", "moutiers", "Commune: code postal"),
    ]
    
    passed = 0
    failed = 0
    
    for endpoint, query, expected, description in tests:
        success, message = test_endpoint(endpoint, query, expected)
        
        status = "✅" if success else "❌"
        print(f"\n{status} {description}")
        print(f"   Query: '{query}' → {message}")
        
        if success:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*60)
    print(f"RÉSULTAT: {passed}/{len(tests)} tests passés")
    
    if failed == 0:
        print("✅ ✅ ✅ TOUT FONCTIONNE PARFAITEMENT ! ✅ ✅ ✅")
        return 0
    else:
        print(f"⚠️  {failed} test(s) échoué(s)")
        return 1

if __name__ == "__main__":
    sys.exit(main())
