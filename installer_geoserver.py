#!/usr/bin/env python3
"""
🚀 INSTALLATION AUTOMATIQUE GEOSERVER
Script pour télécharger et installer GeoServer sur votre Tomcat
"""

import requests
import os
import zipfile
import shutil
from pathlib import Path

def download_geoserver():
    """Télécharge la dernière version stable de GeoServer"""
    
    print("📥 TÉLÉCHARGEMENT DE GEOSERVER")
    print("=" * 40)
    
    # URL de téléchargement GeoServer (version stable)
    geoserver_url = "https://sourceforge.net/projects/geoserver/files/GeoServer/2.24.1/geoserver-2.24.1-war.zip/download"
    
    print(f"🌐 Téléchargement depuis: {geoserver_url}")
    
    try:
        response = requests.get(geoserver_url, stream=True)
        response.raise_for_status()
        
        # Sauvegarde locale
        zip_path = "geoserver-war.zip"
        
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Téléchargement terminé: {zip_path}")
        return zip_path
        
    except Exception as e:
        print(f"❌ Erreur de téléchargement: {e}")
        return None

def extract_geoserver_war(zip_path):
    """Extrait le fichier WAR de GeoServer"""
    
    print("\n📂 EXTRACTION DU FICHIER WAR")
    print("=" * 30)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Chercher le fichier .war
            war_files = [f for f in zip_ref.namelist() if f.endswith('.war')]
            
            if war_files:
                war_file = war_files[0]
                print(f"📦 Fichier WAR trouvé: {war_file}")
                
                # Extraction
                zip_ref.extract(war_file, ".")
                
                # Renommer si nécessaire
                if war_file != "geoserver.war":
                    os.rename(war_file, "geoserver.war")
                
                print("✅ Extraction terminée: geoserver.war")
                return "geoserver.war"
            else:
                print("❌ Aucun fichier WAR trouvé dans l'archive")
                return None
                
    except Exception as e:
        print(f"❌ Erreur d'extraction: {e}")
        return None

def find_tomcat_webapps():
    """Trouve le dossier webapps de Tomcat"""
    
    print("\n🔍 RECHERCHE DU DOSSIER TOMCAT")
    print("=" * 32)
    
    # Emplacements communs de Tomcat sur Windows
    potential_paths = [
        "C:/Program Files/Apache Software Foundation/Tomcat 9.0/webapps",
        "C:/Program Files/Apache Software Foundation/Tomcat 10.0/webapps", 
        "C:/Program Files/Apache Software Foundation/Tomcat 10.1/webapps",
        "C:/apache-tomcat-9.0.95/webapps",
        "C:/apache-tomcat-10.0.27/webapps",
        "C:/apache-tomcat-10.1.30/webapps",
        "C:/tomcat/webapps",
        "C:/tomcat9/webapps",
        "C:/tomcat10/webapps"
    ]
    
    for path in potential_paths:
        if os.path.exists(path):
            print(f"✅ Tomcat trouvé: {path}")
            return path
    
    # Recherche manuelle
    print("⚠️ Tomcat non trouvé aux emplacements standards")
    print("\n📋 Veuillez localiser manuellement votre dossier webapps:")
    print("   1. Cherchez 'tomcat' dans C:/Program Files/")
    print("   2. Ou dans C:/ directement")
    print("   3. Le dossier doit contenir: webapps/")
    
    manual_path = input("\n📁 Entrez le chemin vers webapps (ou ENTER pour continuer): ").strip()
    
    if manual_path and os.path.exists(manual_path):
        return manual_path
    
    return None

def deploy_geoserver(war_path, webapps_path):
    """Déploie GeoServer dans Tomcat"""
    
    print(f"\n🚀 DÉPLOIEMENT DE GEOSERVER")
    print("=" * 30)
    
    try:
        target_path = os.path.join(webapps_path, "geoserver.war")
        
        print(f"📁 Source: {war_path}")
        print(f"📁 Destination: {target_path}")
        
        # Copie du fichier WAR
        shutil.copy2(war_path, target_path)
        
        print("✅ GeoServer déployé avec succès!")
        print("\n🔄 REDÉMARRAGE REQUIS:")
        print("   1. Arrêtez Tomcat")
        print("   2. Redémarrez Tomcat") 
        print("   3. Attendez le déploiement automatique")
        print("   4. Accédez à: http://localhost:8080/geoserver")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de déploiement: {e}")
        return False

def create_startup_script():
    """Crée un script de démarrage pour GeoServer"""
    
    script_content = """@echo off
echo 🚀 Démarrage de GeoServer pour AgriWeb 2.0
echo.

REM Vérification que Tomcat fonctionne
curl -s http://localhost:8080 > nul
if errorlevel 1 (
    echo ❌ Tomcat n'est pas démarré
    echo Démarrez d'abord Tomcat
    pause
    exit /b 1
)

echo ✅ Tomcat détecté sur le port 8080

REM Test de GeoServer
curl -s http://localhost:8080/geoserver > nul
if errorlevel 1 (
    echo ⚠️ GeoServer non accessible
    echo Attendez le déploiement ou redémarrez Tomcat
) else (
    echo ✅ GeoServer accessible!
    echo 🌐 Interface: http://localhost:8080/geoserver/web/
    echo 🔑 Login: admin / geoserver
)

echo.
echo 📖 Consultez GUIDE_GEOSERVER_CONFIGURATION.md pour la configuration
pause
"""
    
    with open("start_geoserver.bat", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("📜 Script de démarrage créé: start_geoserver.bat")

def main():
    """Installation complète de GeoServer"""
    
    print("🚀 INSTALLATION GEOSERVER POUR AGRIWEB 2.0")
    print("=" * 50)
    print("Ce script va:")
    print("   1. Télécharger GeoServer")
    print("   2. Extraire le fichier WAR")  
    print("   3. Le déployer dans Tomcat")
    print("   4. Configurer les scripts de démarrage")
    
    confirm = input("\n▶️ Continuer? (o/N): ").lower().strip()
    if confirm != 'o':
        print("Installation annulée.")
        return
    
    # Étape 1: Téléchargement
    zip_path = download_geoserver()
    if not zip_path:
        return
    
    # Étape 2: Extraction
    war_path = extract_geoserver_war(zip_path)
    if not war_path:
        return
    
    # Étape 3: Localisation Tomcat
    webapps_path = find_tomcat_webapps()
    if not webapps_path:
        print("❌ Impossible de localiser Tomcat")
        print("🔧 Déployez manuellement geoserver.war dans webapps/")
        return
    
    # Étape 4: Déploiement
    success = deploy_geoserver(war_path, webapps_path)
    if success:
        create_startup_script()
        
        print("\n🎉 INSTALLATION TERMINÉE!")
        print("=" * 25)
        print("📋 PROCHAINES ÉTAPES:")
        print("   1. Redémarrez Tomcat")
        print("   2. Attendez 1-2 minutes (déploiement)")
        print("   3. Accédez à: http://localhost:8080/geoserver")
        print("   4. Login: admin / geoserver")
        print("   5. Suivez GUIDE_GEOSERVER_CONFIGURATION.md")
    
    # Nettoyage
    try:
        os.remove(zip_path)
        os.remove(war_path)
        print("🧹 Fichiers temporaires nettoyés")
    except:
        pass

if __name__ == "__main__":
    main()
