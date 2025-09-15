#!/usr/bin/env python3
"""
Test qui identifie exactement où la recherche se bloque
"""

import requests
import time
import threading

def test_with_timing():
    print("🕐 TEST AVEC TIMING DÉTAILLÉ")
    print("=" * 40)
    
    def timeout_monitor():
        """Monitor pour alerter en cas de timeout"""
        time.sleep(15)  # Attendre 15 secondes
        print("⏰ ALERTE: Requête dépasse 15 secondes!")
        
    # Démarrer le monitor en arrière-plan
    monitor_thread = threading.Thread(target=timeout_monitor, daemon=True)
    monitor_thread.start()
    
    try:
        start_time = time.time()
        print(f"🚀 Début requête: {start_time}")
        
        # Test simple avec timeout court
        params = {
            'commune': 'Lyon', 
            'sirene_radius': '0.01',  # Radius très petit
            'filter_rpg': 'false',
            'filter_parkings': 'false',
            'filter_friches': 'false',
            'filter_zones': 'false',
            'filter_toitures': 'false'
        }
        
        print("📍 Paramètres:", params)
        print("⏱️ Timeout configuré: 45 secondes")
        
        response = requests.get(
            'http://localhost:5000/search_by_commune', 
            params=params, 
            timeout=45
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ Durée totale: {duration:.2f}s")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCÈS!")
            data = response.json()
            print(f"🎯 CRM: {data.get('crm_available', False)}")
            print(f"📈 Prospects: {data.get('crm_prospects_detected', 0)}")
        elif response.status_code == 500:
            print("❌ ERREUR 500")
            print("Détails:")
            print(response.text[:800])
        else:
            print(f"⚠️ Status: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("⏰ TIMEOUT CONFIRMÉ")
        print("🔍 La requête prend plus de 45 secondes")
        print("💡 Problème probable: boucle infinie ou API lente")
    except requests.exceptions.ConnectionError:
        print("❌ CONNEXION ÉCHOUÉE")
        print("🔧 Serveur non accessible")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == '__main__':
    test_with_timing()