"""
🚀 Gestionnaire automatique de tunnel ngrok
Solution temporaire gratuite avant upgrade payant
"""
import subprocess
import time
import requests
import json
import os
import signal
import sys

class NgrokManager:
    def __init__(self):
        self.process = None
        self.current_url = None
        
    def kill_existing_ngrok(self):
        """Arrête tous les processus ngrok existants"""
        try:
            subprocess.run(["taskkill", "/F", "/IM", "ngrok.exe"], 
                         capture_output=True, text=True)
            time.sleep(2)
        except:
            pass
    
    def start_tunnel(self):
        """Démarre un nouveau tunnel ngrok"""
        self.kill_existing_ngrok()
        
        print("🔄 Démarrage du tunnel ngrok...")
        
        # Commande ngrok
        cmd = ["ngrok", "http", "8080", "--host-header=localhost:8080"]
        
        # Démarrer en arrière-plan
        self.process = subprocess.Popen(cmd, 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE,
                                      text=True)
        
        # Attendre que le tunnel soit prêt
        for i in range(10):
            time.sleep(2)
            url = self.get_tunnel_url()
            if url:
                self.current_url = url
                print(f"✅ Tunnel prêt: {url}")
                return url
        
        print("❌ Échec démarrage tunnel")
        return None
    
    def get_tunnel_url(self):
        """Récupère l'URL du tunnel via l'API ngrok"""
        try:
            response = requests.get("http://localhost:4040/api/tunnels", timeout=3)
            if response.status_code == 200:
                data = response.json()
                for tunnel in data.get('tunnels', []):
                    if tunnel.get('proto') == 'https':
                        return tunnel.get('public_url')
        except:
            pass
        return None
    
    def update_application(self, url):
        """Met à jour l'application avec la nouvelle URL"""
        if not url:
            return False
            
        geoserver_url = f"{url}/geoserver"
        
        try:
            # Lire le fichier
            with open('agriweb_hebergement_gratuit.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remplacer la première URL
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'ngrok-free.app/geoserver' in line and 'URL ngrok actuelle' in line:
                    lines[i] = f'        "{geoserver_url}",  # URL ngrok actuelle (auto-update {time.strftime("%H:%M")})'
                    break
            
            # Sauvegarder
            with open('agriweb_hebergement_gratuit.py', 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
                
            print(f"📝 Application mise à jour: {geoserver_url}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur mise à jour: {e}")
            return False
    
    def restart_with_update(self):
        """Redémarre le tunnel et met à jour l'app"""
        url = self.start_tunnel()
        if url:
            self.update_application(url)
            return url
        return None
    
    def stop(self):
        """Arrête le gestionnaire"""
        if self.process:
            self.process.terminate()
        self.kill_existing_ngrok()

# Gestionnaire global
manager = NgrokManager()

def signal_handler(sig, frame):
    print("\n🛑 Arrêt du gestionnaire...")
    manager.stop()
    sys.exit(0)

if __name__ == "__main__":
    # Gestion de l'interruption
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🎯 Gestionnaire ngrok automatique")
    print("👆 Ctrl+C pour arrêter")
    print("-" * 40)
    
    # Démarrage initial
    url = manager.restart_with_update()
    
    if url:
        print(f"🌐 URL actuelle: {url}")
        print("🔄 Tunnel actif - gardez cette fenêtre ouverte")
        
        # Maintenir le tunnel ouvert
        try:
            while True:
                time.sleep(30)  # Vérifier toutes les 30 secondes
                if not manager.get_tunnel_url():
                    print("⚠️ Tunnel perdu - redémarrage...")
                    manager.restart_with_update()
        except KeyboardInterrupt:
            signal_handler(None, None)
    else:
        print("❌ Impossible de démarrer le tunnel")
