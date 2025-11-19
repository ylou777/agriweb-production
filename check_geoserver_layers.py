#!/usr/bin/env python3
"""
Script pour lister et analyser les couches GeoServer locales
"""

import requests
import json
from datetime import datetime

def check_local_geoserver():
    """Vérifie et liste le contenu du GeoServer local"""
    
    geoserver_url = "http://localhost:8080/geoserver"
    auth = ("admin", "geoserver")
    
    print("🔍 ANALYSE DU GEOSERVER LOCAL")
    print("=" * 40)
    
    try:
        # Test de connexion
        response = requests.get(f"{geoserver_url}/rest/about/version", 
                              auth=auth, timeout=5)
        
        if response.status_code != 200:
            print("❌ GeoServer local non accessible")
            print("💡 Démarrez votre GeoServer local avec: java -jar start.jar")
            return False
            
        version_info = response.json()
        print(f"✅ GeoServer connecté - Version: {version_info.get('about', {}).get('@version', 'Unknown')}")
        
        # Lister les workspaces
        print(f"\n📁 WORKSPACES:")
        ws_response = requests.get(f"{geoserver_url}/rest/workspaces",
                                 auth=auth,
                                 headers={'Accept': 'application/json'})
        
        if ws_response.status_code == 200:
            workspaces = ws_response.json().get('workspaces', {}).get('workspace', [])
            
            if not workspaces:
                print("   ⚠️  Aucun workspace configuré")
                return True
                
            total_layers = 0
            total_datastores = 0
            
            for ws in workspaces:
                ws_name = ws['name']
                print(f"\n   📂 {ws_name}")
                
                # Datastores
                ds_response = requests.get(f"{geoserver_url}/rest/workspaces/{ws_name}/datastores",
                                         auth=auth,
                                         headers={'Accept': 'application/json'})
                
                if ds_response.status_code == 200:
                    datastores = ds_response.json().get('dataStores', {}).get('dataStore', [])
                    total_datastores += len(datastores)
                    
                    for ds in datastores:
                        print(f"      🗄️  Datastore: {ds['name']}")
                
                # Couches
                layers_response = requests.get(f"{geoserver_url}/rest/workspaces/{ws_name}/layers",
                                             auth=auth,
                                             headers={'Accept': 'application/json'})
                
                if layers_response.status_code == 200:
                    layers = layers_response.json().get('layers', {}).get('layer', [])
                    total_layers += len(layers)
                    
                    for layer in layers:
                        print(f"      🗺️  Couche: {layer['name']}")
            
            print(f"\n📊 RÉSUMÉ:")
            print(f"   Workspaces: {len(workspaces)}")
            print(f"   Datastores: {total_datastores}")
            print(f"   Couches: {total_layers}")
            
            if total_layers > 0:
                print(f"\n💡 MIGRATION NÉCESSAIRE:")
                print(f"   Vous avez {total_layers} couches à migrer vers Railway")
                print(f"   Utilisez: python migrate_geoserver_data.py")
            else:
                print(f"\n✅ Aucune couche à migrer")
                
        else:
            print(f"❌ Erreur lecture workspaces: {ws_response.status_code}")
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ GeoServer local non accessible")
        print("💡 Démarrez votre GeoServer local d'abord")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def check_railway_geoserver():
    """Vérifie l'état du GeoServer Railway"""
    
    geoserver_url = "https://geoserver-agriweb-production.up.railway.app/geoserver"
    auth = ("admin", "admin123")
    
    print(f"\n🚀 GEOSERVER RAILWAY")
    print("=" * 40)
    
    try:
        response = requests.get(f"{geoserver_url}/rest/about/version", 
                              auth=auth, timeout=10)
        
        if response.status_code == 200:
            version_info = response.json()
            print(f"✅ GeoServer Railway connecté - Version: {version_info.get('about', {}).get('@version', 'Unknown')}")
            
            # Vérifier les workspaces existants
            ws_response = requests.get(f"{geoserver_url}/rest/workspaces",
                                     auth=auth,
                                     headers={'Accept': 'application/json'})
            
            if ws_response.status_code == 200:
                workspaces = ws_response.json().get('workspaces', {}).get('workspace', [])
                print(f"📁 Workspaces existants: {len(workspaces)}")
                
                for ws in workspaces:
                    print(f"   📂 {ws['name']}")
            
            return True
        else:
            print(f"❌ GeoServer Railway non accessible (Status: {response.status_code})")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ GeoServer Railway non accessible")
        print("💡 Le service est peut-être encore en cours de démarrage")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    print(f"🔍 VÉRIFICATION GEOSERVER - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Vérifier le GeoServer local
    local_ok = check_local_geoserver()
    
    # Vérifier le GeoServer Railway
    railway_ok = check_railway_geoserver()
    
    print(f"\n🎯 PROCHAINES ÉTAPES:")
    if local_ok and railway_ok:
        print("✅ Les deux GeoServer sont accessibles")
        print("🔄 Vous pouvez lancer la migration: python migrate_geoserver_data.py")
    elif local_ok and not railway_ok:
        print("⏳ GeoServer local OK, Railway en cours de démarrage")
        print("💡 Attendez quelques minutes puis relancez cette vérification")
    elif not local_ok and railway_ok:
        print("⚠️  GeoServer Railway OK, mais local inaccessible")
        print("💡 Démarrez votre GeoServer local pour la migration")
    else:
        print("❌ Aucun GeoServer accessible")
        print("💡 Démarrez le GeoServer local et attendez Railway")

if __name__ == "__main__":
    main()
