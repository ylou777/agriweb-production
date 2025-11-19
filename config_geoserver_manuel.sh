#!/usr/bin/env bash
"""
🔧 CONFIGURATION RAPIDE GEOSERVER
Guide pas-à-pas pour configurer GeoServer avec vos couches AgriWeb
"""

# Guide de configuration manuelle si l'installation automatique ne fonctionne pas

echo "🔧 CONFIGURATION MANUELLE GEOSERVER"
echo "=================================="
echo ""

echo "📋 ÉTAPES DE CONFIGURATION:"
echo ""

echo "1️⃣ TÉLÉCHARGEMENT MANUEL:"
echo "   - Allez sur: https://geoserver.org/release/stable/"
echo "   - Téléchargez: 'Web Archive (.war)'"
echo "   - Sauvegardez comme: geoserver.war"
echo ""

echo "2️⃣ DÉPLOIEMENT DANS TOMCAT:"
echo "   - Localisez votre dossier Tomcat"
echo "   - Copiez geoserver.war dans: tomcat/webapps/"
echo "   - Redémarrez Tomcat"
echo "   - Attendez le déploiement (1-2 minutes)"
echo ""

echo "3️⃣ PREMIÈRE CONNEXION:"
echo "   - URL: http://localhost:8080/geoserver/web/"
echo "   - Login: admin"
echo "   - Password: geoserver"
echo ""

echo "4️⃣ CONFIGURATION AGRIWEB:"
echo "   - Créez le workspace: 'gpu'"
echo "   - Importez vos données (voir guide détaillé)"
echo "   - Configurez les couches selon vos besoins"
echo ""

echo "📖 Pour la configuration détaillée des 14 couches AgriWeb,"
echo "   consultez: GUIDE_GEOSERVER_CONFIGURATION.md"
echo ""

echo "🚨 PROBLÈMES COURANTS:"
echo "   - Si port 8080 occupé: modifiez server.xml de Tomcat"
echo "   - Si déploiement échoue: vérifiez logs/catalina.out"
echo "   - Si login refuse: utilisez admin/geoserver"
echo ""

read -p "▶️ Appuyez sur ENTRÉE pour continuer..."
