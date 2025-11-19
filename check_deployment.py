#!/usr/bin/env python3
"""
Script pour vérifier le statut du déploiement Railway
"""

import requests
import time
import sys

def check_deployment():
    """Vérifie si l'application AgriWeb est déployée sur Railway"""
    
    url = "https://agriweb-production-production.up.railway.app"
    
    print(f"🔍 Vérification du déploiement sur {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Application déployée avec succès!")
            print(f"📱 URL: {url}")
            print(f"📊 Status: {response.status_code}")
            return True
            
        elif response.status_code == 404:
            print(f"❌ Application non trouvée (404)")
            print("🔄 Le déploiement est peut-être en cours...")
            return False
            
        else:
            print(f"⚠️  Status inattendu: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def main():
    """Fonction principale"""
    
    max_attempts = 12  # 12 tentatives = 6 minutes
    attempt = 1
    
    while attempt <= max_attempts:
        print(f"\n🔄 Tentative {attempt}/{max_attempts}")
        
        if check_deployment():
            print(f"\n🎉 AgriWeb est en ligne!")
            sys.exit(0)
        
        if attempt < max_attempts:
            print("⏳ Attente de 30 secondes avant la prochaine vérification...")
            time.sleep(30)
        
        attempt += 1
    
    print(f"\n❌ Le déploiement n'est pas encore disponible après {max_attempts} tentatives")
    print("📝 Suggestions:")
    print("   1. Vérifiez les logs Railway: railway logs")
    print("   2. Vérifiez le dashboard Railway")
    print("   3. Vérifiez que le repository GitHub est connecté")

if __name__ == "__main__":
    main()
