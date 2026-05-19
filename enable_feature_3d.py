"""
Active la fonctionnalite Calpinage 3D (Vue 3D immersive WebGL + remplissage
auto LiDAR) pour un utilisateur non-admin.

La fonctionnalite est gatee par un flag granulaire users.feature_3d_calpinage
(colonne ajoutee automatiquement par la route /crm/prospect/<id>/calpinage).
Permet de donner acces a la 3D a un prospect commercial (Tryba, etc.) sans
lui ouvrir le statut admin (qui donnerait acces a TOUTES les donnees).

Usage :
    $env:DATABASE_URL='postgresql://...'
    python enable_feature_3d.py --user-id 40             # active pour Pascal
    python enable_feature_3d.py --user-id 40 --disable   # desactive
    python enable_feature_3d.py --list                   # liste les actuels
"""
from __future__ import annotations

import argparse
import os
import sys

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    sys.exit("psycopg2 manquant — pip install psycopg2-binary")


def connect():
    url = os.environ.get("DATABASE_URL")
    if not url:
        sys.exit("DATABASE_URL absente.")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(url)


def ensure_column(conn):
    with conn.cursor() as cur:
        cur.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS feature_3d_calpinage BOOLEAN DEFAULT FALSE
        """)
    conn.commit()


def fetch_one(conn, sql, params=()):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        r = cur.fetchone()
        return dict(r) if r else None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--user-id", type=int, default=None,
                   help="user_id cible (ex: 40 pour Pascal)")
    p.add_argument("--disable", action="store_true",
                   help="Desactiver le flag (defaut : l'active)")
    p.add_argument("--list", action="store_true",
                   help="Lister les users avec le flag actif et sortir")
    args = p.parse_args()

    conn = connect()
    print("[OK] connecte a la base PostgreSQL")
    ensure_column(conn)

    if args.list:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, email, COALESCE(name, '') AS nom,
                       COALESCE(company, '') AS company,
                       is_admin, feature_3d_calpinage
                FROM users
                WHERE feature_3d_calpinage = TRUE OR is_admin = 1
                ORDER BY is_admin DESC, id
            """)
            print()
            print(f"  {'ID':<5} {'admin':<6} {'3D':<4} {'email':<40} {'societe':<25}")
            print("  " + "-" * 90)
            for r in cur.fetchall():
                print(f"  {r['id']:<5} "
                      f"{('OUI' if r['is_admin'] else '-'):<6} "
                      f"{('OUI' if r['feature_3d_calpinage'] else '-'):<4} "
                      f"{r['email'][:40]:<40} "
                      f"{(r['company'] or '')[:25]:<25}")
        return

    if not args.user_id:
        sys.exit("--user-id requis (ou --list).")

    user = fetch_one(conn,
        "SELECT id, email, COALESCE(name,'') AS nom, COALESCE(company,'') AS company FROM users WHERE id = %s",
        (args.user_id,))
    if not user:
        sys.exit(f"User id={args.user_id} introuvable.")

    new_value = not args.disable
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET feature_3d_calpinage = %s WHERE id = %s",
            (new_value, args.user_id),
        )
    conn.commit()

    action = "activee" if new_value else "desactivee"
    print(f"[OK] Fonctionnalite Calpinage 3D {action} pour user_id={user['id']} "
          f"({user['email']}, {user['company']}).")
    if new_value:
        print(f"     Pascal pourra utiliser le bouton 'Vue 3D' depuis chaque fiche")
        print(f"     calpinage (/crm/prospect/<id>/calpinage).")


if __name__ == "__main__":
    main()
