#!/usr/bin/env python3
"""
Script de nettoyage du projet AgriWeb
Supprime tous les fichiers inutiles, de test, debug et backup
"""

import os
import shutil
import glob
import fnmatch

def cleanup_project():
    """Nettoie le projet en supprimant les fichiers inutiles"""
    
    # Fichiers à supprimer (patterns)
    files_to_delete = [
        # Fichiers de test
        "test_*.py",
        "test_*.html", 
        "test_*.json",
        "test_*.ps1",
        "*_test.py",
        "*_test.html",
        "*_test.json",
        "test-*.ps1",
        
        # Fichiers de debug
        "debug_*.py",
        "debug_*.html",
        "*_debug.py",
        "diagnostic_*.py",
        
        # Fichiers backup et temporaires
        "*_BACKUP_*.py",
        "backup_*",
        "*_backup.py",
        "*.backup",
        ".tmp.*",
        
        # Fichiers CRM (tous supprimés)
        "*crm*.py",
        "*crm*.html", 
        "*crm*.js",
        "*crm*.db",
        "CRM_*.md",
        "GUIDE_CRM*.md",
        "GUIDE_*CRM*.md",
        
        # Anciennes versions d'agriweb
        "agriweb_*.py",
        "!agriweb_hebergement_gratuit.py",  # Garder le principal
        
        # Fichiers de déploiement multiples
        "deploy_*.py",
        "deploy_*.ps1",
        "deploy_*.sh",
        "Dockerfile.*",
        "!Dockerfile",  # Garder le principal
        
        # Fichiers de configuration multiples
        "config_*.py",
        "!config.py",  # Garder le principal
        "*_config.py",
        "railway_*.py",
        "production_*.py",
        
        # Scripts de démarrage multiples
        "run_*.py",
        "!run_app.py",  # Garder le principal
        "start_*.py",
        "start_*.ps1",
        "start_*.bat",
        "launch_*.py",
        
        # Fichiers de monitoring et analyse
        "monitor_*.py",
        "monitor_*.ps1", 
        "analyze_*.py",
        "analyse_*.py",
        
        # Fichiers GeoServer multiples
        "geoserver_*.py",
        "*geoserver*.py",
        "install_*.py",
        "install_*.ps1",
        "setup_*.py",
        "setup_*.ps1",
        
        # Guides et documentation excessive
        "GUIDE_*.md",
        "TUTORIEL_*.md",
        "INSTRUCTIONS_*.md",
        "PLAN_*.md",
        "STRATEGIE_*.md",
        "HEBERGEMENT_*.md",
        "DEPLOYMENT_*.md",
        "MIGRATION_*.md",
        "OPTIMISATION*.md",
        "REFACTORING*.md",
        "DEBOGAGE_*.md",
        "CHECKLIST_*.md",
        "SOLUTION_*.md",
        "CORRECTION*.md",
        "STATUT_*.md",
        "STATUS_*.md",
        "RESUME_*.md",
        "MISSION_*.md",
        "MEMORY_*.md",
        "SYSTEME_*.md",
        "INTEGRATION_*.md",
        "ANALYSE_*.md",
        "CONFIG_*.md",
        "REPONSE_*.md",
        "DIAGNOSTIC_*.md",
        
        # Fichiers utilitaires multiples
        "utils.py",
        "user_manager.py", 
        "license_*.py",
        "payment_system.py",
        "stripe_*.py",
        "auth_*.py",
        "!auth_routes.py",  # Peut-être nécessaire
        
        # Fichiers divers
        "alternatives_*.py",
        "compare_*.py",
        "fix_*.py",
        "clean_*.py",
        "cleanup_*.py",
        "!cleanup_project.py",  # Garder ce script
        "verify_*.py",
        "update_*.py",
        "migrate_*.py",
        "redeploy_*.py",
        "force_*.py",
        "generate_*.py",
        "enrich_*.py",
        "import_*.py",
        "export_*.py",
        "create_*.py",
        "search_*.py",
        "serveur_*.py",
        "simple_*.py",
        "smoke_*.py",
        "solutions_*.py",
        "integration_*.py",
        "implementation_*.py",
        "interface_*.py",
        "clarification_*.py",
        "demo_*.py",
        "explication_*.py",
        "prochaine_*.py",
        "recherche_*.py",
        "rapport_*.py",
        "sirene_*.py",
        "widget_*.py",
        "tunnel_*.py",
        "get_*.py",
        "find_*.py",
        "detect_*.py",
        
        # Fichiers de configuration ngrok/Railway multiples
        "ngrok*.yml",
        "!ngrok.yml",  # Garder un principal
        "railway*.json",
        "railway*.toml",
        "nixpacks.toml",
        "railway*.txt",
        "Procfile.*",
        "*.env.*",
        "!.env.example",  # Garder l'exemple
        
        # Images multiples
        "AgriWeb_QRCode*.png",
        
        # Fichiers de données de test
        "*.geojson",
        "*_sample.json",
        "osm_*.json",
        "parcelles_*.json",
        "zones_*.json",
        "users.json",
        "production_*.json",
        
        # Scripts shell/batch multiples
        "*.sh",
        "*.bat",
        "*.ps1",
        "!startup.sh",  # Garder si nécessaire pour Railway
        
        # Logs et erreurs
        "error.log",
        "*.log",
        
        # Fichiers temporaires
        "*.spec",
        "*.pyd",
        "deploy_cache_bust.txt",
        "*.txt",
        "!requirements.txt",  # Garder
        "!README.md",  # Garder
        "!runtime.txt",  # Garder si nécessaire
    ]
    
    # Dossiers à supprimer complètement
    folders_to_delete = [
        "backup_*",
        "backup*",
        ".tmp.*",
        "tests",
        "docs", 
        "tools",
        "scripts",
        "__pycache__",
        ".pytest_cache",
        "modules",  # Si vide ou inutile
        "utils",   # Si vide ou inutile
        "cartes",  # Dossier de cartes temporaires
    ]
    
    deleted_files = 0
    deleted_folders = 0
    
    print("🧹 Début du nettoyage du projet AgriWeb...")
    
    # Supprimer les fichiers
    for pattern in files_to_delete:
        if pattern.startswith("!"):
            continue  # Skip les exclusions
            
        matches = glob.glob(pattern)
        for file_path in matches:
            if os.path.isfile(file_path):
                try:
                    # Vérifier les exclusions
                    skip = False
                    for exclusion in files_to_delete:
                        if exclusion.startswith("!") and fnmatch.fnmatch(file_path, exclusion[1:]):
                            skip = True
                            break
                    
                    if not skip:
                        os.remove(file_path)
                        print(f"🗑️  Supprimé: {file_path}")
                        deleted_files += 1
                except Exception as e:
                    print(f"❌ Erreur suppression {file_path}: {e}")
    
    # Supprimer les dossiers
    for pattern in folders_to_delete:
        matches = glob.glob(pattern)
        for folder_path in matches:
            if os.path.isdir(folder_path):
                try:
                    shutil.rmtree(folder_path)
                    print(f"📁 Dossier supprimé: {folder_path}")
                    deleted_folders += 1
                except Exception as e:
                    print(f"❌ Erreur suppression dossier {folder_path}: {e}")
    
    print(f"\n✅ Nettoyage terminé!")
    print(f"📊 {deleted_files} fichiers supprimés")
    print(f"📁 {deleted_folders} dossiers supprimés")
    
    # Afficher les fichiers restants importants
    print(f"\n📋 Fichiers principaux conservés:")
    important_files = [
        "agriweb_hebergement_gratuit.py",
        "run_app.py", 
        "requirements.txt",
        "README.md",
        "Dockerfile",
        ".env.example",
        "ngrok.yml",
        "config.py"
    ]
    
    for file_name in important_files:
        if os.path.exists(file_name):
            print(f"✅ {file_name}")
        else:
            print(f"⚠️  {file_name} (manquant)")

if __name__ == "__main__":
    cleanup_project()
