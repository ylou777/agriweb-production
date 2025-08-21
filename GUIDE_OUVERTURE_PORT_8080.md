# Guide pour ouvrir le port 8080 dans votre routeur

## 🎯 Objectif
Permettre à Railway d'accéder à votre GeoServer local via Internet en ouvrant le port 8080.

## 📋 Informations nécessaires
- **IP publique**: `81.220.178.156` ✅
- **IP locale de votre PC**: À déterminer
- **Port à ouvrir**: `8080`
- **Service**: GeoServer

## 🔍 Étape 1: Trouver l'IP locale de votre PC

Ouvrez PowerShell et tapez:
```powershell
ipconfig | findstr "IPv4"
```

Vous devriez voir quelque chose comme:
```
IPv4 Address. . . . . . . . . . . : 192.168.1.XXX
```

## 🌐 Étape 2: Accéder à votre routeur

1. Ouvrez votre navigateur
2. Tapez l'une de ces adresses (selon votre fournisseur):
   - `http://192.168.1.1` (le plus courant)
   - `http://192.168.0.1`
   - `http://10.0.0.1`

3. Connectez-vous avec vos identifiants administrateur

## ⚙️ Étape 3: Configuration du port forwarding

### Pour la plupart des routeurs:

1. **Cherchez la section**: "Port Forwarding", "Redirection de ports", "NAT" ou "Applications et Gaming"

2. **Créez une nouvelle règle**:
   - **Nom**: `GeoServer`
   - **Protocole**: `TCP`
   - **Port externe**: `8080`
   - **IP interne**: `192.168.1.XXX` (votre IP locale trouvée à l'étape 1)
   - **Port interne**: `8080`
   - **État**: `Activé`

3. **Sauvegardez** et **redémarrez** le routeur si nécessaire

### Selon votre fournisseur:

#### 🟦 **Freebox**:
- Allez dans "Paramètres de la Freebox" > "Mode avancé" > "Redirections de ports"

#### 🟠 **Orange (Livebox)**:
- Allez dans "Réseau" > "NAT/PAT" > "Ajouter une règle"

#### 🟣 **SFR Box**:
- Allez dans "Réseau" > "NAT/PAT" > "Jeux et Applications"

#### 🔵 **Bouygues**:
- Allez dans "Advanced" > "Port Forwarding"

## 🔒 Étape 4: Configuration du firewall Windows

Ouvrez PowerShell en tant qu'administrateur et tapez:

```powershell
# Autoriser le port 8080 entrant
New-NetFirewallRule -DisplayName "GeoServer-8080" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow

# Vérifier la règle
Get-NetFirewallRule -DisplayName "GeoServer-8080"
```

## ✅ Étape 5: Test de connectivité

Une fois configuré, testez avec:

```powershell
# Depuis votre PC, tester l'accès externe
curl -I http://81.220.178.156:8080/geoserver/
```

## 🚨 Sécurité importante

⚠️ **Ouvrir un port expose votre GeoServer à Internet. Assurez-vous que:**
- Le mot de passe admin de GeoServer est fort
- Vous avez désactivé l'anti-bruteforce (déjà fait ✅)
- Vous surveillez les logs de connexion

## 🔧 Alternative: Changer le port GeoServer

Si vous ne pouvez pas ouvrir le port 8080, vous pouvez:

1. **Configurer GeoServer sur le port 80** (souvent ouvert par défaut)
2. **Utiliser le port 443** (HTTPS, généralement ouvert)

## 📞 Support par fournisseur

- **Freebox**: https://www.free.fr/assistance/
- **Orange**: 3900
- **SFR**: 1023  
- **Bouygues**: 1064

## 🎉 Après configuration

Une fois le port ouvert, Railway pourra accéder à votre GeoServer avec:
```
GEOSERVER_URL=http://81.220.178.156:8080/geoserver
GEOSERVER_USERNAME=admin
GEOSERVER_PASSWORD=geoserver
ENVIRONMENT=production
```
