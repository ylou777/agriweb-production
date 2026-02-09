# -*- coding: utf-8 -*-
"""
Module d'abstraction base de données pour l'authentification AgriWeb
=====================================================================
- PostgreSQL si DATABASE_URL est défini (Railway → données persistantes)
- SQLite sinon (développement local)

Usage:
    from auth_database import get_auth_db, init_auth_tables, USE_POSTGRES
    
    conn = get_auth_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    # → Les ? sont automatiquement convertis en %s pour PostgreSQL
"""

import os
import re
import sqlite3

# ── Détection environnement ─────────────────────────────────────────────

_DATABASE_URL = os.environ.get('DATABASE_URL', '')
USE_POSTGRES = False
_pg_url = None

if _DATABASE_URL:
    try:
        import psycopg2
        import psycopg2.extras
        _pg_url = _DATABASE_URL
        if _pg_url.startswith('postgres://'):
            _pg_url = _pg_url.replace('postgres://', 'postgresql://', 1)
        USE_POSTGRES = True
        print("✅ [AUTH_DB] PostgreSQL détecté (Railway — données persistantes entre déploiements)")
    except ImportError:
        print("⚠️ [AUTH_DB] psycopg2 non disponible, fallback SQLite")
else:
    print("ℹ️ [AUTH_DB] Mode local SQLite (agriweb_users.db)")

SQLITE_PATH = 'agriweb_users.db'


# ── Adaptation SQL ──────────────────────────────────────────────────────

def _adapt_sql(sql):
    """Convertit une requête SQLite en PostgreSQL."""
    # ? → %s (placeholders)
    sql = sql.replace('?', '%s')
    
    # Fonctions datetime
    sql = sql.replace("datetime('now')", "NOW()")
    sql = sql.replace("date('now')", "CURRENT_DATE")
    
    # datetime(column) → column::timestamp (SQLite cast → PostgreSQL cast)
    sql = re.sub(r"datetime\((\w+)\)", r"\1::timestamp", sql)
    
    # date('now', '-N days') → CURRENT_DATE - INTERVAL 'N days'
    sql = re.sub(r"date\('now',\s*'-(\d+)\s+days?'\)", r"CURRENT_DATE - INTERVAL '\1 days'", sql)
    
    # date(column) → column::date
    sql = re.sub(r"date\((\w+)\)", r"\1::date", sql)
    
    # INSERT OR IGNORE → INSERT ... ON CONFLICT DO NOTHING
    if re.search(r'INSERT\s+OR\s+IGNORE', sql, re.IGNORECASE):
        sql = re.sub(r'INSERT\s+OR\s+IGNORE\s+INTO', 'INSERT INTO', sql, flags=re.IGNORECASE)
        sql = sql.rstrip().rstrip(';') + ' ON CONFLICT DO NOTHING'
    
    # Boolean columns: = 1 → = TRUE, = 0 → = FALSE
    for col in ('is_active', 'is_admin', 'is_email_verified', 'is_verified'):
        sql = re.sub(rf'\b{col}\s*=\s*1\b', f'{col} = TRUE', sql)
        sql = re.sub(rf'\b{col}\s*=\s*0\b', f'{col} = FALSE', sql)

    # DELETE ... WHERE ... ORDER BY ... LIMIT N 
    # (PostgreSQL ne supporte pas ORDER BY/LIMIT dans DELETE directement)
    delete_match = re.search(
        r'DELETE\s+FROM\s+(\w+)\s+WHERE\s+(.*?)\s+ORDER\s+BY\s+(.*?)\s+LIMIT\s+(\d+)',
        sql, re.IGNORECASE | re.DOTALL
    )
    if delete_match:
        table = delete_match.group(1)
        where = delete_match.group(2).strip()
        order = delete_match.group(3).strip()
        limit = delete_match.group(4)
        sql = (f"DELETE FROM {table} WHERE id IN "
               f"(SELECT id FROM {table} WHERE {where} ORDER BY {order} LIMIT {limit})")
    
    return sql


# ── Cursor wrapper PostgreSQL ───────────────────────────────────────────

class _PgCursorWrapper:
    """Enveloppe un curseur psycopg2 pour accepter la syntaxe SQLite (? placeholders, etc.)."""
    
    def __init__(self, cursor):
        self._cursor = cursor
    
    def execute(self, sql, params=None):
        sql = _adapt_sql(sql)
        if params:
            self._cursor.execute(sql, params)
        else:
            self._cursor.execute(sql)
        return self
    
    def fetchone(self):
        try:
            return self._cursor.fetchone()
        except Exception:
            return None
    
    def fetchall(self):
        try:
            return self._cursor.fetchall()
        except Exception:
            return []
    
    @property
    def lastrowid(self):
        """Tente de récupérer le dernier id inséré (best-effort pour PostgreSQL)."""
        return getattr(self._cursor, 'lastrowid', None)
    
    @property
    def rowcount(self):
        return self._cursor.rowcount
    
    @property
    def description(self):
        return self._cursor.description
    
    def close(self):
        self._cursor.close()


# ── Connection wrapper ──────────────────────────────────────────────────

class _AuthDBConnection:
    """Connexion normalisée SQLite/PostgreSQL avec adaptation automatique des requêtes."""
    
    def __init__(self):
        if USE_POSTGRES:
            import psycopg2
            self._conn = psycopg2.connect(_pg_url)
            self._is_pg = True
        else:
            self._conn = sqlite3.connect(SQLITE_PATH)
            self._is_pg = False
    
    def cursor(self):
        if self._is_pg:
            return _PgCursorWrapper(self._conn.cursor())
        return self._conn.cursor()
    
    def commit(self):
        self._conn.commit()
    
    def rollback(self):
        self._conn.rollback()
    
    def close(self):
        try:
            self._conn.close()
        except Exception:
            pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        self.close()
        return False


def get_auth_db():
    """Retourne une connexion DB pour l'authentification.
    
    - Railway (DATABASE_URL défini) → PostgreSQL (persistant)
    - Local (pas de DATABASE_URL) → SQLite (agriweb_users.db)
    
    Les curseurs adaptent automatiquement la syntaxe SQL.
    """
    return _AuthDBConnection()


# ── Initialisation des tables ───────────────────────────────────────────

def init_auth_tables():
    """Crée les tables d'authentification (schéma unifié, DDL adapté au dialecte)."""
    conn = get_auth_db()
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        # ── PostgreSQL DDL ──
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                company TEXT,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                is_email_verified BOOLEAN DEFAULT FALSE,
                email_verification_token TEXT,
                email_verification_expires TIMESTAMP,
                password_reset_token TEXT,
                password_reset_expires TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                trial_start_date TIMESTAMP,
                trial_end_date TIMESTAMP,
                subscription_status TEXT DEFAULT 'trial',
                subscription_type TEXT,
                subscription_plan TEXT,
                subscription_end_date TIMESTAMP,
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                last_login TIMESTAMP,
                login_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                is_admin BOOLEAN DEFAULT FALSE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                session_token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                expires_at TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                action TEXT,
                endpoint TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Index pour performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id)
        ''')
        
    else:
        # ── SQLite DDL ──
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                company TEXT,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                is_email_verified INTEGER DEFAULT 0,
                email_verification_token TEXT,
                email_verification_expires TIMESTAMP,
                password_reset_token TEXT,
                password_reset_expires TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                trial_start_date TIMESTAMP,
                trial_end_date TIMESTAMP,
                subscription_status TEXT DEFAULT 'trial',
                subscription_type TEXT,
                subscription_plan TEXT,
                subscription_end_date TIMESTAMP,
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                last_login TIMESTAMP,
                login_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                is_admin INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                endpoint TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Ajouter les colonnes manquantes (migration douce)
        for col_def in [
            'subscription_plan TEXT',
            'subscription_type TEXT',
            'subscription_end_date TIMESTAMP',
            'stripe_customer_id TEXT',
            'stripe_subscription_id TEXT',
            'is_admin INTEGER DEFAULT 0',
            'is_email_verified INTEGER DEFAULT 0',
            'email_verification_token TEXT',
            'email_verification_expires TIMESTAMP',
            'password_reset_token TEXT',
            'password_reset_expires TIMESTAMP',
        ]:
            try:
                cursor.execute(f'ALTER TABLE users ADD COLUMN {col_def}')
            except Exception:
                pass  # Colonne existe déjà
    
    conn.commit()
    conn.close()
    
    db_type = 'PostgreSQL (Railway)' if USE_POSTGRES else 'SQLite (local)'
    print(f"✅ [AUTH_DB] Tables d'authentification initialisées ({db_type})")
