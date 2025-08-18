#!/usr/bin/env python3
"""
Test direct de l'endpoint rapport_departement avec requests
"""
import requests
import json

def test_rapport_departement_endpoint():
    """Test de l'endpoint corrigé"""
    
    # Données de test
    test_data = {
        "data": [
            {
                "commune": "Test Commune A",
                "dept": "83",
                "rpg_parcelles": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {
                                "ID_PARCEL": "TEST-001",
                                "code_com": "83001",
                                "section": "AB",
                                "numero": "123",
                                "distance_bt": 200,
                                "surface": "2.5",
                                "nom_com": "Test Commune A"
                            },
                            "geometry": {"type": "Point", "coordinates": [6.1, 43.1]}
                        },
                        {
                            "type": "Feature",
                            "properties": {
                                "ID_PARCEL": "TEST-002",
                                "code_com": "83001",
                                "section": "CD",
                                "numero": "456",
                                "distance_hta": 150,  # Plus proche
                                "surface": "3.0",
                                "nom_com": "Test Commune A"
                            },
                            "geometry": {"type": "Point", "coordinates": [6.2, 43.2]}
                        }
                    ]
                },
                "eleveurs": {
                    "type": "FeatureCollection", 
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {
                                "nom": "Test Eleveur A",
                                "siret": "12345678901234",
                                "activite": "Bovins"
                            },
                            "geometry": {"type": "Point", "coordinates": [6.1, 43.1]}
                        },
                        {
                            "type": "Feature",
                            "properties": {
                                "nom": "Test Eleveur B",
                                "activite": "Ovins"
                                # Pas de SIRET pour tester le cas sans
                            },
                            "geometry": {"type": "Point", "coordinates": [6.15, 43.15]}
                        }
                    ]
                }
            }
        ]
    }
    
    try:
        print("🧪 [TEST] === TEST ENDPOINT RAPPORT DÉPARTEMENT ===")
        print(f"🧪 [TEST] Envoi de {len(test_data['data'])} rapports communaux")
        print(f"🧪 [TEST] Total parcelles test: {len(test_data['data'][0]['rpg_parcelles']['features'])}")
        print(f"🧪 [TEST] Total éleveurs test: {len(test_data['data'][0]['eleveurs']['features'])}")
        
        # Appel POST vers l'endpoint
        url = "http://localhost:5000/rapport_departement"
        headers = {"Content-Type": "application/json"}
        
        print(f"🧪 [TEST] Appel POST vers {url}")
        response = requests.post(url, json=test_data, headers=headers, timeout=30)
        
        print(f"🧪 [TEST] Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ [TEST] Endpoint répond correctement")
            
            # Analyser la réponse HTML
            html_content = response.text
            
            # Recherche des indicateurs de succès des corrections
            success_indicators = []
            
            # 1. Vérifier que les totaux ne sont pas 0
            if "Nombre total d'agriculteurs : <b>2</b>" in html_content:
                success_indicators.append("✅ Total éleveurs correct (2)")
            elif "Nombre total d'agriculteurs : <b>0</b>" in html_content:
                success_indicators.append("❌ Total éleveurs toujours à 0")
            else:
                success_indicators.append("❓ Total éleveurs non trouvé dans HTML")
            
            if "Nombre total de parcelles RPG : <b>2</b>" in html_content:
                success_indicators.append("✅ Total parcelles correct (2)")
            elif "Nombre total de parcelles RPG : <b>0</b>" in html_content:
                success_indicators.append("❌ Total parcelles toujours à 0")
            else:
                success_indicators.append("❓ Total parcelles non trouvé dans HTML")
            
            # 2. Vérifier qu'il n'y a pas de "N/A m" 
            if "N/A m" in html_content:
                success_indicators.append("❌ Encore des distances 'N/A m'")
            else:
                success_indicators.append("✅ Pas de distances 'N/A m'")
            
            # 3. Vérifier les distances formatées
            if "150 m" in html_content and "200 m" in html_content:
                success_indicators.append("✅ Distances formatées correctement")
            else:
                success_indicators.append("❓ Distances formatées à vérifier")
            
            # 4. Vérifier les liens cadastre
            if "cadastre.gouv.fr" in html_content:
                success_indicators.append("✅ Liens cadastre générés")
            else:
                success_indicators.append("❓ Liens cadastre à vérifier")
            
            print("\n🔍 [TEST] RÉSULTATS DES CORRECTIONS:")
            for indicator in success_indicators:
                print(f"    {indicator}")
            
            # Sauvegarder la réponse pour inspection
            with open("test_response.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"\n📄 [TEST] Réponse sauvegardée dans test_response.html")
            
        else:
            print(f"❌ [TEST] Erreur: {response.status_code}")
            print(f"❌ [TEST] Réponse: {response.text[:500]}...")
            
    except requests.exceptions.ConnectionError:
        print("❌ [TEST] Impossible de se connecter au serveur Flask")
        print("❌ [TEST] Assurez-vous que le serveur tourne sur http://localhost:5000")
    except Exception as e:
        print(f"❌ [TEST] Erreur: {e}")

if __name__ == "__main__":
    test_rapport_departement_endpoint()
