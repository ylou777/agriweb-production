#!/usr/bin/env python3

print("🔍 Test d'import serveur_unifie_final...")

try:
    import serveur_unifie_final
    print("✅ Import du module OK")
    
    try:
        from serveur_unifie_final import app
        print("✅ Import de l'app Flask OK")
        print(f"📱 Type app: {type(app)}")
        
        # Test des routes
        with app.test_client() as client:
            response = client.get('/health')
            print(f"✅ Route /health: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur import app: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"❌ Erreur import module: {e}")
    import traceback
    traceback.print_exc()
