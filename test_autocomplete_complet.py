"""
Test de l'autocomplétion pour les adresses et les communes
"""

import requests
import sys

BASE_URL = "http://localhost:5000"

def test_autocomplete_address():
    """Test de l'autocomplétion des adresses"""
    print("🏠 Test Autocomplete ADRESSE")
    print("=" * 60)
    
    test_cases = [
        ("moutier", "Moutiers-d'Ahun"),
        ("verdu", "Verdun"),
        ("23150", "Moutiers-d'Ahun"),
        ("5 rue de la", "Rue de la"),
        ("pari", "Paris"),
    ]
    
    for query, expected in test_cases:
        print(f"\n📍 Test: '{query}'")
        try:
            response = requests.get(f"{BASE_URL}/api/autocomplete/address", params={"q": query})
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    suggestions = data.get("suggestions", [])
                    count = data.get("count", 0)
                    
                    print(f"   ✅ Statut: {response.status_code}")
                    print(f"   ✅ Nombre de suggestions: {count}")
                    
                    if suggestions:
                        print(f"   📋 Suggestions:")
                        for i, sugg in enumerate(suggestions[:3], 1):
                            label = sugg.get("properties", {}).get("label", "N/A")
                            print(f"      {i}. {label}")
                        
                        # Vérifier que la suggestion attendue est présente
                        labels = [s.get("properties", {}).get("label", "") for s in suggestions]
                        if any(expected.lower() in label.lower() for label in labels):
                            print(f"   ✅ Suggestion attendue '{expected}' trouvée")
                        else:
                            print(f"   ⚠️  Suggestion attendue '{expected}' non trouvée")
                    else:
                        print(f"   ⚠️  Aucune suggestion")
                else:
                    print(f"   ❌ Erreur: {data.get('error')}")
            else:
                print(f"   ❌ Statut HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")


def test_autocomplete_commune():
    """Test de l'autocomplétion des communes"""
    print("\n\n🏘️  Test Autocomplete COMMUNE")
    print("=" * 60)
    
    test_cases = [
        ("limo", "Limoges"),
        ("pari", "Paris"),
        ("verdu", "Verdun"),
        ("ahun", "Ahun"),
        ("87", "Limoges"),
    ]
    
    for query, expected in test_cases:
        print(f"\n📍 Test: '{query}'")
        try:
            response = requests.get(f"{BASE_URL}/api/autocomplete/commune", params={"q": query})
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    suggestions = data.get("suggestions", [])
                    count = data.get("count", 0)
                    
                    print(f"   ✅ Statut: {response.status_code}")
                    print(f"   ✅ Nombre de suggestions: {count}")
                    
                    if suggestions:
                        print(f"   📋 Suggestions:")
                        for i, sugg in enumerate(suggestions[:3], 1):
                            nom = sugg.get("nom", "N/A")
                            codes = sugg.get("codesPostaux", [])
                            code_postal = codes[0] if codes else "N/A"
                            pop = sugg.get("population", 0)
                            print(f"      {i}. {nom} ({code_postal}) - {pop:,} hab.")
                        
                        # Vérifier que la suggestion attendue est présente
                        noms = [s.get("nom", "") for s in suggestions]
                        if any(expected.lower() in nom.lower() for nom in noms):
                            print(f"   ✅ Suggestion attendue '{expected}' trouvée")
                        else:
                            print(f"   ⚠️  Suggestion attendue '{expected}' non trouvée")
                    else:
                        print(f"   ⚠️  Aucune suggestion")
                else:
                    print(f"   ❌ Erreur: {data.get('error')}")
            else:
                print(f"   ❌ Statut HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")


def test_typo_tolerance():
    """Test de la tolérance aux fautes de frappe"""
    print("\n\n🔤 Test TOLÉRANCE AUX TYPOS")
    print("=" * 60)
    
    typos = [
        # (saisie_incorrecte, suggestion_attendue, type)
        ("montiers", "Moutiers", "address"),
        ("limmoge", "Limoges", "commune"),
        ("verdon", "Verdun", "address"),
        ("pariz", "Paris", "commune"),
    ]
    
    for typo, expected, search_type in typos:
        endpoint = f"{BASE_URL}/api/autocomplete/{search_type}"
        print(f"\n📝 Test typo: '{typo}' → '{expected}' ({search_type})")
        
        try:
            response = requests.get(endpoint, params={"q": typo})
            
            if response.status_code == 200:
                data = response.json()
                suggestions = data.get("suggestions", [])
                
                if suggestions:
                    if search_type == "address":
                        labels = [s.get("properties", {}).get("label", "") for s in suggestions]
                        found = any(expected.lower() in label.lower() for label in labels)
                    else:  # commune
                        noms = [s.get("nom", "") for s in suggestions]
                        found = any(expected.lower() in nom.lower() for nom in noms)
                    
                    if found:
                        print(f"   ✅ Tolérance OK: '{expected}' trouvé malgré la typo")
                    else:
                        print(f"   ⚠️  Tolérance KO: '{expected}' non trouvé")
                        print(f"      Suggestions reçues: {labels[:2] if search_type == 'address' else noms[:2]}")
                else:
                    print(f"   ❌ Aucune suggestion")
            else:
                print(f"   ❌ Statut HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")


def test_server_health():
    """Vérifier que le serveur Flask est accessible"""
    print("\n🏥 Test SANTÉ DU SERVEUR")
    print("=" * 60)
    
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            print(f"✅ Serveur accessible sur {BASE_URL}")
            return True
        else:
            print(f"⚠️  Serveur répond avec le statut: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Impossible de se connecter à {BASE_URL}")
        print("   Vérifiez que Flask est démarré: python agriweb_hebergement_gratuit.py")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def main():
    """Lancer tous les tests"""
    print("\n" + "=" * 60)
    print("🧪 TESTS D'AUTOCOMPLÉTION - ADRESSES & COMMUNES")
    print("=" * 60 + "\n")
    
    # Vérifier la santé du serveur
    if not test_server_health():
        print("\n❌ Impossible de continuer sans serveur Flask")
        sys.exit(1)
    
    # Tests d'autocomplétion
    test_autocomplete_address()
    test_autocomplete_commune()
    test_typo_tolerance()
    
    # Résumé
    print("\n\n" + "=" * 60)
    print("✅ TESTS TERMINÉS")
    print("=" * 60)
    print("\n💡 Pour tester manuellement:")
    print("   1. Ouvrez http://localhost:5000")
    print("   2. Testez le champ 'Adresse' (accordéon 1)")
    print("   3. Testez le champ 'Commune' (accordéon 2)")
    print("   4. Vérifiez les suggestions dans la console (F12)")


if __name__ == "__main__":
    main()
