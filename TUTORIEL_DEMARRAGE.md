# 🚀 TUTORIEL DE DÉMARRAGE - AgriWeb Application

## 📋 Vue d'ensemble
Ce guide vous explique comment démarrer votre application AgriWeb avec toutes ses fonctionnalités :
- Application web Flask
- Tunnel ngrok pour GeoServer
- Interface d'administration
- Gestion des cartes et données géographiques

---

## ⚡ DÉMARRAGE RAPIDE (3 étapes)

### 1️⃣ **Démarrer GeoServer** (Terminal 1)
```bash
# Aller dans le répertoire GeoServer et le démarrer
cd "chemin/vers/geoserver/bin"
./startup.sh    # Linux/Mac
# ou
startup.bat     # Windows
```
**📍 GeoServer sera accessible sur :** `http://localhost:8080/geoserver`

### 2️⃣ **Démarrer le tunnel ngrok** (Terminal 2)
```bash
cd "C:\Users\Utilisateur\Desktop\AG32.1\ag3reprise\AgW3b"
python ngrok_manager.py
```
**✅ Résultat attendu :**
```
🎯 Gestionnaire ngrok automatique
✅ Tunnel prêt: https://xxxxxxxxx.ngrok-free.app
📝 Application mise à jour: https://xxxxxxxxx.ngrok-free.app/geoserver
🔄 Tunnel actif - gardez cette fenêtre ouverte
```

### 3️⃣ **Démarrer l'application AgriWeb** (Terminal 3)
```bash
cd "C:\Users\Utilisateur\Desktop\AG32.1\ag3reprise\AgW3b"

# Activer l'environnement virtuel
.venv\Scripts\Activate.ps1

# Démarrer l'application
python agriweb_hebergement_gratuit.py
```
**✅ Résultat attendu :**
```
✅ GeoServer accessible: https://xxxxxxxxx.ngrok-free.app/geoserver
🔄 Démarrage du serveur Flask...
* Running on http://127.0.0.1:5000
```

---

## 🌐 ACCÈS AUX APPLICATIONS

### 🏠 **Application principale**
- **URL locale :** http://localhost:5000
- **URL Railway :** https://aware-surprise-production.up.railway.app/

### 👑 **Interface d'administration**
- **URL :** http://localhost:5000/admin
- **Login :** admin@test.com
- **Mot de passe :** admin123

### 🗺️ **GeoServer (données géographiques)**
- **Local :** http://localhost:8080/geoserver
- **Via ngrok :** https://xxxxxxxxx.ngrok-free.app/geoserver

---

## 📁 STRUCTURE DES FICHIERS

```
AgW3b/
├── 📄 agriweb_hebergement_gratuit.py    # Application principale
├── 🔧 ngrok_manager.py                  # Gestionnaire tunnel automatique
├── ⚙️ update_ngrok_url.py               # Mise à jour URL ngrok
├── 📋 restart-ngrok.ps1                 # Script redémarrage ngrok
├── 🗂️ static/                          # Fichiers CSS/JS/images
├── 🗂️ templates/                       # Templates HTML
└── 💾 agriweb_users.db                  # Base de données utilisateurs
```

---

## 🔧 SCRIPTS UTILES

### 🚀 **Démarrage automatique complet**
```bash
# Script PowerShell pour tout démarrer en une fois
# À créer : start_all.ps1

# Terminal 1 : GeoServer (à adapter selon votre installation)
Start-Process -FilePath "cmd" -ArgumentList "/c", "cd /d C:\geoserver\bin && startup.bat"

# Terminal 2 : Tunnel ngrok
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\Utilisateur\Desktop\AG32.1\ag3reprise\AgW3b'; python ngrok_manager.py"

# Attendre 10 secondes pour que ngrok démarre
Start-Sleep -Seconds 10

# Terminal 3 : Application AgriWeb
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\Utilisateur\Desktop\AG32.1\ag3reprise\AgW3b'; .venv\Scripts\Activate.ps1; python agriweb_hebergement_gratuit.py"
```

### 📊 **Vérification de l'état**
```bash
# Vérifier que tout fonctionne
python -c "
import requests
import json

# Test GeoServer local
try:
    r = requests.get('http://localhost:8080/geoserver', timeout=5)
    print(f'🗺️ GeoServer local: ✅ Status {r.status_code}')
except:
    print('🗺️ GeoServer local: ❌ Non accessible')

# Test ngrok tunnel
try:
    r = requests.get('http://localhost:4040/api/tunnels', timeout=3)
    data = r.json()
    for tunnel in data.get('tunnels', []):
        if tunnel.get('proto') == 'https':
            print(f'🔗 Tunnel ngrok: ✅ {tunnel.get(\"public_url\")}')
except:
    print('🔗 Tunnel ngrok: ❌ Non accessible')

# Test application
try:
    r = requests.get('http://localhost:5000', timeout=5)
    print(f'🌐 Application: ✅ Status {r.status_code}')
except:
    print('🌐 Application: ❌ Non accessible')
"
```

---

## 🛠️ RÉSOLUTION DE PROBLÈMES

### ❌ **Erreur : "Port 5000 already in use"**
```bash
# Trouver et arrêter le processus
netstat -ano | findstr :5000
taskkill /PID <PID_NUMBER> /F
```

### ❌ **Erreur : "GeoServer not accessible"**
```bash
# Vérifier que GeoServer est démarré
curl -I http://localhost:8080/geoserver
# Si erreur, redémarrer GeoServer
```

### ❌ **Erreur : "ngrok tunnel failed"**
```bash
# Redémarrer le gestionnaire ngrok
Ctrl+C  # Dans le terminal ngrok
python ngrok_manager.py
```

### ❌ **Erreur : "Module not found"**
```bash
# Réinstaller les dépendances
pip install -r requirements.txt
```

---

## 📱 FONCTIONNALITÉS DISPONIBLES

### 🗺️ **Cartes et données géographiques**
- Visualisation de parcelles agricoles
- Couches de données : bâtiments, toitures, réseaux
- Recherche par adresse
- Export PDF des rapports

### 👑 **Administration**
- Gestion des utilisateurs
- Statistiques de connexion
- Sessions actives (max 3 par utilisateur)
- Codes QR pour accès rapide

### 💳 **Paiements** (si activé)
- Intégration Stripe
- Gestion des abonnements
- Historique des transactions

---

## 🔄 ARRÊT PROPRE

### Pour arrêter tous les services :
1. **Application Flask :** `Ctrl+C` dans le terminal de l'app
2. **Tunnel ngrok :** `Ctrl+C` dans le terminal ngrok
3. **GeoServer :** Aller dans `geoserver/bin/` et exécuter `shutdown.sh` (Linux/Mac) ou `shutdown.bat` (Windows)

---

## 📞 SUPPORT

### 🆘 **En cas de problème :**
1. Vérifiez que tous les services sont démarrés
2. Consultez les logs dans les terminaux
3. Utilisez le script de vérification d'état
4. Redémarrez les services un par un

### 📋 **Logs utiles :**
- Application Flask : Affiché dans le terminal
- ngrok : Affiché dans le gestionnaire
- GeoServer : `geoserver/logs/geoserver.log`

---

## 🎯 URLS DE RÉFÉRENCE

| Service | URL Locale | URL Publique |
|---------|------------|--------------|
| **Application** | http://localhost:5000 | https://aware-surprise-production.up.railway.app |
| **Admin** | http://localhost:5000/admin | https://aware-surprise-production.up.railway.app/admin |
| **GeoServer** | http://localhost:8080/geoserver | https://xxxxxxxxx.ngrok-free.app/geoserver |
| **ngrok Dashboard** | http://localhost:4040 | - |

---

**🎉 Votre application AgriWeb est maintenant prête à l'emploi !**
