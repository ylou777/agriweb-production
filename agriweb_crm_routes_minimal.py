"""
Routes CRM minimales pour démarrage
"""

from flask import jsonify

# Import du bridge CRM
try:
    from agriweb_crm_bridge_intelligent import (
        integrate_agriweb_search_to_crm_intelligent, 
        get_sirene_analysis_for_widget,
        extract_prospects_from_commune_search_intelligent
    )
    CRM_ENABLED = True
except ImportError:
    CRM_ENABLED = False

def add_crm_routes(app):
    """Ajoute les routes CRM minimales à l'application Flask"""
    
    @app.route('/api/crm/status')
    def api_crm_status():
        """Status simple du CRM"""
        return jsonify({
            'crm_enabled': CRM_ENABLED,
            'status': 'active' if CRM_ENABLED else 'disabled'
        })
    
    @app.route('/crm/dashboard')
    def crm_dashboard_simple():
        """Dashboard CRM simple"""
        if not CRM_ENABLED:
            return jsonify({'error': 'CRM non disponible'}), 500
        
        return jsonify({
            'message': 'CRM Dashboard - Version simplifiée',
            'crm_enabled': True
        })