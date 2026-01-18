"""
Script pour réduire le nombre de prospects dans PostgreSQL Railway
Supprime la moitié des prospects les plus anciens
"""

import os
from database_adapter import execute_query

def reduce_prospects():
    """Supprime 1000 prospects les plus anciens"""
    
    # Compter le nombre total de prospects
    result = execute_query('SELECT COUNT(*) as total FROM agriweb_prospects', fetch_one=True)
    total = result['total'] if result else 0
    
    print(f"📊 Total actuel: {total} prospects")
    
    if total == 0:
        print("❌ Aucun prospect à supprimer")
        return
    
    # Supprimer 1000 prospects
    to_delete = min(1000, total)
    
    print(f"🗑️  Suppression de {to_delete} prospects les plus anciens...")
    
    # Supprimer les prospects les plus anciens (par date de création)
    # D'abord récupérer leurs IDs
    prospects_to_delete = execute_query(f'''
        SELECT id FROM agriweb_prospects 
        ORDER BY date_creation ASC 
        LIMIT {to_delete}
    ''', fetch_all=True)
    
    if not prospects_to_delete:
        print("❌ Erreur lors de la récupération des prospects à supprimer")
        return
    
    ids = [p['id'] for p in prospects_to_delete]
    
    # Supprimer d'abord les projets associés
    print(f"🗑️  Suppression des projets associés...")
    for prospect_id in ids:
        execute_query('DELETE FROM projects WHERE prospect_id = %s', (prospect_id,))
    
    # Supprimer les prospects
    print(f"🗑️  Suppression des {to_delete} prospects...")
    placeholders = ','.join(['%s'] * len(ids))
    execute_query(f'DELETE FROM agriweb_prospects WHERE id IN ({placeholders})', tuple(ids))
    
    # Vérifier le résultat
    result_after = execute_query('SELECT COUNT(*) as total FROM agriweb_prospects', fetch_one=True)
    total_after = result_after['total'] if result_after else 0
    
    print(f"✅ Terminé !")
    print(f"📊 Avant: {total} prospects")
    print(f"📊 Après: {total_after} prospects")
    print(f"🗑️  Supprimés: {total - total_after} prospects")

if __name__ == '__main__':
    reduce_prospects()
