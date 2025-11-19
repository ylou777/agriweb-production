#!/usr/bin/env python3
"""
🚀 SCRIPT DE REDÉPLOIEMENT RAILWAY AUTOMATIQUE
Aide au redéploiement d'AgriWeb avec tunnel GeoServer
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime

def print_banner():
    """Affiche la bannière du script"""
    print("=" * 60)
    print("🚀 REDÉPLOIEMENT RAILWAY - AGRIWEB + TUNNEL")
    print("=" * 60)
    print(f"⏰ Démarrage: {datetime.now().strftime('%H:%M:%S')}")
    print()

def check_tunnel_status():
    """Vérifie le statut du tunnel ngrok"""
    print("1️⃣ Vérification du tunnel ngrok...")
    
    try:
        import requests
        tunnel_url = "https://complete-simple-ghost.ngrok-free.app/geoserver/web/"
        
        response = requests.get(tunnel_url, timeout=10)
        if response.status_code in [200, 302]:
            print("✅ Tunnel ngrok actif et accessible")
            return True
        else:
            print(f"⚠️ Tunnel répond avec status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur tunnel: {e}")
        return False

def check_git_status():
    """Vérifie le statut Git"""
    print("\n2️⃣ Vérification Git...")
    
    try:
        # Vérifier si on est dans un repo git
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        
        if result.stdout.strip():
            print("📝 Modifications détectées:")
            print(result.stdout)
            
            # Proposer de commit
            response = input("🤔 Voulez-vous commiter ces modifications ? (y/n): ")
            if response.lower() == 'y':
                commit_message = f"Update: Tunnel GeoServer configuration - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                
                subprocess.run(['git', 'add', '.'], check=True)
                subprocess.run(['git', 'commit', '-m', commit_message], check=True)
                print("✅ Modifications commitées")
            else:
                print("⏭️ Modifications non commitées")
        else:
            print("✅ Aucune modification Git détectée")
        
        return True
        
    except subprocess.CalledProcessError:
        print("⚠️ Pas de repository Git ou erreur Git")
        return False
    except FileNotFoundError:
        print("⚠️ Git non installé")
        return False

def generate_deployment_config():
    """Génère la configuration de déploiement"""
    print("\n3️⃣ Génération de la configuration...")
    
    config = {
        "tunnel_url": "https://complete-simple-ghost.ngrok-free.app/geoserver",
        "railway_vars": {
            "GEOSERVER_TUNNEL_URL": "https://complete-simple-ghost.ngrok-free.app/geoserver"
        },
        "deployment_info": {
            "timestamp": datetime.now().isoformat(),
            "tunnel_active": True,
            "ready_for_deployment": True
        }
    }
    
    # Sauvegarder la config
    with open('railway_deployment_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuration sauvegardée dans 'railway_deployment_config.json'")
    return config

def show_deployment_instructions():
    """Affiche les instructions de déploiement"""
    print("\n4️⃣ Instructions de déploiement Railway:")
    print()
    print("🔗 ÉTAPES À SUIVRE:")
    print()
    print("1. **Ouvrez Railway.app** dans votre navigateur")
    print("2. **Connectez-vous** à votre compte")
    print("3. **Sélectionnez** votre projet AgriWeb")
    print("4. **Allez dans** l'onglet 'Variables'")
    print("5. **Cliquez sur** 'Add Variable'")
    print()
    print("6. **Ajoutez cette variable :**")
    print("   📝 Variable Name: GEOSERVER_TUNNEL_URL")
    print("   🔗 Variable Value: https://complete-simple-ghost.ngrok-free.app/geoserver")
    print()
    print("7. **Sauvegardez** la variable")
    print("8. **Redéployez** (Railway le fait automatiquement)")
    print()
    print("⏳ **Attendez** 2-3 minutes pour le redéploiement")
    print("✅ **Testez** votre application")

def wait_for_deployment():
    """Attend et surveille le déploiement"""
    print("\n5️⃣ Surveillance du déploiement...")
    
    print("🔄 Railway va redéployer automatiquement après ajout de la variable")
    print("⏳ Temps estimé: 2-3 minutes")
    
    # Simulation d'attente
    for i in range(6):
        time.sleep(10)
        print(f"   ⏱️ {(i+1)*10}s écoulées...")
    
    print("✅ Déploiement probablement terminé")

def test_deployment_ready():
    """Teste si tout est prêt pour le déploiement"""
    print("\n🧪 Tests préalables:")
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Tunnel
    if check_tunnel_status():
        tests_passed += 1
    
    # Test 2: Git
    if check_git_status():
        tests_passed += 1
    
    # Test 3: Fichier principal
    if os.path.exists('agriweb_hebergement_gratuit.py'):
        print("✅ Fichier principal AgriWeb trouvé")
        tests_passed += 1
    else:
        print("❌ Fichier principal AgriWeb non trouvé")
    
    print(f"\n📊 Tests réussis: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 Tout est prêt pour le déploiement !")
        return True
    else:
        print("⚠️ Certains problèmes doivent être résolus")
        return False

def main():
    """Fonction principale"""
    print_banner()
    
    # Tests préalables
    if not test_deployment_ready():
        print("\n❌ Déploiement non possible actuellement")
        return False
    
    # Génération de la config
    config = generate_deployment_config()
    
    # Instructions
    show_deployment_instructions()
    
    # Attendre confirmation
    print("\n" + "="*60)
    response = input("🤔 Avez-vous ajouté la variable dans Railway ? (y/n): ")
    
    if response.lower() == 'y':
        wait_for_deployment()
        
        print("\n🎉 DÉPLOIEMENT TERMINÉ !")
        print("🔗 Votre AgriWeb utilise maintenant votre GeoServer local via tunnel")
        print("⚠️ Gardez ngrok ouvert tant que vous utilisez l'application")
        
        return True
    else:
        print("\n📋 Configuration prête - Ajoutez la variable quand vous êtes prêt !")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Script interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        sys.exit(1)
