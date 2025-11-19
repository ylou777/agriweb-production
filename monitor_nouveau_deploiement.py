#!/usr/bin/env python3
"""
🔄 Monitor nouveau déploiement GeoServer
Suivre les logs en temps réel jusqu'à ce que GeoServer soit opérationnel
"""

import requests
import time
import subprocess
from datetime import datetime

def monitor_geoserver_deployment():
    """Monitorer le déploiement GeoServer en temps réel"""
    
    base_url = "https://geoserver-agriweb-production.up.railway.app"
    print("🔄 MONITORING NOUVEAU DÉPLOIEMENT GEOSERVER")
    print("=" * 60)
    print(f"🌐 URL: {base_url}")
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Vérifier que le redéploiement a commencé
    print("📋 Étapes attendues pour GeoServer (kartoza/geoserver):")
    print("1. Téléchargement image kartoza/geoserver:2.24.0")
    print("2. Initialisation Java avec 512M-1536M RAM")
    print("3. Démarrage Tomcat")
    print("4. 🎯 Déploiement GeoServer (ça va prendre 2-3 minutes)")
    print("5. Initialisation des données GeoServer")
    print("6. Interface admin disponible sur /geoserver/web/")
    print()
    
    # Attendre que le nouveau déploiement commence
    print("⏳ Attente du nouveau déploiement...")
    time.sleep(30)  # Laisser le temps au déploiement de commencer
    
    # Monitoring en temps réel
    attempt = 1
    max_attempts = 20  # 10 minutes max
    
    previous_status = None
    
    while attempt <= max_attempts:
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"\n🔍 [{timestamp}] Tentative {attempt}/{max_attempts}")
            
            # Test serveur de base
            response = requests.get(f"{base_url}/", timeout=15)
            current_status = response.status_code
            
            if current_status != previous_status:
                print(f"   Status changé: {previous_status} → {current_status}")
                previous_status = current_status
            
            # Analyser la réponse
            if current_status == 200:
                content = response.text.lower()
                
                if "geoserver" in content:
                    print("✅ GeoServer détecté dans la réponse!")
                    
                    # Test interface admin
                    try:
                        admin_response = requests.get(f"{base_url}/geoserver/web/", timeout=15)
                        if admin_response.status_code == 200:
                            print("🎉 GEOSERVER COMPLÈTEMENT OPÉRATIONNEL!")
                            print(f"🌐 Interface admin: {base_url}/geoserver/web/")
                            print("👤 Login: admin / admin123")
                            
                            # Test API REST
                            try:
                                rest_response = requests.get(
                                    f"{base_url}/geoserver/rest/workspaces",
                                    auth=("admin", "admin123"),
                                    timeout=10
                                )
                                if rest_response.status_code == 200:
                                    print("✅ API REST fonctionnelle")
                                    workspaces = rest_response.json()
                                    count = len(workspaces.get('workspaces', {}).get('workspace', []))
                                    print(f"📁 Workspaces: {count}")
                            except:
                                print("⏳ API REST encore en initialisation")
                            
                            return True
                        else:
                            print(f"⏳ Interface admin en cours d'initialisation ({admin_response.status_code})")
                    except:
                        print("⏳ Interface admin pas encore prête")
                
                elif "tomcat" in content:
                    print("🔄 Tomcat opérationnel, GeoServer en cours de déploiement...")
                else:
                    print("📦 Serveur répond, analyse du contenu...")
                    
            elif current_status == 502:
                print("🔄 Déploiement en cours (502 = redémarrage)")
            elif current_status == 503:
                print("🔄 Service temporairement indisponible (déploiement)")
            else:
                print(f"⚠️ Status inattendu: {current_status}")
            
        except requests.exceptions.Timeout:
            print("⏳ Timeout - déploiement toujours en cours")
        except requests.exceptions.ConnectionError:
            print("🔄 Connexion impossible - redéploiement actif")
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        attempt += 1
        
        if attempt <= max_attempts:
            print("   Attente 30 secondes...")
            time.sleep(30)
    
    print("\n⚠️ Timeout du monitoring")
    print("💡 Le déploiement GeoServer peut prendre jusqu'à 10 minutes")
    print(f"🌐 Continuez à vérifier: {base_url}/geoserver/web/")
    return False

def get_railway_logs():
    """Récupérer les logs Railway récents"""
    try:
        print("\n📋 Logs Railway récents:")
        result = subprocess.run(
            ["railway", "logs", "--tail", "20"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.stdout:
            print(result.stdout)
        else:
            print("Aucun log disponible")
    except Exception as e:
        print(f"❌ Erreur logs: {e}")

if __name__ == "__main__":
    print("🚀 Lancement du monitoring GeoServer...")
    
    # Afficher les logs d'abord
    get_railway_logs()
    
    # Puis monitorer
    success = monitor_geoserver_deployment()
    
    if success:
        print("\n🎉 SUCCÈS! GeoServer est opérationnel")
        print("📋 Prochaines étapes:")
        print("1. Créer workspace 'agriweb'")
        print("2. Importer vos 100 Go de données")
        print("3. Tester avec votre app Flask")
    else:
        print("\n⏳ Le déploiement continue en arrière-plan")
        print("🔄 Relancez ce script dans quelques minutes")
