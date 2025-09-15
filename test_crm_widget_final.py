#!/usr/bin/env python3
"""
Test final de l'intégration CRM Widget
Teste que le widget CRM s'affiche après une recherche par commune
"""

import requests
import json
import time

def test_crm_widget_integration():
    """Test complet de l'intégration du widget CRM"""
    
    print("🧪 === TEST FINAL INTÉGRATION CRM WIDGET ===")
    print()
    
    base_url = "http://localhost:5000"
    
    # 1️⃣ Test de disponibilité de l'application
    print("1️⃣ Vérification de l'application...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Application disponible")
        else:
            print(f"❌ Application non disponible (status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Erreur connexion application: {e}")
        return False
    
    # 2️⃣ Test des routes CRM
    print("\n2️⃣ Vérification des routes CRM...")
    try:
        # Test dashboard CRM
        response = requests.get(f"{base_url}/crm/dashboard", timeout=5)
        print(f"   📊 Dashboard CRM: {response.status_code}")
        
        # Test API CRM
        response = requests.get(f"{base_url}/api/crm/dashboard", timeout=5)
        print(f"   🔗 API CRM Dashboard: {response.status_code}")
        
    except Exception as e:
        print(f"⚠️ Erreur routes CRM: {e}")
    
    # 3️⃣ Test de recherche par commune avec données CRM
    print("\n3️⃣ Test recherche commune avec intégration CRM...")
    
    # Paramètres de test pour une commune avec des entreprises
    test_params = {
        'commune': 'Lyon',  # Grande ville avec beaucoup d'entreprises SIRENE
        'sirene_radius': '0.1',  # Rayon pour avoir des entreprises
        'filter_rpg': 'false',
        'filter_parkings': 'false', 
        'filter_friches': 'false',
        'filter_zones': 'false',
        'filter_toitures': 'false'
    }
    
    try:
        print(f"   🔍 Recherche pour: {test_params['commune']}")
        response = requests.get(f"{base_url}/search_by_commune", params=test_params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Recherche réussie (status: {response.status_code})")
            
            # Vérification des données CRM dans la réponse
            crm_available = data.get('crm_available', False)
            crm_prospects = data.get('crm_prospects_detected', 0)
            crm_analysis = data.get('crm_sirene_analysis', {})
            
            print(f"   📊 CRM disponible: {crm_available}")
            print(f"   🎯 Prospects détectés: {crm_prospects}")
            
            if crm_available:
                print("   ✅ Module CRM actif dans la réponse")
                
                if crm_prospects > 0:
                    print(f"   🎉 {crm_prospects} prospects qualifiés détectés!")
                    print(f"   📈 Analyse SIRENE: {crm_analysis.get('qualified_prospects', 0)}/{crm_analysis.get('total_enterprises', 0)} entreprises qualifiées")
                    
                    # Test de l'intégration CRM
                    print("\n4️⃣ Test de création des prospects CRM...")
                    
                    crm_payload = {
                        'search_results': data,
                        'search_metadata': {
                            'commune': test_params['commune'],
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'test_mode': True
                        }
                    }
                    
                    try:
                        crm_response = requests.post(
                            f"{base_url}/api/crm/integrate_commune_search",
                            json=crm_payload,
                            headers={'Content-Type': 'application/json'},
                            timeout=10
                        )
                        
                        if crm_response.status_code == 200:
                            crm_result = crm_response.json()
                            if crm_result.get('success'):
                                print("   ✅ Intégration CRM réussie!")
                                summary = crm_result.get('summary', {})
                                print(f"   📊 Prospects créés: {summary.get('prospects_created', 0)}")
                            else:
                                print(f"   ⚠️ Intégration CRM échouée: {crm_result.get('error', 'Erreur inconnue')}")
                        else:
                            print(f"   ❌ Erreur API CRM (status: {crm_response.status_code})")
                            
                    except Exception as e:
                        print(f"   ❌ Erreur test intégration CRM: {e}")
                else:
                    print("   ℹ️ Aucun prospect qualifié détecté pour cette commune")
            else:
                print("   ❌ Module CRM non disponible dans la réponse")
                
        else:
            print(f"   ❌ Erreur recherche commune (status: {response.status_code})")
            print(f"   📝 Réponse: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur lors du test de recherche: {e}")
        return False
    
    # 5️⃣ Instructions pour l'utilisateur
    print("\n" + "="*60)
    print("🎯 INSTRUCTIONS POUR VOIR LE WIDGET CRM")
    print("="*60)
    print("1. Ouvrez votre navigateur sur: http://localhost:5000")
    print("2. Dans le panneau de recherche de commune:")
    print("   - Saisissez 'Lyon' (ou une grande ville)")
    print("   - Cochez 'Données SIRENE'")
    print("   - Cliquez sur 'Rechercher commune'")
    print("3. Après les résultats, vous devriez voir:")
    print("   📋 Un widget vert 'CRM Commercial Intelligent'")
    print("   🎯 Le nombre de prospects qualifiés détectés")
    print("   🔘 Des boutons pour créer les prospects")
    print("4. Cliquez sur 'Créer Prospects Qualifiés' pour alimenter le CRM")
    print("5. Visitez /crm/dashboard pour voir les prospects créés")
    print()
    print("✅ Si le widget n'apparaît pas, vérifiez la console navigateur (F12)")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = test_crm_widget_integration()
    if success:
        print("\n🎉 Test terminé - Widget CRM prêt à être testé!")
    else:
        print("\n❌ Test échoué - Vérifiez la configuration")