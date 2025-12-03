# Script PowerShell pour uploader sur Railway via CLI

Write-Host "🚀 UPLOAD PROPRIÉTAIRES MAJIC SUR RAILWAY" -ForegroundColor Cyan
Write-Host "=" * 80
Write-Host ""

# Vérifier que Railway CLI est installé
$railwayCli = Get-Command railway -ErrorAction SilentlyContinue
if (-not $railwayCli) {
    Write-Host "❌ Railway CLI n'est pas installé" -ForegroundColor Red
    Write-Host "💡 Installez-le avec: npm install -g @railway/cli" -ForegroundColor Yellow
    exit 1
}

# Fichier SQL compressé
$sqlFile = "C:\Users\Utilisateur\Desktop\AG32.1\proprietaires_parcelles.sql.gz"
if (-not (Test-Path $sqlFile)) {
    Write-Host "❌ Fichier introuvable: $sqlFile" -ForegroundColor Red
    exit 1
}

$fileSize = [math]::Round((Get-Item $sqlFile).Length / 1MB, 2)
Write-Host "📁 Fichier: proprietaires_parcelles.sql.gz ($fileSize MB)" -ForegroundColor Green
Write-Host ""

Write-Host "Étape 1: Connexion à Railway..." -ForegroundColor Yellow
railway login

Write-Host ""
Write-Host "Étape 2: Lier le projet..." -ForegroundColor Yellow
Set-Location "C:\Users\Utilisateur\Desktop\AG32.1\ag3reprise\AgriWeb-Railway-Deploy"
railway link

Write-Host ""
Write-Host "Étape 3: Copier le fichier dans le projet..." -ForegroundColor Yellow
Copy-Item $sqlFile -Destination ".\proprietaires_parcelles.sql.gz" -Force
Write-Host "✅ Fichier copié" -ForegroundColor Green

Write-Host ""
Write-Host "Étape 4: Ajouter au Git..." -ForegroundColor Yellow
git add proprietaires_parcelles.sql.gz import_proprietaires_to_railway.py
git commit -m "Add MAJIC proprietaires SQL dump (164 MB compressed)"

Write-Host ""
Write-Host "⚠️  ATTENTION: Le fichier fait 164 MB" -ForegroundColor Yellow
Write-Host "Le push peut prendre plusieurs minutes..." -ForegroundColor Yellow
Write-Host ""
$continue = Read-Host "Continuer avec git push? (y/n)"

if ($continue -eq 'y') {
    Write-Host ""
    Write-Host "Étape 5: Push vers Railway..." -ForegroundColor Yellow
    git push origin main
    
    Write-Host ""
    Write-Host "✅ Fichier uploadé sur Railway!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 PROCHAINES ÉTAPES:" -ForegroundColor Cyan
    Write-Host "1. Sur Railway Dashboard, attendez que le déploiement soit terminé"
    Write-Host "2. Ouvrez Railway Shell:"
    Write-Host "   railway shell"
    Write-Host "3. Décompressez le fichier:"
    Write-Host "   gunzip proprietaires_parcelles.sql.gz"
    Write-Host "4. Importez dans PostgreSQL:"
    Write-Host "   psql `$DATABASE_URL < proprietaires_parcelles.sql"
    Write-Host ""
    Write-Host "OU utilisez le script Python:"
    Write-Host "   python import_proprietaires_to_railway.py"
} else {
    Write-Host "❌ Annulé" -ForegroundColor Red
}
