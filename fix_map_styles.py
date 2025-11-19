#!/usr/bin/env python3
"""
Script pour corriger les styles de carte qui apparaissent en orange.
Ce script remplace les fonctions lambda par des styles statiques.
"""

import folium

def test_styles_fix():
    """Test des styles fixes"""
    print("🧪 Test des styles de carte fixes...")
    
    # Création d'une carte de test
    test_map = folium.Map(location=[46.8, 2.0], zoom_start=8)
    
    # Ajouter le fond Esri satellite
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite",
        overlay=False, 
        control=True, 
        show=True
    ).add_to(test_map)
    
    # Test des polygones avec styles STATIQUES (pas de lambda)
    test_polygon = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [2.0, 46.0], [2.1, 46.0], [2.1, 46.1], [2.0, 46.1], [2.0, 46.0]
            ]]
        },
        "properties": {"name": "Test Parking"}
    }
    
    # STYLES STATIQUES - pas de fonction lambda
    parking_style = {
        "color": "orange", 
        "weight": 3, 
        "fillColor": "orange", 
        "fillOpacity": 0.4, 
        "opacity": 0.8
    }
    
    friches_style = {
        "color": "brown", 
        "weight": 3, 
        "fillColor": "brown", 
        "fillOpacity": 0.4, 
        "opacity": 0.8
    }
    
    solaire_style = {
        "color": "gold", 
        "weight": 3, 
        "fillColor": "gold", 
        "fillOpacity": 0.4, 
        "opacity": 0.8
    }
    
    zaer_style = {
        "color": "cyan", 
        "weight": 3, 
        "fillColor": "cyan", 
        "fillOpacity": 0.4, 
        "opacity": 0.8
    }
    
    # Ajout des polygones de test avec styles statiques
    folium.GeoJson(
        test_polygon, 
        style_function=lambda feature: parking_style,  # Simple wrapper
        tooltip="Test Parking - Orange"
    ).add_to(test_map)
    
    # Test avec style direct (encore plus simple)
    test_polygon2 = {
        "type": "Feature", 
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [2.2, 46.0], [2.3, 46.0], [2.3, 46.1], [2.2, 46.1], [2.2, 46.0]
            ]]
        }
    }
    
    folium.GeoJson(
        test_polygon2,
        style_function=lambda feature: friches_style,
        tooltip="Test Friches - Brown"
    ).add_to(test_map)
    
    # Contrôle des couches
    folium.LayerControl().add_to(test_map)
    
    # Sauvegarder
    test_map.save("test_styles_fixes.html")
    print("✅ Carte test sauvegardée: test_styles_fixes.html")
    print("🎨 Styles utilisés:")
    print(f"  • Parking: {parking_style}")
    print(f"  • Friches: {friches_style}")
    print(f"  • Solaire: {solaire_style}")
    print(f"  • ZAER: {zaer_style}")
    
    return {
        "parking": parking_style,
        "friches": friches_style, 
        "solaire": solaire_style,
        "zaer": zaer_style
    }

if __name__ == "__main__":
    styles = test_styles_fix()
    print("\n✅ Test terminé - vérifiez test_styles_fixes.html")
