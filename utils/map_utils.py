import folium
import os

def create_map(lat, lon, parcelle, postes, plu_info, api_carto_info):
    """
    Crée une carte interactive à l'aide de Folium.
    """
    map_obj = folium.Map(location=[lat, lon], zoom_start=17)
    folium.Marker([lat, lon], popup="Position centrale").add_to(map_obj)

    # Parcelle
    if parcelle and parcelle.get("geometry"):
        folium.GeoJson(
            parcelle["geometry"],
            style_function=lambda x: {"fillColor": "blue", "color": "blue", "weight": 2},
            name="Parcelle",
            tooltip=folium.Tooltip(f"Informations cadastrales : {parcelle}")
        ).add_to(map_obj)

    # Postes électriques
    for poste in postes:
        props = poste.get("properties", {})
        distance = poste.get("distance", None)
        # Prend les coordonnées depuis geometry si elles existent
        coords = poste.get("geometry", {}).get("coordinates", None)
        if coords and len(coords) == 2:
            poste_lon, poste_lat = coords
        else:
            poste_lat = props.get("latitude")
            poste_lon = props.get("longitude")
        if poste_lat is not None and poste_lon is not None:
            folium.Marker(
                [poste_lat, poste_lon],
                popup=f"Poste électrique à {distance} m" if distance else "Poste électrique",
                icon=folium.Icon(color="green")
            ).add_to(map_obj)

    # PLU (affichage en GeoJSON si possible)
    for plu in plu_info:
        if isinstance(plu, dict) and "geometry" in plu:
            folium.GeoJson(
                plu["geometry"],
                style_function=lambda x: {"fillColor": "orange", "color": "orange", "weight": 1},
                name="PLU",
                tooltip=folium.Tooltip(str(plu.get("properties", {})))
            ).add_to(map_obj)
        else:
            folium.Marker(
                [lat, lon],
                popup=f"PLU : {plu}",
                icon=folium.Icon(color="orange")
            ).add_to(map_obj)

    # API Carto Info
    for feature in api_carto_info:
        if "geometry" in feature and "properties" in feature:
            folium.GeoJson(
                feature["geometry"],
                style_function=lambda x: {"fillColor": "purple", "color": "purple", "weight": 1},
                tooltip=folium.Tooltip(str(feature["properties"])),
                name="API Carto"
            ).add_to(map_obj)

    folium.LayerControl().add_to(map_obj)
    
    # Sauvegarde dans static/maps/ (plus sûr)
    os.makedirs("static/maps", exist_ok=True)
    map_file = os.path.join("static", "maps", "map.html")
    map_obj.save(map_file)
    return map_file
