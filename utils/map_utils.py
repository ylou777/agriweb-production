# --- Module utils/map_utils.py ---
import folium
import os

def create_map(lat, lon, parcelle, postes, plu_info, api_carto_info):
    """
    Crée une carte interactive à l'aide de Folium.
    
    Args:
        lat (float): Latitude de la position centrale.
        lon (float): Longitude de la position centrale.
        parcelle (dict): Informations sur la parcelle (géométrie et propriétés).
        postes (list): Liste des postes électriques proches.
        plu_info (list): Liste des informations PLU..

    Returns:
        str: Chemin du fichier HTML généré pour la carte.
    """
    # Initialisation de la carte
    map_obj = folium.Map(location=[lat, lon], zoom_start=17)

    # Ajout d'un marqueur pour la position centrale
    folium.Marker([lat, lon], popup="Position centrale").add_to(map_obj)

    # Ajout des informations de la parcelle si disponible
    if parcelle:
        parcelle_geom = parcelle.get("geometry")
        folium.GeoJson(
            parcelle_geom,
            style_function=lambda x: {"fillColor": "blue", "color": "blue", "weight": 2},
            name="Parcelle",
            tooltip=folium.Tooltip(f"Informations cadastrales : {parcelle}")
        ).add_to(map_obj)

    # Ajout des postes électriques
    for poste in postes:
        props = poste["properties"]
        distance = poste["distance"]
        poste_lat = props.get("latitude")  # Remplacez par la clé réelle si différente
        poste_lon = props.get("longitude")
        folium.Marker(
            [poste_lat, poste_lon],
            popup=f"Poste électrique à {distance} m",
            icon=folium.Icon(color="green")
        ).add_to(map_obj)

    # Ajout des informations PLU
    for plu in plu_info:
        folium.Marker(
            [lat, lon],
            popup=f"PLU : {plu}",
            icon=folium.Icon(color="orange")
        ).add_to(map_obj)

    # Ajout des informations API Carto
    for feature in api_carto_info:
        folium.GeoJson(
            feature["geometry"],
            style_function=lambda x: {"fillColor": "purple", "color": "purple", "weight": 1},
            tooltip=folium.Tooltip(str(feature["properties"])),
            name="API Carto"
        ).add_to(map_obj)


    # Ajout du contrôle des couches
    folium.LayerControl().add_to(map_obj)

    # Sauvegarde de la carte dans un fichier HTML
    map_file = os.path.join("templates", "map.html")
    map_obj.save(map_file)
    return map_file
