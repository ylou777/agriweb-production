"""
🔍 Script de vérification de l'état des services AgriWeb
Exécuter avec : python check_status.py
"""
import requests
import json
import subprocess
import time
from datetime import datetime

def print_header():
    print("🔍 VÉRIFICATION DE L'ÉTAT DES SERVICES AGRIWEB")
    print("=" * 60)
    print(f"⏰ Heure: {datetime.now().strftime('%H:%M:%S - %d/%m/%Y')}")
    print("-" * 60)

def check_service(name, url, timeout=5, headers=None):
    """Vérifie l'état d'un service"""
    try:
        response = requests.get(url, timeout=timeout, headers=headers or {})
        status = "✅ ACTIF" if response.status_code in [200, 302] else f"⚠️ CODE {response.status_code}"
        print(f"{name:<20} {status:<15} {url}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"{name:<20} ❌ INACTIF      {url}")
        return False
    except requests.exceptions.Timeout:
        print(f"{name:<20} ⏱️ TIMEOUT      {url}")
        return False
    except Exception as e:
        print(f"{name:<20} ❌ ERREUR       {url} ({str(e)[:30]})")
        return False

def check_ngrok_tunnels():
    """Vérifie les tunnels ngrok actifs"""
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=3)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            if tunnels:
                print(f"\n🔗 TUNNELS NGROK ACTIFS ({len(tunnels)}):")
                for tunnel in tunnels:
                    proto = tunnel.get('proto', 'unknown')
                    public_url = tunnel.get('public_url', 'N/A')
                    local_addr = tunnel.get('config', {}).get('addr', 'N/A')
                    print(f"   {proto.upper():<6} {public_url} -> {local_addr}")
                return True
        return False
    except:
        print("\n🔗 TUNNELS NGROK: ❌ Non accessible")
        return False

def check_processes():
    """Vérifie les processus en cours"""
    print(f"\n🔄 PROCESSUS ACTIFS:")
    
    # Python processes
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True, timeout=5)
        python_count = len([line for line in result.stdout.split('\n') if 'python.exe' in line])
        print(f"   Python        {python_count} processus")
    except:
        print(f"   Python        ❌ Impossible de vérifier")
    
    # ngrok processes
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq ngrok.exe'], 
                              capture_output=True, text=True, timeout=5)
        ngrok_count = len([line for line in result.stdout.split('\n') if 'ngrok.exe' in line])
        print(f"   ngrok         {ngrok_count} processus")
    except:
        print(f"   ngrok         ❌ Impossible de vérifier")

def check_database():
    """Vérifie la base de données"""
    try:
        import sqlite3
        conn = sqlite3.connect('agriweb_users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = 1')
        admin_count = cursor.fetchone()[0]
        conn.close()
        print(f"\n💾 BASE DE DONNÉES:")
        print(f"   Utilisateurs  {user_count} total ({admin_count} admin)")
        return True
    except Exception as e:
        print(f"\n💾 BASE DE DONNÉES: ❌ Erreur ({e})")
        return False

def main():
    print_header()
    
    # Vérification des services principaux
    print(f"{'SERVICE':<20} {'ÉTAT':<15} URL")
    print("-" * 60)
    
    services = [
        ("App Flask", "http://localhost:5000"),
        ("Admin Flask", "http://localhost:5000/admin"),
        ("GeoServer", "http://localhost:8080/geoserver"),
        ("ngrok API", "http://localhost:4040"),
        ("Railway Prod", "https://aware-surprise-production.up.railway.app")
    ]
    
    active_services = 0
    for name, url in services:
        if check_service(name, url):
            active_services += 1
    
    # Vérification des tunnels ngrok
    check_ngrok_tunnels()
    
    # Vérification des processus
    check_processes()
    
    # Vérification de la base de données
    check_database()
    
    # Résumé
    print("\n" + "=" * 60)
    print(f"📊 RÉSUMÉ: {active_services}/{len(services)} services actifs")
    
    if active_services == len(services):
        print("🎉 Tous les services fonctionnent parfaitement!")
    elif active_services >= 3:
        print("⚠️ La plupart des services fonctionnent, quelques problèmes mineurs")
    else:
        print("❌ Plusieurs services sont en panne, vérifiez la configuration")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
