#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de connectivité ngrok et GeoServer
"""
import requests
import time
import json

GEOSERVER_BASE = "https://3de153b73a2d.ngrok-free.app/geoserver"

def test_ngrok_connectivity():
    """Test la connectivité de base avec ngrok"""
    print("🔍 Test de connectivité ngrok...")
    
    try:
        # Test simple de la racine ngrok
        response = requests.get("https://3de153b73a2d.ngrok-free.app", timeout=30)
        print(f"✅ Ngrok racine: Status {response.status_code}")
        if response.status_code == 200:
            print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"   Content-Length: {len(response.content)} bytes")
        return True
    except Exception as e:
        print(f"❌ Erreur ngrok racine: {e}")
        return False

def test_geoserver_web_interface():
    """Test l'interface web GeoServer"""
    print("\n🌐 Test interface web GeoServer...")
    
    try:
        response = requests.get(f"{GEOSERVER_BASE}/web", timeout=30)
        print(f"✅ GeoServer web: Status {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erreur GeoServer web: {e}")
        return False

def test_geoserver_capabilities():
    """Test les capabilities WFS"""
    print("\n📋 Test capabilities WFS...")
    
    try:
        capabilities_url = f"{GEOSERVER_BASE}/ows?service=WFS&version=2.0.0&request=GetCapabilities"
        response = requests.get(capabilities_url, timeout=30)
        print(f"✅ WFS Capabilities: Status {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            if "gpu:" in content:
                print("✅ Workspace 'gpu' trouvé dans les capabilities")
                # Compter les couches
                layer_count = content.count("gpu:")
                print(f"✅ {layer_count} références à 'gpu:' trouvées")
            else:
                print("⚠️ Workspace 'gpu' non trouvé")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erreur capabilities: {e}")
        return False

def test_specific_layers():
    """Test des couches spécifiques problématiques"""
    print("\n🔍 Test couches spécifiques...")
    
    layers_to_test = [
        "gpu:poste_elec_shapefile",
        "gpu:postes-electriques-rte", 
        "gpu:CapacitesDAccueil",
        "gpu:PARCELLE2024",
        "gpu:gpu1"
    ]
    
    bbox = "6.1354087,48.600019200000006,6.1554087,48.6200192,EPSG:4326"
    
    for layer in layers_to_test:
        try:
            url = f"{GEOSERVER_BASE}/ows?service=WFS&version=2.0.0&request=GetFeature&typeName={layer}&outputFormat=application/json&bbox={bbox}&srsname=EPSG:4326&maxFeatures=1"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ {layer}: OK (Status 200)")
                try:
                    data = response.json()
                    feature_count = len(data.get('features', []))
                    print(f"   📊 {feature_count} features trouvées")
                except:
                    print(f"   📊 Réponse non-JSON reçue")
            else:
                print(f"❌ {layer}: Status {response.status_code}")
                
        except Exception as e:
            print(f"❌ {layer}: Erreur {e}")

def test_geoserver_rest_api():
    """Test de l'API REST GeoServer"""
    print("\n🔧 Test API REST GeoServer...")
    
    try:
        rest_url = f"{GEOSERVER_BASE}/rest/workspaces/gpu"
        response = requests.get(rest_url, timeout=30)
        print(f"✅ REST workspace gpu: Status {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Workspace 'gpu' accessible via REST")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erreur REST API: {e}")
        return False

def main():
    """Test complet de connectivité"""
    print("🚀 === TEST COMPLET CONNECTIVITÉ GEOSERVER ===")
    print(f"🔗 URL de base: {GEOSERVER_BASE}")
    print(f"⏰ Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    # Tests séquentiels
    results = {
        "ngrok": test_ngrok_connectivity(),
        "geoserver_web": test_geoserver_web_interface(),
        "wfs_capabilities": test_geoserver_capabilities(),
        "rest_api": test_geoserver_rest_api()
    }
    
    # Test des couches
    test_specific_layers()
    
    # Résumé final
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS:")
    for test_name, result in results.items():
        status = "✅ OK" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    total_ok = sum(results.values())
    print(f"\n🎯 Score: {total_ok}/{len(results)} tests réussis")
    
    if total_ok == 0:
        print("\n🚨 DIAGNOSTIC: Le tunnel ngrok semble complètement hors service")
        print("💡 SOLUTION: Redémarrer ngrok et GeoServer")
    elif total_ok < len(results):
        print("\n⚠️ DIAGNOSTIC: Connectivité partielle - problème GeoServer")
        print("💡 SOLUTION: Redémarrer GeoServer ou vérifier la configuration")
    else:
        print("\n✅ DIAGNOSTIC: Connectivité OK - problème potentiel ailleurs")

if __name__ == "__main__":
    main()
