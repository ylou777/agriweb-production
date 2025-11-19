# license_manager.py
import os
import json
import datetime
from pathlib import Path
from cryptography.fernet import Fernet

# Clé de chiffrement pour licences (doit être secrète)
SECRET_KEY = b'V9IOdZhPWHEppKmzwRI1SQFKO9Q5YK5deTUcAszxR9c='  # Exemple seulement!

# Définissez le nom de votre application et le chemin où la licence sera stockée
APP_NAME = "MonApplication"
APP_DIR = Path.home() / f".{APP_NAME.lower()}"
LICENSE_FILE = APP_DIR / "license.lic"  # <== Ceci est la variable à importer

# Assurez-vous que le dossier existe
APP_DIR.mkdir(parents=True, exist_ok=True)
print("Le fichier de licence sera stocké ici :", LICENSE_FILE)

# ================= Gestion de la période d'essai ====================
def init_trial():
    """Initialise la période d'essai."""
    trial_file = APP_DIR / "trial_info.json"
    if not trial_file.exists():
        trial_info = {
            "install_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(trial_file, "w") as f:
            json.dump(trial_info, f)

def is_trial_valid(days=3):
    """Vérifie si la période d'essai est toujours valide."""
    trial_file = APP_DIR / "trial_info.json"
    if not trial_file.exists():
        init_trial()

    with open(trial_file, "r") as f:
        trial_info = json.load(f)

    install_date = datetime.datetime.strptime(trial_info["install_date"], "%Y-%m-%d %H:%M:%S")
    return (datetime.datetime.now() - install_date).days < days

# ================= Gestion des licences ====================
def generate_license(expiry_date: str):
    """Crée une licence valide jusqu'à expiry_date (format 'YYYY-MM-DD')."""
    data = {"expiry": expiry_date}
    data_json = json.dumps(data).encode()
    cipher = Fernet(SECRET_KEY)
    license_encrypted = cipher.encrypt(data_json)
    
    with open(LICENSE_FILE, "wb") as f:
        f.write(license_encrypted)

def is_license_valid():
    """Vérifie si la licence existe et est valide."""
    if not LICENSE_FILE.exists():
        return False

    try:
        cipher = Fernet(SECRET_KEY)
        with open(LICENSE_FILE, "rb") as f:
            data_json = cipher.decrypt(f.read())

        data = json.loads(data_json.decode())
        expiry_date = datetime.datetime.strptime(data["expiry"], "%Y-%m-%d")
        return expiry_date >= datetime.datetime.now()
    except Exception as e:
        print(f"Erreur validation licence : {e}")
        return False

def check_access():
    """
    Vérifie licence d'abord, puis période d'essai.
    Retourne 'LICENSED', 'TRIAL' ou 'EXPIRED'
    """
    if is_license_valid():
        return "LICENSED"
    elif is_trial_valid():
        return "TRIAL"
    else:
        return "EXPIRED"

# Test (optionnel) :
if __name__ == "__main__":
    init_trial()
    statut = check_access()
    print(f"Statut actuel : {statut}")
    # Pour générer une licence de test, décommentez la ligne suivante:
    generate_license("2025-12-31")
