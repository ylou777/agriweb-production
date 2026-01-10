# Script de nettoyage pour libérer de l'espace disque et mémoire

Write-Host "🧹 Nettoyage du projet AgriWeb..." -ForegroundColor Cyan

# Compteurs
$totalSize = 0
$filesDeleted = 0
$dirsDeleted = 0

# Nettoyer les dossiers __pycache__
Write-Host "`n📁 Suppression des dossiers __pycache__..." -ForegroundColor Yellow
$pycacheDirs = Get-ChildItem -Path . -Recurse -Force -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
foreach ($dir in $pycacheDirs) {
    $size = (Get-ChildItem -Path $dir.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    $totalSize += $size
    Remove-Item -Path $dir.FullName -Recurse -Force -ErrorAction SilentlyContinue
    $dirsDeleted++
}
Write-Host "   ✓ $dirsDeleted dossiers supprimés" -ForegroundColor Green

# Nettoyer les fichiers .pyc
Write-Host "`n📄 Suppression des fichiers .pyc..." -ForegroundColor Yellow
$pycFiles = Get-ChildItem -Path . -Recurse -Force -Filter "*.pyc" -ErrorAction SilentlyContinue
foreach ($file in $pycFiles) {
    $totalSize += $file.Length
    Remove-Item -Path $file.FullName -Force -ErrorAction SilentlyContinue
    $filesDeleted++
}
Write-Host "   ✓ $filesDeleted fichiers supprimés" -ForegroundColor Green

# Nettoyer les fichiers .log volumineux
Write-Host "`n📋 Nettoyage des fichiers log..." -ForegroundColor Yellow
$logFiles = Get-ChildItem -Path . -Recurse -Force -Filter "*.log" -ErrorAction SilentlyContinue | Where-Object { $_.Length -gt 1MB }
$logCount = 0
foreach ($file in $logFiles) {
    $totalSize += $file.Length
    Remove-Item -Path $file.FullName -Force -ErrorAction SilentlyContinue
    $logCount++
}
Write-Host "   ✓ $logCount fichiers log supprimés" -ForegroundColor Green

# Nettoyer .pytest_cache
Write-Host "`n🧪 Suppression des caches pytest..." -ForegroundColor Yellow
$pytestDirs = Get-ChildItem -Path . -Recurse -Force -Directory -Filter ".pytest_cache" -ErrorAction SilentlyContinue
$pytestCount = 0
foreach ($dir in $pytestDirs) {
    $size = (Get-ChildItem -Path $dir.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    $totalSize += $size
    Remove-Item -Path $dir.FullName -Recurse -Force -ErrorAction SilentlyContinue
    $pytestCount++
}
Write-Host "   ✓ $pytestCount caches pytest supprimés" -ForegroundColor Green

# Résumé
$totalSizeMB = [math]::Round($totalSize / 1MB, 2)
Write-Host "`n✅ Nettoyage terminé!" -ForegroundColor Green
Write-Host "   📊 Espace libéré: $totalSizeMB Mo" -ForegroundColor Cyan
Write-Host "   📁 Total suppressions: $($dirsDeleted + $pytestCount) dossiers, $filesDeleted fichiers" -ForegroundColor Cyan

Write-Host "`n💡 Conseil: Redémarrez VS Code pour libérer la mémoire" -ForegroundColor Magenta
