# -*- coding: utf-8 -*-
"""
Création du compte demo NEWS-SOLAR
===================================
Crée un utilisateur dédié à la démo investisseurs NEWS-SOLAR,
directement en base (SQLite local ou PostgreSQL Railway).

USAGE :
    python create_newssolar_demo_user.py

CE SCRIPT NE MODIFIE AUCUN AUTRE FICHIER DU PROGRAMME.
"""

import hashlib
import secrets
import sys
from datetime import datetime, timedelta

# ── Import de la couche DB existante (sans toucher au code principal) ──
try:
    from auth_database import get_auth_db, init_auth_tables, USE_POSTGRES
except ImportError:
    print("❌ Impossible d'importer auth_database. Lance ce script depuis le dossier du projet.")
    sys.exit(1)

# ── Paramètres du compte demo ──────────────────────────────────────────
DEMO_USER = {
    "email":    "demo@news-solar.com",
    "name":     "Demo NEWS-SOLAR",
    "company":  "NEWS-SOLAR",
    "password": "NewsSolar2026!",          # mot de passe provisoire — à changer après 1ère connexion
}

def hash_password(password, salt=None):
    """PBKDF2-SHA256 — identique à auth_system_improved.py"""
    if salt is None:
        salt = secrets.token_hex(32)
    pw_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return pw_hash.hex(), salt

def create_demo_user():
    # Initialise les tables si elles n'existent pas encore
    init_auth_tables()

    conn   = get_auth_db()
    cursor = conn.cursor()

    # Vérification si le compte existe déjà
    cursor.execute("SELECT id, email FROM users WHERE email = ?", (DEMO_USER["email"],))
    existing = cursor.fetchone()
    if existing:
        print(f"ℹ️  Le compte '{DEMO_USER['email']}' existe déjà (id={existing[0]}).")
        print("   Pour réinitialiser le mot de passe, relance ce script avec --reset.")
        if "--reset" not in sys.argv:
            conn.close()
            return
        # --reset : on met juste à jour le mot de passe
        pw_hash, salt = hash_password(DEMO_USER["password"])
        cursor.execute(
            "UPDATE users SET password_hash = ?, salt = ?, is_active = 1, is_email_verified = 1 WHERE email = ?",
            (pw_hash, salt, DEMO_USER["email"])
        )
        conn.commit()
        conn.close()
        print(f"✅ Mot de passe réinitialisé pour '{DEMO_USER['email']}'.")
        return

    # Création du compte
    pw_hash, salt = hash_password(DEMO_USER["password"])
    now           = datetime.utcnow()
    far_future    = now + timedelta(days=36500)   # ~100 ans — compte permanent

    cursor.execute("""
        INSERT INTO users (
            email, name, company,
            password_hash, salt,
            is_email_verified, is_active, is_admin,
            subscription_status, subscription_type, subscription_plan,
            trial_start_date, trial_end_date, subscription_end_date,
            created_at, login_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        DEMO_USER["email"],
        DEMO_USER["name"],
        DEMO_USER["company"],
        pw_hash,
        salt,
        1,              # is_email_verified — pas besoin de vérification email
        1,              # is_active
        0,              # is_admin — compte demo, pas admin
        "active",       # subscription_status — pas de trial limité
        "demo",         # subscription_type
        "news_solar_demo",  # subscription_plan
        now.isoformat(),
        far_future.isoformat(),    # trial_end_date  (lointain = jamais expiré)
        far_future.isoformat(),    # subscription_end_date (lointain = jamais expiré)
        now.isoformat(),
        0
    ))

    conn.commit()
    conn.close()

    print("=" * 55)
    print("✅  Compte demo NEWS-SOLAR créé avec succès")
    print("=" * 55)
    print(f"   Email    : {DEMO_USER['email']}")
    print(f"   Mot de passe : {DEMO_USER['password']}")
    print(f"   Statut   : actif — sans expiration")
    print(f"   Admin    : non")
    print(f"   Base     : {'PostgreSQL (Railway)' if USE_POSTGRES else 'SQLite local (agriweb_users.db)'}")
    print("=" * 55)
    print("⚠️  Pensez à changer le mot de passe après la première connexion.")

if __name__ == "__main__":
    create_demo_user()
