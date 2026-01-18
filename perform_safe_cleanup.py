import os
import shutil
from pathlib import Path

def cleanup():
    # Patterns for directories to remove entirely
    dir_patterns = ["__pycache__", ".pytest_cache", ".tmp.driveupload"]
    
    # Patterns for files to remove
    file_patterns = [
        "*.pyc", "*.pyo",            # Python compiled
        "*.log",                     # Logs
        "*.tmp",                     # Temp files
        "*.bak",                     # Backups
        "*~",                        # Editor backups
        ".DS_Store",                 # Mac metadata
        "cleanup_analysis_report.txt", # Old reports
        "server_output.log",
        "server_error.log",
        "error.log",
        "pyarmor.bug.log",
        "~$*"                        # Excel/Word temporary lock files
    ]
    
    deleted_count = 0
    
    print("Nettoyage des fichiers temporaires en cours...")
    
    # Use os.walk to handle directory modification safely
    for dirpath, dirnames, filenames in os.walk(".", topdown=True):
        # Skip .git and .venv folders traversal
        if ".git" in dirnames:
            dirnames.remove(".git")
        if ".venv" in dirnames:
            dirnames.remove(".venv")
            
        # Modify dirnames in-place to prune directories we delete or don't want to visit
        # Check for directories to remove
        dirs_to_remove = []
        for d in dirnames:
            if d in dir_patterns:
                dirs_to_remove.append(d)
        
        for d in dirs_to_remove:
            full_path = Path(dirpath) / d
            try:
                shutil.rmtree(full_path)
                print(f"Dossier supprimé: {full_path}")
                deleted_count += 1
                dirnames.remove(d) # Prevent descending
            except Exception as e:
                print(f"Erreur dossier {full_path}: {e}")

        # Check files
        for f in filenames:
            file_path = Path(dirpath) / f
            is_temp = False
            for p in file_patterns:
                if file_path.match(p):
                    is_temp = True
                    break
            
            if is_temp:
                 try:
                    file_path.unlink()
                    print(f"Fichier supprimé: {file_path}")
                    deleted_count += 1
                 except Exception as e:
                    print(f"Erreur fichier {file_path}: {e}")

    print("-" * 30)
    print(f"Terminé. {deleted_count} éléments supprimés.")

if __name__ == "__main__":
    cleanup()
