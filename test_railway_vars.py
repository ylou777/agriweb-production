import os

# Simuler les variables Railway AVEC HTTPS
os.environ['GEOSERVER_URL'] = 'https://agriweb-prod.ngrok-free.app/geoserver'
os.environ['GEOSERVER_USERNAME'] = 'admin'
os.environ['GEOSERVER_PASSWORD'] = 'geoserver'
os.environ['SECRET_KEY'] = 'agriweb-secret-key-2025-commercial'
os.environ['HOST'] = '0.0.0.0'
os.environ['PORT'] = '5000'
os.environ['FLASK_DEBUG'] = 'False'

print("🔧 Variables Railway simulées définies")

# Maintenant importer le serveur
try:
    print("🚀 [STARTUP] Démarrage du serveur AgriWeb 2.0 Unifié (test)")
    
    from serveur_unifie_final import app
    
    print("✅ [SUCCESS] Serveur unifié importé avec variables Railway")
    print("🌐 [TEST] Test des routes de base...")
    
    # Test des routes critiques
    with app.test_client() as client:
        # Test health
        response = client.get('/health')
        print(f"✅ /health: {response.status_code}")
        
        # Test favicon
        response = client.get('/favicon.ico')
        print(f"✅ /favicon.ico: {response.status_code}")
        
        # Test accueil
        response = client.get('/')
        print(f"✅ /: {response.status_code}")
        
        # Test status
        response = client.get('/status')
        print(f"✅ /status: {response.status_code}")
        
    print("🎉 Tous les tests OK - Le problème n'est pas dans le code !")
    
except Exception as e:
    print(f"❌ [ERROR] {e}")
    import traceback
    traceback.print_exc()
