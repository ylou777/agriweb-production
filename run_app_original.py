# run_app.py

# Import du fichier Python modifié au lieu du module compilé
import agriweb_source
import traceback

if __name__ == '__main__':
    # Lance le serveur Flask directement sans la fonction main()
    try:
        print("🚀 [STARTUP] Démarrage AgriWeb ORIGINAL avec GeoServer intégré")
        print(f"🔧 [DEBUG] App type: {type(agriweb_source.app)}")
        print(f"🔧 [DEBUG] Routes: {len(list(agriweb_source.app.url_map.iter_rules()))}")
        print("🔧 [DEBUG] Configuration GeoServer: http://localhost:8080/geoserver")
        print("🔧 [DEBUG] Tentative de lancement...")
        agriweb_source.app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
        print("✅ [SUCCESS] Serveur lancé avec succès")
    except Exception as e:
        print(f"❌ [ERROR] Exception: {e}")
        print(f"❌ [TYPE] Type: {type(e)}")
        print("❌ [TRACEBACK] Détail:")
        traceback.print_exc()
