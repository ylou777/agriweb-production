#!/usr/bin/env python3
"""
Analyse des paramètres d'authentification GeoServer critiques
Impact sur l'accès distant Railway
"""

def analyze_auth_settings():
    """Analyse des paramètres d'authentification GeoServer"""
    
    print("🔒 ANALYSE PARAMÈTRES D'AUTHENTIFICATION GEOSERVER")
    print("="*55)
    
    settings = {
        "Port SSL": {
            "valeur": "443",
            "impact": "CRITIQUE",
            "description": "Port HTTPS pour accès sécurisé",
            "recommandation": "✅ 443 est correct pour HTTPS",
            "railway_impact": "Railway peut accéder via HTTPS si configuré"
        },
        "URL de redirection déconnexion": {
            "valeur": "/web/",
            "impact": "MINEUR",
            "description": "Redirection après logout",
            "recommandation": "✅ /web/ est standard",
            "railway_impact": "N'affecte pas l'accès API Railway"
        },
        "Protection force brute": {
            "valeur": "Activée",
            "impact": "MAJEUR",
            "description": "Bloque les tentatives répétées",
            "recommandation": "⚠️ Peut bloquer Railway si erreurs répétées",
            "railway_impact": "ATTENTION: Railway pourrait être bloqué"
        },
        "Délai minimum échec": {
            "valeur": "1 seconde",
            "impact": "MODÉRÉ",
            "description": "Délai après échec d'auth",
            "recommandation": "✅ 1s est raisonnable",
            "railway_impact": "Ralentit légèrement Railway si erreur"
        },
        "Délai maximum échec": {
            "valeur": "5 secondes",
            "impact": "MODÉRÉ", 
            "description": "Délai max après échecs répétés",
            "recommandation": "✅ 5s acceptable",
            "railway_impact": "Peut ralentir Railway si problèmes"
        },
        "Masques exclus": {
            "valeur": "127.0.0.1",
            "impact": "CRITIQUE",
            "description": "IPs exemptées de la protection",
            "recommandation": "❌ PROBLÈME: seul localhost est exempté",
            "railway_impact": "Railway N'EST PAS exempté des protections"
        },
        "Max threads bloqués": {
            "valeur": "100",
            "impact": "MINEUR",
            "description": "Threads max en attente",
            "recommandation": "✅ 100 est suffisant",
            "railway_impact": "Peu d'impact direct"
        }
    }
    
    print("\n📋 DÉTAIL DES PARAMÈTRES:")
    for param, info in settings.items():
        print(f"\n🔧 {param}")
        print(f"   Valeur actuelle: {info['valeur']}")
        print(f"   Impact: {info['impact']}")
        print(f"   Description: {info['description']}")
        print(f"   Recommandation: {info['recommandation']}")
        print(f"   Impact Railway: {info['railway_impact']}")

def identify_critical_issues():
    """Identifie les problèmes critiques pour Railway"""
    
    print(f"\n❗ PROBLÈMES CRITIQUES IDENTIFIÉS")
    print("="*40)
    
    print(f"\n🚨 PROBLÈME #1: Masques réseau exclus")
    print(f"   Actuel: 127.0.0.1 (localhost uniquement)")
    print(f"   Problème: Railway n'est PAS exempté de la protection anti-bruteforce")
    print(f"   Risque: Railway peut être bloqué après quelques erreurs d'auth")
    
    print(f"\n🚨 PROBLÈME #2: Protection force brute trop stricte")
    print(f"   Actuel: Activée pour toutes les IPs externes")
    print(f"   Problème: Railway sera soumis aux délais et blocages")
    print(f"   Risque: Timeouts et blocages temporaires")

def recommend_fixes():
    """Recommandations pour corriger les problèmes"""
    
    print(f"\n🛠️ CORRECTIONS RECOMMANDÉES")
    print("="*35)
    
    print(f"\n1️⃣ AJOUTER L'IP RAILWAY AUX MASQUES EXCLUS")
    print(f"   Étape 1: Obtenir l'IP sortante Railway")
    print(f"   railway variables")
    print(f"   # Chercher RAILWAY_STATIC_URL ou utiliser Static IP addon")
    
    print(f"\n   Étape 2: Dans GeoServer Admin → Security → Authentication")
    print(f"   Masques de réseau exclus: 127.0.0.1,IP_RAILWAY")
    print(f"   Exemple: 127.0.0.1,52.1.2.3")
    
    print(f"\n2️⃣ ALTERNATIVE: DÉSACTIVER TEMPORAIREMENT LA PROTECTION")
    print(f"   Paramètres de prévention des attaques en force brute: Désactiver")
    print(f"   ⚠️ Moins sécurisé mais évite les blocages Railway")
    
    print(f"\n3️⃣ ALTERNATIVE: AUGMENTER LES SEUILS")
    print(f"   Délai minimum: 1 → 0.5 secondes")
    print(f"   Délai maximum: 5 → 3 secondes")
    print(f"   Nombre max threads: 100 → 200")

def test_railway_ip_detection():
    """Aide à détecter l'IP Railway"""
    
    print(f"\n🔍 DÉTECTION IP RAILWAY")
    print("="*25)
    
    print(f"\n💡 Méthodes pour obtenir l'IP Railway:")
    
    print(f"\n📍 Méthode 1: Variables Railway")
    print(f"   railway variables | grep -i ip")
    print(f"   railway variables | findstr /i ip  # Windows")
    
    print(f"\n📍 Méthode 2: API de test depuis Railway")
    print(f"   Déployez ce code sur Railway:")
    
    test_code = '''
import requests
@app.route("/my-ip")
def get_my_ip():
    response = requests.get("https://ipinfo.io/json")
    return response.json()
'''
    print(f"   {test_code}")
    
    print(f"\n📍 Méthode 3: Logs GeoServer")
    print(f"   Regarder les logs GeoServer pour voir l'IP source des requêtes Railway")
    print(f"   Tail -f geoserver.log | grep authentication")
    
    print(f"\n📍 Méthode 4: Static IP Railway (payant)")
    print(f"   railway add")
    print(f"   # Choisir 'Static Outbound IP'")
    print(f"   # Coût: ~5$/mois mais IP fixe garantie")

def create_test_endpoint():
    """Crée un endpoint de test pour vérifier l'IP"""
    
    print(f"\n🧪 ENDPOINT DE TEST POUR VOTRE APP")
    print("="*35)
    
    endpoint_code = '''
# Ajoutez ceci à votre app Flask
@app.route("/debug/my-ip")
def debug_my_ip():
    """Endpoint pour voir l'IP publique de Railway"""
    try:
        import requests
        response = requests.get("https://ipinfo.io/json", timeout=10)
        ip_info = response.json()
        
        return {
            "railway_ip": ip_info.get("ip"),
            "city": ip_info.get("city"),
            "region": ip_info.get("region"),
            "country": ip_info.get("country"),
            "org": ip_info.get("org"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}
'''
    
    print(f"Code à ajouter:")
    print(endpoint_code)
    
    print(f"\nUtilisation:")
    print(f"1. Ajoutez ce code à votre app")
    print(f"2. Déployez sur Railway") 
    print(f"3. Visitez: https://votre-app.railway.app/debug/my-ip")
    print(f"4. Notez l'IP affichée")
    print(f"5. Ajoutez cette IP aux masques exclus GeoServer")

def main():
    """Analyse principale"""
    
    analyze_auth_settings()
    identify_critical_issues()
    recommend_fixes()
    test_railway_ip_detection()
    create_test_endpoint()
    
    print(f"\n🎯 RÉSUMÉ ACTIONS PRIORITAIRES")
    print("="*35)
    print(f"1. 🔍 Identifier l'IP sortante Railway")
    print(f"2. 🔧 Ajouter cette IP aux masques exclus GeoServer")
    print(f"3. 🧪 Tester l'accès depuis Railway")
    print(f"4. 📊 Monitorer les logs d'authentification")
    
    print(f"\n⚠️ ATTENTION:")
    print(f"Sans ces corrections, Railway risque d'être bloqué")
    print(f"après quelques erreurs d'authentification !")

if __name__ == "__main__":
    main()
