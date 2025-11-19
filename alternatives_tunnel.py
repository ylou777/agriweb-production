#!/usr/bin/env python3
"""
🔄 ALTERNATIVES GRATUITES À NGROK
Solutions sans avertissement pour l'exposition publique de GeoServer
"""

import subprocess
import os
import time

class TunnelAlternatives:
    """Alternatives gratuites à ngrok sans avertissement"""
    
    def __init__(self):
        self.alternatives = {
            "cloudflared": {
                "name": "Cloudflare Tunnel",
                "cost": "Gratuit",
                "warning": "Aucun",
                "install": "winget install cloudflare.cloudflared",
                "command": "cloudflared tunnel --url localhost:8080",
                "pros": ["Gratuit illimité", "Pas d'avertissement", "Très stable"],
                "cons": ["Nécessite compte Cloudflare"]
            },
            "serveo": {
                "name": "Serveo.net",
                "cost": "Gratuit",
                "warning": "Aucun",
                "install": "Aucune installation",
                "command": "ssh -R 80:localhost:8080 serveo.net",
                "pros": ["Immédiat", "Pas d'inscription", "Pas d'avertissement"],
                "cons": ["URL aléatoire", "Moins stable"]
            },
            "localtunnel": {
                "name": "LocalTunnel",
                "cost": "Gratuit",
                "warning": "Minimal",
                "install": "npm install -g localtunnel",
                "command": "lt --port 8080",
                "pros": ["Simple", "Rapide", "Avertissement discret"],
                "cons": ["Nécessite Node.js"]
            },
            "pagekite": {
                "name": "PageKite",
                "cost": "Gratuit (limité)",
                "warning": "Aucun",
                "install": "pip install pagekite",
                "command": "python pagekite.py 8080 yourname.pagekite.me",
                "pros": ["Professionnel", "Stable"],
                "cons": ["Inscription requise", "Limite gratuite"]
            }
        }
    
    def show_alternatives(self):
        """Affiche toutes les alternatives"""
        print("🔄 ALTERNATIVES GRATUITES À NGROK SANS AVERTISSEMENT:")
        print("=" * 60)
        
        for key, alt in self.alternatives.items():
            print(f"\n📌 {alt['name']}")
            print(f"   💰 Coût: {alt['cost']}")
            print(f"   ⚠️ Avertissement: {alt['warning']}")
            print(f"   📦 Installation: {alt['install']}")
            print(f"   🚀 Commande: {alt['command']}")
            print(f"   ✅ Avantages: {', '.join(alt['pros'])}")
            print(f"   ❌ Inconvénients: {', '.join(alt['cons'])}")
    
    def install_cloudflared(self):
        """Installation de Cloudflare Tunnel (recommandé)"""
        print("🌐 Installation de Cloudflare Tunnel...")
        try:
            # Vérification si déjà installé
            result = subprocess.run(["cloudflared", "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Cloudflare Tunnel déjà installé")
                return True
        except:
            pass
        
        # Installation via winget
        try:
            subprocess.run(["winget", "install", "cloudflare.cloudflared"], 
                          check=True)
            print("✅ Cloudflare Tunnel installé avec succès")
            return True
        except:
            print("❌ Échec installation via winget")
            print("💡 Téléchargez manuellement: https://github.com/cloudflare/cloudflared/releases")
            return False

if __name__ == "__main__":
    alternatives = TunnelAlternatives()
    alternatives.show_alternatives()
    
    print("\n" + "="*60)
    print("🎯 RECOMMANDATION: Cloudflare Tunnel")
    print("   • Gratuit et illimité")
    print("   • Aucun avertissement")
    print("   • Très professionnel")
    print("   • Stable et rapide")
