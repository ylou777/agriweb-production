# 🔧 FIX NGROK - Mise à jour vers v3

## Problème identifié

Vous utilisez **ngrok v2.3.41** qui n'a pas le flag `--url`.
Le flag `--url` a été introduit dans **ngrok v3+**.

```
❌ Votre version: v2.3.41
✅ Version recommandée: v3.x (dernière)
```

---

## 🚀 Solution Rapide (Utiliser --hostname)

**Pour votre version actuelle (v2.x), utilisez `--hostname` :**

```powershell
.\ngrok http --hostname=agriweb-prod.ngrok-free.app 5000
```

C'est l'équivalent de `--url` dans l'ancienne version.

---

## 📥 Mise à jour vers ngrok v3 (RECOMMANDÉ)

### Méthode 1: Téléchargement direct

1. **Télécharger ngrok v3:**
   - Allez sur https://ngrok.com/download
   - Téléchargez la version Windows (64-bit)
   - Extrayez `ngrok.exe`

2. **Remplacer l'ancien fichier:**
   ```powershell
   # Sauvegarder l'ancien
   Move-Item .\ngrok.exe .\ngrok.exe.old -Force
   
   # Placer le nouveau ngrok.exe dans le dossier AgW3b
   # (glissez-déposez ou copiez le fichier téléchargé)
   ```

3. **Vérifier la version:**
   ```powershell
   .\ngrok version
   # Devrait afficher: ngrok version 3.x.x
   ```

### Méthode 2: Winget (si disponible)

```powershell
# Désinstaller l'ancienne version
winget uninstall ngrok

# Installer la nouvelle
winget install ngrok
```

---

## ✅ Commandes correctes selon la version

### Ngrok v2 (votre version actuelle)
```powershell
.\ngrok http --hostname=agriweb-prod.ngrok-free.app 5000
```

### Ngrok v3 (après mise à jour)
```powershell
.\ngrok http --url=agriweb-prod.ngrok-free.app 5000
# OU simplement
.\ngrok http --domain=agriweb-prod.ngrok-free.app 5000
```

---

## 🔍 Vérifier votre configuration ngrok

```powershell
# Voir la version
.\ngrok version

# Voir les options disponibles
.\ngrok http --help

# Lister vos domaines/réserved domains
.\ngrok api reserved-domains list
```

---

## 📝 Script de démarrage mis à jour

Pour ngrok v2 (votre version actuelle):

```powershell
# Arrêter les processus existants
Get-Process python,ngrok -ErrorAction SilentlyContinue | Stop-Process -Force

# Démarrer Flask
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\.venv\Scripts\Activate.ps1; python agriweb_hebergement_gratuit.py"

# Attendre que Flask démarre
Start-Sleep -Seconds 10

# Démarrer ngrok avec --hostname (v2)
.\ngrok http --hostname=agriweb-prod.ngrok-free.app 5000
```

---

## 🎯 Commande finale pour VOUS

**Utilisez cette commande maintenant (compatible v2) :**

```powershell
.\ngrok http --hostname=agriweb-prod.ngrok-free.app 5000
```

---

## 📊 Comparaison v2 vs v3

| Fonctionnalité | ngrok v2 | ngrok v3 |
|----------------|----------|----------|
| **Flag domaine réservé** | `--hostname` | `--url` ou `--domain` |
| **API** | v2 | v3 (améliorée) |
| **Dashboard** | http://127.0.0.1:4040 | http://127.0.0.1:4040 |
| **Authentification** | Token dans commande | Token dans config |
| **Performance** | Bonne | Meilleure |
| **Support** | ⚠️ Fin de support | ✅ Actif |

---

## ⚠️ Important

Votre domaine `agriweb-prod.ngrok-free.app` est configuré dans votre compte ngrok. 
Que vous utilisiez v2 ou v3, le domaine fonctionnera, seule la syntaxe change.

---

**Commande à exécuter MAINTENANT:**

```powershell
.\ngrok http --hostname=agriweb-prod.ngrok-free.app 5000
```

Vous devriez voir:
```
Session Status                online
Account                       ylou777 (Plan: Pay-as-you-go)
Forwarding                    https://agriweb-prod.ngrok-free.app -> http://localhost:5000
```

✅ Si vous voyez cela, c'est bon ! Le tunnel est actif.
