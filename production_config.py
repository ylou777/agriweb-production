# Configuration spécifique pour votre app Railway
# URL: https://ample-manifestation-production-7b1a.up.railway.app/

import os

class ProductionConfig:
    """Configuration pour votre app Railway existante"""
    
    # URL de base de votre app Railway
    BASE_URL = "https://ample-manifestation-production-7b1a.up.railway.app"
    
    # Configuration email Gmail (à ajouter aux variables d'environnement Railway)
    SMTP_EMAIL = os.getenv('SMTP_EMAIL', 'ylaurent.perso@gmail.com')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')  # Votre mot de passe d'application Gmail
    
    # Configuration Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'votre-clé-secrète-longue-et-sécurisée')
    
    # Mode production
    DEBUG = False
    
    @staticmethod
    def init_app(app):
        """Initialise l'application avec cette configuration"""
        app.config['SECRET_KEY'] = ProductionConfig.SECRET_KEY
        app.config['DEBUG'] = ProductionConfig.DEBUG
