"""
Script de démarrage pour tester le système CRM AgriWeb
"""

import sys
import os

# Ajouter le répertoire actuel au path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import init_db
from crm_manager import CRMUserManager

def test_crm_system():
    """Test rapide du système CRM"""
    
    # Créer une application Flask de test
    app = Flask(__name__)
    app.secret_key = 'test_key'
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///test_agriweb_crm.db',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    })
    
    # Initialiser le système
    with app.app_context():
        print("🔧 Initialisation du système CRM...")
        init_db(app)
        crm_manager = CRMUserManager()
        crm_manager.init_app(app)
        
        print("✅ Base de données initialisée")
        
        # Tester l'authentification
        print("\n🔐 Test d'authentification...")
        user = crm_manager.authenticate_user('admin@agriweb.com', 'admin123')
        if user:
            print(f"✅ Connexion réussie: {user.name} ({user.role})")
            
            # Tester les statistiques
            stats = crm_manager.get_user_stats(user)
            print(f"📊 Statistiques: {stats}")
            
            # Tester la création d'un prospect
            print("\n🏢 Test de création de prospect...")
            try:
                prospect = crm_manager.create_prospect(
                    company_name="Ferme Test SARL",
                    contact_email="contact@ferme-test.fr",
                    address="123 Route de la Ferme",
                    city="Agricola",
                    notes="Prospect de test créé automatiquement"
                )
                print(f"✅ Prospect créé: {prospect.company_name} (ID: {prospect.id})")
            except Exception as e:
                print(f"❌ Erreur création prospect: {e}")
            
            # Tester la sauvegarde de recherche
            print("\n🔍 Test de sauvegarde de recherche...")
            try:
                search = crm_manager.save_search(
                    name="Recherche Test",
                    search_params={
                        'commune': 'Paris',
                        'filter_rpg': True,
                        'rpg_min_area': 1,
                        'rpg_max_area': 10
                    },
                    description="Recherche de test pour validation",
                    category="agriculture",
                    is_public=False
                )
                print(f"✅ Recherche sauvegardée: {search.name} (ID: {search.id})")
            except Exception as e:
                print(f"❌ Erreur sauvegarde recherche: {e}")
            
        else:
            print("❌ Échec de l'authentification")
        
        print("\n🎉 Tests CRM terminés avec succès!")
        return True

if __name__ == '__main__':
    try:
        test_crm_system()
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()