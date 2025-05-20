import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# Lecture du CSV
csv_path = r"C:\Users\Public\Documents\eleveurs\etablissements_eleveurs.csv"
df = pd.read_csv(csv_path, dtype=str)

# Conversion des coordonnées
df["x"] = pd.to_numeric(df["coordonneeLambertAbscisseEtablissement"], errors="coerce")
df["y"] = pd.to_numeric(df["coordonneeLambertOrdonneeEtablissement"], errors="coerce")

# Suppression des lignes sans coordonnées valides
df = df.dropna(subset=["x", "y"])

# Création de la géométrie (points Lambert 93 - EPSG:2154)
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["x"], df["y"]), crs="EPSG:2154")

# Sauvegarde en Shapefile
output_path = r"C:\Users\Public\Documents\eleveurs\etablissements_eleveurs.shp"
gdf.to_file(output_path, encoding="utf-8")

print("✅ Shapefile généré avec succès :", output_path)
