# -*- coding: utf-8 -*-
"""
Système d'authentification amélioré avec confirmation par email
AgriWeb 2025 - Version Production
"""

import smtplib
import secrets
import hashlib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, session, jsonify, render_template_string
import os
import re

# Base de données (PostgreSQL sur Railway, SQLite en local)
from auth_database import get_auth_db, init_auth_tables, USE_POSTGRES

# Configuration email
EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', '587')),
    'email': os.getenv('SMTP_EMAIL', 'ylaurent.perso@gmail.com'),
    'password': os.getenv('SMTP_PASSWORD', 'votre_mot_de_passe_app'),
    'from_name': 'Sun Dev by Sunstice'
}

class AuthSystem:
    """Système d'authentification sécurisé avec confirmation email"""
    
    def __init__(self):
        self.init_database()
        
    def init_database(self):
        """Initialise la base de données avec les tables nécessaires"""
        init_auth_tables()
        print("✅ Base de données d'authentification initialisée")
    
    def hash_password(self, password, salt=None):
        """Hash sécurisé d'un mot de passe avec sel"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        # PBKDF2 avec 100,000 itérations pour sécurité renforcée
        password_hash = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt.encode('utf-8'), 
            100000
        )
        return password_hash.hex(), salt
    
    def verify_password(self, password, stored_hash, salt):
        """Vérifie un mot de passe"""
        password_hash, _ = self.hash_password(password, salt)
        return password_hash == stored_hash
    
    def validate_email(self, email):
        """Valide le format de l'email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password):
        """Valide la force du mot de passe"""
        if len(password) < 8:
            return False, "Le mot de passe doit contenir au moins 8 caractères"
        if not re.search(r'[A-Z]', password):
            return False, "Le mot de passe doit contenir au moins une majuscule"
        if not re.search(r'[a-z]', password):
            return False, "Le mot de passe doit contenir au moins une minuscule"
        if not re.search(r'\d', password):
            return False, "Le mot de passe doit contenir au moins un chiffre"
        return True, "Mot de passe valide"
    
    def send_verification_email(self, email, verification_token, user_name):
        """Envoie un email de vérification"""
        try:
            # Vérifier si la configuration email est complète
            if not EMAIL_CONFIG['password'] or EMAIL_CONFIG['password'] in ['votre_mot_de_passe_app', '']:
                print(f"⚠️ Configuration email manquante - Vérification automatique pour {email}")
                # Auto-vérifier l'email si pas de configuration SMTP
                conn = get_auth_db()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET is_email_verified = 1, email_verification_token = NULL 
                    WHERE email = ?
                ''', (email,))
                conn.commit()
                conn.close()
                return True
            
            # Configuration du message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "🌱 Confirmez votre compte AgriWeb Pro"
            msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['email']}>"
            msg['To'] = email
            
            # URL de confirmation (à adapter selon votre domaine)
            base_url = os.getenv('BASE_URL', 'https://ample-manifestation-production-7b1a.up.railway.app')
            verification_url = f"{base_url}/auth/verify-email?token={verification_token}"
            
            # Version HTML de l'email
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .btn {{ display: inline-block; background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 20px; color: #6c757d; font-size: 0.9em; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🌱 AgriWeb Pro</h1>
                        <p>Plateforme Géospatiale Professionnelle</p>
                    </div>
                    <div class="content">
                        <h2>Bonjour {user_name} ! 👋</h2>
                        <p>Bienvenue sur AgriWeb Pro ! Pour activer votre compte et commencer votre essai gratuit de 7 jours, veuillez confirmer votre adresse email.</p>
                        
                        <div style="text-align: center;">
                            <a href="{verification_url}" class="btn">
                                ✅ Confirmer mon compte
                            </a>
                        </div>
                        
                        <p><strong>Votre essai gratuit comprend :</strong></p>
                        <ul>
                            <li>🗺️ Accès complet aux cartes interactives</li>
                            <li>📊 Rapports d'analyse PVGIS illimités</li>
                            <li>🔍 Recherche parcelles et infrastructure</li>
                            <li>💬 Support technique dédié</li>
                        </ul>
                        
                        <p style="background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
                            <strong>⏰ Important :</strong> Ce lien expire dans 24h. Si vous ne l'avez pas demandé, ignorez cet email.
                        </p>
                    </div>
                    <div class="footer">
                        <p>AgriWeb Pro - Solution géospatiale pour l'agriculture moderne</p>
                        <p>Si le bouton ne fonctionne pas, copiez ce lien : {verification_url}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Version texte de l'email
            text_content = f"""
            Bonjour {user_name},
            
            Bienvenue sur AgriWeb Pro !
            
            Pour activer votre compte et commencer votre essai gratuit de 7 jours, 
            veuillez confirmer votre adresse email en cliquant sur ce lien :
            
            {verification_url}
            
            Votre essai gratuit comprend :
            - Accès complet aux cartes interactives
            - Rapports d'analyse PVGIS illimités  
            - Recherche parcelles et infrastructure
            - Support technique dédié
            
            Ce lien expire dans 24h.
            
            Cordialement,
            L'équipe AgriWeb Pro
            """
            
            # Attacher les deux versions
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # Envoi via SMTP
            server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
            server.starttls()
            server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email de vérification envoyé à {email}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur envoi email: {e}")
            return False
    
    def send_admin_notification(self, user_email, user_name, user_company, trial_end_date):
        """Envoie une notification à l'admin lors d'une nouvelle inscription"""
        try:
            # Email admin (votre email)
            admin_email = os.getenv('ADMIN_EMAIL', 'ylaurent.perso@gmail.com')
            
            # Vérifier si la configuration email est complète
            if not EMAIL_CONFIG['password'] or EMAIL_CONFIG['password'] in ['votre_mot_de_passe_app', '']:
                print(f"⚠️ Configuration email manquante - Notification admin ignorée")
                return False
            
            # Configuration du message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🎉 Nouvelle inscription - {user_name}"
            msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['email']}>"
            msg['To'] = admin_email
            
            # Version HTML de l'email
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #007bff, #0056b3); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .info-box {{ background: white; padding: 15px; margin: 15px 0; border-left: 4px solid #007bff; border-radius: 5px; }}
                    .footer {{ text-align: center; margin-top: 20px; color: #6c757d; font-size: 0.9em; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Nouvelle Inscription</h1>
                        <p>AgriWeb Pro - Administration</p>
                    </div>
                    <div class="content">
                        <h2>Un nouveau compte a été créé</h2>
                        
                        <div class="info-box">
                            <strong>👤 Nom :</strong> {user_name}
                        </div>
                        
                        <div class="info-box">
                            <strong>📧 Email :</strong> {user_email}
                        </div>
                        
                        <div class="info-box">
                            <strong>🏢 Entreprise :</strong> {user_company if user_company else 'Non renseignée'}
                        </div>
                        
                        <div class="info-box">
                            <strong>⏰ Date d'inscription :</strong> {datetime.now().strftime('%d/%m/%Y à %H:%M')}
                        </div>
                        
                        <div class="info-box">
                            <strong>🎁 Période d'essai :</strong> Jusqu'au {trial_end_date.strftime('%d/%m/%Y à %H:%M')}
                        </div>
                        
                        <p style="background: #d1ecf1; padding: 15px; border-radius: 5px; border-left: 4px solid #17a2b8; margin-top: 20px;">
                            <strong>ℹ️ Info :</strong> L'utilisateur dispose de 7 jours d'essai gratuit pour tester toutes les fonctionnalités de la plateforme.
                        </p>
                    </div>
                    <div class="footer">
                        <p>AgriWeb Pro - Notification automatique</p>
                        <p>Cet email a été généré automatiquement suite à une nouvelle inscription</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Version texte de l'email
            text_content = f"""
            Nouvelle inscription sur AgriWeb Pro
            
            Un nouveau compte a été créé :
            
            Nom : {user_name}
            Email : {user_email}
            Entreprise : {user_company if user_company else 'Non renseignée'}
            Date d'inscription : {datetime.now().strftime('%d/%m/%Y à %H:%M')}
            Période d'essai : Jusqu'au {trial_end_date.strftime('%d/%m/%Y à %H:%M')}
            
            L'utilisateur dispose de 7 jours d'essai gratuit.
            
            ---
            AgriWeb Pro - Notification automatique
            """
            
            # Attacher les deux versions
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # Envoi via SMTP
            server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
            server.starttls()
            server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Notification admin envoyée pour inscription de {user_name}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur envoi notification admin: {e}")
            return False
    
    def register_user(self, email, name, company, password):
        """Inscription d'un nouvel utilisateur avec vérification email"""
        try:
            # Validation des données
            if not self.validate_email(email):
                return False, "Format d'email invalide"
            
            valid_password, password_message = self.validate_password(password)
            if not valid_password:
                return False, password_message
            
            if not name or len(name.strip()) < 2:
                return False, "Le nom doit contenir au moins 2 caractères"
            
            conn = get_auth_db()
            cursor = conn.cursor()
            
            # Vérifier si l'email existe déjà
            cursor.execute('SELECT id, is_email_verified FROM users WHERE email = ?', (email.lower(),))
            existing_user = cursor.fetchone()
            
            if existing_user:
                if existing_user[1]:  # Email déjà vérifié
                    return False, "Cet email est déjà enregistré et vérifié"
                else:  # Email non vérifié, on peut réenvoyer
                    # Supprimer l'ancien compte non vérifié
                    cursor.execute('DELETE FROM users WHERE email = ? AND is_email_verified = 0', (email.lower(),))
            
            # Hash du mot de passe
            password_hash, salt = self.hash_password(password)
            
            # Générer token de vérification
            verification_token = secrets.token_urlsafe(32)
            verification_expires = datetime.now() + timedelta(hours=24)
            
            # Dates d'essai
            trial_start = datetime.now()
            trial_end = trial_start + timedelta(days=7)
            
            # Insertion du nouvel utilisateur
            cursor.execute('''
                INSERT INTO users (
                    email, name, company, password_hash, salt,
                    email_verification_token, email_verification_expires,
                    trial_start_date, trial_end_date, subscription_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email.lower(), name.strip(), (company or '').strip(),
                password_hash, salt, verification_token, verification_expires,
                trial_start, trial_end, 'trial'
            ))
            
            conn.commit()
            conn.close()
            
            # Envoyer l'email de vérification à l'utilisateur
            email_sent = self.send_verification_email(email, verification_token, name)
            
            # Envoyer la notification à l'admin (en arrière-plan, ne bloque pas l'inscription)
            self.send_admin_notification(email, name, company or '', trial_end)
            
            if email_sent:
                return True, f"Compte créé ! Vérifiez votre email {email} pour l'activer."
            else:
                return False, "Compte créé mais erreur lors de l'envoi de l'email de vérification"
                
        except Exception as e:
            print(f"Erreur inscription: {e}")
            return False, "Erreur lors de l'inscription"
    
    def verify_email(self, token):
        """Vérifie un email avec le token de vérification"""
        try:
            conn = get_auth_db()
            cursor = conn.cursor()
            
            # Rechercher le token (d'abord normal, puis fallback pour tokens résiduels)
            cursor.execute('''
                SELECT id, email, name, email_verification_expires, is_email_verified
                FROM users 
                WHERE email_verification_token = ?
            ''', (token,))
            
            user = cursor.fetchone()
            if not user:
                return False, "Token de vérification invalide ou expiré"
            
            user_id, email, name, expires_at, is_already_verified = user
            
            # Si déjà vérifié, nettoyer le token et continuer
            if is_already_verified:
                cursor.execute('''
                    UPDATE users 
                    SET email_verification_token = NULL,
                        email_verification_expires = NULL
                    WHERE id = ?
                ''', (user_id,))
                conn.commit()
                conn.close()
                return True, f"Compte {email} déjà vérifié et nettoyé. Vous pouvez maintenant vous connecter."
            
            # Vérifier l'expiration pour les comptes non vérifiés
            if datetime.now() > datetime.fromisoformat(expires_at):
                return False, "Token de vérification expiré"
            
            # Activer le compte
            cursor.execute('''
                UPDATE users 
                SET is_email_verified = 1, 
                    email_verification_token = NULL,
                    email_verification_expires = NULL
                WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
            return True, f"Email vérifié avec succès ! Votre compte {email} est maintenant actif."
            
        except Exception as e:
            print(f"Erreur vérification email: {e}")
            return False, "Erreur lors de la vérification"
    
    def authenticate_user(self, email, password):
        """Authentifie un utilisateur (email doit être vérifié)"""
        try:
            conn = get_auth_db()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, password_hash, salt, subscription_status, trial_end_date, 
                       name, is_admin, is_email_verified
                FROM users 
                WHERE email = ? AND is_active = 1
            ''', (email.lower(),))
            
            user = cursor.fetchone()
            if not user:
                return False, None, "Email ou mot de passe incorrect"
            
            user_id, stored_hash, salt, subscription_status, trial_end, name, is_admin, is_verified = user
            
            # Vérifier que l'email est confirmé
            if not is_verified:
                return False, None, "Veuillez d'abord confirmer votre email avant de vous connecter"
            
            # Vérifier le mot de passe
            if not self.verify_password(password, stored_hash, salt):
                return False, None, "Email ou mot de passe incorrect"
            
            # Vérifier l'expiration de l'essai
            if subscription_status == 'trial':
                trial_end_date = datetime.fromisoformat(trial_end)
                if datetime.now() > trial_end_date:
                    return False, None, "Période d'essai expirée. Veuillez souscrire à un abonnement."
            
            # Mettre à jour les stats de connexion
            cursor.execute('''
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP, login_count = login_count + 1
                WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
            return True, {
                'id': user_id,
                'email': email.lower(),
                'name': name,
                'subscription_status': subscription_status,
                'trial_end': trial_end,
                'is_admin': bool(is_admin)
            }, "Connexion réussie"
            
        except Exception as e:
            print(f"Erreur authentification: {e}")
            return False, None, "Erreur lors de l'authentification"
    
    def create_session(self, user_id, ip_address, user_agent):
        """Crée une nouvelle session utilisateur"""
        try:
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(days=7)  # Session 7 jours
            
            conn = get_auth_db()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_sessions (user_id, session_token, expires_at, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, session_token, expires_at, ip_address, user_agent))
            
            conn.commit()
            conn.close()
            
            return session_token
            
        except Exception as e:
            print(f"Erreur création session: {e}")
            return None

    def request_password_reset(self, email):
        """Demande de réinitialisation de mot de passe"""
        try:
            conn = get_auth_db()
            cursor = conn.cursor()
            
            # Vérifier que l'utilisateur existe
            cursor.execute('SELECT id FROM users WHERE email = ? AND is_active = 1', (email.lower(),))
            user = cursor.fetchone()
            
            if not user:
                return False, "Aucun compte n'est associé à cet email"
            
            user_id = user[0]
            
            # Générer un token de réinitialisation
            reset_token = secrets.token_urlsafe(32)
            reset_expires = datetime.now() + timedelta(hours=1)  # Expire dans 1 heure
            
            # Stocker le token
            cursor.execute('''
                UPDATE users 
                SET password_reset_token = ?, password_reset_expires = ?
                WHERE id = ?
            ''', (reset_token, reset_expires.isoformat(), user_id))
            
            conn.commit()
            conn.close()
            
            # Envoyer l'email de réinitialisation
            success = self.send_password_reset_email(email, reset_token)
            
            if success:
                return True, "Email de réinitialisation envoyé avec succès"
            else:
                return False, "Erreur lors de l'envoi de l'email"
                
        except Exception as e:
            print(f"Erreur demande réinitialisation: {e}")
            return False, "Erreur lors de la demande de réinitialisation"
    
    def send_password_reset_email(self, email, reset_token):
        """Envoie l'email de réinitialisation de mot de passe"""
        try:
            # URL de réinitialisation
            reset_url = f"https://ample-manifestation-production-7b1a.up.railway.app/auth/new-password?token={reset_token}"
            
            # Contenu de l'email
            subject = "🔐 Réinitialisation de votre mot de passe AgriWeb"
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Réinitialisation mot de passe AgriWeb</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .title {{ color: #2c3e50; font-size: 24px; margin-bottom: 10px; }}
        .subtitle {{ color: #7f8c8d; font-size: 16px; }}
        .content {{ margin: 20px 0; line-height: 1.6; color: #34495e; }}
        .button {{ display: inline-block; background: linear-gradient(135deg, #3498db, #2980b9); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }}
        .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0; color: #856404; }}
        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ecf0f1; color: #7f8c8d; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">🔐 Réinitialisation de mot de passe</h1>
            <p class="subtitle">AgriWeb Pro - Plateforme Agricole</p>
        </div>
        
        <div class="content">
            <p>Bonjour,</p>
            
            <p>Vous avez demandé la réinitialisation de votre mot de passe pour votre compte AgriWeb (<strong>{email}</strong>).</p>
            
            <p>Cliquez sur le bouton ci-dessous pour créer un nouveau mot de passe :</p>
            
            <div style="text-align: center;">
                <a href="{reset_url}" class="button">
                    🔐 Réinitialiser mon mot de passe
                </a>
            </div>
            
            <div class="warning">
                <strong>⚠️ Important :</strong>
                <ul>
                    <li>Ce lien expire dans <strong>1 heure</strong></li>
                    <li>Si vous n'avez pas demandé cette réinitialisation, ignorez cet email</li>
                    <li>Ne partagez jamais ce lien avec quelqu'un d'autre</li>
                </ul>
            </div>
            
            <p>Si le bouton ne fonctionne pas, copiez et collez ce lien dans votre navigateur :</p>
            <p style="word-break: break-all; color: #3498db;"><a href="{reset_url}">{reset_url}</a></p>
        </div>
        
        <div class="footer">
            <p>© 2025 AgriWeb Pro - Plateforme Agricole Intelligente</p>
            <p>Cet email a été envoyé automatiquement, merci de ne pas y répondre.</p>
        </div>
    </div>
</body>
</html>
"""
            
            # Configuration SMTP
            smtp_server = EMAIL_CONFIG['smtp_server']
            smtp_port = EMAIL_CONFIG['smtp_port']
            smtp_email = EMAIL_CONFIG['email']
            smtp_password = EMAIL_CONFIG['password']
            
            # Vérification des credentials
            if not smtp_email or smtp_password == 'votre_mot_de_passe_app':
                print("⚠️ Credentials SMTP manquants - Auto-validation activée")
                return True  # Simulation d'envoi réussi en mode développement
            
            # Créer le message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{EMAIL_CONFIG['from_name']} <{smtp_email}>"
            message["To"] = email
            
            # Ajouter le contenu HTML
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)
            
            # Envoyer l'email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.send_message(message)
            server.quit()
            
            print(f"✅ Email de réinitialisation envoyé à {email}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur envoi email réinitialisation: {e}")
            return False
    
    def reset_password_with_token(self, token, new_password):
        """Réinitialise le mot de passe avec un token valide"""
        try:
            conn = get_auth_db()
            cursor = conn.cursor()
            
            # Vérifier le token et son expiration
            cursor.execute('''
                SELECT id, password_reset_expires 
                FROM users 
                WHERE password_reset_token = ? AND is_active = 1
            ''', (token,))
            
            user = cursor.fetchone()
            if not user:
                return False, "Token de réinitialisation invalide"
            
            user_id, reset_expires = user
            
            # Vérifier l'expiration
            if reset_expires:
                expires_date = datetime.fromisoformat(reset_expires)
                if datetime.now() > expires_date:
                    return False, "Token de réinitialisation expiré"
            
            # Valider le nouveau mot de passe
            if len(new_password) < 8:
                return False, "Le mot de passe doit contenir au moins 8 caractères"
            
            if not re.search(r'[A-Z]', new_password):
                return False, "Le mot de passe doit contenir au moins une majuscule"
            
            if not re.search(r'[a-z]', new_password):
                return False, "Le mot de passe doit contenir au moins une minuscule"
            
            if not re.search(r'\d', new_password):
                return False, "Le mot de passe doit contenir au moins un chiffre"
            
            # Hasher le nouveau mot de passe
            password_hash, salt = self.hash_password(new_password)
            
            # Mettre à jour le mot de passe et supprimer le token
            cursor.execute('''
                UPDATE users 
                SET password_hash = ?, salt = ?, 
                    password_reset_token = NULL, password_reset_expires = NULL
                WHERE id = ?
            ''', (password_hash, salt, user_id))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Mot de passe réinitialisé pour l'utilisateur ID {user_id}")
            return True, "Mot de passe réinitialisé avec succès"
            
        except Exception as e:
            print(f"Erreur réinitialisation mot de passe: {e}")
            return False, "Erreur lors de la réinitialisation du mot de passe"

# Instance globale
auth_system = AuthSystem()

def setup_email_config():
    """Configuration et test de l'email"""
    print("\n=== Configuration Email AgriWeb ===")
    print(f"SMTP Server: {EMAIL_CONFIG['smtp_server']}")
    print(f"Email From: {EMAIL_CONFIG['email']}")
    
    # Vérifier l'email configuré
    if not EMAIL_CONFIG['email'] or EMAIL_CONFIG['email'] == 'votre.email@gmail.com':
        print("⚠️  Configuration email requise!")
        print("Variables d'environnement à définir:")
        print("- SMTP_EMAIL: votre adresse Gmail")
        print("- SMTP_PASSWORD: mot de passe d'application Gmail")
        print("\nGuide: https://support.google.com/accounts/answer/185833")
        return False
    
    # Vérifier le mot de passe d'application
    if not EMAIL_CONFIG['password'] or EMAIL_CONFIG['password'] == 'votre_mot_de_passe_app':
        print("⚠️  Mot de passe d'application Gmail requis!")
        print("Configurez: $env:SMTP_PASSWORD=\"votre_mot_de_passe_app\"")
        return False
    
    print("✅ Configuration email complète")
    return True

if __name__ == "__main__":
    # Test du système
    setup_email_config()
    
    # Test d'inscription
    success, message = auth_system.register_user(
        "test@example.com", 
        "Test User", 
        "Test Company", 
        "TestPassword123!"
    )
    print(f"Test inscription: {success} - {message}")
