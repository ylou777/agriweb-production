#!/usr/bin/env python3
"""
🔍 DIAGNOSTIC SIMPLE GEOSERVER
LECTURE SEULE - AUCUNE MODIFICATION
"""

print("🛡️ DIAGNOSTIC SÉCURISÉ DE VOTRE GEOSERVER")
print("=" * 50)
print("⚠️ MODE LECTURE SEULE - Aucune modification")

try:
    import requests
    print("✅ Module requests disponible")
    
    # Test simple de votre GeoServer
    test_urls = [
        "http://localhost:8080",
        "http://localhost:8080/geoserver", 
        "http://localhost:8081/geoserver"
    ]
    
    print("\n🔍 Test de votre GeoServer...")
    
    for url in test_urls:
        try:
            print(f"\n🧭 Test: {url}")
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                content = response.text.lower()
                if "geoserver" in content:
                    print(f"   ✅ GeoServer trouvé !")
                    print(f"   📍 URL opérationnelle: {url}")
                    
                    # Test rapide WFS
                    try:
                        wfs_url = f"{url}/ows" if "/geoserver" in url else f"{url}/geoserver/ows"
                        wfs_params = {
                            "service": "WFS",
                            "request": "GetCapabilities"
                        }
                        wfs_response = requests.get(wfs_url, params=wfs_params, timeout=5)
                        
                        if "WFS_Capabilities" in wfs_response.text:
                            print(f"   ✅ Service WFS opérationnel")
                            
                            # Compter les couches
                            import re
                            layers = re.findall(r'<Name>([^<]+)</Name>', wfs_response.text)
                            print(f"   📊 {len(layers)} couches détectées")
                            
                            if len(layers) > 0:
                                print(f"   📋 Exemples de couches:")
                                for layer in layers[:5]:  # 5 premières seulement
                                    print(f"      - {layer}")
                                if len(layers) > 5:
                                    print(f"      ... et {len(layers)-5} autres")
                            
                        else:
                            print(f"   ⚠️ Service WFS: problème de configuration")
                            
                    except Exception as e:
                        print(f"   ⚠️ Test WFS: {str(e)[:40]}...")
                        
                elif "tomcat" in content:
                    print(f"   ℹ️ Tomcat trouvé (GeoServer peut être sur /geoserver)")
                else:
                    print(f"   ❌ Pas GeoServer (code {response.status_code})")
            else:
                print(f"   ❌ Erreur HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connexion impossible")
        except Exception as e:
            print(f"   ❌ Erreur: {str(e)[:40]}...")
    
    print(f"\n🎯 RÉSULTAT:")
    print(f"Si un GeoServer a été trouvé ci-dessus,")
    print(f"nous pouvons maintenant l'intégrer à AgriWeb 2.0")
    print(f"en toute sécurité (mode lecture seule)")
    
except ImportError:
    print("❌ Module requests non installé")
    print("Installation en cours...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    print("✅ Requests installé, relancer le script")
    
except Exception as e:
    print(f"❌ Erreur: {e}")

print(f"\n📖 Guide complet: GUIDE_GEOSERVER_CONFIGURATION.md")
