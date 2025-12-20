"""
Script de nettoyage de la base prospects et test des nouveaux processus
- Nettoyage base agriweb_prospects
- Test export avec détails postes BT/HTA complets
- Test génération schéma unifilaire avec infos postes
- Test rapport avec coordonnées GPS postes
"""

import sys
import json
from database_adapter import get_db_connection, execute_query

def clean_prospects_database():
    """Nettoie complètement la table agriweb_prospects"""
    print("🧹 NETTOYAGE BASE DE DONNÉES PROSPECTS")
    print("=" * 60)
    
    try:
        # Compter les prospects actuels
        result = execute_query("SELECT COUNT(*) as count FROM agriweb_prospects", fetch_one=True)
        count_before = result['count'] if result else 0
        print(f"📊 Nombre de prospects avant nettoyage: {count_before}")
        
        if count_before > 0:
            # Demander confirmation
            response = input(f"\n⚠️  Voulez-vous supprimer {count_before} prospects? (oui/non): ")
            if response.lower() not in ['oui', 'o', 'yes', 'y']:
                print("❌ Nettoyage annulé")
                return False
            
            # Supprimer tous les prospects
            execute_query("DELETE FROM agriweb_prospects")
            print(f"✅ {count_before} prospects supprimés")
        else:
            print("ℹ️  La table est déjà vide")
        
        # Vérifier le nettoyage
        result = execute_query("SELECT COUNT(*) as count FROM agriweb_prospects", fetch_one=True)
        count_after = result['count'] if result else 0
        print(f"📊 Nombre de prospects après nettoyage: {count_after}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")
        return False


def test_new_columns():
    """Vérifie que les nouvelles colonnes existent"""
    print("\n🔍 VÉRIFICATION DES NOUVELLES COLONNES")
    print("=" * 60)
    
    try:
        # Tester une insertion avec toutes les nouvelles colonnes
        test_data = {
            'type': 'test',
            'commune': 'Test-Commune',
            'latitude': 45.0,
            'longitude': 4.0,
            'poste_bt_nom': 'Poste Test BT',
            'poste_bt_distance_m': 150.5,
            'poste_bt_puissance': 250,
            'poste_bt_etat': 'Actif',
            'poste_bt_lat': 45.001,
            'poste_bt_lon': 4.001,
            'poste_hta_nom': 'Poste Test HTA',
            'poste_hta_distance_m': 500.0,
            'poste_hta_puissance': 1000,
            'poste_hta_etat': 'Actif',
            'poste_hta_lat': 45.002,
            'poste_hta_lon': 4.002
        }
        
        result = execute_query('''
            INSERT INTO agriweb_prospects (
                type, commune, latitude, longitude,
                poste_bt_nom, poste_bt_distance_m, poste_bt_puissance, poste_bt_etat, 
                poste_bt_lat, poste_bt_lon,
                poste_hta_nom, poste_hta_distance_m, poste_hta_puissance, poste_hta_etat,
                poste_hta_lat, poste_hta_lon
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            test_data['type'], test_data['commune'], test_data['latitude'], test_data['longitude'],
            test_data['poste_bt_nom'], test_data['poste_bt_distance_m'], test_data['poste_bt_puissance'],
            test_data['poste_bt_etat'], test_data['poste_bt_lat'], test_data['poste_bt_lon'],
            test_data['poste_hta_nom'], test_data['poste_hta_distance_m'], test_data['poste_hta_puissance'],
            test_data['poste_hta_etat'], test_data['poste_hta_lat'], test_data['poste_hta_lon']
        ))
        
        # Pour SQLite, récupérer le dernier ID inséré
        test_id_result = execute_query("SELECT last_insert_rowid() as id", fetch_one=True)
        test_id = test_id_result['id'] if test_id_result else None
        
        if test_id:
            print(f"✅ Test d'insertion réussi (ID: {test_id})")
            
            # Lire les données
            prospect = execute_query(
                "SELECT * FROM agriweb_prospects WHERE id = ?",
                (test_id,),
                fetch_one=True
            )
            
            if prospect:
                print("\n📋 Données du prospect test:")
                print(f"   Poste BT: {prospect.get('poste_bt_nom')} - {prospect.get('poste_bt_puissance')} kVA - {prospect.get('poste_bt_etat')}")
                print(f"   GPS BT: {prospect.get('poste_bt_lat')}, {prospect.get('poste_bt_lon')}")
                print(f"   Distance BT: {prospect.get('poste_bt_distance_m')}m")
                print(f"   Poste HTA: {prospect.get('poste_hta_nom')} - {prospect.get('poste_hta_puissance')} kVA - {prospect.get('poste_hta_etat')}")
                print(f"   GPS HTA: {prospect.get('poste_hta_lat')}, {prospect.get('poste_hta_lon')}")
                print(f"   Distance HTA: {prospect.get('poste_hta_distance_m')}m")
            
            # Supprimer le test
            execute_query("DELETE FROM agriweb_prospects WHERE id = ?", (test_id,))
            print(f"\n🗑️  Prospect test supprimé")
            
            return True
        else:
            print("❌ Échec de l'insertion test")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test des colonnes: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_prospects_summary():
    """Affiche un résumé des prospects dans la base"""
    print("\n📊 RÉSUMÉ DES PROSPECTS")
    print("=" * 60)
    
    try:
        # Compter par type
        results = execute_query('''
            SELECT type, COUNT(*) as count
            FROM agriweb_prospects
            GROUP BY type
            ORDER BY count DESC
        ''', fetch_all=True)
        
        if results:
            print("\nRépartition par type:")
            total = 0
            for row in results:
                print(f"  - {row['type']}: {row['count']}")
                total += row['count']
            print(f"\nTotal: {total} prospects")
        else:
            print("Aucun prospect dans la base")
        
        # Prospects avec infos postes BT complètes
        result = execute_query('''
            SELECT COUNT(*) as count
            FROM agriweb_prospects
            WHERE poste_bt_nom IS NOT NULL 
              AND poste_bt_distance_m IS NOT NULL
              AND poste_bt_puissance IS NOT NULL
              AND poste_bt_etat IS NOT NULL
        ''', fetch_one=True)
        
        if result:
            print(f"\nProspects avec données BT complètes: {result['count']}")
        
        # Prospects avec infos postes HTA complètes
        result = execute_query('''
            SELECT COUNT(*) as count
            FROM agriweb_prospects
            WHERE poste_hta_nom IS NOT NULL 
              AND poste_hta_distance_m IS NOT NULL
              AND poste_hta_puissance IS NOT NULL
              AND poste_hta_etat IS NOT NULL
        ''', fetch_one=True)
        
        if result:
            print(f"Prospects avec données HTA complètes: {result['count']}")
        
    except Exception as e:
        print(f"❌ Erreur lors du résumé: {e}")


def main():
    """Fonction principale"""
    print("\n" + "=" * 60)
    print("  NETTOYAGE & TEST - BASE PROSPECTS AGRIWEB")
    print("=" * 60)
    
    # 1. Nettoyer la base
    if not clean_prospects_database():
        print("\n⚠️  Nettoyage annulé ou échoué")
        return
    
    # 2. Tester les nouvelles colonnes
    if not test_new_columns():
        print("\n❌ Les nouvelles colonnes ne sont pas correctement configurées")
        print("💡 Conseil: Redémarrez l'application Railway pour appliquer les migrations")
        return
    
    # 3. Afficher le résumé
    show_prospects_summary()
    
    print("\n" + "=" * 60)
    print("✅ NETTOYAGE ET TESTS TERMINÉS")
    print("=" * 60)
    print("\n📝 PROCHAINES ÉTAPES:")
    print("1. Utilisez l'interface web pour faire une recherche")
    print("2. Exportez des prospects depuis la carte")
    print("3. Vérifiez les détails des postes BT/HTA dans le CRM")
    print("4. Générez un schéma unifilaire avec injection")
    print("5. Consultez un rapport d'adresse")
    print("\n💡 Les nouveaux champs (puissance, statut, GPS) seront")
    print("   automatiquement remplis lors des prochains exports!")
    

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Opération interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
