"""
Modèles de base de données pour le système CRM AgriWeb
Hiérarchie commerciale: Admin > Directeur Commercial > Commercial
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

db = SQLAlchemy()

class User(db.Model):
    """Modèle utilisateur avec rôles hiérarchiques"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    
    # Système de rôles
    role = db.Column(db.Enum('admin', 'directeur_commercial', 'commercial', name='user_roles'), 
                     nullable=False, default='commercial')
    
    # Hiérarchie commerciale
    manager_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    manager = db.relationship('User', remote_side=[id], backref='subordinates')
    
    # Informations de licence
    license_type = db.Column(db.String(20), default='trial')
    searches_used = db.Column(db.Integer, default=0)
    searches_limit = db.Column(db.Integer, default=50)
    
    # Statut
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relations
    saved_searches = db.relationship('SavedSearch', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    assigned_prospects = db.relationship('Prospect', foreign_keys='Prospect.assigned_to_id', backref='assigned_to', lazy='dynamic')
    created_prospects = db.relationship('Prospect', foreign_keys='Prospect.created_by_id', backref='created_by', lazy='dynamic')
    
    def set_password(self, password):
        """Hash et stocke le mot de passe"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Vérifie le mot de passe"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_admin(self):
        """Vérifie si l'utilisateur est admin"""
        return self.role == 'admin'
    
    @property
    def is_director(self):
        """Vérifie si l'utilisateur est directeur commercial"""
        return self.role == 'directeur_commercial'
    
    @property
    def is_commercial(self):
        """Vérifie si l'utilisateur est commercial"""
        return self.role == 'commercial'
    
    def can_manage_user(self, other_user):
        """Vérifie si cet utilisateur peut gérer un autre utilisateur"""
        if self.is_admin:
            return True
        if self.is_director and other_user.role == 'commercial':
            return True
        return False
    
    def get_subordinates(self):
        """Retourne tous les subordonnés (récursif pour admin)"""
        if self.is_admin:
            return User.query.filter(User.role != 'admin').all()
        elif self.is_director:
            return User.query.filter_by(manager_id=self.id).all()
        return []
    
    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class Prospect(db.Model):
    """Modèle prospect pour la gestion commerciale"""
    __tablename__ = 'prospects'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Informations de base
    company_name = db.Column(db.String(200), nullable=False)
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    contact_name = db.Column(db.String(100))
    
    # Adresse et localisation
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    postal_code = db.Column(db.String(10))
    department = db.Column(db.String(3))  # Code département
    coordinates = db.Column(db.String(50))  # "lat,lng"
    
    # Statut commercial
    status = db.Column(db.Enum('nouveau', 'contacte', 'interesse', 'negocie', 'converti', 'perdu', 
                              name='prospect_status'), default='nouveau')
    priority = db.Column(db.Enum('basse', 'normale', 'haute', 'critique', name='prospect_priority'), 
                        default='normale')
    
    # Source du prospect
    source = db.Column(db.String(50))  # 'recherche_automatique', 'import_manuel', 'recommandation'
    source_search_id = db.Column(db.String(36), db.ForeignKey('saved_searches.id'), nullable=True)
    
    # Assignation
    assigned_to_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    created_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Métadonnées
    notes = db.Column(db.Text)
    tags = db.Column(db.Text)  # JSON string pour stockage de tags
    estimated_value = db.Column(db.Float)  # Valeur estimée du contrat
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_contact = db.Column(db.DateTime)
    next_action_date = db.Column(db.DateTime)
    converted_at = db.Column(db.DateTime)
    
    # Relations
    interactions = db.relationship('ProspectInteraction', backref='prospect', lazy='dynamic', 
                                 cascade='all, delete-orphan')
    source_search = db.relationship('SavedSearch', backref='generated_prospects')
    
    def add_tag(self, tag):
        """Ajoute un tag au prospect"""
        import json
        current_tags = json.loads(self.tags) if self.tags else []
        if tag not in current_tags:
            current_tags.append(tag)
            self.tags = json.dumps(current_tags)
    
    def get_tags(self):
        """Retourne la liste des tags"""
        import json
        return json.loads(self.tags) if self.tags else []
    
    def __repr__(self):
        return f'<Prospect {self.company_name} ({self.status})>'


class SavedSearch(db.Model):
    """Modèle pour les recherches sauvegardées"""
    __tablename__ = 'saved_searches'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Informations de base
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Paramètres de recherche (stockés en JSON)
    search_params = db.Column(db.Text, nullable=False)  # JSON des paramètres de recherche
    
    # Géographie
    department = db.Column(db.String(3))
    city = db.Column(db.String(100))
    coordinates = db.Column(db.String(50))  # Centre de la recherche
    radius = db.Column(db.Integer)  # Rayon en km
    
    # Catégorisation
    tags = db.Column(db.Text)  # JSON string pour tags
    category = db.Column(db.String(50))  # agriculture, industrie, résidentiel, etc.
    
    # Propriétaire et partage
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=False)  # Visible par l'équipe
    auto_prospect = db.Column(db.Boolean, default=False)  # Créer auto des prospects
    
    # Statistiques
    usage_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime)
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_search_params(self):
        """Retourne les paramètres de recherche décodés"""
        import json
        return json.loads(self.search_params) if self.search_params else {}
    
    def set_search_params(self, params):
        """Encode et stocke les paramètres de recherche"""
        import json
        self.search_params = json.dumps(params)
    
    def get_tags(self):
        """Retourne la liste des tags"""
        import json
        return json.loads(self.tags) if self.tags else []
    
    def add_tag(self, tag):
        """Ajoute un tag à la recherche"""
        import json
        current_tags = json.loads(self.tags) if self.tags else []
        if tag not in current_tags:
            current_tags.append(tag)
            self.tags = json.dumps(current_tags)
    
    def increment_usage(self):
        """Incrémente le compteur d'utilisation"""
        self.usage_count += 1
        self.last_used = datetime.utcnow()
    
    def __repr__(self):
        return f'<SavedSearch {self.name} by {self.user.email}>'


class ProspectInteraction(db.Model):
    """Modèle pour les interactions avec les prospects"""
    __tablename__ = 'prospect_interactions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Relations
    prospect_id = db.Column(db.String(36), db.ForeignKey('prospects.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Type d'interaction
    type = db.Column(db.Enum('appel', 'email', 'rencontre', 'demonstration', 'proposition', 'suivi', 
                            name='interaction_types'), nullable=False)
    
    # Contenu
    subject = db.Column(db.String(200))
    content = db.Column(db.Text)
    outcome = db.Column(db.String(100))  # Résultat de l'interaction
    
    # Planification
    scheduled_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    next_action = db.Column(db.String(200))
    next_action_date = db.Column(db.DateTime)
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    user = db.relationship('User', backref='interactions')
    
    def __repr__(self):
        return f'<Interaction {self.type} for {self.prospect.company_name}>'


# Fonction utilitaire pour initialiser la base de données
def init_db(app):
    """Initialise la base de données avec les tables et données de base"""
    db.init_app(app)
    
    with app.app_context():
        # Créer toutes les tables
        db.create_all()
        
        # Créer un utilisateur admin par défaut s'il n'existe pas
        admin = User.query.filter_by(email='admin@agriweb.com').first()
        if not admin:
            admin = User(
                email='admin@agriweb.com',
                name='Administrateur Système',
                role='admin',
                license_type='enterprise',
                searches_limit=999999
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Créer un directeur commercial de démonstration
            director = User(
                email='directeur@agriweb.com',
                name='Directeur Commercial',
                role='directeur_commercial',
                license_type='professional',
                searches_limit=1000,
                manager_id=admin.id
            )
            director.set_password('director123')
            db.session.add(director)
            
            # Créer un commercial de démonstration
            commercial = User(
                email='commercial@agriweb.com',
                name='Commercial',
                role='commercial',
                license_type='standard',
                searches_limit=100,
                manager_id=director.id
            )
            commercial.set_password('commercial123')
            db.session.add(commercial)
            
            db.session.commit()
            print("✅ Base de données CRM initialisée avec utilisateurs de démonstration")


# Configuration de la base de données
DATABASE_CONFIG = {
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///agriweb_crm.db',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SQLALCHEMY_ENGINE_OPTIONS': {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
}