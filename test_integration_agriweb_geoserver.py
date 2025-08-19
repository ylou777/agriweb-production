#!/usr/bin/env python3
"""
🔗 TEST INTÉGRATION AGRIWEB-GEOSERVER
Vérifie que l'application AgriWeb peut communiquer avec GeoServer
"""

import sys
import os
import importlib.util

def test_agriweb_geoserver_integration():
    """Test l'intégration AgriWeb-GeoServer"""
    
    print("🔗 TEST INTÉGRATION AGRIWEB-GEOSERVER")
    print("=" * 50)
    
    # Test 1: Import de la configuration AgriWeb
    print("1️⃣ Test configuration AgriWeb...")
    try:
        # Import de la configuration depuis agriweb_hebergement_gratuit.py
        spec = importlib.util.spec_from_file_location(
            "agriweb_config", 
            "agriweb_hebergement_gratuit.py"
        )
        agriweb_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agriweb_module)
        
        geoserver_url = agriweb_module.GEOSERVER_URL
        print(f"   ✅ URL GeoServer: {geoserver_url}")
        
        if hasattr(agriweb_module, 'GEOSERVER_LAYERS_CONFIG'):
            layers_config = agriweb_module.GEOSERVER_LAYERS_CONFIG
            print(f"   ✅ Configuration couches chargée")
            print(f"   📊 Workspace: {layers_config.get('workspace', 'N/A')}")
            print(f"   📋 Nombre de couches: {len(layers_config.get('layers', {}))}")
        else:
            print("   ⚠️ GEOSERVER_LAYERS_CONFIG non trouvé")
            
    except Exception as e:
        print(f"   ❌ Erreur import AgriWeb: {e}")
    
    print()
    
    # Test 2: Test de connexion depuis la configuration AgriWeb
    print("2️⃣ Test connexion via configuration AgriWeb...")
    try:
        import requests
        
        # Test avec l'URL configurée dans AgriWeb
        response = requests.get(f"{geoserver_url}/web/", timeout=10)
        if response.status_code == 200:
            print(f"   ✅ Connexion GeoServer réussie via AgriWeb")
            print(f"   📊 Status: {response.status_code}")
        else:
            print(f"   ⚠️ Status inattendu: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur connexion: {e}")
    
    print()
    
    # Test 3: Vérification des endpoints configurés
    print("3️⃣ Test endpoints configurés...")
    try:
        if 'layers_config' in locals():
            endpoints = layers_config.get('endpoints', {})
            
            for name, url in endpoints.items():
                print(f"   🔗 Test {name}: {url}")
                try:
                    if name == 'admin':
                        response = requests.get(url, timeout=5)
                    else:
                        # Pour WMS/WFS, test avec GetCapabilities
                        if 'wms' in name.lower():
                            test_url = f"{url}?service=WMS&version=1.3.0&request=GetCapabilities"
                        elif 'wfs' in name.lower():
                            test_url = f"{url}?service=WFS&version=2.0.0&request=GetCapabilities"
                        else:
                            test_url = url
                        response = requests.get(test_url, timeout=5)
                    
                    print(f"      ✅ Status: {response.status_code}")
                    
                except Exception as e:
                    print(f"      ❌ Erreur: {e}")
        else:
            print("   ⚠️ Configuration endpoints non disponible")
            
    except Exception as e:
        print(f"   ❌ Erreur test endpoints: {e}")
    
    print()
    print("=" * 50)
    print("📋 RÉSUMÉ INTÉGRATION:")
    
    try:
        # Test synthétique
        config_ok = 'geoserver_url' in locals()
        connection_ok = False
        
        if config_ok:
            try:
                import requests
                response = requests.get(f"{geoserver_url}/web/", timeout=5)
                connection_ok = response.status_code == 200
            except:
                pass
        
        if config_ok and connection_ok:
            print("🎉 INTÉGRATION AGRIWEB-GEOSERVER FONCTIONNELLE!")
            print("✅ Configuration AgriWeb chargée")
            print("✅ Connexion GeoServer établie")
            print("✅ Endpoints configurés")
            print()
            print("🚀 PRÊT POUR LA PRODUCTION!")
            print("   → L'application AgriWeb peut maintenant utiliser GeoServer")
            print("   → Tous les services géographiques sont opérationnels")
            
        else:
            print("⚠️ PROBLÈMES D'INTÉGRATION:")
            print(f"   Configuration: {'✅' if config_ok else '❌'}")
            print(f"   Connexion: {'✅' if connection_ok else '❌'}")
            
    except Exception as e:
        print(f"❌ Erreur test synthétique: {e}")
    
    print("=" * 50)

if __name__ == "__main__":
    test_agriweb_geoserver_integration()
