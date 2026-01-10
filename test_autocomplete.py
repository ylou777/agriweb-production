"""
Script de test pour l'autocomplétion d'adresses et communes
Teste la tolérance aux fautes de frappe
"""

import requests
import time

# Configuration
BASE_URL = "http://localhost:5000"
ADDRESS_ENDPOINT = f"{BASE_URL}/api/autocomplete/address"
COMMUNE_ENDPOINT = f"{BASE_URL}/api/autocomplete/commune"

def test_autocomplete(endpoint, query, test_name):
    """Test une requête d'autocomplétion"""
    print(f"\n{'='*60}")
    print(f"🧪 TEST: {test_name}")
    print(f"{'='*60}")
    print(f"📝 Requête: {query}")
    
    try:
        response = requests.get(endpoint, params={'q': query}, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            suggestions = data.get('suggestions', [])
            
            print(f"✅ Status: {response.status_code}")
            print(f"📊 Nombre de suggestions: {len(suggestions)}")
            
            if suggestions:
                print(f"\n💡 Suggestions:")
                for i, sugg in enumerate(suggestions[:5], 1):  # Afficher les 5 premiers
                    display = sugg.get('display', sugg.get('label', 'N/A'))
                    score = sugg.get('score', 'N/A')
                    print(f"   {i}. {display}")
                    if score != 'N/A':
                        print(f"      Score: {score:.2f}")
            else:
                print("⚠️  Aucune suggestion trouvée")
            
            return True
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏱️  Timeout (> 5s)")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def run_all_tests():
    """Lance tous les tests"""
    print("\n" + "="*60)
    print("🚀 TESTS D'AUTOCOMPLÉTION - AGRIWEB")
    print("="*60)
    
    # Attendre que le serveur soit prêt
    print("\n⏳ Attente du démarrage du serveur...")
    time.sleep(2)
    
    tests_passed = 0
    tests_total = 0
    
    # TESTS ADRESSES
    print("\n" + "="*60)
    print("📍 TESTS RECHERCHE D'ADRESSES")
    print("="*60)
    
    address_tests = [
        ("montiers d'ahun", "Faute de typo: montiers → moutiers"),
        ("verdun 55", "Recherche avec code département"),
        ("10 rue de la paix pari", "Adresse partielle avec faute"),
        ("lyon", "Nom de ville simple"),
        ("75001", "Code postal"),
        ("saint etienne", "Accent manquant"),
        ("moutier", "Recherche partielle"),
        ("bd victor hugo", "Abréviation boulevard"),
    ]
    
    for query, description in address_tests:
        tests_total += 1
        if test_autocomplete(ADDRESS_ENDPOINT, query, description):
            tests_passed += 1
        time.sleep(0.5)  # Éviter de surcharger l'API
    
    # TESTS COMMUNES
    print("\n" + "="*60)
    print("🏛️  TESTS RECHERCHE DE COMMUNES")
    print("="*60)
    
    commune_tests = [
        ("verdun", "Commune simple (devrait trouver plusieurs Verdun)"),
        ("montiers", "Faute de typo: montiers → moutiers"),
        ("75001", "Code postal Paris"),
        ("lyon", "Grande ville"),
        ("moutiers-d'ahun", "Nom exact avec tirets"),
        ("saint-etienne", "Tirets et accents"),
        ("creuse", "Département (devrait trouver des communes)"),
    ]
    
    for query, description in commune_tests:
        tests_total += 1
        if test_autocomplete(COMMUNE_ENDPOINT, query, description):
            tests_passed += 1
        time.sleep(0.5)
    
    # RÉSUMÉ
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*60)
    print(f"✅ Tests réussis: {tests_passed}/{tests_total}")
    print(f"❌ Tests échoués: {tests_total - tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS!")
    elif tests_passed > tests_total / 2:
        print("\n⚠️  La majorité des tests sont passés")
    else:
        print("\n❌ Beaucoup de tests ont échoué - vérifier le serveur")
    
    print("="*60)

if __name__ == "__main__":
    run_all_tests()
