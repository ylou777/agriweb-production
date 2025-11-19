# Configuration Railway pour AgriWeb Authentication
# Déploiement production avec PostgreSQL et emails Gmail

import os
import psycopg2
from urllib.parse import urlparse

class RailwayConfig:
    """Configuration spécifique pour Railway"""
    
    # Base de données PostgreSQL (Railway recommandé)
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Configuration email Gmail
    SMTP_EMAIL = os.getenv('SMTP_EMAIL', 'ylaurent.perso@gmail.com')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')  # Mot de passe d'application Gmail
    
    # URL de base (automatique sur Railway)
    BASE_URL = os.getenv('BASE_URL', 'https://agriweb-auth.railway.app')
    
    # Port Railway
    PORT = int(os.getenv('PORT', 8080))
    
    # Mode production
    DEBUG = False
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24))

def get_database_connection():
    """Connexion PostgreSQL pour Railway"""
    if RailwayConfig.DATABASE_URL:
        # PostgreSQL sur Railway
        url = urlparse(RailwayConfig.DATABASE_URL)
        return psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
    else:
        # Fallback SQLite pour développement
        import sqlite3
        return sqlite3.connect('agriweb_users.db')

# Scripts SQL pour PostgreSQL
POSTGRESQL_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    is_email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token TEXT,
    email_verification_expires TIMESTAMP,
    password_reset_token TEXT,
    password_reset_expires TIMESTAMP,
    subscription_status VARCHAR(50) DEFAULT 'trial',
    trial_start_date TIMESTAMP,
    trial_end_date TIMESTAMP,
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    login_attempts INTEGER DEFAULT 0,
    last_failed_login TIMESTAMP,
    account_locked_until TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS activity_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(255) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
"""
