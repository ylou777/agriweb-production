#!/usr/bin/env python3
"""
Health check avancé pour GeoServer Railway
"""
import requests
import json
import time
from datetime import datetime

def test_geoserver_health():
    base_url = "https://geoserver-agriweb-production.up.railway.app"
    
    print("🏥 Health Check GeoServer Railway")
    print("=" * 50)
    
    # Tests à effectuer
    tests = [
        {"name": "Page principale", "url": f"{base_url}", "timeout": 30},
        {"name": "GeoServer root", "url": f"{base_url}/geoserver", "timeout": 30},
        {"name": "Interface web", "url": f"{base_url}/geoserver/web", "timeout": 20},
        {"name": "API REST", "url": f"{base_url}/geoserver/rest", "timeout": 15},
        {"name": "Version info", "url": f"{base_url}/geoserver/rest/about/version", "timeout": 15},
    ]
    
    results = []
    
    for test in tests:
        print(f"\n🔍 Test: {test['name']}")
        print(f"   URL: {test['url']}")
        
        try:
            start_time = time.time()
            response = requests.get(
                test['url'], 
                timeout=test['timeout'],
                allow_redirects=True
            )
            elapsed = round(time.time() - start_time, 2)
            
            status = {
                "name": test['name'],
                "url": test['url'],
                "status_code": response.status_code,
                "response_time": elapsed,
                "success": 200 <= response.status_code < 400,
                "content_length": len(response.content),
                "content_type": response.headers.get('content-type', 'unknown')
            }
            
            if status['success']:
                print(f"   ✅ Status: {response.status_code} ({elapsed}s)")
                print(f"   📊 Taille: {len(response.content)} bytes")
                print(f"   📄 Type: {status['content_type']}")
            else:
                print(f"   ❌ Status: {response.status_code} ({elapsed}s)")
                
        except requests.exceptions.Timeout:
            status = {
                "name": test['name'],
                "url": test['url'],
                "error": "Timeout",
                "success": False
            }
            print(f"   ⏰ Timeout après {test['timeout']}s")
            
        except requests.exceptions.ConnectionError as e:
            status = {
                "name": test['name'],
                "url": test['url'],
                "error": f"Connection error: {str(e)[:100]}",
                "success": False
            }
            print(f"   🔌 Erreur connexion: {str(e)[:100]}")
            
        except Exception as e:
            status = {
                "name": test['name'],
                "url": test['url'],
                "error": str(e)[:100],
                "success": False
            }
            print(f"   ❌ Erreur: {str(e)[:100]}")
        
        results.append(status)
        time.sleep(1)  # Pause entre tests
    
    # Résumé
    print(f"\n📋 RÉSUMÉ ({datetime.now().strftime('%H:%M:%S')})")
    print("=" * 50)
    
    success_count = sum(1 for r in results if r.get('success', False))
    total_tests = len(results)
    
    for result in results:
        if result.get('success'):
            print(f"✅ {result['name']}: OK ({result.get('status_code', 'N/A')})")
        else:
            error = result.get('error', 'Erreur inconnue')
            print(f"❌ {result['name']}: {error}")
    
    print(f"\n🎯 Score: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 Tous les tests réussis - GeoServer opérationnel!")
        return True
    elif success_count > 0:
        print("⚠️  Démarrage partiel - GeoServer en cours d'initialisation")
        return False
    else:
        print("❌ Aucun test réussi - Problème de déploiement")
        return False

if __name__ == "__main__":
    success = test_geoserver_health()
    exit(0 if success else 1)
