"""
Système de sauvegarde de recherches et création automatique de prospects
"""

from models import db, SavedSearch, Prospect, User
from crm_manager import CRMUserManager
import json
from datetime import datetime

class SearchProspectManager:
    """Gestionnaire pour les recherches sauvegardées et création automatique de prospects"""
    
    def __init__(self, crm_manager):
        self.crm_manager = crm_manager
    
    def save_search_with_results(self, name, search_params, results_data, **kwargs):
        """
        Sauvegarde une recherche avec ses résultats et crée des prospects si demandé
        
        Args:
            name: Nom de la recherche
            search_params: Paramètres de recherche (dict)
            results_data: Données des résultats de recherche
            **kwargs: Autres options (auto_create_prospects, tags, etc.)
        """
        current_user = self.crm_manager.get_current_user()
        if not current_user:
            raise PermissionError("Utilisateur non connecté")
        
        # Créer la recherche sauvegardée
        search = SavedSearch(
            name=name,
            user_id=current_user.id,
            description=kwargs.get('description', ''),
            department=kwargs.get('department'),
            city=kwargs.get('city'),
            category=kwargs.get('category', 'general'),
            is_public=kwargs.get('is_public', False),
            auto_prospect=kwargs.get('auto_create_prospects', False)
        )
        
        search.set_search_params(search_params)
        
        # Ajouter des tags si fournis
        if 'tags' in kwargs:
            for tag in kwargs['tags']:
                search.add_tag(tag)
        
        db.session.add(search)
        db.session.flush()  # Pour obtenir l'ID de la recherche
        
        # Créer automatiquement des prospects si demandé
        created_prospects = []
        if kwargs.get('auto_create_prospects', False) and results_data:
            created_prospects = self._create_prospects_from_results(
                search, results_data, current_user
            )
        
        db.session.commit()
        
        return {
            'search': search,
            'prospects_created': len(created_prospects),
            'prospects': created_prospects
        }
    
    def _create_prospects_from_results(self, search, results_data, user):
        """
        Crée des prospects à partir des résultats de recherche
        
        Args:
            search: Object SavedSearch
            results_data: Données des résultats (dict avec coordonnées, adresses, etc.)
            user: Utilisateur créateur
        """
        prospects = []
        
        # Parser les résultats selon le format des données
        if 'features' in results_data:
            # Format GeoJSON
            for feature in results_data['features'][:10]:  # Limiter à 10 prospects max
                prospect_data = self._parse_geojson_feature(feature)
                if prospect_data:
                    prospect = self._create_prospect_from_data(
                        prospect_data, search, user
                    )
                    if prospect:
                        prospects.append(prospect)
        
        elif 'results' in results_data:
            # Format résultats de recherche classique
            for result in results_data['results'][:10]:
                prospect_data = self._parse_search_result(result)
                if prospect_data:
                    prospect = self._create_prospect_from_data(
                        prospect_data, search, user
                    )
                    if prospect:
                        prospects.append(prospect)
        
        return prospects
    
    def _parse_geojson_feature(self, feature):
        """Parse une feature GeoJSON pour extraire les données prospect"""
        properties = feature.get('properties', {})
        geometry = feature.get('geometry', {})
        
        # Extraire les coordonnées
        coords = None
        if geometry.get('type') == 'Point':
            coords = geometry.get('coordinates')
        elif geometry.get('type') in ['Polygon', 'MultiPolygon']:
            # Calculer le centroïde pour les polygones
            coords = self._calculate_centroid(geometry)
        
        # Extraire les informations d'adresse
        address_info = self._extract_address_from_properties(properties)
        
        return {
            'company_name': self._generate_company_name(properties, address_info),
            'address': address_info.get('address'),
            'city': address_info.get('city'),
            'postal_code': address_info.get('postal_code'),
            'coordinates': f"{coords[1]},{coords[0]}" if coords else None,
            'source_properties': properties
        }
    
    def _parse_search_result(self, result):
        """Parse un résultat de recherche classique"""
        return {
            'company_name': result.get('name', 'Prospect sans nom'),
            'address': result.get('address'),
            'city': result.get('city'),
            'postal_code': result.get('postal_code'),
            'coordinates': result.get('coordinates'),
            'contact_email': result.get('email'),
            'contact_phone': result.get('phone'),
            'source_properties': result
        }
    
    def _extract_address_from_properties(self, properties):
        """Extrait l'adresse des propriétés d'une feature"""
        address_fields = ['addr:street', 'addr:housenumber', 'name', 'street']
        city_fields = ['addr:city', 'city']
        postal_fields = ['addr:postcode', 'postal_code']
        
        address_parts = []
        
        # Numéro et rue
        house_number = properties.get('addr:housenumber', '')
        street = properties.get('addr:street', properties.get('street', ''))
        
        if house_number and street:
            address_parts.append(f"{house_number} {street}")
        elif street:
            address_parts.append(street)
        
        # Ville
        city = None
        for field in city_fields:
            if properties.get(field):
                city = properties[field]
                break
        
        # Code postal
        postal_code = None
        for field in postal_fields:
            if properties.get(field):
                postal_code = properties[field]
                break
        
        return {
            'address': ' '.join(address_parts) if address_parts else None,
            'city': city,
            'postal_code': postal_code
        }
    
    def _generate_company_name(self, properties, address_info):
        """Génère un nom de société basé sur les propriétés disponibles"""
        
        # Essayer d'abord les champs de nom
        name_fields = ['name', 'operator', 'brand', 'amenity', 'landuse', 'building']
        
        for field in name_fields:
            if properties.get(field):
                name = properties[field]
                if name and name != 'yes':  # Éviter les valeurs génériques
                    return name
        
        # Si pas de nom, utiliser l'adresse
        if address_info.get('address'):
            city = address_info.get('city', 'Ville inconnue')
            return f"Prospect - {address_info['address']}, {city}"
        
        # Dernier recours
        return f"Prospect - {address_info.get('city', 'Localisation inconnue')}"
    
    def _calculate_centroid(self, geometry):
        """Calcule le centroïde d'un polygone"""
        # Implémentation simplifiée - prendre le premier point du premier ring
        coords = geometry.get('coordinates', [])
        if coords and len(coords) > 0:
            if isinstance(coords[0][0], list):  # Polygon
                return coords[0][0]  # Premier point du premier ring
            else:  # MultiPolygon
                return coords[0][0][0]  # Premier point du premier polygon
        return None
    
    def _create_prospect_from_data(self, prospect_data, search, user):
        """Crée un prospect à partir des données extraites"""
        try:
            # Vérifier si un prospect similaire existe déjà
            existing = Prospect.query.filter(
                Prospect.company_name == prospect_data['company_name'],
                Prospect.address == prospect_data['address']
            ).first()
            
            if existing:
                return None  # Éviter les doublons
            
            prospect = Prospect(
                company_name=prospect_data['company_name'],
                contact_email=prospect_data.get('contact_email'),
                contact_phone=prospect_data.get('contact_phone'),
                address=prospect_data.get('address'),
                city=prospect_data.get('city'),
                postal_code=prospect_data.get('postal_code'),
                coordinates=prospect_data.get('coordinates'),
                source='recherche_automatique',
                source_search_id=search.id,
                created_by_id=user.id,
                status='nouveau',
                priority='normale'
            )
            
            # Auto-assignation selon les règles CRM
            prospect.assigned_to_id = self._auto_assign_prospect(user)
            
            # Ajouter des tags basés sur la recherche
            prospect.add_tag('auto-généré')
            if search.category:
                prospect.add_tag(search.category)
            
            # Ajouter des métadonnées dans les notes
            notes = [
                f"Prospect créé automatiquement depuis la recherche '{search.name}'",
                f"Date de création: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            ]
            
            if prospect_data.get('source_properties'):
                notes.append("Propriétés source:")
                for key, value in prospect_data['source_properties'].items():
                    if value and value != 'yes':
                        notes.append(f"  {key}: {value}")
            
            prospect.notes = '\n'.join(notes)
            
            db.session.add(prospect)
            return prospect
            
        except Exception as e:
            print(f"Erreur lors de la création du prospect: {e}")
            return None
    
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
    
    def get_search_statistics(self, search_id):
        """Retourne les statistiques d'une recherche sauvegardée"""
        search = SavedSearch.query.get(search_id)
        if not search:
            return None
        
        # Compter les prospects générés
        prospects_count = Prospect.query.filter_by(source_search_id=search_id).count()
        
        # Compter les prospects convertis
        converted_count = Prospect.query.filter(
            Prospect.source_search_id == search_id,
            Prospect.status == 'converti'
        ).count()
        
        # Taux de conversion
        conversion_rate = (converted_count / prospects_count * 100) if prospects_count > 0 else 0
        
        return {
            'search_name': search.name,
            'usage_count': search.usage_count,
            'prospects_generated': prospects_count,
            'prospects_converted': converted_count,
            'conversion_rate': round(conversion_rate, 1),
            'roi_estimated': converted_count * 5000  # Estimation 5000€ par conversion
        }
    
    def execute_saved_search(self, search_id, create_new_prospects=False):
        """
        Exécute une recherche sauvegardée et optionnellement crée de nouveaux prospects
        """
        search = SavedSearch.query.get(search_id)
        if not search:
            raise ValueError("Recherche introuvable")
        
        current_user = self.crm_manager.get_current_user()
        if not current_user:
            raise PermissionError("Utilisateur non connecté")
        
        # Incrémenter le compteur d'utilisation
        search.increment_usage()
        
        # Récupérer les paramètres de recherche
        params = search.get_search_params()
        
        # Ici, on appellerait la fonction de recherche existante
        # Pour l'instant, on retourne un placeholder
        results = {
            'success': True,
            'search_executed': search.name,
            'parameters': params,
            'message': 'Recherche exécutée avec succès'
        }
        
        # Si demandé, créer de nouveaux prospects
        if create_new_prospects and search.auto_prospect:
            # Ici on intégrerait avec le système de recherche existant
            pass
        
        db.session.commit()
        return results