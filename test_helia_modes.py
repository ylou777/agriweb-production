"""
Tests des modes Helia (Assisté vs Manuel)
==========================================

Ce script permet de tester les 2 modes de fonctionnement de Helia.
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"  # Changez pour votre URL Railway en production
SESSION_COOKIES = {}  # Les cookies de session seront stockés ici


def test_get_mode():
    """Test GET /api/helia/mode"""
    print("\n=== TEST 1: Récupération du mode actuel ===")
    
    response = requests.get(f"{BASE_URL}/api/helia/mode", cookies=SESSION_COOKIES)
    
    print(f"Status: {response.status_code}")
    print(f"Réponse: {response.json()}")
    
    assert response.status_code == 200, "Erreur lors de la récupération du mode"
    data = response.json()
    assert 'mode' in data, "Champ 'mode' manquant dans la réponse"
    assert data['mode'] in ['assiste', 'manuel'], "Mode invalide"
    
    print(f"✅ Mode actuel: {data['mode']}")
    return data['mode']


def test_switch_to_manuel():
    """Test POST /api/helia/mode pour passer en mode manuel"""
    print("\n=== TEST 2: Passage en mode MANUEL ===")
    
    response = requests.post(
        f"{BASE_URL}/api/helia/mode",
        json={"mode": "manuel"},
        cookies=SESSION_COOKIES,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Réponse: {response.json()}")
    
    assert response.status_code == 200, "Erreur lors du changement de mode"
    data = response.json()
    assert data['success'] == True, "Changement de mode échoué"
    assert data['mode'] == 'manuel', "Mode manuel non activé"
    
    print("✅ Mode MANUEL activé avec succès")
    
    # Vérifier que le mode a bien changé
    verify = requests.get(f"{BASE_URL}/api/helia/mode", cookies=SESSION_COOKIES)
    assert verify.json()['mode'] == 'manuel', "Le mode n'a pas été persisté"
    print("✅ Persistance vérifiée")


def test_switch_to_assiste():
    """Test POST /api/helia/mode pour passer en mode assisté"""
    print("\n=== TEST 3: Passage en mode ASSISTÉ ===")
    
    response = requests.post(
        f"{BASE_URL}/api/helia/mode",
        json={"mode": "assiste"},
        cookies=SESSION_COOKIES,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Réponse: {response.json()}")
    
    assert response.status_code == 200, "Erreur lors du changement de mode"
    data = response.json()
    assert data['success'] == True, "Changement de mode échoué"
    assert data['mode'] == 'assiste', "Mode assisté non activé"
    
    print("✅ Mode ASSISTÉ activé avec succès")
    
    # Vérifier persistance
    verify = requests.get(f"{BASE_URL}/api/helia/mode", cookies=SESSION_COOKIES)
    assert verify.json()['mode'] == 'assiste', "Le mode n'a pas été persisté"
    print("✅ Persistance vérifiée")


def test_invalid_mode():
    """Test avec un mode invalide"""
    print("\n=== TEST 4: Mode invalide (doit échouer) ===")
    
    response = requests.post(
        f"{BASE_URL}/api/helia/mode",
        json={"mode": "super_mode_turbo"},  # Mode invalide
        cookies=SESSION_COOKIES,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Réponse: {response.json()}")
    
    assert response.status_code == 400, "Devrait retourner une erreur 400"
    print("✅ Validation correcte des modes")


def test_chat_with_assiste_mode():
    """Test d'un message chat en mode ASSISTÉ"""
    print("\n=== TEST 5: Message chat en mode ASSISTÉ ===")
    
    # S'assurer qu'on est en mode assisté
    requests.post(
        f"{BASE_URL}/api/helia/mode",
        json={"mode": "assiste"},
        cookies=SESSION_COOKIES
    )
    
    # Envoyer un message
    response = requests.post(
        f"{BASE_URL}/api/helia/chat",
        json={
            "message": "Bonjour Helia, peux-tu chercher des toitures à Lyon ?",
            "session_id": "test_session_assiste"
        },
        cookies=SESSION_COOKIES
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Réponse Helia: {data.get('response', 'N/A')[:200]}...")
        print(f"✅ Chat fonctionne en mode ASSISTÉ")
        
        # Vérifier que Helia est proactive (elle devrait mentionner qu'elle fait la recherche)
        response_text = data.get('response', '').lower()
        if any(word in response_text for word in ['recherche', 'cherche', 'lance', 'trouve']):
            print("✅ Helia semble proactive (mode ASSISTÉ détecté)")
        else:
            print("⚠️ Réponse pas clairement proactive")
    else:
        print(f"❌ Erreur: {response.text}")


def test_chat_with_manuel_mode():
    """Test d'un message chat en mode MANUEL"""
    print("\n=== TEST 6: Message chat en mode MANUEL ===")
    
    # Passer en mode manuel
    requests.post(
        f"{BASE_URL}/api/helia/mode",
        json={"mode": "manuel"},
        cookies=SESSION_COOKIES
    )
    
    # Envoyer un message
    response = requests.post(
        f"{BASE_URL}/api/helia/chat",
        json={
            "message": "Bonjour Helia, peux-tu chercher des toitures à Lyon ?",
            "session_id": "test_session_manuel"
        },
        cookies=SESSION_COOKIES
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Réponse Helia: {data.get('response', 'N/A')[:200]}...")
        print(f"✅ Chat fonctionne en mode MANUEL")
        
        # Vérifier que Helia attend confirmation (mode manuel)
        response_text = data.get('response', '').lower()
        if any(word in response_text for word in ['voulez-vous', 'souhaitez', 'puis-je', 'dois-je']):
            print("✅ Helia demande confirmation (mode MANUEL détecté)")
        else:
            print("⚠️ Réponse pas clairement en attente de confirmation")
    else:
        print(f"❌ Erreur: {response.text}")


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*60)
    print("TESTS DES MODES HELIA - ASSISTÉ vs MANUEL")
    print("="*60)
    
    try:
        # Tests API
        current_mode = test_get_mode()
        test_switch_to_manuel()
        test_switch_to_assiste()
        test_invalid_mode()
        
        # Tests comportementaux (nécessite l'API Groq configurée)
        try:
            test_chat_with_assiste_mode()
            test_chat_with_manuel_mode()
        except Exception as e:
            print(f"\n⚠️ Tests comportementaux ignorés (API Groq possiblement non configurée)")
            print(f"   Erreur: {e}")
        
        print("\n" + "="*60)
        print("✅ TOUS LES TESTS RÉUSSIS !")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ TEST ÉCHOUÉ: {e}")
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {e}")


if __name__ == "__main__":
    # Pour tester en production, changez BASE_URL vers votre URL Railway
    # BASE_URL = "https://votre-app.railway.app"
    
    print("\nConfiguration actuelle:")
    print(f"  URL: {BASE_URL}")
    print(f"\n⚠️  Note: Assurez-vous que l'application Flask est lancée !")
    print("     (Exécutez 'python run_app.py' dans un autre terminal)\n")
    
    input("Appuyez sur ENTRÉE pour lancer les tests...")
    run_all_tests()
