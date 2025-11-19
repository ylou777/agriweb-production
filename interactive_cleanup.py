#!/usr/bin/env python3
"""
Script de nettoyage interactif pour AgriWeb
Supprime les fichiers inutiles en toute sécurité avec confirmation utilisateur
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Import du script d'analyse
from analyze_and_cleanup import AgriWebCleaner

def create_backup_before_cleanup(workspace_path: Path):
    """Crée une sauvegarde avant le nettoyage"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = workspace_path / f"backup_avant_nettoyage_{timestamp}"
    
    print(f"📦 Création d'une sauvegarde dans: {backup_dir}")
    
    # Créer le dossier de backup
    backup_dir.mkdir(exist_ok=True)
    
    # Sauvegarder uniquement les fichiers importants (pas .venv)
    important_files = [
        "agriweb_hebergement_gratuit.py",
        "run_app.py", 
        "requirements.txt",
        "config.py",
        ".env",
        ".gitignore",
        "README.md"
    ]
    
    for file in important_files:
        src = workspace_path / file
        if src.exists():
            dst = backup_dir / file
            shutil.copy2(src, dst)
            print(f"  ✅ {file}")
    
    # Sauvegarder les dossiers importants
    important_dirs = ["static", "templates", "modules"]
    for dir_name in important_dirs:
        src_dir = workspace_path / dir_name
        if src_dir.exists():
            dst_dir = backup_dir / dir_name
            shutil.copytree(src_dir, dst_dir)
            print(f"  ✅ {dir_name}/")
    
    print(f"✅ Sauvegarde créée avec succès !")
    return backup_dir

def interactive_cleanup():
    """Nettoyage interactif avec confirmation utilisateur"""
    workspace_path = Path(r"c:\Users\Utilisateur\Desktop\AG32.1\ag3reprise\AgW3b")
    
    print("🧹 NETTOYAGE INTERACTIF DU WORKSPACE AGRIWEB")
    print("=" * 50)
    
    # Charger l'analyse
    cleaner = AgriWebCleaner(str(workspace_path))
    cleaner.analyze_files()
    cleanup_plan = cleaner.suggest_cleanup()
    
    print(f"\n📊 Résumé de l'analyse:")
    print(f"  🗑️  Fichiers à supprimer (sûr): {len(cleanup_plan['phase_1_safe'])}")
    print(f"  ❓ Fichiers à réviser: {len(cleanup_plan['phase_2_review'])}")
    print(f"  🔒 Fichiers à conserver: {len(cleanup_plan['phase_3_keep'])}")
    
    # Créer une sauvegarde
    print(f"\n📦 Voulez-vous créer une sauvegarde avant le nettoyage ?")
    backup_choice = input("(o/n): ").lower().strip()
    
    if backup_choice in ['o', 'oui', 'y', 'yes']:
        backup_dir = create_backup_before_cleanup(workspace_path)
    
    # Phase 1: Suppression sûre
    print(f"\n🗑️ PHASE 1: Suppression des fichiers sûrs ({len(cleanup_plan['phase_1_safe'])} fichiers)")
    
    # Filtrer pour exclure .venv et les fichiers système
    safe_files_filtered = []
    for file in cleanup_plan['phase_1_safe']:
        if not any(exclude in file for exclude in ['.venv', '__pycache__', '.git']):
            safe_files_filtered.append(file)
    
    if safe_files_filtered:
        print(f"\nFichiers à supprimer:")
        for i, file in enumerate(safe_files_filtered[:20], 1):  # Afficher les 20 premiers
            print(f"  {i:2d}. {file}")
        
        if len(safe_files_filtered) > 20:
            print(f"  ... et {len(safe_files_filtered) - 20} autres")
        
        choice = input(f"\nSupprimer ces {len(safe_files_filtered)} fichiers ? (o/n): ").lower().strip()
        
        if choice in ['o', 'oui', 'y', 'yes']:
            deleted_count = 0
            failed_count = 0
            
            for file in safe_files_filtered:
                file_path = workspace_path / file
                try:
                    if file_path.exists():
                        if file_path.is_file():
                            file_path.unlink()
                            deleted_count += 1
                        elif file_path.is_dir():
                            shutil.rmtree(file_path)
                            deleted_count += 1
                except Exception as e:
                    print(f"  ❌ Erreur suppression {file}: {e}")
                    failed_count += 1
            
            print(f"✅ {deleted_count} fichiers supprimés")
            if failed_count > 0:
                print(f"❌ {failed_count} erreurs")
    else:
        print("Aucun fichier sûr à supprimer trouvé.")
    
    # Phase 2: Révision manuelle des fichiers obsolètes
    print(f"\n❓ PHASE 2: Révision des fichiers obsolètes")
    
    # Filtrer les fichiers obsolètes (exclure .venv)
    obsolete_files = []
    for file in cleanup_plan['phase_2_review']:
        if not any(exclude in file for exclude in ['.venv', '__pycache__', '.git']):
            obsolete_files.append(file)
    
    if obsolete_files:
        print(f"\nFichiers potentiellement obsolètes ({len(obsolete_files)}):")
        
        # Groupe par type
        agriweb_files = [f for f in obsolete_files if f.startswith('agriweb_') and f.endswith('.py')]
        serveur_files = [f for f in obsolete_files if f.startswith('serveur_') and f.endswith('.py')]
        docker_files = [f for f in obsolete_files if 'dockerfile' in f.lower() or 'docker' in f.lower()]
        other_files = [f for f in obsolete_files if f not in agriweb_files + serveur_files + docker_files]
        
        if agriweb_files:
            print(f"\n  📄 Anciennes versions agriweb ({len(agriweb_files)}):")
            for f in agriweb_files[:10]:
                print(f"    • {f}")
            if len(agriweb_files) > 10:
                print(f"    ... et {len(agriweb_files) - 10} autres")
            
            choice = input(f"  Supprimer ces {len(agriweb_files)} anciens fichiers agriweb ? (o/n): ").lower().strip()
            if choice in ['o', 'oui', 'y', 'yes']:
                for file in agriweb_files:
                    try:
                        (workspace_path / file).unlink()
                        print(f"    ✅ {file}")
                    except Exception as e:
                        print(f"    ❌ {file}: {e}")
        
        if serveur_files:
            print(f"\n  🖥️ Anciens fichiers serveur ({len(serveur_files)}):")
            for f in serveur_files[:5]:
                print(f"    • {f}")
            if len(serveur_files) > 5:
                print(f"    ... et {len(serveur_files) - 5} autres")
            
            choice = input(f"  Supprimer ces {len(serveur_files)} anciens serveurs ? (o/n): ").lower().strip()
            if choice in ['o', 'oui', 'y', 'yes']:
                for file in serveur_files:
                    try:
                        (workspace_path / file).unlink()
                        print(f"    ✅ {file}")
                    except Exception as e:
                        print(f"    ❌ {file}: {e}")
        
        if docker_files:
            print(f"\n  🐳 Fichiers Docker ({len(docker_files)}):")
            for f in docker_files:
                print(f"    • {f}")
            
            choice = input(f"  Supprimer ces {len(docker_files)} fichiers Docker ? (o/n): ").lower().strip()
            if choice in ['o', 'oui', 'y', 'yes']:
                for file in docker_files:
                    try:
                        (workspace_path / file).unlink()
                        print(f"    ✅ {file}")
                    except Exception as e:
                        print(f"    ❌ {file}: {e}")
    
    # Nettoyage final des dossiers vides
    print(f"\n🧹 Nettoyage des dossiers vides...")
    empty_dirs_removed = 0
    
    for root, dirs, files in os.walk(workspace_path, topdown=False):
        for dirname in dirs:
            dir_path = Path(root) / dirname
            try:
                if dir_path.is_dir() and not any(dir_path.iterdir()):
                    # Éviter de supprimer des dossiers importants
                    if not any(important in str(dir_path) for important in ['.venv', '.git', 'static', 'templates']):
                        dir_path.rmdir()
                        empty_dirs_removed += 1
                        print(f"  🗂️ {dir_path.relative_to(workspace_path)}")
            except Exception:
                pass
    
    if empty_dirs_removed > 0:
        print(f"✅ {empty_dirs_removed} dossiers vides supprimés")
    
    print(f"\n🎉 NETTOYAGE TERMINÉ !")
    print(f"✅ Votre workspace est maintenant plus propre et organisé.")
    
    # Statistiques finales
    remaining_files = len(list(workspace_path.rglob('*')))
    print(f"📊 Fichiers restants: {remaining_files}")

if __name__ == "__main__":
    try:
        interactive_cleanup()
    except KeyboardInterrupt:
        print(f"\n🛑 Nettoyage annulé par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")