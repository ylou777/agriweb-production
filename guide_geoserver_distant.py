#!/usr/bin/env python3
"""
Guide de configuration GeoServer pour accès distant
Étapes détaillées selon recommandations ChatGPT
"""

def show_network_configuration_guide():
    """Guide de configuration réseau"""
    
    print("🌐 CONFIGURATION RÉSEAU POUR ACCÈS DISTANT")
    print("="*50)
    
    print("\n1️⃣ OUVERTURE DES PORTS SUR VOTRE ROUTEUR/BOX")
    print("-" * 45)
    print("▶️ Accédez à l'interface de votre box (192.168.1.1 ou 192.168.0.1)")
    print("▶️ Cherchez 'Redirection de ports' ou 'NAT/PAT'")
    print("▶️ Configurez:")
    print("   Port externe: 8080")
    print("   Port interne: 8080") 
    print("   IP locale: [IP de votre PC GeoServer]")
    print("   Protocole: TCP")
    
    print("\n2️⃣ FIREWALL WINDOWS")
    print("-" * 20)
    print("▶️ Ouvrir 'Pare-feu Windows Defender'")
    print("▶️ 'Paramètres avancés' → 'Règles de trafic entrant'")
    print("▶️ 'Nouvelle règle' → Port → TCP → Port 8080")
    print("▶️ Autoriser la connexion")
    
    print("\n3️⃣ VÉRIFICATION IP PUBLIQUE")
    print("-" * 30)
    print("▶️ Visitez: https://whatismyipaddress.com/")
    print("▶️ Notez votre IP publique")
    print("▶️ Testez: http://VOTRE-IP:8080/geoserver")

def show_geoserver_user_configuration():
    """Guide de configuration utilisateur GeoServer"""
    
    print("\n👤 CONFIGURATION UTILISATEUR GEOSERVER")
    print("="*45)
    
    print("\n1️⃣ ACCÈS ADMIN GEOSERVER")
    print("-" * 25)
    print("▶️ Ouvrez: http://localhost:8080/geoserver/web")
    print("▶️ Connectez-vous avec admin/geoserver")
    
    print("\n2️⃣ CRÉER UTILISATEUR RAILWAY")
    print("-" * 30)
    print("▶️ Aller dans: Security → Users, Groups, Roles")
    print("▶️ Onglet 'Users' → 'Add new user'")
    print("▶️ Configurer:")
    print("   Username: railway_user")
    print("   Password: [mot de passe fort]")
    print("   Enabled: ✓")
    print("▶️ Sauvegarder")
    
    print("\n3️⃣ ASSIGNER RÔLE READER")
    print("-" * 25)
    print("▶️ Sélectionner l'utilisateur 'railway_user'")
    print("▶️ Onglet 'Roles' → Cocher 'ROLE_READER'")
    print("▶️ Sauvegarder")
    
    print("\n4️⃣ CONFIGURER SERVICE SECURITY")
    print("-" * 35)
    print("▶️ Security → Services")
    print("▶️ Pour chaque service (WMS, WFS, WCS):")
    print("   - Mode: CHALLENGE")
    print("   - Autoriser: ROLE_READER")
    print("▶️ Apply → Save")
    
    print("\n5️⃣ CONFIGURER DATA SECURITY")
    print("-" * 30)
    print("▶️ Security → Data")
    print("▶️ Pour chaque workspace/layer:")
    print("   - Read access: ROLE_READER")
    print("   - Write access: ROLE_ADMIN (ou vide)")
    print("▶️ Apply → Save")

def show_geoserver_global_settings():
    """Guide des paramètres globaux GeoServer"""
    
    print("\n⚙️ PARAMÈTRES GLOBAUX GEOSERVER")
    print("="*35)
    
    print("\n1️⃣ PROXY BASE URL (TRÈS IMPORTANT)")
    print("-" * 35)
    print("▶️ Settings → Global")
    print("▶️ Proxy Base URL: http://VOTRE-IP-PUBLIQUE:8080/geoserver")
    print("▶️ Exemple: http://81.220.178.156:8080/geoserver")
    print("▶️ Save")
    print("ℹ️  Ceci corrige les URLs dans les réponses GetCapabilities")
    
    print("\n2️⃣ LOGGING (OPTIONNEL)")
    print("-" * 20)
    print("▶️ Settings → Global → Logging")
    print("▶️ Log Level: INFO ou DEBUG")
    print("▶️ Save")

def show_test_commands():
    """Commandes de test"""
    
    print("\n🧪 COMMANDES DE TEST")
    print("="*25)
    
    print("\n1️⃣ TEST DEPUIS VOTRE PC")
    print("-" * 25)
    print("PowerShell:")
    print('curl "http://localhost:8080/geoserver/wms?service=WMS&request=GetCapabilities&version=1.3.0" -u railway_user:votre_mot_de_passe')
    
    print("\n2️⃣ TEST DEPUIS INTERNET")
    print("-" * 25)
    print("Depuis un autre réseau:")
    print('curl "http://VOTRE-IP:8080/geoserver/wms?service=WMS&request=GetCapabilities&version=1.3.0" -u railway_user:votre_mot_de_passe')
    
    print("\n3️⃣ TEST AUTHENTIFICATION")
    print("-" * 25)
    print('curl "http://VOTRE-IP:8080/geoserver/rest/about/version" -u railway_user:votre_mot_de_passe')

def show_railway_configuration():
    """Configuration Railway"""
    
    print("\n🚂 CONFIGURATION RAILWAY")
    print("="*30)
    
    print("\n1️⃣ VARIABLES D'ENVIRONNEMENT")
    print("-" * 30)
    print("railway variables set GEOSERVER_URL=http://VOTRE-IP:8080/geoserver")
    print("railway variables set GEOSERVER_USERNAME=railway_user") 
    print("railway variables set GEOSERVER_PASSWORD=votre_mot_de_passe")
    print("railway variables set ENVIRONMENT=production")
    
    print("\n2️⃣ TEST DEPUIS RAILWAY")
    print("-" * 25)
    print("▶️ Déployez votre app")
    print("▶️ Vérifiez les logs Railway")
    print("▶️ Testez les endpoints /proxy/wms")

def generate_test_script():
    """Génère un script de test automatisé"""
    
    print("\n📝 SCRIPT DE TEST AUTOMATIQUE")
    print("="*35)
    
    script = '''
# Script PowerShell de test GeoServer distant
param(
    [string]$IP = "81.220.178.156",
    [string]$User = "railway_user", 
    [string]$Pass = "votre_mot_de_passe"
)

$BaseURL = "http://$IP:8080/geoserver"

Write-Host "🧪 Test GeoServer Distant: $BaseURL" -ForegroundColor Green

# Test 1: Connectivité
Write-Host "1️⃣ Test connectivité..." -ForegroundColor Blue
try {
    $response = Invoke-WebRequest -Uri $BaseURL -TimeoutSec 10
    Write-Host "✅ Serveur accessible (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "❌ Serveur non accessible: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 2: WMS Capabilities avec auth
Write-Host "2️⃣ Test WMS avec authentification..." -ForegroundColor Blue
$wmsUrl = "$BaseURL/wms?service=WMS&request=GetCapabilities&version=1.3.0"
$creds = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("$User`:$Pass"))

try {
    $response = Invoke-WebRequest -Uri $wmsUrl -Headers @{Authorization="Basic $creds"} -TimeoutSec 20
    if ($response.Content -like "*WMS_Capabilities*") {
        Write-Host "✅ WMS OK - Capabilities reçues" -ForegroundColor Green
    } else {
        Write-Host "⚠️ WMS répond mais contenu inattendu" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Erreur WMS: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Workspaces REST
Write-Host "3️⃣ Test accès REST..." -ForegroundColor Blue
$restUrl = "$BaseURL/rest/workspaces"
try {
    $response = Invoke-WebRequest -Uri $restUrl -Headers @{Authorization="Basic $creds"; Accept="application/json"} -TimeoutSec 10
    Write-Host "✅ REST accessible" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur REST: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "✅ Tests terminés!" -ForegroundColor Green
'''
    
    print("Sauvegardez ce script comme 'test-geoserver.ps1':")
    print(script)

def main():
    """Guide principal"""
    
    print("🎯 GUIDE COMPLET: GEOSERVER ACCESSIBLE À DISTANCE")
    print("="*55)
    
    show_network_configuration_guide()
    show_geoserver_user_configuration()
    show_geoserver_global_settings()
    show_test_commands()
    show_railway_configuration()
    generate_test_script()
    
    print(f"\n🏁 RÉSUMÉ DES ÉTAPES")
    print(f"="*25)
    print(f"1️⃣ Ouvrir port 8080 sur routeur + firewall")
    print(f"2️⃣ Créer utilisateur 'railway_user' avec ROLE_READER")
    print(f"3️⃣ Configurer Service & Data Security")
    print(f"4️⃣ Définir Proxy Base URL")
    print(f"5️⃣ Tester depuis Internet")
    print(f"6️⃣ Configurer variables Railway")
    print(f"7️⃣ Déployer et tester")
    
    print(f"\n💡 Une fois configuré, vous aurez:")
    print(f"✅ Accès GeoServer depuis Railway (production)")
    print(f"✅ Accès GeoServer depuis votre PC (développement)")
    print(f"✅ Même configuration partout")
    print(f"✅ Sécurité avec utilisateur dédié")

if __name__ == "__main__":
    main()
