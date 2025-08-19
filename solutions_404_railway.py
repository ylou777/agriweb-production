#!/usr/bin/env python3
"""
🚂 RAILWAY GEOSERVER - SOLUTIONS 404
Guide de résolution de l'erreur 404 GeoServer Railway
"""

print("""
🔍 ERREUR 404 GEOSERVER RAILWAY - ANALYSE
==========================================

Votre erreur indique:
• Status: HTTP 404 - Non trouvé  
• Message: /geoserver/web/
• Serveur: Apache Tomcat/9.0.20

📋 CAUSES POSSIBLES:
===================

1. 🕒 DÉMARRAGE EN COURS (Le plus probable)
   • GeoServer prend 5-10 minutes à démarrer
   • Tomcat 9.0.20 est détecté = Service actif
   • L'interface web n'est pas encore prête

2. 🔧 CONFIGURATION DOCKER
   • Image kartoza/geoserver peut avoir une config différente
   • Path /geoserver/web/ pourrait être différent

3. 🌐 URL INCORRECTE
   • L'endpoint pourrait être différent
   • Railway peut avoir une structure spécifique

🛠️ SOLUTIONS IMMÉDIATES:
========================

1. ⏱️ ATTENDRE (Recommandé)
   Patientez 5-10 minutes puis retestez

2. 🌐 TESTER URLS ALTERNATIVES:
   • https://geoserver-agriweb-production.up.railway.app/
   • https://geoserver-agriweb-production.up.railway.app/geoserver/
   • https://geoserver-agriweb-production.up.railway.app/web/

3. 📝 VÉRIFIER RAILWAY LOGS:
   railway logs --follow

4. 🔄 REDÉMARRER SI NÉCESSAIRE:
   railway service restart

🎯 PROCHAINES ÉTAPES:
====================

1. Testez le diagnostic automatique
2. Vérifiez les logs Railway  
3. Attendez le démarrage complet
4. Testez les URLs alternatives

💡 INFO IMPORTANTE:
==================
Tomcat/9.0.20 détecté = GeoServer fonctionne
Erreur 404 = Interface web pas encore prête
➡️ C'est normal lors du premier démarrage !

""")

# Test rapide de connectivité
import requests

def quick_test():
    print("🔍 TEST RAPIDE DE CONNECTIVITÉ:")
    print("=" * 35)
    
    urls_to_test = [
        "https://geoserver-agriweb-production.up.railway.app/",
        "https://geoserver-agriweb-production.up.railway.app/geoserver/",
    ]
    
    for url in urls_to_test:
        try:
            print(f"Testing: {url}")
            response = requests.get(url, timeout=5)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ SUCCÈS!")
            elif response.status_code == 404:
                print("   ❌ 404 - Pas encore prêt")
            else:
                print(f"   ⚠️ Code: {response.status_code}")
        except:
            print("   ❌ Connexion impossible")
        print()

if __name__ == "__main__":
    quick_test()
