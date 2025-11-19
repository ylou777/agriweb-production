#!/usr/bin/env python3
"""
Test du calcul de distance aux lignes HTA.
"""

from shapely.geometry import Point, LineString, shape
import json

def calculate_min_distance_to_lines(centroid, lines_features):
    """
    Calcule la distance minimale d'un point (centroïde) aux lignes HTA.
    
    Args:
        centroid: [longitude, latitude] du point
        lines_features: Liste des features de lignes (GeoJSON LineString)
    
    Returns:
        float: Distance minimale en mètres, ou None si pas de lignes
    """
    if not lines_features:
        return None
    
    point = Point(centroid)
    distances = []
    
    for line_feature in lines_features:
        try:
            line_geom = shape(line_feature["geometry"])
            # Calcul de la distance (en degrés) puis conversion en mètres
            dist_degrees = line_geom.distance(point)
            dist_meters = dist_degrees * 111000  # Approximation: 1 degré ≈ 111km
            distances.append(dist_meters)
        except Exception as e:
            print(f"⚠️ Erreur calcul distance ligne: {e}")
            continue
    
    return min(distances) if distances else None

# Test avec des données fictives
if __name__ == "__main__":
    # Point test (centroïde)
    test_centroid = [2.3522, 48.8566]  # Paris
    
    # Ligne test
    test_line_feature = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [2.3500, 48.8560],  # Point proche
                [2.3600, 48.8570]   # Point proche
            ]
        },
        "properties": {
            "type": "aerienne"
        }
    }
    
    # Test du calcul
    distance = calculate_min_distance_to_lines(test_centroid, [test_line_feature])
    
    print(f"🧪 Test de calcul de distance aux lignes HTA")
    print(f"📍 Point test: {test_centroid}")
    print(f"📏 Distance calculée: {distance:.2f}m" if distance else "❌ Distance non calculée")
    
    # Test avec plusieurs lignes
    test_lines = [
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[2.3500, 48.8560], [2.3600, 48.8570]]
            },
            "properties": {"type": "aerienne"}
        },
        {
            "type": "Feature", 
            "geometry": {
                "type": "LineString",
                "coordinates": [[2.3400, 48.8550], [2.3450, 48.8555]]
            },
            "properties": {"type": "souterraine"}
        }
    ]
    
    distance_multi = calculate_min_distance_to_lines(test_centroid, test_lines)
    print(f"📏 Distance min avec plusieurs lignes: {distance_multi:.2f}m" if distance_multi else "❌ Distance non calculée")