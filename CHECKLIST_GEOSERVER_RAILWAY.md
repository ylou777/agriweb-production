📋 CHECKLIST CONFIGURATION GEOSERVER POUR RAILWAY
=====================================================

🎯 OBJECTIF: Permettre à Railway d'accéder à votre GeoServer sans blocage

⚠️ PROBLÈME IDENTIFIÉ:
Votre protection anti-bruteforce GeoServer va bloquer Railway !

🛠️ ACTIONS IMMÉDIATES REQUISES:

┌─────────────────────────────────────────────────────────────┐
│ ÉTAPE 1: OBTENIR L'IP RAILWAY                              │
└─────────────────────────────────────────────────────────────┘

1. Déployez votre app sur Railway avec le nouvel endpoint
2. Visitez: https://votre-app.railway.app/debug/my-ip  
3. Notez l'IP affichée (ex: 52.1.2.3)

┌─────────────────────────────────────────────────────────────┐
│ ÉTAPE 2: CONFIGURER GEOSERVER (CRITIQUE)                   │
└─────────────────────────────────────────────────────────────┘

🔧 Dans GeoServer Admin Panel:

1. Aller à: Security → Authentication
2. Section "Paramètres de prévention des attaques en force brute"
3. Masques de réseau exclus: 
   AVANT: 127.0.0.1
   APRÈS: 127.0.0.1,IP_RAILWAY

   Exemple: 127.0.0.1,52.1.2.3

4. Cliquer "Appliquer" et "Sauvegarder"

┌─────────────────────────────────────────────────────────────┐
│ ÉTAPE 3: CONFIGURER L'UTILISATEUR RAILWAY                  │
└─────────────────────────────────────────────────────────────┘

🔧 Dans GeoServer Admin Panel:

1. Aller à: Security → Users, Groups, Roles
2. Créer utilisateur: railway_user
3. Mot de passe: [fort et sécurisé]
4. Assigner role: ROLE_READER (pas ADMIN!)

🔧 Permissions:

1. Security → Services
   - WMS: ROLE_READER (READ)
   - WFS: ROLE_READER (READ) 
   - WCS: ROLE_READER (READ)

2. Security → Data
   - Workspace: * (tous)
   - Access mode: READ
   - Role: ROLE_READER

┌─────────────────────────────────────────────────────────────┐
│ ÉTAPE 4: CONFIGURER PROXY BASE URL                         │
└─────────────────────────────────────────────────────────────┘

🔧 Dans GeoServer Admin Panel:

1. Aller à: Settings → Global
2. Proxy Base URL: http://81.220.178.156:8080/geoserver
   (ou votre URL publique réelle)
3. Sauvegarder

┌─────────────────────────────────────────────────────────────┐
│ ÉTAPE 5: VARIABLES RAILWAY                                  │
└─────────────────────────────────────────────────────────────┘

PowerShell/Terminal:
railway variables set GEOSERVER_URL=http://81.220.178.156:8080/geoserver
railway variables set GEOSERVER_USERNAME=railway_user  
railway variables set GEOSERVER_PASSWORD=votre_mot_de_passe_fort

┌─────────────────────────────────────────────────────────────┐
│ ÉTAPE 6: TEST FINAL                                         │
└─────────────────────────────────────────────────────────────┘

1. Déployez avec les nouvelles variables
2. Surveillez les logs Railway
3. Testez vos fonctionnalités cartographiques

🚨 ALERTES IMPORTANTES:

❌ SANS l'IP Railway dans les masques exclus:
   → Railway sera bloqué après 3-5 erreurs d'auth
   → Timeouts et erreurs 403/401 récurrents

❌ SANS utilisateur railway_user:
   → Échecs d'authentification constants
   → Fonctionnalités cartes ne marcheront pas

❌ SANS Proxy Base URL:
   → Links incorrects dans GetCapabilities
   → Problèmes d'affichage des couches

✅ AVEC configuration complète:
   → Accès stable depuis Railway
   → Pas de blocages
   → Cartes fonctionnelles

💡 ALTERNATIVES SI PROBLÈMES:

1. Désactiver temporairement la protection anti-bruteforce
   (moins sécurisé mais évite les blocages)

2. Acheter Static IP Railway ($5/mois)
   (IP fixe garantie, plus facile à whitelister)

3. Configurer reverse proxy HTTPS avec domaine
   (plus professionnel, meilleure sécurité)

⏰ TEMPS ESTIMÉ: 15-20 minutes
🎯 PRIORITÉ: CRITIQUE - À faire immédiatement

Une fois terminé, votre Railway pourra accéder à GeoServer
sans risque de blocage par la protection anti-bruteforce !
