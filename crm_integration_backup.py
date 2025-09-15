"""
Système d'intégration pour la création automatique de prospects
Module pour connecter les recherches AgriWeb avec le CRM
"""

import json
import sqlite3
import uuid
from datetime import datetime

class AgriWebCRMIntegrator:
    """Intégrateur pour connecter les recherches AgriWeb au système CRM"""
    
    def __init__(self, db_path='agriweb_crm.db'):
        self.db_path = db_path
    
    def create_prospects_from_search_results(self, search_results, search_name, user_id, auto_assign=True):
        """
        Crée des prospects à partir des résultats de recherche AgriWeb
        
        Args:
            search_results: Résultats de recherche (dict avec features GeoJSON)
            search_name: Nom de la recherche
            user_id: ID de l'utilisateur qui lance la recherche
            auto_assign: Assigner automatiquement selon la hiérarchie
        
        Returns:
            dict: Résumé de la création (prospects créés, erreurs, etc.)
        """
        
        summary = {
            'prospects_created': 0,
            'prospects_skipped': 0,
            'errors': [],
            'created_prospect_ids': []
        }
        
        if not search_results or 'features' not in search_results:
            summary['errors'].append("Aucun résultat de recherche fourni")
            return summary
        
        # D'abord, sauvegarder la recherche
        search_id = self._save_search_if_needed(search_name, search_results, user_id)
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Récupérer les infos utilisateur pour l'assignation
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            summary['errors'].append(f"Utilisateur {user_id} introuvable")
            conn.close()
            return summary
        
        # Traiter chaque feature
        for feature in search_results['features'][:20]:  # Limiter à 20 prospects max
            try:
                prospect_data = self._extract_prospect_from_feature(feature, search_id, user_id)
                
                if prospect_data:
                    # Vérifier si le prospect existe déjà
                    if self._prospect_exists(cursor, prospect_data['company_name'], prospect_data.get('address')):
                        summary['prospects_skipped'] += 1
                        continue
                    
                    # Déterminer l'assignation
                    assigned_to_id = user_id
                    if auto_assign:
                        assigned_to_id = self._determine_assignment(cursor, user)
                    
                    prospect_data['assigned_to_id'] = assigned_to_id
                    
                    # Créer le prospect
                    prospect_id = self._create_prospect(cursor, prospect_data)
                    
                    if prospect_id:
                        summary['prospects_created'] += 1
                        summary['created_prospect_ids'].append(prospect_id)
                    
            except Exception as e:
                summary['errors'].append(f"Erreur traitement feature: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return summary
    
    def _save_search_if_needed(self, search_name, search_results, user_id):
        """Sauvegarde la recherche si elle n'existe pas déjà"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Vérifier si une recherche similaire existe
        cursor.execute("""
            SELECT id FROM saved_searches 
            WHERE name = ? AND user_id = ?
        """, (search_name, user_id))
        
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return existing[0]
        
        # Créer nouvelle recherche
        search_id = str(uuid.uuid4())
        search_params = {
            'type': 'auto_search',
            'features_count': len(search_results.get('features', [])),
            'timestamp': datetime.now().isoformat()
        }
        
        cursor.execute('''
            INSERT INTO saved_searches (
                id, name, description, search_params, user_id, 
                category, auto_prospect, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            search_id, search_name,
            f"Recherche automatique générée le {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            json.dumps(search_params), user_id, 'auto_generated', True
        ))
        
        conn.commit()
        conn.close()
        return search_id
    
    def _extract_prospect_from_feature(self, feature, search_id, created_by_id):
        """Extrait les données prospect d'une feature GeoJSON"""
        properties = feature.get('properties', {})
        geometry = feature.get('geometry', {})
        
        # Extraire les coordonnées
        coordinates = None
        if geometry.get('type') == 'Point':
            coords = geometry.get('coordinates', [])
            if len(coords) >= 2:
                coordinates = f"{coords[1]},{coords[0]}"  # lat,lng
        
        # Extraire le nom de la société
        company_name = self._extract_company_name(properties)
        if not company_name:
            return None
        
        # Extraire l'adresse
        address_info = self._extract_address_info(properties)
        
        # Déterminer la catégorie du prospect
        category = self._determine_prospect_category(properties)
        
        # Construire les notes
        notes = self._build_prospect_notes(properties, feature, search_id)
        
        return {
            'id': str(uuid.uuid4()),
            'company_name': company_name,
            'address': address_info.get('address'),
            'city': address_info.get('city'),
            'postal_code': address_info.get('postal_code'),
            'coordinates': coordinates,
            'source': 'recherche_automatique',
            'source_search_id': search_id,
            'created_by_id': created_by_id,
            'status': 'nouveau',
            'priority': 'normale',
            'notes': notes,
            'tags': json.dumps([category, 'auto-généré'] if category else ['auto-généré'])
        }
    
    def _extract_company_name(self, properties):
        """Extrait le nom de société des propriétés"""
        name_fields = ['name', 'operator', 'brand', 'company', 'denomination']
        
        for field in name_fields:
            value = properties.get(field)
            if value and str(value).strip() and str(value).lower() not in ['yes', 'no', 'unknown']:
                return str(value).strip()
        
        # Si pas de nom spécifique, utiliser le type d'activité
        activity_fields = ['amenity', 'landuse', 'leisure', 'shop', 'craft', 'office']
        for field in activity_fields:
            value = properties.get(field)
            if value and str(value).strip():
                return f"Entreprise {str(value).title()}"
        
        # Dernier recours
        if properties.get('siret'):
            return f"Entreprise SIRET {properties['siret']}"
        
        return "Prospect sans nom"
    
    def _extract_address_info(self, properties):
        """Extrait les informations d'adresse"""
        address_parts = []
        
        # Numéro et rue
        house_number = properties.get('addr:housenumber', '')
        street = properties.get('addr:street', properties.get('street', ''))
        
        if house_number and street:
            address_parts.append(f"{house_number} {street}")
        elif street:
            address_parts.append(street)
        
        return {
            'address': ' '.join(address_parts) if address_parts else None,
            'city': properties.get('addr:city', properties.get('city', '')),
            'postal_code': properties.get('addr:postcode', properties.get('postal_code', ''))
        }
    
    def _determine_prospect_category(self, properties):
        """Détermine la catégorie du prospect basée sur les propriétés"""
        
        # Agriculture
        agriculture_indicators = ['farm', 'agricultural', 'agriculture', 'barn', 'silo', 'greenhouse']
        landuse_agriculture = ['farmland', 'farmyard', 'vineyard', 'orchard']
        
        for indicator in agriculture_indicators:
            for value in properties.values():
                if indicator in str(value).lower():
                    return 'agriculture'
        
        if properties.get('landuse') in landuse_agriculture:
            return 'agriculture'
        
        # Industrie
        industry_indicators = ['industrial', 'factory', 'warehouse', 'manufacture']
        if properties.get('landuse') == 'industrial':
            return 'industrie'
        
        for indicator in industry_indicators:
            for value in properties.values():
                if indicator in str(value).lower():
                    return 'industrie'
        
        # Commercial
        commercial_indicators = ['shop', 'office', 'commercial', 'retail']
        if properties.get('landuse') == 'commercial':
            return 'commercial'
        
        for indicator in commercial_indicators:
            for value in properties.values():
                if indicator in str(value).lower():
                    return 'commercial'
        
        return 'général'
    
    def _build_prospect_notes(self, properties, feature, search_id):
        """Construit les notes du prospect"""
        notes = []
        notes.append(f"Prospect créé automatiquement le {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        notes.append(f"Source: Recherche géographique (ID: {search_id})")
        
        # Ajouter les propriétés importantes
        important_props = ['amenity', 'landuse', 'building', 'operator', 'phone', 'website', 'siret']
        for prop in important_props:
            value = properties.get(prop)
            if value and str(value).strip():
                notes.append(f"{prop.title()}: {value}")
        
        return '\n'.join(notes)
    
    def _prospect_exists(self, cursor, company_name, address):
        """Vérifie si un prospect similaire existe déjà"""
        cursor.execute("""
            SELECT id FROM prospects 
            WHERE company_name = ? 
            OR (address IS NOT NULL AND address = ?)
        """, (company_name, address))
        
        return cursor.fetchone() is not None
    
    def _determine_assignment(self, cursor, user):
        """Détermine l'assignation du prospect selon la hiérarchie"""
        user_role = user['role']
        
        if user_role == 'commercial':
            return user['id']
        
        elif user_role == 'directeur_commercial':
            # Assigner au commercial avec le moins de prospects
            cursor.execute("""
                SELECT u.id, COUNT(p.id) as prospect_count
                FROM users u
                LEFT JOIN prospects p ON u.id = p.assigned_to_id
                WHERE u.manager_id = ?
                GROUP BY u.id
                ORDER BY prospect_count ASC
                LIMIT 1
            """, (user['id'],))
            
            result = cursor.fetchone()
            return result['id'] if result else user['id']
        
        else:  # admin
            # Assigner au directeur commercial par défaut
            cursor.execute("""
                SELECT id FROM users 
                WHERE role = 'directeur_commercial' 
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            return result['id'] if result else user['id']
    
    def _create_prospect(self, cursor, prospect_data):
        """Crée un prospect en base de données"""
        try:
            cursor.execute('''
                INSERT INTO prospects (
                    id, company_name, address, city, postal_code, coordinates,
                    source, source_search_id, created_by_id, assigned_to_id,
                    status, priority, notes, tags, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                prospect_data['id'], prospect_data['company_name'],
                prospect_data['address'], prospect_data['city'], prospect_data['postal_code'],
                prospect_data['coordinates'], prospect_data['source'], prospect_data['source_search_id'],
                prospect_data['created_by_id'], prospect_data['assigned_to_id'],
                prospect_data['status'], prospect_data['priority'],
                prospect_data['notes'], prospect_data['tags']
            ))
            
            return prospect_data['id']
            
        except Exception as e:
            print(f"Erreur création prospect: {e}")
            return None
    
    def get_integration_stats(self, user_id):
        """Retourne les statistiques d'intégration pour un utilisateur"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Prospects créés automatiquement
        cursor.execute("""
            SELECT COUNT(*) as count FROM prospects 
            WHERE source = 'recherche_automatique' AND created_by_id = ?
        """, (user_id,))
        auto_prospects = cursor.fetchone()['count']
        
        # Recherches avec auto-création activée
        cursor.execute("""
            SELECT COUNT(*) as count FROM saved_searches 
            WHERE auto_prospect = 1 AND user_id = ?
        """, (user_id,))
        auto_searches = cursor.fetchone()['count']
        
        conn.close()
        
        return {
            'auto_prospects_created': auto_prospects,
            'auto_searches_configured': auto_searches
        }

# Fonction utilitaire pour l'intégration
def integrate_search_results_to_crm(search_results, search_name, user_session_data):
    """
    Fonction utilitaire pour intégrer facilement les résultats de recherche au CRM
    
    Args:
        search_results: Résultats de recherche GeoJSON
        search_name: Nom de la recherche
        user_session_data: Données de session utilisateur (doit contenir user_id)
    """
    
    if not user_session_data or 'user_id' not in user_session_data:
        return {'success': False, 'error': 'Session utilisateur invalide'}
    
    try:
        integrator = AgriWebCRMIntegrator()
        summary = integrator.create_prospects_from_search_results(
            search_results, search_name, user_session_data['user_id']
        )
        
        return {
            'success': True,
            'message': f"Intégration terminée: {summary['prospects_created']} prospects créés",
            'summary': summary
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Erreur d'intégration: {str(e)}"
        }