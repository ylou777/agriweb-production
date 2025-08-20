#!/usr/bin/env python3
"""
🔍 Test diagnostic des couches de carte
Teste l'affichage des couches avec leurs styles pour identifier le problème orange
"""

import folium

def test_couches_styles():
    """Test des styles de couches pour identifier le problème orange"""
    
    print("🔍 Test des styles de couches Folium")
    print("=" * 50)
    
    # Créer une carte de test
    test_map = folium.Map(location=[46.8, 2.0], zoom_start=6)
    
    # Test 1: Couche Esri Satellite
    print("📡 Test couche Esri Satellite...")
    try:
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri World Imagery",
            name="Satellite",
            overlay=False,
            control=True,
            show=True
        ).add_to(test_map)
        print("✅ Couche Esri ajoutée avec succès")
    except Exception as e:
        print(f"❌ Erreur couche Esri: {e}")
    
    # Test 2: Styles de polygones colorés
    test_polygons = [
        {
            "name": "Test Orange",
            "coords": [[[2.0, 46.0], [2.1, 46.0], [2.1, 46.1], [2.0, 46.1], [2.0, 46.0]]],
            "color": "orange"
        },
        {
            "name": "Test Purple", 
            "coords": [[[2.2, 46.0], [2.3, 46.0], [2.3, 46.1], [2.2, 46.1], [2.2, 46.0]]],
            "color": "purple"
        },
        {
            "name": "Test Green",
            "coords": [[[2.4, 46.0], [2.5, 46.0], [2.5, 46.1], [2.4, 46.1], [2.4, 46.0]]],
            "color": "green"
        }
    ]
    
    print("\n🎨 Test des styles de polygones...")
    for i, poly in enumerate(test_polygons):
        try:
            geom = {
                "type": "Polygon",
                "coordinates": poly["coords"]
            }
            
            style_func = lambda x, color=poly["color"]: {
                "color": color,
                "weight": 3,
                "fillColor": color,
                "fillOpacity": 0.4,
                "opacity": 0.8
            }
            
            folium.GeoJson(
                geom,
                style_function=style_func,
                tooltip=f"Test {poly['name']}"
            ).add_to(test_map)
            
            print(f"✅ Polygone {poly['name']} ajouté en {poly['color']}")
            
        except Exception as e:
            print(f"❌ Erreur polygone {poly['name']}: {e}")
    
    # Test 3: Markers colorés
    print("\n📍 Test des marqueurs colorés...")
    test_markers = [
        {"lat": 46.2, "lon": 2.0, "color": "red", "name": "Rouge"},
        {"lat": 46.2, "lon": 2.2, "color": "blue", "name": "Bleu"},
        {"lat": 46.2, "lon": 2.4, "color": "green", "name": "Vert"},
        {"lat": 46.2, "lon": 2.6, "color": "orange", "name": "Orange"}
    ]
    
    for marker in test_markers:
        try:
            folium.Marker(
                [marker["lat"], marker["lon"]],
                popup=f"Marker {marker['name']}",
                icon=folium.Icon(color=marker["color"], icon="info-sign")
            ).add_to(test_map)
            print(f"✅ Marqueur {marker['name']} ajouté")
        except Exception as e:
            print(f"❌ Erreur marqueur {marker['name']}: {e}")
    
    # Test 4: LayerControl
    print("\n🎛️ Test LayerControl...")
    try:
        folium.LayerControl().add_to(test_map)
        print("✅ LayerControl ajouté")
    except Exception as e:
        print(f"❌ Erreur LayerControl: {e}")
    
    # Sauvegarder la carte de test
    try:
        test_map.save("test_couches_styles.html")
        print(f"\n💾 Carte de test sauvée: test_couches_styles.html")
        print(f"📂 Ouvrez ce fichier dans un navigateur pour voir le résultat")
        
        # Afficher quelques stats
        map_html = test_map._repr_html_()
        print(f"\n📊 Statistiques:")
        print(f"   • Taille HTML: {len(map_html)} caractères")
        print(f"   • Contient 'orange': {'orange' in map_html}")
        print(f"   • Contient 'purple': {'purple' in map_html}")
        print(f"   • Contient 'Esri': {'Esri' in map_html}")
        
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")

if __name__ == "__main__":
    test_couches_styles()
