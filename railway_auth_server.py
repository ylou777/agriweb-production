#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AgriWeb Authentication - Version Railway Production
Serveur d'authentification avec emails Gmail pour Railway
"""

import os
import sys
from flask import Flask, request, session, jsonify, redirect, render_template_string
from railway_config import RailwayConfig, get_database_connection, POSTGRESQL_SCHEMA

# Import du système d'authentification
from auth_system_improved import AuthSystem

app = Flask(__name__)
app.secret_key = RailwayConfig.SECRET_KEY

# Initialisation de la base de données pour Railway
def init_railway_database():
    """Initialise la base de données PostgreSQL sur Railway"""
    try:
        if RailwayConfig.DATABASE_URL:
            conn = get_database_connection()
            cursor = conn.cursor()
            cursor.execute(POSTGRESQL_SCHEMA)
            conn.commit()
            conn.close()
            print("✅ Base de données PostgreSQL initialisée sur Railway")
        else:
            print("⚠️  Utilisation de SQLite (développement)")
    except Exception as e:
        print(f"❌ Erreur base de données: {e}")

# Routes importées du serveur d'authentification
from production_auth_server import *

# Configuration spécifique Railway
@app.before_first_request
def setup_railway():
    """Configuration au premier démarrage sur Railway"""
    init_railway_database()
    
    # Vérification des variables d'environnement critiques
    if not RailwayConfig.SMTP_PASSWORD:
        print("⚠️  SMTP_PASSWORD non configuré sur Railway")
    if not RailwayConfig.DATABASE_URL:
        print("⚠️  DATABASE_URL non configuré sur Railway")

if __name__ == '__main__':
    print("🚀 AGRIWEB AUTHENTICATION - RAILWAY PRODUCTION")
    print("=" * 60)
    print(f"📧 Email configuré : {RailwayConfig.SMTP_EMAIL}")
    print(f"🌐 URL de base : {RailwayConfig.BASE_URL}")
    print(f"🐘 Base de données : {'PostgreSQL' if RailwayConfig.DATABASE_URL else 'SQLite'}")
    
    if RailwayConfig.SMTP_PASSWORD:
        print("✅ Mot de passe Gmail : Configuré")
        print("✅ Mode production : Emails réels activés")
    else:
        print("⚠️  Mot de passe Gmail : MANQUANT")
        print("📋 Configurez SMTP_PASSWORD sur Railway")
    
    print("=" * 60)
    
    # Démarrage sur Railway (port automatique)
    app.run(
        host='0.0.0.0', 
        port=RailwayConfig.PORT, 
        debug=RailwayConfig.DEBUG
    )
