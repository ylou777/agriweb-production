"""
Gestionnaire d'utilisateurs CRM pour HeliaPV
Gestion hiérarchique avec rôles admin, directeur commercial, commercial
"""

from models import db, User, Prospect, SavedSearch, ProspectInteraction
from flask import session, request
from datetime import datetime
import json
import uuid

class CRMUserManager:
    """Gestionnaire d'utilisateurs avec système CRM complet"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialise le gestionnaire avec l'application Flask"""
        app.config.update({
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///agriweb_crm.db',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False
        })
        db.init_app(app)
        
        with app.app_context():
            db.create_all()
            self._create_default_users()
    
    def _create_default_users(self):
        """Crée les utilisateurs par défaut si ils n'existent pas"""
        if not User.query.filter_by(email='admin@agriweb.com').first():
            # Admin principal
            admin = User(
                email='admin@agriweb.com',
                name='Administrateur Système',
                role='admin',
                license_type='enterprise',
                searches_limit=999999
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Directeur commercial
            director = User(
                email='directeur@agriweb.com',
                name='Directeur Commercial',
                role='directeur_commercial',
                license_type='professional',
                searches_limit=1000
            )
            director.set_password('director123')
            director.manager = admin
            db.session.add(director)
            
            # Commercial
            commercial = User(
                email='commercial@agriweb.com',
                name='Commercial Terrain',
                role='commercial',
                license_type='standard',
                searches_limit=100
            )
            commercial.set_password('commercial123')
            commercial.manager = director
            db.session.add(commercial)
            
            db.session.commit()
            print("✅ Utilisateurs CRM par défaut créés")
    
    # === AUTHENTIFICATION ===
    
    def authenticate_user(self, email, password):
        """Authentifie un utilisateur"""
        user = User.query.filter_by(email=email, active=True).first()
        if user and user.check_password(password):
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Stocker en session
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_role'] = user.role
            session['user_name'] = user.name
            
            return user
        return None
    
    def get_current_user(self):
        """Retourne l'utilisateur actuellement connecté"""
        user_id = session.get('user_id')
        if user_id:
            return User.query.get(user_id)
        return None
    
    def logout_user(self):
        """Déconnecte l'utilisateur"""
        session.clear()
    
    def require_login(self):
        """Vérifie que l'utilisateur est connecté"""
        return self.get_current_user() is not None
    
    def require_role(self, required_roles):
        """Vérifie que l'utilisateur a un des rôles requis"""
        user = self.get_current_user()
        if not user:
            return False
        if isinstance(required_roles, str):
            required_roles = [required_roles]
        return user.role in required_roles
    
    # === GESTION DES UTILISATEURS ===
    
    def create_user(self, email, password, name, role='commercial', manager_email=None):
        """Crée un nouvel utilisateur"""
        if User.query.filter_by(email=email).first():
            raise ValueError(f"L'utilisateur {email} existe déjà")
        
        # Vérifier les permissions
        current_user = self.get_current_user()
        if not current_user:
            raise PermissionError("Utilisateur non connecté")
        
        if not self._can_create_role(current_user, role):
            raise PermissionError(f"Permission insuffisante pour créer un {role}")
        
        # Créer l'utilisateur
        user = User(
            email=email,
            name=name,
            role=role,
            license_type=self._get_default_license(role),
            searches_limit=self._get_default_searches_limit(role)
        )
        user.set_password(password)
        
        # Assigner un manager
        if manager_email:
            manager = User.query.filter_by(email=manager_email).first()
            if manager:
                user.manager = manager
        elif role == 'commercial':
            # Assigner automatiquement au directeur si pas de manager spécifié
            director = User.query.filter_by(role='directeur_commercial').first()
            if director:
                user.manager = director
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    def _can_create_role(self, creator, target_role):
        """Vérifie si un utilisateur peut créer un rôle"""
        if creator.is_admin:
            return True
        if creator.is_director and target_role == 'commercial':
            return True
        return False
    
    def _get_default_license(self, role):
        """Retourne la licence par défaut pour un rôle"""
        licenses = {
            'admin': 'enterprise',
            'directeur_commercial': 'professional',
            'commercial': 'standard'
        }
        return licenses.get(role, 'trial')
    
    def _get_default_searches_limit(self, role):
        """Retourne la limite de recherches par défaut pour un rôle"""
        limits = {
            'admin': 999999,
            'directeur_commercial': 1000,
            'commercial': 100
        }
        return limits.get(role, 50)
    
    def get_team_members(self, user=None):
        """Retourne les membres de l'équipe visibles pour l'utilisateur"""
        if not user:
            user = self.get_current_user()
        
        if not user:
            return []
        
        if user.is_admin:
            return User.query.filter(User.id != user.id).all()
        elif user.is_director:
            return User.query.filter_by(manager_id=user.id).all()
        else:
            # Commercial voit ses collègues du même manager
            if user.manager:
                return User.query.filter(
                    User.manager_id == user.manager_id,
                    User.id != user.id
                ).all()
        
        return []
    
    # === GESTION DES PROSPECTS ===
    
    def create_prospect(self, company_name, **kwargs):
        """Crée un nouveau prospect"""
        current_user = self.get_current_user()
        if not current_user:
            raise PermissionError("Utilisateur non connecté")
        
        prospect = Prospect(
            company_name=company_name,
            created_by_id=current_user.id,
            **kwargs
        )
        
        # Auto-assignation selon les règles
        if not prospect.assigned_to_id:
            prospect.assigned_to_id = self._auto_assign_prospect(current_user)
        
        db.session.add(prospect)
        db.session.commit()
        
        return prospect
    
    def _auto_assign_prospect(self, creator):
        """Assigne automatiquement un prospect selon la hiérarchie"""
        if creator.is_commercial:
            return creator.id
        elif creator.is_director:
            # Assigner au commercial avec le moins de prospects
            commercials = User.query.filter_by(manager_id=creator.id).all()
            if commercials:
                min_prospects = min(len(c.assigned_prospects.all()) for c in commercials)
                for commercial in commercials:
                    if len(commercial.assigned_prospects.all()) == min_prospects:
                        return commercial.id
        return creator.id
    
    def get_user_prospects(self, user=None, status=None):
        """Retourne les prospects visibles pour l'utilisateur"""
        if not user:
            user = self.get_current_user()
        
        query = Prospect.query
        
        if user.is_admin:
            # Admin voit tous les prospects
            pass
        elif user.is_director:
            # Directeur voit ses prospects + ceux de son équipe
            team_ids = [u.id for u in user.get_subordinates()] + [user.id]
            query = query.filter(Prospect.assigned_to_id.in_(team_ids))
        else:
            # Commercial voit ses prospects
            query = query.filter_by(assigned_to_id=user.id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(Prospect.created_at.desc()).all()
    
    # === GESTION DES RECHERCHES SAUVEGARDÉES ===
    
    def save_search(self, name, search_params, **kwargs):
        """Sauvegarde une recherche"""
        current_user = self.get_current_user()
        if not current_user:
            raise PermissionError("Utilisateur non connecté")
        
        search = SavedSearch(
            name=name,
            user_id=current_user.id,
            **kwargs
        )
        search.set_search_params(search_params)
        
        db.session.add(search)
        db.session.commit()
        
        return search
    
    def get_user_searches(self, user=None, include_public=True):
        """Retourne les recherches de l'utilisateur"""
        if not user:
            user = self.get_current_user()
        
        query = SavedSearch.query.filter_by(user_id=user.id)
        
        if include_public:
            # Inclure les recherches publiques de l'équipe
            team_searches = SavedSearch.query.filter(
                SavedSearch.is_public == True,
                SavedSearch.user_id != user.id
            )
            
            if user.is_commercial and user.manager:
                # Commercial voit les recherches publiques de son équipe
                team_ids = [u.id for u in user.manager.get_subordinates()]
                team_searches = team_searches.filter(SavedSearch.user_id.in_(team_ids))
            
            # Combiner les requêtes
            query = query.union(team_searches)
        
        return query.order_by(SavedSearch.created_at.desc()).all()
    
    # === STATISTIQUES ET REPORTING ===
    
    def get_user_stats(self, user=None):
        """Retourne les statistiques de l'utilisateur"""
        if not user:
            user = self.get_current_user()
        
        prospects = self.get_user_prospects(user)
        
        stats = {
            'total_prospects': len(prospects),
            'prospects_by_status': {},
            'prospects_this_month': 0,
            'conversion_rate': 0,
            'searches_used': user.searches_used,
            'searches_remaining': user.searches_limit - user.searches_used
        }
        
        # Prospects par statut
        for prospect in prospects:
            status = prospect.status
            stats['prospects_by_status'][status] = stats['prospects_by_status'].get(status, 0) + 1
        
        # Prospects ce mois
        current_month = datetime.now().replace(day=1)
        stats['prospects_this_month'] = len([
            p for p in prospects if p.created_at >= current_month
        ])
        
        # Taux de conversion
        total = len(prospects)
        converted = stats['prospects_by_status'].get('converti', 0)
        if total > 0:
            stats['conversion_rate'] = round((converted / total) * 100, 1)
        
        return stats
    
    def get_team_stats(self, user=None):
        """Retourne les statistiques de l'équipe"""
        if not user:
            user = self.get_current_user()
        
        if not user.is_director and not user.is_admin:
            return None
        
        team_members = user.get_subordinates()
        team_stats = {
            'team_size': len(team_members),
            'total_prospects': 0,
            'team_performance': [],
            'monthly_evolution': {}
        }
        
        for member in team_members:
            member_prospects = self.get_user_prospects(member)
            member_stats = {
                'name': member.name,
                'email': member.email,
                'prospects_count': len(member_prospects),
                'converted_count': len([p for p in member_prospects if p.status == 'converti']),
                'conversion_rate': 0
            }
            
            if member_stats['prospects_count'] > 0:
                member_stats['conversion_rate'] = round(
                    (member_stats['converted_count'] / member_stats['prospects_count']) * 100, 1
                )
            
            team_stats['team_performance'].append(member_stats)
            team_stats['total_prospects'] += member_stats['prospects_count']
        
        return team_stats
    
    # === UTILITAIRES ===
    
    def increment_search_usage(self, user=None):
        """Incrémente l'utilisation des recherches"""
        if not user:
            user = self.get_current_user()
        
        if user and user.searches_used < user.searches_limit:
            user.searches_used += 1
            db.session.commit()
            return True
        return False
    
    def can_search(self, user=None):
        """Vérifie si l'utilisateur peut faire une recherche"""
        if not user:
            user = self.get_current_user()
        
        return user and user.searches_used < user.searches_limit