#!/usr/bin/env python3
"""
Script pour tester différentes configurations ngrok avec GeoServer
"""

import subprocess
import time
import requests
import sys

def test_ngrok_config(options, port=8080):
    """Teste une configuration ngrok spécifique"""
    print(f"\n🧪 Test configuration: ngrok http {options} {port}")
    
    # Arrêter ngrok existant
    try:
        subprocess.run(["taskkill", "/F", "/IM", "ngrok.exe"], 
                      capture_output=True, shell=True)
        time.sleep(2)
    except:
        pass
    
    # Démarrer ngrok avec les options
    cmd = f"ngrok http {options} {port}"
    print(f"   Commande: {cmd}")
    
    # Lancer en arrière-plan et attendre quelques secondes
    try:
        process = subprocess.Popen(cmd, shell=True)
        time.sleep(5)
        
        # Tester l'API ngrok
        try:
            response = requests.get("http://localhost:4040/api/tunnels", timeout=3)
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get('tunnels', [])
                if tunnels:
                    public_url = tunnels[0].get('public_url')
                    print(f"   ✅ URL obtenue: {public_url}")
                    
                    # Tester l'accès GeoServer
                    test_url = f"{public_url}/geoserver/"
                    try:
                        test_response = requests.head(
                            test_url, 
                            timeout=10,
                            headers={'ngrok-skip-browser-warning': 'any'}
                        )
                        print(f"   Status: {test_response.status_code}")
                        
                        if 'Ngrok-Error-Code' in test_response.headers:
                            print(f"   ❌ Erreur: {test_response.headers['Ngrok-Error-Code']}")
                            return False
                        else:
                            print(f"   ✅ Connexion réussie!")
                            return True
                            
                    except Exception as e:
                        print(f"   ❌ Erreur test: {e}")
                        return False
                        
        except Exception as e:
            print(f"   ❌ Erreur API ngrok: {e}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur lancement: {e}")
        return False
    
    return False

def main():
    """Teste différentes configurations ngrok"""
    
    print("🔧 Test automatique des configurations ngrok pour GeoServer")
    print("=" * 60)
    
    # Vérifier que GeoServer fonctionne localement
    try:
        response = requests.head("http://localhost:8080/geoserver/", timeout=5)
        print(f"✅ GeoServer local: {response.status_code}")
    except Exception as e:
        print(f"❌ GeoServer local non accessible: {e}")
        return
    
    # Configurations à tester
    configs = [
        "--host-header=localhost",
        "--host-header=rewrite", 
        "--host-header=127.0.0.1",
        "http://localhost:8080",
        "8080",
        "--region=eu",
        "--region=eu --host-header=localhost"
    ]
    
    for config in configs:
        success = test_ngrok_config(config)
        if success:
            print(f"\n🎉 Configuration réussie: {config}")
            input("Appuyez sur Entrée pour continuer les tests ou Ctrl+C pour arrêter...")
        else:
            time.sleep(2)
    
    print("\n📋 Tests terminés")

if __name__ == "__main__":
    main()
