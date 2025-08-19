#!/usr/bin/env python3
"""
🧪 TEST AGRIWEB AVEC TUNNEL GEOSERVER
Test de l'AgriWeb hébergé avec le tunnel ngrok vers GeoServer local
"""

import os
import sys
import time
import requests
from datetime import datetime

# Configuration du tunnel
TUNNEL_URL = "https://84a78f08d305.ngrok-free.app/geoserver"
AGRIWEB_URL = "http://localhost:5000"  # AgriWeb local pour test

def test_tunnel_geoserver():
    """Teste l'accès au GeoServer via tunnel"""
    print("🔍 Test du tunnel GeoServer...")
    
    try:
        # Test accès GeoServer via tunnel
        response = requests.get(f"{TUNNEL_URL}/web/", timeout=10, 
                              headers={'User-Agent': 'AgriWeb-Test'})
        
        if response.status_code == 200:
            print("✅ GeoServer accessible via tunnel")
            return True
        else:
            print(f"⚠️ GeoServer tunnel: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur tunnel GeoServer: {e}")
        return False

def test_agriweb_with_tunnel():
    """Lance AgriWeb avec configuration tunnel"""
    print("🚀 Test AgriWeb avec tunnel...")
    
    # Configuration des variables d'environnement
    os.environ['GEOSERVER_TUNNEL_URL'] = TUNNEL_URL
    os.environ['DEBUG'] = 'True'
    os.environ['SECRET_KEY'] = 'test-key-123'
    
    try:
        # Import du module AgriWeb
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from agriweb_hebergement_gratuit import app, Config
        
        print(f"🌐 GeoServer configuré: {Config.get_geoserver_url()}")
        
        # Test de démarrage
        with app.test_client() as client:
            # Test page d'accueil
            response = client.get('/')
            print(f"📄 Page d'accueil: Status {response.status_code}")
            
            # Test health check
            response = client.get('/health')
            if response.status_code == 200:
                data = response.get_json()
                print(f"💚 Health check: {data}")
                return True
            
        return False
        
    except Exception as e:
        print(f"❌ Erreur AgriWeb: {e}")
        return False

def run_full_test():
    """Test complet du système"""
    print("=" * 60)
    print("🎯 TEST COMPLET AGRIWEB + TUNNEL GEOSERVER")
    print("=" * 60)
    print(f"⏰ Démarrage: {datetime.now().strftime('%H:%M:%S')}")
    
    # Test 1: Tunnel GeoServer
    print("\n1️⃣ Test du tunnel GeoServer")
    tunnel_ok = test_tunnel_geoserver()
    
    if not tunnel_ok:
        print("❌ Tunnel GeoServer non accessible - Arrêt des tests")
        return False
    
    # Test 2: AgriWeb avec tunnel
    print("\n2️⃣ Test AgriWeb avec tunnel")
    agriweb_ok = test_agriweb_with_tunnel()
    
    # Résultats
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS FINAUX")
    print("=" * 60)
    print(f"🌐 Tunnel GeoServer: {'✅ OK' if tunnel_ok else '❌ ÉCHEC'}")
    print(f"🚀 AgriWeb: {'✅ OK' if agriweb_ok else '❌ ÉCHEC'}")
    
    if tunnel_ok and agriweb_ok:
        print("\n🎉 SUCCÈS COMPLET !")
        print("✅ Votre configuration est prête pour le déploiement")
        print(f"🔗 URL tunnel: {TUNNEL_URL}")
        print("\n📋 ÉTAPES SUIVANTES:")
        print("1. Ajoutez GEOSERVER_TUNNEL_URL dans votre plateforme")
        print("2. Redéployez AgriWeb")
        print("3. Gardez ngrok ouvert")
        return True
    else:
        print("\n⚠️ Configuration incomplète")
        return False

if __name__ == "__main__":
    success = run_full_test()
    sys.exit(0 if success else 1)
