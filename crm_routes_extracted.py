"""
Routes CRM extraites de agriweb_hebergement_gratuit.py
Générées automatiquement le 2025-11-19 19:30:56

INSTRUCTIONS D'INTÉGRATION DANS agriweb_railway_deploy.py:

1. Vérifier les imports nécessaires en haut du fichier:
   - from datetime import datetime
   - import json
   - import sqlite3 (à remplacer par database_adapter)

2. Remplacer toutes les connexions SQLite directes par database_adapter:
   
   AVANT:
   conn = sqlite3.connect(CRM_DB_PATH)
   cursor = conn.cursor()
   cursor.execute("SELECT * FROM table WHERE id = ?", (id,))
   
   APRÈS:
   from database_adapter import execute_query
   results = execute_query("SELECT * FROM table WHERE id = %s", (id,), fetch_all=True)

3. Copier toutes les routes ci-dessous dans agriweb_railway_deploy.py
   AVANT la ligne: if __name__ == "__main__":

4. Vérifier que CRM_DB_PATH est défini ou utiliser database_adapter partout
"""

# Imports nécessaires
from datetime import datetime
import json

# Routes CRM
# ============================================================================
@app.route('/crm')
def crm_dashboard():
@app.route('/crm/stats')
def crm_stats_page():
@app.route('/crm/desktop')
def crm_desktop():
@app.route('/api/crm/stats')
def crm_stats():
@app.route('/api/crm/launch', methods=['POST'])
def crm_launch():
@app.route('/test/crm')
def test_crm():
@app.route('/test/rapport')
def test_rapport_rapide():
@app.route('/api/crm/export', methods=['POST'])
def crm_export():
@app.route('/api/crm/prospects')
def get_prospects():
@app.route('/api/crm/prospects/<int:prospect_id>', methods=['PUT'])
def update_prospect(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>', methods=['DELETE'])
def delete_prospect(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/send-email', methods=['POST'])
def send_prospect_email(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/appointment', methods=['POST'])
def create_prospect_appointment(prospect_id):
@app.route('/api/crm/appointments', methods=['GET'])
def get_all_appointments():
@app.route('/api/crm/prospects/<int:prospect_id>/proposal', methods=['POST'])
def save_prospect_proposal(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/proposal/pdf', methods=['POST'])
def generate_proposal_pdf(prospect_id):
@app.route('/api/crm/dashboard/stats')
def get_dashboard_stats():
@app.route('/api/crm/dashboard/users')
def get_dashboard_users():
@app.route('/crm/projets')
def crm_projets():
@app.route('/crm/calendrier')
def crm_calendrier():
@app.route('/api/crm/projets', methods=['GET'])
def get_projets():
@app.route('/api/crm/projets', methods=['POST'])
def create_projet():
@app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
def get_projet_details(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/crm/stats')
def crm_stats_page():
@app.route('/crm/desktop')
def crm_desktop():
@app.route('/api/crm/stats')
def crm_stats():
@app.route('/api/crm/launch', methods=['POST'])
def crm_launch():
@app.route('/test/crm')
def test_crm():
@app.route('/test/rapport')
def test_rapport_rapide():
@app.route('/api/crm/export', methods=['POST'])
def crm_export():
@app.route('/api/crm/prospects')
def get_prospects():
@app.route('/api/crm/prospects/<int:prospect_id>', methods=['PUT'])
def update_prospect(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>', methods=['DELETE'])
def delete_prospect(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/send-email', methods=['POST'])
def send_prospect_email(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/appointment', methods=['POST'])
def create_prospect_appointment(prospect_id):
@app.route('/api/crm/appointments', methods=['GET'])
def get_all_appointments():
@app.route('/api/crm/prospects/<int:prospect_id>/proposal', methods=['POST'])
def save_prospect_proposal(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/proposal/pdf', methods=['POST'])
def generate_proposal_pdf(prospect_id):
@app.route('/api/crm/dashboard/stats')
def get_dashboard_stats():
@app.route('/api/crm/dashboard/users')
def get_dashboard_users():
@app.route('/crm/projets')
def crm_projets():
@app.route('/crm/calendrier')
def crm_calendrier():
@app.route('/api/crm/projets', methods=['GET'])
def get_projets():
@app.route('/api/crm/projets', methods=['POST'])
def create_projet():
@app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
def get_projet_details(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/crm/desktop')
def crm_desktop():
@app.route('/api/crm/stats')
def crm_stats():
@app.route('/api/crm/launch', methods=['POST'])
def crm_launch():
@app.route('/test/crm')
def test_crm():
@app.route('/test/rapport')
def test_rapport_rapide():
@app.route('/api/crm/export', methods=['POST'])
def crm_export():
@app.route('/api/crm/prospects')
def get_prospects():
@app.route('/api/crm/prospects/<int:prospect_id>', methods=['PUT'])
def update_prospect(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>', methods=['DELETE'])
def delete_prospect(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/send-email', methods=['POST'])
def send_prospect_email(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/appointment', methods=['POST'])
def create_prospect_appointment(prospect_id):
@app.route('/api/crm/appointments', methods=['GET'])
def get_all_appointments():
@app.route('/api/crm/prospects/<int:prospect_id>/proposal', methods=['POST'])
def save_prospect_proposal(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/proposal/pdf', methods=['POST'])
def generate_proposal_pdf(prospect_id):
@app.route('/api/crm/dashboard/stats')
def get_dashboard_stats():
@app.route('/api/crm/dashboard/users')
def get_dashboard_users():
@app.route('/crm/projets')
def crm_projets():
@app.route('/crm/calendrier')
def crm_calendrier():
@app.route('/api/crm/projets', methods=['GET'])
def get_projets():
@app.route('/api/crm/projets', methods=['POST'])
def create_projet():
@app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
def get_projet_details(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/stats')
def crm_stats():
@app.route('/api/crm/launch', methods=['POST'])
def crm_launch():
@app.route('/test/crm')
def test_crm():
@app.route('/test/rapport')
def test_rapport_rapide():
@app.route('/api/crm/export', methods=['POST'])
def crm_export():
@app.route('/api/crm/prospects')
def get_prospects():
@app.route('/api/crm/prospects/<int:prospect_id>', methods=['PUT'])
def update_prospect(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>', methods=['DELETE'])
def delete_prospect(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/send-email', methods=['POST'])
def send_prospect_email(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/appointment', methods=['POST'])
def create_prospect_appointment(prospect_id):
@app.route('/api/crm/appointments', methods=['GET'])
def get_all_appointments():
@app.route('/api/crm/prospects/<int:prospect_id>/proposal', methods=['POST'])
def save_prospect_proposal(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/proposal/pdf', methods=['POST'])
def generate_proposal_pdf(prospect_id):
@app.route('/api/crm/dashboard/stats')
def get_dashboard_stats():
@app.route('/api/crm/dashboard/users')
def get_dashboard_users():
@app.route('/crm/projets')
def crm_projets():
@app.route('/crm/calendrier')
def crm_calendrier():
@app.route('/api/crm/projets', methods=['GET'])
def get_projets():
@app.route('/api/crm/projets', methods=['POST'])
def create_projet():
@app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
def get_projet_details(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/launch', methods=['POST'])
def crm_launch():
@app.route('/test/crm')
def test_crm():
@app.route('/test/rapport')
def test_rapport_rapide():
@app.route('/api/crm/export', methods=['POST'])
def crm_export():
@app.route('/api/crm/prospects')
def get_prospects():
@app.route('/api/crm/prospects/<int:prospect_id>', methods=['PUT'])
def update_prospect(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>', methods=['DELETE'])
def delete_prospect(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/send-email', methods=['POST'])
def send_prospect_email(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/appointment', methods=['POST'])
def create_prospect_appointment(prospect_id):
@app.route('/api/crm/appointments', methods=['GET'])
def get_all_appointments():
@app.route('/api/crm/prospects/<int:prospect_id>/proposal', methods=['POST'])
def save_prospect_proposal(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/proposal/pdf', methods=['POST'])
def generate_proposal_pdf(prospect_id):
@app.route('/api/crm/dashboard/stats')
def get_dashboard_stats():
@app.route('/api/crm/dashboard/users')
def get_dashboard_users():
@app.route('/crm/projets')
def crm_projets():
@app.route('/crm/calendrier')
def crm_calendrier():
@app.route('/api/crm/projets', methods=['GET'])
def get_projets():
@app.route('/api/crm/projets', methods=['POST'])
def create_projet():
@app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
def get_projet_details(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/export', methods=['POST'])
def crm_export():
@app.route('/api/crm/prospects')
def get_prospects():
@app.route('/api/crm/prospects/<int:prospect_id>', methods=['PUT'])
def update_prospect(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>', methods=['DELETE'])
def delete_prospect(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/send-email', methods=['POST'])
def send_prospect_email(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/appointment', methods=['POST'])
def create_prospect_appointment(prospect_id):
@app.route('/api/crm/appointments', methods=['GET'])
def get_all_appointments():
@app.route('/api/crm/prospects/<int:prospect_id>/proposal', methods=['POST'])
def save_prospect_proposal(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/proposal/pdf', methods=['POST'])
def generate_proposal_pdf(prospect_id):
@app.route('/api/crm/dashboard/stats')
def get_dashboard_stats():
@app.route('/api/crm/dashboard/users')
def get_dashboard_users():
@app.route('/crm/projets')
def crm_projets():
@app.route('/crm/calendrier')
def crm_calendrier():
@app.route('/api/crm/projets', methods=['GET'])
def get_projets():
@app.route('/api/crm/projets', methods=['POST'])
def create_projet():
@app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
def get_projet_details(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/prospects')
def get_prospects():
@app.route('/api/crm/prospects/<int:prospect_id>', methods=['PUT'])
def update_prospect(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>', methods=['DELETE'])
def delete_prospect(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/send-email', methods=['POST'])
def send_prospect_email(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/appointment', methods=['POST'])
def create_prospect_appointment(prospect_id):
@app.route('/api/crm/appointments', methods=['GET'])
def get_all_appointments():
@app.route('/api/crm/prospects/<int:prospect_id>/proposal', methods=['POST'])
def save_prospect_proposal(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/proposal/pdf', methods=['POST'])
def generate_proposal_pdf(prospect_id):
@app.route('/api/crm/dashboard/stats')
def get_dashboard_stats():
@app.route('/api/crm/dashboard/users')
def get_dashboard_users():
@app.route('/crm/projets')
def crm_projets():
@app.route('/crm/calendrier')
def crm_calendrier():
@app.route('/api/crm/projets', methods=['GET'])
def get_projets():
@app.route('/api/crm/projets', methods=['POST'])
def create_projet():
@app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
def get_projet_details(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/prospects/<int:prospect_id>', methods=['PUT'])
def update_prospect(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>', methods=['DELETE'])
def delete_prospect(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/send-email', methods=['POST'])
def send_prospect_email(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/appointment', methods=['POST'])
def create_prospect_appointment(prospect_id):
@app.route('/api/crm/appointments', methods=['GET'])
def get_all_appointments():
@app.route('/api/crm/prospects/<int:prospect_id>/proposal', methods=['POST'])
def save_prospect_proposal(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/proposal/pdf', methods=['POST'])
def generate_proposal_pdf(prospect_id):
@app.route('/api/crm/dashboard/stats')
def get_dashboard_stats():
@app.route('/api/crm/dashboard/users')
def get_dashboard_users():
@app.route('/crm/projets')
def crm_projets():
@app.route('/crm/calendrier')
def crm_calendrier():
@app.route('/api/crm/projets', methods=['GET'])
def get_projets():
@app.route('/api/crm/projets', methods=['POST'])
def create_projet():
@app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
def get_projet_details(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/prospects/<int:prospect_id>', methods=['DELETE'])
def delete_prospect(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/send-email', methods=['POST'])
def send_prospect_email(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/appointment', methods=['POST'])
def create_prospect_appointment(prospect_id):
@app.route('/api/crm/appointments', methods=['GET'])
def get_all_appointments():
@app.route('/api/crm/prospects/<int:prospect_id>/proposal', methods=['POST'])
def save_prospect_proposal(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/proposal/pdf', methods=['POST'])
def generate_proposal_pdf(prospect_id):
@app.route('/api/crm/dashboard/stats')
def get_dashboard_stats():
@app.route('/api/crm/dashboard/users')
def get_dashboard_users():
@app.route('/crm/projets')
def crm_projets():
@app.route('/crm/calendrier')
def crm_calendrier():
@app.route('/api/crm/projets', methods=['GET'])
def get_projets():
@app.route('/api/crm/projets', methods=['POST'])
def create_projet():
@app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
def get_projet_details(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/prospects/<int:prospect_id>/send-email', methods=['POST'])
def send_prospect_email(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/appointment', methods=['POST'])
def create_prospect_appointment(prospect_id):
@app.route('/api/crm/appointments', methods=['GET'])
def get_all_appointments():
@app.route('/api/crm/prospects/<int:prospect_id>/proposal', methods=['POST'])
def save_prospect_proposal(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/proposal/pdf', methods=['POST'])
def generate_proposal_pdf(prospect_id):
@app.route('/api/crm/dashboard/stats')
def get_dashboard_stats():
@app.route('/api/crm/dashboard/users')
def get_dashboard_users():
@app.route('/crm/projets')
def crm_projets():
@app.route('/crm/calendrier')
def crm_calendrier():
@app.route('/api/crm/projets', methods=['GET'])
def get_projets():
@app.route('/api/crm/projets', methods=['POST'])
def create_projet():
@app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
def get_projet_details(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/prospects/<int:prospect_id>/appointment', methods=['POST'])
def create_prospect_appointment(prospect_id):
@app.route('/api/crm/appointments', methods=['GET'])
def get_all_appointments():
@app.route('/api/crm/prospects/<int:prospect_id>/proposal', methods=['POST'])
def save_prospect_proposal(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/proposal/pdf', methods=['POST'])
def generate_proposal_pdf(prospect_id):
@app.route('/api/crm/dashboard/stats')
def get_dashboard_stats():
@app.route('/api/crm/dashboard/users')
def get_dashboard_users():
@app.route('/crm/projets')
def crm_projets():
@app.route('/crm/calendrier')
def crm_calendrier():
@app.route('/api/crm/projets', methods=['GET'])
def get_projets():
@app.route('/api/crm/projets', methods=['POST'])
def create_projet():
@app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
def get_projet_details(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/appointments', methods=['GET'])
def get_all_appointments():
@app.route('/api/crm/prospects/<int:prospect_id>/proposal', methods=['POST'])
def save_prospect_proposal(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/proposal/pdf', methods=['POST'])
def generate_proposal_pdf(prospect_id):
@app.route('/api/crm/dashboard/stats')
def get_dashboard_stats():
@app.route('/api/crm/dashboard/users')
def get_dashboard_users():
@app.route('/crm/projets')
def crm_projets():
@app.route('/crm/calendrier')
def crm_calendrier():
@app.route('/api/crm/projets', methods=['GET'])
def get_projets():
@app.route('/api/crm/projets', methods=['POST'])
def create_projet():
@app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
def get_projet_details(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/prospects/<int:prospect_id>/proposal', methods=['POST'])
def save_prospect_proposal(prospect_id):
@app.route('/api/crm/prospects/<int:prospect_id>/proposal/pdf', methods=['POST'])
def generate_proposal_pdf(prospect_id):
@app.route('/api/crm/dashboard/stats')
def get_dashboard_stats():
@app.route('/api/crm/dashboard/users')
def get_dashboard_users():
@app.route('/crm/projets')
def crm_projets():
@app.route('/crm/calendrier')
def crm_calendrier():
@app.route('/api/crm/projets', methods=['GET'])
def get_projets():
@app.route('/api/crm/projets', methods=['POST'])
def create_projet():
@app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
def get_projet_details(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/prospects/<int:prospect_id>/proposal/pdf', methods=['POST'])
def generate_proposal_pdf(prospect_id):
@app.route('/api/crm/dashboard/stats')
def get_dashboard_stats():
@app.route('/api/crm/dashboard/users')
def get_dashboard_users():
@app.route('/crm/projets')
def crm_projets():
@app.route('/crm/calendrier')
def crm_calendrier():
@app.route('/api/crm/projets', methods=['GET'])
def get_projets():
@app.route('/api/crm/projets', methods=['POST'])
def create_projet():
@app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
def get_projet_details(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/dashboard/stats')
def get_dashboard_stats():
@app.route('/api/crm/dashboard/users')
def get_dashboard_users():
@app.route('/crm/projets')
def crm_projets():
@app.route('/crm/calendrier')
def crm_calendrier():
@app.route('/api/crm/projets', methods=['GET'])
def get_projets():
@app.route('/api/crm/projets', methods=['POST'])
def create_projet():
@app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
def get_projet_details(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/dashboard/users')
def get_dashboard_users():
@app.route('/crm/projets')
def crm_projets():
@app.route('/crm/calendrier')
def crm_calendrier():
@app.route('/api/crm/projets', methods=['GET'])
def get_projets():
@app.route('/api/crm/projets', methods=['POST'])
def create_projet():
@app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
def get_projet_details(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/crm/projets')
def crm_projets():
@app.route('/crm/calendrier')
def crm_calendrier():
@app.route('/api/crm/projets', methods=['GET'])
def get_projets():
@app.route('/api/crm/projets', methods=['POST'])
def create_projet():
@app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
def get_projet_details(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/crm/calendrier')
def crm_calendrier():
@app.route('/api/crm/projets', methods=['GET'])
def get_projets():
@app.route('/api/crm/projets', methods=['POST'])
def create_projet():
@app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
def get_projet_details(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/projets', methods=['GET'])
def get_projets():
@app.route('/api/crm/projets', methods=['POST'])
def create_projet():
@app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
def get_projet_details(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/projets', methods=['POST'])
def create_projet():
@app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
def get_projet_details(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
def get_projet_details(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
def update_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
def delete_projet(project_id):
@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
def update_etape(project_id, etape_id):
@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
def add_document(project_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
def update_document(project_id, doc_id):
@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):

@app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(project_id, doc_id):


