# 🚀 Configuration GeoServer pour AgriWeb 2.0
# Script PowerShell pour Windows

Write-Host "🚀 CONFIGURATION GEOSERVER AGRIWEB 2.0" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""

# Test de Tomcat
Write-Host "1️⃣ VÉRIFICATION DE TOMCAT" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080" -TimeoutSec 10 -ErrorAction Stop
    Write-Host "   ✅ Tomcat accessible sur le port 8080" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Tomcat non accessible sur le port 8080" -ForegroundColor Red
    Write-Host "   🔧 Démarrez Tomcat avant de continuer" -ForegroundColor Yellow
    exit 1
}

# Test de GeoServer
Write-Host ""
Write-Host "2️⃣ VÉRIFICATION DE GEOSERVER" -ForegroundColor Yellow
try {
    $geoserver_response = Invoke-WebRequest -Uri "http://localhost:8080/geoserver" -TimeoutSec 10 -ErrorAction Stop
    Write-Host "   ✅ GeoServer déjà installé!" -ForegroundColor Green
    
    # Test des services
    try {
        $wfs_response = Invoke-WebRequest -Uri "http://localhost:8080/geoserver/ows?service=WFS&request=GetCapabilities" -TimeoutSec 10 -ErrorAction Stop
        Write-Host "   ✅ Service WFS fonctionnel" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️ Service WFS non accessible" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "   ❌ GeoServer non installé" -ForegroundColor Red
    Write-Host ""
    Write-Host "📥 INSTALLATION DE GEOSERVER" -ForegroundColor Yellow
    Write-Host "   Option 1: Exécutez installer_geoserver.py" -ForegroundColor Cyan
    Write-Host "   Option 2: Installation manuelle:" -ForegroundColor Cyan
    Write-Host "     - Téléchargez geoserver.war depuis geoserver.org" -ForegroundColor White
    Write-Host "     - Copiez dans le dossier webapps de Tomcat" -ForegroundColor White
    Write-Host "     - Redémarrez Tomcat" -ForegroundColor White
    
    $install_choice = Read-Host "   Voulez-vous installer automatiquement? (o/N)"
    if ($install_choice -eq "o" -or $install_choice -eq "O") {
        Write-Host "   🚀 Lancement de l'installation..." -ForegroundColor Green
        python installer_geoserver.py
    }
    exit 0
}

# Configuration AgriWeb
Write-Host ""
Write-Host "3️⃣ CONFIGURATION AGRIWEB" -ForegroundColor Yellow

Write-Host "   🌐 Interface GeoServer: http://localhost:8080/geoserver/web/" -ForegroundColor Cyan
Write-Host "   🔑 Login par défaut: admin / geoserver" -ForegroundColor Cyan

Write-Host ""
Write-Host "📋 COUCHES À CONFIGURER:" -ForegroundColor Yellow
$layers = @(
    "gpu:prefixes_sections",
    "gpu:poste_elec_shapefile", 
    "gpu:batiments_dgfip_shapefile",
    "gpu:parcelles_graphiques_rpg",
    "gpu:zones_urbanisees_gpu",
    "gpu:adresses_ban_shapefile",
    "gpu:communes_departement_region",
    "gpu:iris_population_shapefile",
    "gpu:departements_2023_shapefile",
    "gpu:regions_2023_shapefile",
    "gpu:eleveurs_porc_gpu",
    "gpu:eleveurs_volaille_gpu",
    "gpu:nature_culture_gpu",
    "gpu:exploitations_agricoles_gpu"
)

foreach ($layer in $layers) {
    Write-Host "   - $layer" -ForegroundColor White
}

Write-Host ""
Write-Host "🔧 PROCHAINES ÉTAPES:" -ForegroundColor Yellow
Write-Host "   1. Connectez-vous à l'interface GeoServer" -ForegroundColor White
Write-Host "   2. Créez le workspace 'gpu'" -ForegroundColor White  
Write-Host "   3. Ajoutez vos sources de données" -ForegroundColor White
Write-Host "   4. Publiez les 14 couches listées ci-dessus" -ForegroundColor White
Write-Host "   5. Testez avec diagnostic_geoserver.py" -ForegroundColor White

Write-Host ""
Write-Host "📖 DOCUMENTATION COMPLÈTE:" -ForegroundColor Yellow
Write-Host "   📄 GUIDE_GEOSERVER_CONFIGURATION.md" -ForegroundColor Cyan
Write-Host "   🧪 diagnostic_geoserver.py" -ForegroundColor Cyan

Write-Host ""
$open_browser = Read-Host "Voulez-vous ouvrir l'interface GeoServer? (o/N)"
if ($open_browser -eq "o" -or $open_browser -eq "O") {
    Start-Process "http://localhost:8080/geoserver/web/"
}

Write-Host ""
Write-Host "✨ Configuration terminée! Consultez le guide détaillé pour la suite." -ForegroundColor Green
