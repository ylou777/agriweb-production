# 🌐 Configuration et Démarrage Ngrok pour AgriWeb

## 📋 Problème identifié

Votre tunnel ngrok redirige vers le port **80**, mais Flask écoute sur le port **5000**.

```
❌ ACTUEL:
ngrok (port 80) → localhost:80 (rien n'écoute)
Flask → localhost:5000 (accessible mais pas via ngrok)

✅ CORRECT:
ngrok (port 5000) → localhost:5000 (Flask)
```

---

## 🔧 Solution - 3 méthodes

### Méthode 1: Ngrok vers port 5000 (RECOMMANDÉ ⭐)

**Avantages:**
- Pas de modification du code Flask
- Simple et rapide
- Fonctionne immédiatement

**Commandes:**
```powershell
# 1. Arrêter ngrok actuel
Get-Process ngrok -ErrorAction SilentlyContinue | Stop-Process -Force

# 2. Vérifier que Flask tourne sur 5000
# (Votre serveur devrait déjà tourner)

# 3. Lancer ngrok sur le BON port
ngrok http --url=agriweb-prod.ngrok-free.app 5000
```

---

### Méthode 2: Flask sur port 80 (AVANCÉ)

**Avantages:**
- URL plus propre (pas de :5000)
- Standard HTTP

**Inconvénients:**
- Nécessite droits admin sur Windows
- Modification du code Flask

**⚠️ Sur Windows, port 80 nécessite des droits admin**

---

### Méthode 3: Utiliser un port personnalisé

**Si vous voulez un autre port (ex: 8080):**
```powershell
# Flask sur 8080
python agriweb_hebergement_gratuit.py --port 8080

# Ngrok vers 8080
ngrok http --url=agriweb-prod.ngrok-free.app 8080
```

---

## 🚀 Script de démarrage complet

Créez un fichier `start_with_ngrok.ps1`:

```powershell
# ===== SCRIPT DE DÉMARRAGE AGRIWEB + NGROK =====

Write-Host "🚀 Démarrage AgriWeb avec Ngrok" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Gray

# 1. Arrêter les processus existants
Write-Host "`n1️⃣ Nettoyage des processus existants..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*AgW3b*"} | Stop-Process -Force
Get-Process ngrok -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# 2. Activer l'environnement virtuel
Write-Host "`n2️⃣ Activation de l'environnement virtuel..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# 3. Démarrer Flask en arrière-plan
Write-Host "`n3️⃣ Démarrage du serveur Flask (port 5000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\.venv\Scripts\Activate.ps1; python agriweb_hebergement_gratuit.py" -WindowStyle Normal

# Attendre que Flask démarre
Write-Host "   ⏳ Attente du démarrage du serveur (10 secondes)..." -ForegroundColor Gray
Start-Sleep -Seconds 10

# 4. Vérifier que Flask répond
Write-Host "`n4️⃣ Vérification du serveur Flask..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000" -TimeoutSec 5 -UseBasicParsing
    Write-Host "   ✅ Flask répond sur le port 5000" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Flask ne répond pas sur le port 5000" -ForegroundColor Red
    Write-Host "   Vérifiez que le serveur a bien démarré dans la fenêtre PowerShell" -ForegroundColor Yellow
    exit 1
}

# 5. Démarrer Ngrok
Write-Host "`n5️⃣ Démarrage de Ngrok..." -ForegroundColor Yellow
Write-Host "   🌐 URL publique: https://agriweb-prod.ngrok-free.app" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ngrok http --url=agriweb-prod.ngrok-free.app 5000" -WindowStyle Normal

# 6. Attendre que ngrok démarre
Start-Sleep -Seconds 5

# 7. Afficher le dashboard ngrok
Write-Host "`n6️⃣ Dashboard Ngrok disponible sur:" -ForegroundColor Yellow
Write-Host "   📊 http://127.0.0.1:4040" -ForegroundColor Cyan

# 8. Résumé
Write-Host "`n" + "="*60 -ForegroundColor Gray
Write-Host "✅ DÉMARRAGE TERMINÉ" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Gray
Write-Host ""
Write-Host "🔗 URLs d'accès:" -ForegroundColor Cyan
Write-Host "   • Local:     http://localhost:5000" -ForegroundColor White
Write-Host "   • Public:    https://agriweb-prod.ngrok-free.app" -ForegroundColor White
Write-Host "   • Dashboard: http://127.0.0.1:4040" -ForegroundColor White
Write-Host ""
Write-Host "📝 Logs:" -ForegroundColor Cyan
Write-Host "   • Flask: Fenêtre PowerShell séparée" -ForegroundColor White
Write-Host "   • Ngrok: Fenêtre PowerShell séparée" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  Pour arrêter:" -ForegroundColor Yellow
Write-Host "   1. Fermez les fenêtres PowerShell Flask et Ngrok" -ForegroundColor White
Write-Host "   2. Ou exécutez: Get-Process python,ngrok | Stop-Process -Force" -ForegroundColor White
Write-Host ""
Write-Host "="*60 -ForegroundColor Gray

# Garder la fenêtre ouverte
Write-Host "`nAppuyez sur une touche pour fermer cette fenêtre..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
```

---

## 🎯 Commandes rapides

### Démarrage manuel (étape par étape)

**Terminal 1 - Flask:**
```powershell
# Activer venv
.\.venv\Scripts\Activate.ps1

# Démarrer Flask
python agriweb_hebergement_gratuit.py
```

**Terminal 2 - Ngrok:**
```powershell
# Démarrer ngrok sur port 5000
ngrok http --url=agriweb-prod.ngrok-free.app 5000
```

### Vérification

```powershell
# Tester en local
curl http://localhost:5000

# Tester via ngrok
curl https://agriweb-prod.ngrok-free.app

# Voir le dashboard ngrok
start http://127.0.0.1:4040
```

---

## 🐛 Dépannage

### Erreur: 502 Bad Gateway

**Cause:** Ngrok redirige vers un port où rien n'écoute

**Solution:**
```powershell
# 1. Vérifier le port de Flask
netstat -ano | findstr :5000

# 2. Arrêter et redémarrer ngrok sur le bon port
Get-Process ngrok | Stop-Process -Force
ngrok http --url=agriweb-prod.ngrok-free.app 5000
```

### Erreur: Address already in use

**Cause:** Port 5000 déjà utilisé

**Solution:**
```powershell
# Trouver le processus
netstat -ano | findstr :5000

# Arrêter le processus (remplacer PID)
Stop-Process -Id <PID> -Force

# Ou arrêter tous les python
Get-Process python | Stop-Process -Force
```

### Erreur: Ngrok not found

**Solution:**
```powershell
# Installer ngrok si nécessaire
winget install ngrok

# Ou télécharger depuis https://ngrok.com/download
```

---

## 📊 Configuration Ngrok recommandée

### Créer un fichier de config ngrok

**Fichier:** `%USERPROFILE%\.ngrok2\ngrok.yml`

```yaml
version: "2"
authtoken: VOTRE_TOKEN_ICI

tunnels:
  agriweb:
    proto: http
    addr: 5000
    domain: agriweb-prod.ngrok-free.app
    inspect: true
    
  agriweb-geoserver:
    proto: http
    addr: 8080
    subdomain: agriweb-geoserver
```

**Démarrer avec la config:**
```powershell
# Démarrer le tunnel agriweb
ngrok start agriweb

# Démarrer tous les tunnels
ngrok start --all
```

---

## 🔐 Sécurité

### Ajouter une authentification Ngrok

```powershell
# Avec authentification basique
ngrok http --url=agriweb-prod.ngrok-free.app 5000 --basic-auth="user:password"

# Avec IP whitelisting (plan payant)
ngrok http --url=agriweb-prod.ngrok-free.app 5000 --cidr-allow="1.2.3.4/32"
```

---

## 📈 Monitoring

### Voir les requêtes en temps réel

```powershell
# Dashboard web (automatique)
start http://127.0.0.1:4040

# Via API
curl http://127.0.0.1:4040/api/tunnels
```

### Logs Ngrok

```powershell
# Avec logs détaillés
ngrok http --url=agriweb-prod.ngrok-free.app 5000 --log=stdout --log-level=debug
```

---

## ✅ Checklist de vérification

- [ ] Flask tourne sur port 5000
- [ ] `http://localhost:5000` répond
- [ ] Ngrok lancé avec `ngrok http ... 5000`
- [ ] Dashboard ngrok accessible: `http://127.0.0.1:4040`
- [ ] URL publique fonctionne: `https://agriweb-prod.ngrok-free.app`
- [ ] Autocomplétion testée via l'URL publique

---

## 🎯 Commande finale (une seule ligne)

**La commande correcte à utiliser:**
```powershell
ngrok http --url=agriweb-prod.ngrok-free.app 5000
```

**PAS:**
```powershell
ngrok http --url=agriweb-prod.ngrok-free.app 80  # ❌ INCORRECT
```

---

**Version:** 1.0.0  
**Date:** Octobre 2025  
**Pour:** AgriWeb Production
