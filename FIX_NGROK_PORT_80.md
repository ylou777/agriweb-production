# 🚨 FIX URGENT - Ngrok redirige vers port 80 au lieu de 5000

## Problème observé

```
Forwarding: http://agriweb-prod.ngrok-free.app -> http://localhost:80 ❌
                                                                      ^^^ MAUVAIS PORT
```

**Devrait être :**
```
Forwarding: http://agriweb-prod.ngrok-free.app -> http://localhost:5000 ✅
```

---

## 🔧 Solutions (dans l'ordre de priorité)

### Solution 1: Arrêter TOUS les ngrok et redémarrer proprement

```powershell
# 1. Arrêter TOUS les processus ngrok
Get-Process ngrok -ErrorAction SilentlyContinue | Stop-Process -Force

# 2. Attendre 2 secondes
Start-Sleep -Seconds 2

# 3. Vérifier qu'il n'y en a plus
Get-Process ngrok -ErrorAction SilentlyContinue

# 4. Relancer avec le BON port
.\ngrok http --hostname=agriweb-prod.ngrok-free.app 5000
```

---

### Solution 2: Vérifier et supprimer la config ngrok par défaut

Le problème peut venir d'un fichier de configuration ngrok qui force le port 80.

```powershell
# Trouver le fichier de config ngrok
$ngrokConfig = "$env:USERPROFILE\.ngrok2\ngrok.yml"

# Vérifier s'il existe
if (Test-Path $ngrokConfig) {
    Write-Host "Config trouvée: $ngrokConfig"
    notepad $ngrokConfig
} else {
    Write-Host "Pas de config ngrok trouvée (normal)"
}
```

**Si le fichier existe, cherchez une section comme :**
```yaml
tunnels:
  agriweb-prod:
    addr: 80  # ← CECI EST LE PROBLÈME
    proto: http
```

**Modifiez-la en :**
```yaml
tunnels:
  agriweb-prod:
    addr: 5000  # ← CORRECTION
    proto: http
    hostname: agriweb-prod.ngrok-free.app
```

---

### Solution 3: Utiliser une URL différente temporairement

Si le domaine `agriweb-prod.ngrok-free.app` est "bloqué" sur port 80 :

```powershell
# Générer une URL aléatoire (gratuite)
.\ngrok http 5000

# Vous obtiendrez une URL comme:
# https://abc123.ngrok-free.app -> http://localhost:5000
```

---

### Solution 4: Réinitialiser complètement ngrok

```powershell
# 1. Arrêter tous les ngrok
Get-Process ngrok -EA SilentlyContinue | Stop-Process -Force

# 2. Supprimer la config ngrok
Remove-Item "$env:USERPROFILE\.ngrok2" -Recurse -Force -EA SilentlyContinue

# 3. Reconfigurer avec votre authtoken
.\ngrok authtoken VOTRE_TOKEN_ICI

# 4. Relancer
.\ngrok http --hostname=agriweb-prod.ngrok-free.app 5000
```

---

## 🎯 Commande DÉFINITIVE à utiliser

**Pour ngrok v2 (votre version):**

```powershell
# Arrêter tout d'abord
Get-Process ngrok -EA SilentlyContinue | Stop-Process -Force
Start-Sleep 2

# Puis lancer proprement
.\ngrok http --hostname=agriweb-prod.ngrok-free.app 5000
```

**Vous DEVEZ voir :**
```
Forwarding    https://agriweb-prod.ngrok-free.app -> http://localhost:5000
                                                                      ^^^^ BON PORT!
```

---

## 🔍 Vérification après démarrage

```powershell
# 1. Vérifier que Flask répond sur 5000
curl http://localhost:5000

# 2. Vérifier le dashboard ngrok
start http://127.0.0.1:4040

# 3. Dans le dashboard, vérifiez la section "Forwarding":
# Doit indiquer: http://localhost:5000
```

---

## 🐛 Si le problème persiste

### Option A: Configuration du domaine sur le site ngrok

1. Allez sur https://dashboard.ngrok.com/cloud-edge/domains
2. Trouvez `agriweb-prod.ngrok-free.app`
3. Vérifiez qu'il n'y a pas de configuration "Target" fixée à 80
4. Supprimez toute configuration spécifique

### Option B: Utiliser un nouveau domaine

Sur https://dashboard.ngrok.com/cloud-edge/domains :
1. Créez un nouveau domaine (ex: `agriweb2.ngrok-free.app`)
2. Utilisez-le dans la commande :
   ```powershell
   .\ngrok http --hostname=agriweb2.ngrok-free.app 5000
   ```

---

## 📝 Script de démarrage correct

Créez `start_ngrok_fixed.ps1`:

```powershell
# Arrêter TOUT
Write-Host "🛑 Arrêt de tous les processus..." -ForegroundColor Yellow
Get-Process python,ngrok -EA SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3

# Démarrer Flask
Write-Host "🚀 Démarrage Flask sur port 5000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\.venv\Scripts\Activate.ps1; python agriweb_hebergement_gratuit.py"

# Attendre Flask
Write-Host "⏳ Attente Flask (10 secondes)..." -ForegroundColor Gray
Start-Sleep -Seconds 10

# Vérifier Flask
Write-Host "🔍 Vérification Flask..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ Flask OK (port 5000)" -ForegroundColor Green
} catch {
    Write-Host "❌ Flask ne répond pas!" -ForegroundColor Red
    exit 1
}

# Démarrer Ngrok avec le BON port
Write-Host "🌐 Démarrage Ngrok vers port 5000..." -ForegroundColor Cyan
Write-Host "   Domaine: agriweb-prod.ngrok-free.app" -ForegroundColor Gray
Write-Host "   Port cible: 5000" -ForegroundColor Gray

.\ngrok http --hostname=agriweb-prod.ngrok-free.app 5000

# Le script s'arrête ici car ngrok est au premier plan
```

---

## ✅ Vérification finale

Après avoir lancé ngrok, vous **DEVEZ** voir dans le terminal:

```
Session Status                online
Account                       ylou777 (Plan: Pay-as-you-go)
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://agriweb-prod.ngrok-free.app -> http://localhost:5000
                                                                                      ^^^^
                                                                              VÉRIFIEZ CE NUMÉRO!
```

**Si vous voyez `80` au lieu de `5000`, recommencez Solution 1.**

---

## 🚨 IMPORTANT

Le problème vient probablement du fait que vous avez plusieurs processus ngrok qui tournent, ou qu'il y a une configuration persistante.

**Essayez cette commande MAINTENANT:**

```powershell
Get-Process ngrok -EA SilentlyContinue | Stop-Process -Force; Start-Sleep 3; .\ngrok http --hostname=agriweb-prod.ngrok-free.app 5000
```

Et **vérifiez bien** que la ligne "Forwarding" indique `localhost:5000` et non `localhost:80`.

---

**Date:** Octobre 2025  
**Status:** 🚨 FIX URGENT
