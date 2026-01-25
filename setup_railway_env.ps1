# Configuration Railway PostgreSQL pour import Enedis
# Variables récupérées depuis Railway

$env:POSTGRES_USER = "postgres"
$env:POSTGRES_PASSWORD = "WbjgkcXDKvbbYJhWprDDQQobbpnggYJc"
$env:POSTGRES_DB = "railway"
$env:PGPORT = "5432"

# ⚠️ COMPLETER avec le hostname Railway
# Allez dans Railway > Postgres > Variables et copiez la valeur de DATABASE_PUBLIC_URL ou DATABASE_URL
# Exemple: mondomaine.railway.app ou railway.internal

Write-Host "🔧 Variables PostgreSQL Railway:" -ForegroundColor Cyan
Write-Host "   User: $env:POSTGRES_USER" -ForegroundColor Green
Write-Host "   Database: $env:POSTGRES_DB" -ForegroundColor Green
Write-Host "   Port: $env:PGPORT" -ForegroundColor Green
Write-Host "   Password: ****" -ForegroundColor Green

Write-Host "`n⚠️  MANQUANT: Hostname Railway" -ForegroundColor Yellow
Write-Host "📋 Veuillez copier l'URL complète DATABASE_PUBLIC_URL depuis Railway" -ForegroundColor White
Write-Host "   Exemple: postgresql://postgres:PASSWORD@xxxx.railway.app:PORT/railway" -ForegroundColor Gray

Write-Host "`n💡 Puis définir:" -ForegroundColor Cyan
Write-Host '   $env:DATABASE_URL="postgresql://postgres:WbjgkcXDKvbbYJhWprDDQQobbpnggYJc@HOST:PORT/railway"' -ForegroundColor White
