@app.route("/test_rapport_nature")
def test_rapport_nature():
    """Route de test pour vérifier l'affichage des données nature dans le rapport"""
    
    # Simuler des données API Nature telles qu'elles devraient être dans api_details
    test_api_details = {
        "nature": {
            "success": True,
            "data": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "NOM": "ÎLE DE PORT-CROS ET DE BAGAUD",
                            "TYPE_PROTECTION": "ZNIEFF Type 1",
                            "TYPE": "Zone naturelle d'intérêt écologique",
                            "STATUT": "Protégée",
                            "SUPERFICIE": "650 ha"
                        },
                        "geometry": {"type": "Point", "coordinates": [6.396759, 43.006497]}
                    },
                    {
                        "type": "Feature", 
                        "properties": {
                            "NOM": "Port-Cros",
                            "TYPE_PROTECTION": "Parcs Nationaux",
                            "TYPE": "Parc National",
                            "STATUT": "Protégé",
                            "SUPERFICIE": "1700 ha"
                        },
                        "geometry": {"type": "Point", "coordinates": [6.396759, 43.006497]}
                    }
                ]
            },
            "count": 2,
            "error": None
        }
    }
    
    # Créer un rapport minimal pour tester le template
    test_report = {
        "lat": 43.006497,
        "lon": 6.396759,
        "address": "Test Hyères API Nature",
        "api_details": test_api_details
    }
    
    return render_template("rapport_point.html", report=test_report)
