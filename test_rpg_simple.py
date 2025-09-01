#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test RPG direct - Version simplifiée avec timeout plus long
"""

import requests
import json
from datetime import datetime

def test_rpg_simple():
    print(f"🧪 Test RPG Simple - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Test 1: Vérifier que le serveur répond
    try:
        print("🏥 [TEST_PING] Vérification serveur...")
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Serveur actif")
        else:
            print(f"⚠️ Serveur répond avec code {response.status_code}")
    except Exception as e:
        print(f"❌ Serveur inaccessible: {e}")
        return
    
    # Test 2: Test avec SSE (plus rapide)
    print("\n🌊 [TEST_SSE] Test avec Server-Sent Events")
    print("-" * 40)
    
    try:
        # Utiliser l'endpoint SSE qui est plus rapide
        url = "http://localhost:5000/commune_search_sse"
        params = {
            'commune': 'guéret',
            'filter_rpg': 'true', 
            'rpg_min_area': '5',
            'rpg_max_area': '50',
            'filter_parkings': 'false',
            'filter_friches': 'false',
            'filter_zones': 'false',
            'filter_toitures': 'false'
        }
        
        print(f"📡 Connexion SSE vers: {url}")
        print(f"📋 Paramètres: {params}")
        
        # Connexion SSE avec timeout plus long
        response = requests.get(url, params=params, stream=True, timeout=120)
        
        if response.status_code == 200:
            print("✅ Connexion SSE établie")
            print("📊 Lecture des événements (30 premiers)...")
            
            event_count = 0
            rpg_found = False
            
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    print(f"📨 {line[:100]}{'...' if len(line) > 100 else ''}")
                    
                    # Rechercher des mentions de RPG
                    if 'rpg' in line.lower() or 'parcelle' in line.lower():
                        rpg_found = True
                        print(f"🌾 RPG détecté: {line}")
                    
                    event_count += 1
                    if event_count >= 30:  # Limiter pour éviter un spam
                        print("📋 [LIMIT] Arrêt après 30 événements...")
                        break
            
            if rpg_found:
                print("✅ Données RPG détectées dans le flux SSE")
            else:
                print("⚠️ Aucune donnée RPG détectée")
                
        else:
            print(f"❌ Erreur SSE: {response.status_code}")
            print(f"📝 Réponse: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout SSE - La requête a pris trop de temps")
    except Exception as e:
        print(f"❌ Erreur SSE: {e}")
    
    # Test 3: Test simple avec paramètres minimaux
    print("\n🎯 [TEST_MINIMAL] Test avec paramètres minimaux")
    print("-" * 40)
    
    try:
        url = "http://localhost:5000/search_by_commune"
        params = {
            'commune': 'guéret',
            'filter_rpg': 'true'
        }
        
        print(f"📡 Requête GET vers: {url}")
        print(f"📋 Paramètres: {params}")
        
        response = requests.get(url, params=params, timeout=60)
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ Réponse JSON reçue")
                
                # Analyser la réponse
                if 'rpg' in data:
                    rpg_count = len(data['rpg']) if isinstance(data['rpg'], list) else 0
                    print(f"🌾 Parcelles RPG trouvées: {rpg_count}")
                    
                    if rpg_count > 0:
                        print("✅ TEST RÉUSSI - Les données RPG remontent correctement!")
                        
                        # Afficher quelques exemples
                        for i, parcelle in enumerate(data['rpg'][:3]):
                            if isinstance(parcelle, dict):
                                surface = parcelle.get('properties', {}).get('SURF_PARC', 'N/A')
                                culture = parcelle.get('properties', {}).get('Culture', 'N/A')
                                print(f"  📄 Parcelle {i+1}: {surface}ha - {culture}")
                    else:
                        print("⚠️ Aucune parcelle RPG trouvée")
                else:
                    print("❌ Clé 'rpg' non trouvée dans la réponse")
                    print(f"🔍 Clés disponibles: {list(data.keys())}")
                    
            except json.JSONDecodeError:
                print("❌ Réponse non-JSON")
                print(f"📝 Début de réponse: {response.text[:200]}")
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            print(f"📝 Réponse: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout - La requête a pris trop de temps")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print(f"\n🏁 Test terminé - {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    test_rpg_simple()
