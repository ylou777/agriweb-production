#!/usr/bin/env python3
"""
🌐 SCRIPT COMPLET - CONNEXION GEOSERVER LOCAL VIA TUNNEL
Automatise la connexion de votre GeoServer local à AgriWeb en ligne
"""

import subprocess
import time
import requests
import json
import os
from datetime import datetime

class NgrokGeoServerManager:
    def __init__(self):
        self.ngrok_path = self.find_ngrok()
        self.geoserver_local = "http://localhost:8080/geoserver"
        self.tunnel_url = None
        self.process = None
    
    def find_ngrok(self):
        """Trouve l'exécutable ngrok"""
        possible_paths = [
            "C:\\ngrok\\ngrok.exe",
            "ngrok.exe",
            "ngrok",
            os.path.expanduser("~\\AppData\\Local\\ngrok\\ngrok.exe")
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, "version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print(f"✅ ngrok trouvé: {path}")
                    return path
            except:
                continue
        
        print("❌ ngrok non trouvé. Assurez-vous qu'il est installé et accessible.")
        return None
    
    def check_geoserver_local(self):
        """Vérifie si GeoServer local est accessible"""
        try:
            response = requests.get(f"{self.geoserver_local}/web/", timeout=5)
            if response.status_code == 200:
                print("✅ GeoServer local accessible")
                return True
            else:
                print(f"⚠️ GeoServer local répond avec code: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ GeoServer local non accessible: {e}")
            print("💡 Assurez-vous que GeoServer est démarré sur le port 8080")
            return False
    
    def start_tunnel(self):
        """Démarre le tunnel ngrok"""
        if not self.ngrok_path:
            print("❌ Impossible de démarrer le tunnel: ngrok non trouvé")
            return False
        
        if not self.check_geoserver_local():
            print("❌ Impossible de démarrer le tunnel: GeoServer local non accessible")
            return False
        
        try:
            print("🚀 Démarrage du tunnel ngrok...")
            # Arrêter d'éventuels tunnels existants
            self.stop_tunnel()
            
            # Démarrer le nouveau tunnel
            self.process = subprocess.Popen(
                [self.ngrok_path, "http", "8080"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            print("⏳ Attente du démarrage du tunnel...")
            time.sleep(3)  # Laisser le temps au tunnel de démarrer
            
            # Récupérer l'URL du tunnel
            tunnel_url = self.get_tunnel_url()
            if tunnel_url:
                self.tunnel_url = tunnel_url
                print(f"✅ Tunnel démarré: {tunnel_url}")
                return True
            else:
                print("❌ Échec du démarrage du tunnel")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors du démarrage du tunnel: {e}")
            return False
    
    def get_tunnel_url(self):
        """Récupère l'URL du tunnel ngrok"""
        try:
            response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
            if response.status_code == 200:
                tunnels = response.json()
                for tunnel in tunnels.get('tunnels', []):
                    if tunnel.get('proto') == 'https':
                        return tunnel.get('public_url')
            return None
        except:
            return None
    
    def test_tunnel_access(self):
        """Test l'accès au GeoServer via tunnel"""
        if not self.tunnel_url:
            return False
        
        try:
            geoserver_url = f"{self.tunnel_url}/geoserver"
            response = requests.get(f"{geoserver_url}/web/", timeout=10)
            if response.status_code == 200:
                print(f"✅ GeoServer accessible via tunnel: {geoserver_url}")
                return geoserver_url
            else:
                print(f"⚠️ Tunnel répond mais GeoServer non accessible")
                return False
        except Exception as e:
            print(f"❌ Erreur d'accès via tunnel: {e}")
            return False
    
    def generate_agriweb_config(self, geoserver_tunnel_url):
        """Génère la configuration pour AgriWeb"""
        config = f"""
# 🌐 CONFIGURATION TUNNEL GEOSERVER LOCAL
# Généré le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Variable d'environnement pour AgriWeb
export GEOSERVER_TUNNEL_URL="{geoserver_tunnel_url}"

# Pour Railway/Render/Heroku, ajoutez cette variable:
# GEOSERVER_TUNNEL_URL={geoserver_tunnel_url}

# PowerShell (pour tests locaux):
$env:GEOSERVER_TUNNEL_URL = "{geoserver_tunnel_url}"

# Test de la configuration:
# curl "{geoserver_tunnel_url}/web/"
        """
        
        with open("tunnel_config.env", "w") as f:
            f.write(config)
        
        print("📝 Configuration sauvée dans: tunnel_config.env")
        print(f"🌐 URL GeoServer tunnel: {geoserver_tunnel_url}")
        
        return config
    
    def stop_tunnel(self):
        """Arrête le tunnel ngrok"""
        try:
            # Arrêter le processus si il existe
            if self.process:
                self.process.terminate()
                self.process = None
            
            # Arrêter via API ngrok
            tunnels = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2).json()
            for tunnel in tunnels.get('tunnels', []):
                tunnel_name = tunnel.get('name')
                requests.delete(f"http://127.0.0.1:4040/api/tunnels/{tunnel_name}", timeout=2)
            
            print("✅ Tunnel arrêté")
            return True
        except:
            print("⚠️ Tunnel probablement déjà arrêté")
            return True
    
    def run_complete_setup(self):
        """Exécute la configuration complète"""
        print("🌐 CONFIGURATION COMPLÈTE TUNNEL GEOSERVER")
        print("=" * 50)
        
        # 1. Vérifications préliminaires
        print("\n1. Vérifications préliminaires...")
        if not self.ngrok_path:
            print("❌ ngrok non trouvé")
            return False
        
        if not self.check_geoserver_local():
            print("❌ GeoServer local non accessible")
            return False
        
        # 2. Démarrage du tunnel
        print("\n2. Démarrage du tunnel...")
        if not self.start_tunnel():
            print("❌ Échec du démarrage du tunnel")
            return False
        
        # 3. Test d'accès
        print("\n3. Test d'accès via tunnel...")
        geoserver_tunnel_url = self.test_tunnel_access()
        if not geoserver_tunnel_url:
            print("❌ Accès via tunnel échoué")
            return False
        
        # 4. Génération de la configuration
        print("\n4. Génération de la configuration...")
        self.generate_agriweb_config(geoserver_tunnel_url)
        
        # 5. Instructions finales
        print("\n5. Instructions finales:")
        print("✅ Configuration terminée avec succès !")
        print(f"🌐 Votre GeoServer est accessible via: {geoserver_tunnel_url}")
        print("\n📋 Prochaines étapes:")
        print("1. Ajoutez cette variable dans votre plateforme d'hébergement:")
        print(f"   GEOSERVER_TUNNEL_URL={geoserver_tunnel_url}")
        print("2. Redéployez AgriWeb")
        print("3. AgriWeb utilisera automatiquement votre GeoServer local !")
        print("\n⚠️ IMPORTANT: Gardez ce terminal ouvert pour maintenir le tunnel actif")
        
        return True

def main():
    """Fonction principale"""
    manager = NgrokGeoServerManager()
    
    print("🎯 MENU TUNNEL GEOSERVER")
    print("1. 🚀 Configuration complète automatique")
    print("2. 🔍 Vérifier GeoServer local seulement")
    print("3. 🌐 Démarrer tunnel seulement")
    print("4. 🛑 Arrêter tunnel")
    
    try:
        choice = input("\nVotre choix (1-4): ").strip()
        
        if choice == "1":
            manager.run_complete_setup()
            # Maintenir le tunnel actif
            try:
                print("\n🔄 Tunnel actif. Appuyez sur Ctrl+C pour arrêter.")
                while True:
                    time.sleep(30)
                    # Vérifier que le tunnel est toujours actif
                    if not manager.get_tunnel_url():
                        print("⚠️ Tunnel déconnecté, tentative de redémarrage...")
                        manager.start_tunnel()
            except KeyboardInterrupt:
                print("\n🛑 Arrêt du tunnel...")
                manager.stop_tunnel()
        
        elif choice == "2":
            manager.check_geoserver_local()
        
        elif choice == "3":
            manager.start_tunnel()
        
        elif choice == "4":
            manager.stop_tunnel()
        
        else:
            print("Choix invalide")
    
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé...")
        manager.stop_tunnel()

if __name__ == "__main__":
    main()
