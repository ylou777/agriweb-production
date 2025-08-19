#!/usr/bin/env python3
"""
🌐 CONFIGURATION TUNNEL GEOSERVER LOCAL
Expose votre GeoServer local pour AgriWeb en ligne
"""

import os
import subprocess
import time
import requests
import json
from datetime import datetime

class GeoServerTunnelManager:
    def __init__(self):
        self.local_geoserver = "http://localhost:8080/geoserver"
        self.ngrok_url = None
        self.tunnel_process = None
        
    def check_geoserver_local(self):
        """Vérifie si GeoServer local est accessible"""
        try:
            response = requests.get(f"{self.local_geoserver}/web/", timeout=5)
            if response.status_code == 200:
                print("✅ GeoServer local accessible")
                return True
            else:
                print(f"⚠️ GeoServer local répond avec code: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ GeoServer local non accessible: {e}")
            return False
    
    def install_ngrok(self):
        """Instructions pour installer ngrok"""
        print("""
🔧 INSTALLATION NGROK

1. Téléchargez ngrok depuis: https://ngrok.com/download
2. Décompressez dans un dossier accessible (ex: C:\\ngrok\\)
3. Créez un compte gratuit sur https://ngrok.com/signup
4. Récupérez votre authtoken depuis: https://dashboard.ngrok.com/get-started/your-authtoken
5. Configurez: ngrok authtoken VOTRE_TOKEN

📝 Commandes pour Windows PowerShell:
   cd C:\\ngrok\\
   .\\ngrok.exe authtoken VOTRE_TOKEN
   .\\ngrok.exe http 8080
        """)
    
    def start_tunnel_manual(self):
        """Guide pour démarrer le tunnel manuellement"""
        print("""
🚀 DÉMARRAGE DU TUNNEL NGROK

1. Ouvrez PowerShell/CMD
2. Naviguez vers le dossier ngrok
3. Exécutez: ngrok http 8080
4. Copiez l'URL HTTPS affichée (ex: https://abc123.ngrok.io)
5. Utilisez cette URL pour configurer AgriWeb

⚡ Exemple de commande:
   cd C:\\ngrok\\
   .\\ngrok.exe http 8080

📋 Une fois le tunnel actif, vous verrez:
   Forwarding    https://abc123.ngrok.io -> http://localhost:8080
        """)
    
    def get_ngrok_url(self):
        """Récupère l'URL du tunnel ngrok actif"""
        try:
            response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
            if response.status_code == 200:
                tunnels = response.json()
                for tunnel in tunnels.get('tunnels', []):
                    if tunnel.get('proto') == 'https':
                        public_url = tunnel.get('public_url')
                        print(f"✅ Tunnel ngrok détecté: {public_url}")
                        return public_url
            return None
        except:
            print("⚠️ Ngrok API non accessible (tunnel non démarré?)")
            return None
    
    def test_tunnel_access(self, tunnel_url):
        """Test l'accès au GeoServer via tunnel"""
        try:
            geoserver_url = f"{tunnel_url}/geoserver"
            response = requests.get(f"{geoserver_url}/web/", timeout=10)
            if response.status_code == 200:
                print(f"✅ GeoServer accessible via tunnel: {geoserver_url}")
                return geoserver_url
            else:
                print(f"⚠️ Tunnel répond mais GeoServer non accessible")
                return None
        except Exception as e:
            print(f"❌ Erreur d'accès via tunnel: {e}")
            return None
    
    def update_agriweb_config(self, geoserver_tunnel_url):
        """Met à jour la configuration AgriWeb avec l'URL du tunnel"""
        config_update = f"""
# Configuration pour utiliser GeoServer local via tunnel
GEOSERVER_LOCAL_TUNNEL = "{geoserver_tunnel_url}"

# À ajouter dans votre fichier de configuration:
export GEOSERVER_URL="{geoserver_tunnel_url}"
        """
        
        print("📝 Configuration à utiliser:")
        print(config_update)
        
        # Créer un fichier de configuration
        with open("geoserver_tunnel_config.txt", "w") as f:
            f.write(config_update)
        
        print("✅ Configuration sauvée dans: geoserver_tunnel_config.txt")
    
    def run_diagnostic(self):
        """Diagnostic complet de la configuration tunnel"""
        print("🔍 DIAGNOSTIC TUNNEL GEOSERVER LOCAL")
        print("=" * 50)
        
        # 1. Vérifier GeoServer local
        print("\n1. Vérification GeoServer local:")
        local_ok = self.check_geoserver_local()
        
        # 2. Vérifier tunnel ngrok
        print("\n2. Vérification tunnel ngrok:")
        tunnel_url = self.get_ngrok_url()
        
        if tunnel_url:
            # 3. Tester accès via tunnel
            print("\n3. Test accès via tunnel:")
            geoserver_tunnel = self.test_tunnel_access(tunnel_url)
            
            if geoserver_tunnel:
                print("\n4. Configuration AgriWeb:")
                self.update_agriweb_config(geoserver_tunnel)
                
                print(f"\n✅ SUCCÈS! Utilisez cette URL pour AgriWeb:")
                print(f"🌐 {geoserver_tunnel}")
            else:
                print("\n❌ Tunnel non fonctionnel")
        else:
            print("\n📝 Instructions pour configurer ngrok:")
            self.install_ngrok()
            print("\n🚀 Après installation, relancez ce script")

def main():
    """Fonction principale"""
    print("🌐 CONFIGURATION TUNNEL GEOSERVER LOCAL")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    manager = GeoServerTunnelManager()
    
    print("\nOptions disponibles:")
    print("1. 🔍 Diagnostic complet")
    print("2. 📖 Instructions ngrok") 
    print("3. 🚀 Guide tunnel manuel")
    print("4. 🌐 Détecter tunnel actif")
    
    choice = input("\nVotre choix (1-4): ").strip()
    
    if choice == "1":
        manager.run_diagnostic()
    elif choice == "2":
        manager.install_ngrok()
    elif choice == "3":
        manager.start_tunnel_manual()
    elif choice == "4":
        url = manager.get_ngrok_url()
        if url:
            geoserver_url = manager.test_tunnel_access(url)
            if geoserver_url:
                manager.update_agriweb_config(geoserver_url)
    else:
        print("Choix invalide")

if __name__ == "__main__":
    main()
