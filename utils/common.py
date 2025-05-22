# utils/common.py

from typing import Dict, Any

def bbox_to_polygon(lon: float, lat: float, delta: float) -> Dict[str, Any]:
    """
    Crée un polygone carré autour du point (lon, lat)
    avec une demi-largeur 'delta' (en degrés).
    """
    return {
        "type": "Polygon",
        "coordinates": [[
            [lon - delta, lat - delta],
            [lon + delta, lat - delta],
            [lon + delta, lat + delta],
            [lon - delta, lat + delta],
            [lon - delta, lat - delta]  # Fermeture du polygone
        ]]
    }

def decode_rpg_feature(feature: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrait la géométrie et les propriétés d'une entité GeoJSON de type RPG.

    Args:
        feature (dict): Une entité GeoJSON (RPG).

    Returns:
        dict: Contenant 'geometry' et 'properties'.
    """
    return {
        "geometry": feature.get("geometry"),
        "properties": feature.get("properties", {})
    }
