# ✅ SOLUTION DÉFINITIVE - Ngrok Port 5000

## 🎯 Le problème

Ngrok continue de rediriger vers le port **80** au lieu du port **5000** :
```
❌ Forwarding: https://agriweb-prod.ngrok-free.app -> http://localhost:80
✅ Devrait être: https://agriweb-prod.ngrok-free.app -> http://localhost:5000
```

---

## 🚀 SOLUTION RAPIDE (Copy-Paste)

**Exécutez ces 3 commandes dans PowerShell :**

```powershell
# 1. Arrêter TOUS les ngrok
Get-Process ngrok -EA SilentlyContinue | Stop-Process -Force; Start-Sleep 3

# 2. Vérifier que Flask tourne
curl http://localhost:5000

# 3. Lancer ngrok sur le BON port
.\ngrok http --hostname=agriweb-prod.ngrok-free.app 5000
```

**Vous DEVEZ voir :**
```
Forwarding    https://agriweb-prod.ngrok-free.app -> http://localhost:5000
                                                                      ^^^^
                                                                  BON PORT!
```

---

## 📝 OU utilisez le script automatique

```powershell
.\start_ngrok_fixed.ps1
```

Ce script :
- ✅ Arrête tous les ngrok existants
- ✅ Vérifie que Flask répond sur 5000
- ✅ Lance ngrok avec le bon port
- ✅ Affiche des instructions claires

---

## 🔍 Pourquoi ça arrive ?

Plusieurs causes possibles :

### 1. Plusieurs processus ngrok
Vous avez peut-être plusieurs ngrok qui tournent, dont un ancien qui utilise port 80.

**Solution :**
```powershell
Get-Process ngrok | Stop-Process -Force
```

### 2. Configuration ngrok persistante
Un fichier `ngrok.yml` qui force le port 80.

**Vérifier :**
```powershell
notepad "$env:USERPROFILE\.ngrok2\ngrok.yml"
```

**Si vous voyez :**
```yaml
tunnels:
  agriweb-prod:
    addr: 80  # ← PROBLÈME ICI
```

**Changez en :**
```yaml
tunnels:
  agriweb-prod:
    addr: 5000  # ← CORRECTION
```

### 3. Configuration du domaine sur ngrok.com
Le domaine `agriweb-prod.ngrok-free.app` a peut-être une configuration "Target" sur le dashboard ngrok.

**Vérifier sur :**
https://dashboard.ngrok.com/cloud-edge/domains

**Cherchez :** agriweb-prod.ngrok-free.app  
**Vérifiez :** Qu'il n'y a pas de "Target URL" ou "Backend" forcé à 80

---

## ✅ Checklist de vérification

Après avoir lancé ngrok, vérifiez :

- [ ] Dans le terminal ngrok, ligne "Forwarding" indique `localhost:5000` (PAS 80)
- [ ] Dashboard ngrok : http://127.0.0.1:4040
- [ ] Dans le dashboard, section "Status" → "Tunnel Details" → Port = 5000
- [ ] Test local : `curl http://localhost:5000` → ✅
- [ ] Test public : `curl https://agriweb-prod.ngrok-free.app` → ✅ (pas 502)

---

## 🧪 Tests après démarrage

```powershell
# Test 1: Local (doit marcher)
curl http://localhost:5000

# Test 2: Via ngrok (doit marcher maintenant)
curl https://agriweb-prod.ngrok-free.app

# Test 3: Autocomplétion
curl "https://agriweb-prod.ngrok-free.app/api/autocomplete/commune?q=verdun"
```

**Si Test 2 donne encore 502 :**
- Ngrok redirige toujours vers port 80
- Recommencez la solution rapide ci-dessus

---

## 🔄 Workflow complet

### Terminal 1 - Flask
```powershell
cd C:\Users\Utilisateur\Desktop\AG32.1\ag3reprise\AgW3b
.\.venv\Scripts\Activate.ps1
python agriweb_hebergement_gratuit.py
```

**Attendez de voir :**
```
🚀 Démarrage AgriWeb sur 0.0.0.0:5000
```

### Terminal 2 - Ngrok
```powershell
cd C:\Users\Utilisateur\Desktop\AG32.1\ag3reprise\AgW3b

# Arrêter tout
Get-Process ngrok -EA SilentlyContinue | Stop-Process -Force
Start-Sleep 3

# Lancer proprement
.\ngrok http --hostname=agriweb-prod.ngrok-free.app 5000
```

**Attendez de voir :**
```
Forwarding    https://agriweb-prod.ngrok-free.app -> http://localhost:5000
```

---

## 🐛 Dépannage avancé

### Si ngrok force toujours port 80

**Option 1: Supprimer la config ngrok**
```powershell
Remove-Item "$env:USERPROFILE\.ngrok2\ngrok.yml" -Force -EA SilentlyContinue
```

**Option 2: Utiliser un tunnel sans domaine réservé**
```powershell
# Générer une URL aléatoire (teste que ngrok marche bien)
.\ngrok http 5000
# Vous obtiendrez: https://xyz123.ngrok-free.app -> http://localhost:5000
```

**Option 3: Forcer avec authtoken**
```powershell
.\ngrok http --authtoken=VOTRE_TOKEN --hostname=agriweb-prod.ngrok-free.app 5000
```

### Si vous voyez "tunnel not found" ou "unauthorized"

Votre domaine `agriweb-prod.ngrok-free.app` n'est peut-être plus actif.

**Vérifier sur :**
https://dashboard.ngrok.com/cloud-edge/domains

**Ou créer un nouveau domaine :**
1. Allez sur le dashboard
2. Cloud Edge → Domains
3. "+ New Domain"
4. Choisissez un nom (ex: agriweb2.ngrok-free.app)
5. Utilisez-le dans la commande

---

## 📊 Comparaison

| Situation | Forwarding | Status |
|-----------|-----------|--------|
| ❌ **Avant** | `-> http://localhost:80` | 502 Bad Gateway |
| ✅ **Après** | `-> http://localhost:5000` | 200 OK |

---

## 💡 Astuce Pro

Pour éviter ce problème à l'avenir, créez un alias dans votre profil PowerShell :

```powershell
# Ouvrir le profil
notepad $PROFILE

# Ajouter cette ligne
function Start-AgriwebNgrok {
    Get-Process ngrok -EA SilentlyContinue | Stop-Process -Force
    Start-Sleep 2
    Set-Location "C:\Users\Utilisateur\Desktop\AG32.1\ag3reprise\AgW3b"
    .\ngrok http --hostname=agriweb-prod.ngrok-free.app 5000
}

# Sauvegarder et fermer

# Recharger le profil
. $PROFILE
```

**Utilisation :**
```powershell
Start-AgriwebNgrok
```

---

## 📞 Commandes de diagnostic

```powershell
# 1. Voir tous les processus ngrok
Get-Process ngrok

# 2. Voir les ports en écoute
netstat -ano | findstr "LISTENING" | findstr ":5000"

# 3. Vérifier l'API ngrok local
curl http://127.0.0.1:4040/api/tunnels | ConvertFrom-Json | Select -Expand tunnels | Select public_url, config

# 4. Tester Flask directement
Invoke-WebRequest http://localhost:5000 | Select StatusCode
```

---

## ✅ Confirmation finale

Quand tout fonctionne, vous devriez voir :

**Dans le terminal ngrok :**
```
Session Status                online
Forwarding                    https://agriweb-prod.ngrok-free.app -> http://localhost:5000
```

**Dans le navigateur (https://agriweb-prod.ngrok-free.app) :**
- ✅ Page d'accueil AgriWeb s'affiche
- ✅ Pas d'erreur 502 Bad Gateway
- ✅ Autocomplétion fonctionne

---

**Version :** 1.1.0  
**Date :** Octobre 2025  
**Status :** ✅ SOLUTION VALIDÉE

🎉 **Votre tunnel ngrok est maintenant correctement configuré !**
