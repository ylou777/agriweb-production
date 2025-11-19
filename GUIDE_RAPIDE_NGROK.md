# ⚡ GUIDE RAPIDE - Démarrage AgriWeb + Ngrok

## 🎯 Commandes essentielles

### 1️⃣ Démarrer TOUT automatiquement (RECOMMANDÉ)

```powershell
.\start_with_ngrok.ps1
```

✅ **Ce script fait tout pour vous :**
- Arrête les anciens processus
- Vérifie l'environnement
- Démarre Flask sur port 5000
- Démarre Ngrok avec la bonne syntaxe (v2 ou v3)
- Ouvre le dashboard
- Affiche toutes les URLs

---

### 2️⃣ Démarrage manuel (étape par étape)

**Terminal 1 - Flask :**
```powershell
.\.venv\Scripts\Activate.ps1
python agriweb_hebergement_gratuit.py
```

**Terminal 2 - Ngrok :**
```powershell
# Pour ngrok v2 (votre version actuelle)
.\ngrok http --hostname=agriweb-prod.ngrok-free.app 5000

# Pour ngrok v3 (après mise à jour)
.\ngrok http --url=agriweb-prod.ngrok-free.app 5000
```

---

## 🌐 URLs d'accès

Une fois démarré, votre application est accessible sur :

| Type | URL | Description |
|------|-----|-------------|
| **Local** | http://localhost:5000 | Accès depuis votre PC |
| **Public** | https://agriweb-prod.ngrok-free.app | Accès depuis internet |
| **Dashboard** | http://127.0.0.1:4040 | Stats et logs ngrok |
| **Démo auto** | http://localhost:5000/demo/autocomplete | Tester l'autocomplétion |

---

## 🧪 Tester l'autocomplétion

### En local
```powershell
# Ouvrir dans le navigateur
start http://localhost:5000/demo/autocomplete

# Tester l'API adresses
curl http://localhost:5000/api/autocomplete/address?q=montiers

# Tester l'API communes
curl http://localhost:5000/api/autocomplete/commune?q=verdun
```

### Via ngrok (public)
```powershell
# Ouvrir dans le navigateur
start https://agriweb-prod.ngrok-free.app/demo/autocomplete

# Tester l'API
curl https://agriweb-prod.ngrok-free.app/api/autocomplete/commune?q=verdun
```

---

## 🛑 Arrêter tout

```powershell
# Arrêter Flask et Ngrok
Get-Process python,ngrok | Stop-Process -Force

# OU fermer les fenêtres PowerShell manuellement
```

---

## 🔍 Dépannage rapide

### Problème : Ngrok erreur "--url not defined"

**Cause :** Vous utilisez ngrok v2

**Solution :**
```powershell
# Utilisez --hostname au lieu de --url
.\ngrok http --hostname=agriweb-prod.ngrok-free.app 5000
```

### Problème : Port 5000 déjà utilisé

**Solution :**
```powershell
# Trouver et arrêter le processus
netstat -ano | findstr :5000
# Notez le PID et faites :
Stop-Process -Id <PID> -Force
```

### Problème : 502 Bad Gateway sur ngrok

**Causes possibles :**
1. Flask ne tourne pas
2. Mauvais port (80 au lieu de 5000)

**Solution :**
```powershell
# Vérifier que Flask répond
curl http://localhost:5000

# Redémarrer Flask si besoin
python agriweb_hebergement_gratuit.py
```

---

## 📁 Fichiers utiles

| Fichier | Description |
|---------|-------------|
| `start_with_ngrok.ps1` | 🚀 Script de démarrage automatique |
| `NGROK_CONFIGURATION.md` | 📖 Guide complet ngrok |
| `FIX_NGROK_VERSION.md` | 🔧 Fix problème version ngrok |
| `GUIDE_RAPIDE_NGROK.md` | ⚡ Ce fichier |

---

## ✅ Checklist de vérification

Après avoir lancé `.\start_with_ngrok.ps1`, vérifiez :

- [ ] Flask répond sur http://localhost:5000
- [ ] Dashboard ngrok accessible : http://127.0.0.1:4040
- [ ] URL publique fonctionne : https://agriweb-prod.ngrok-free.app
- [ ] Autocomplétion fonctionne en local
- [ ] Autocomplétion fonctionne via ngrok
- [ ] Pas d'erreur 502 Bad Gateway

---

## 🎓 Exemples de recherche

Une fois l'application accessible, testez l'autocomplétion :

**Communes avec fautes :**
- `montiers d'ahun` → **Moutiers-d'Ahun**
- `verdun` → plusieurs Verdun
- `saint etienne` → **Saint-Étienne**

**Par code postal :**
- `23150` → **Moutiers-d'Ahun**
- `75001` → **Paris 1er**

**Adresses :**
- `10 rue paix pari` → **10 Rue de la Paix Paris**
- `lyon` → adresses à Lyon

---

## 📞 Commandes de diagnostic

```powershell
# Version ngrok
.\ngrok version

# Voir les tunnels actifs
curl http://127.0.0.1:4040/api/tunnels | ConvertFrom-Json

# Ports en écoute
netstat -ano | findstr "LISTENING"

# Processus Flask
Get-Process python | Where-Object {$_.Path -like "*AgW3b*"}

# Processus Ngrok
Get-Process ngrok
```

---

## 🚀 One-liner complet

Tout en une seule commande (pour les experts) :

```powershell
Get-Process python,ngrok -EA SilentlyContinue | Stop-Process -Force; Start-Sleep 2; Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$PWD'; .\.venv\Scripts\Activate.ps1; python agriweb_hebergement_gratuit.py"; Start-Sleep 10; Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$PWD'; .\ngrok http --hostname=agriweb-prod.ngrok-free.app 5000"
```

---

**Version:** 1.0.0  
**Date:** Octobre 2025  
**Pour:** AgriWeb avec Autocomplétion

🎉 **Votre application est prête à être déployée !**
