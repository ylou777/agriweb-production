"""
Script de conversion des fichiers MAJIC (Propriétaires Personnes Morales) 
vers GeoPackage avec géométries des parcelles cadastrales

Ce script :
1. Lit tous les fichiers CSV MAJIC d'un dossier
2. Récupère les géométries des parcelles via l'API Cadastre IGN
3. Crée un GeoPackage (.gpkg) avec table proprietaires_parcelles
4. Prêt pour upload dans GeoServer

Dépendances: pip install geopandas pandas requests tqdm
"""

import pandas as pd
import geopandas as gpd
import requests
import json
from pathlib import Path
from shapely.geometry import shape
from tqdm import tqdm
import time

class MajicToGeoPackage:
    def __init__(self, csv_folders, output_gpkg="proprietaires_parcelles.gpkg"):
        """
        Args:
            csv_folders: Liste de dossiers contenant les fichiers CSV MAJIC
            output_gpkg: Nom du fichier GeoPackage de sortie
        """
        # Accepter soit un dossier unique, soit une liste
        if isinstance(csv_folders, (str, Path)):
            self.csv_folders = [Path(csv_folders)]
        else:
            self.csv_folders = [Path(folder) for folder in csv_folders]
            
        self.output_gpkg = output_gpkg
        self.api_cadastre_url = "https://apicarto.ign.fr/api/cadastre/parcelle"
        
        # Cache pour éviter de redemander les mêmes parcelles
        self.geometry_cache = {}
        
    def parse_csv_file(self, csv_path):
        """Parse un fichier CSV MAJIC"""
        print(f"📖 Lecture: {csv_path.name}")
        
        try:
            # Lire le CSV avec séparateur point-virgule et encoding latin-1
            df = pd.read_csv(
                csv_path, 
                sep=';', 
                encoding='latin-1',
                dtype=str,  # Tout en string pour éviter les conversions
                low_memory=False
            )
            
            # Nettoyer les noms de colonnes (enlever guillemets)
            df.columns = df.columns.str.strip('"')
            
            print(f"   ✓ {len(df)} lignes chargées")
            return df
            
        except Exception as e:
            print(f"   ✗ Erreur: {e}")
            return None
    
    def get_parcelle_geometry(self, code_insee, section, numero):
        """Récupère la géométrie d'une parcelle via l'API Cadastre IGN"""
        
        # Créer une clé unique pour le cache
        cache_key = f"{code_insee}_{section}_{numero}"
        
        if cache_key in self.geometry_cache:
            return self.geometry_cache[cache_key]
        
        # Construire la référence cadastrale
        # Format attendu par l'API: code_insee + section + numero (ex: "06088AB0123")
        ref_cadastrale = f"{code_insee}{section}{numero}"
        
        try:
            params = {
                "code_parcelle": ref_cadastrale
            }
            
            response = requests.get(
                self.api_cadastre_url, 
                params=params, 
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('features') and len(data['features']) > 0:
                    # Extraire la géométrie
                    geom = shape(data['features'][0]['geometry'])
                    self.geometry_cache[cache_key] = geom
                    return geom
            
            # Si pas de résultat, mettre None dans le cache
            self.geometry_cache[cache_key] = None
            return None
            
        except Exception as e:
            print(f"      ⚠️ Erreur géométrie {ref_cadastrale}: {e}")
            self.geometry_cache[cache_key] = None
            return None
    
    def process_department(self, csv_path, batch_size=100):
        """Traite un fichier département et retourne un GeoDataFrame"""
        
        df = self.parse_csv_file(csv_path)
        if df is None or len(df) == 0:
            return None
        
        # Colonnes importantes à extraire
        important_cols = {
            'Code Commune (Champ géographique)': 'code_commune',
            'Nom Commune (Champ géographique)': 'nom_commune',
            'Section (Références cadastrales)': 'section',
            'N° plan (Références cadastrales)': 'numero',
            'N° SIREN (Propriétaire(s) parcelle)': 'siren',
            'Forme juridique abrégée (Propriétaire(s) parcelle)': 'forme_juridique',
            'Dénomination (Propriétaire(s) parcelle)': 'denomination',
            'Contenance (Caractéristiques parcelle)': 'contenance',
            'Nom voie (Adresse parcelle)': 'nom_voie',
            'Nature voie (Adresse parcelle)': 'nature_voie'
        }
        
        # Renommer les colonnes
        df_clean = df.rename(columns=important_cols)
        
        # Garder seulement les colonnes qui existent
        cols_to_keep = [v for k, v in important_cols.items() if k in df.columns]
        df_clean = df_clean[cols_to_keep]
        
        # Nettoyer les données
        df_clean['code_commune'] = df_clean['code_commune'].str.strip().str.zfill(5)
        df_clean['section'] = df_clean['section'].str.strip()
        df_clean['numero'] = df_clean['numero'].str.strip()
        df_clean['siren'] = df_clean['siren'].str.strip()
        df_clean['denomination'] = df_clean['denomination'].str.strip()
        
        # Créer une référence cadastrale unique
        df_clean['ref_cadastrale'] = (
            df_clean['code_commune'] + 
            df_clean['section'] + 
            df_clean['numero']
        )
        
        # Grouper par parcelle (plusieurs propriétaires possibles)
        # On va prendre le premier propriétaire de chaque parcelle
        df_parcelles = df_clean.drop_duplicates(subset=['ref_cadastrale'], keep='first')
        
        print(f"🔍 Récupération des géométries pour {len(df_parcelles)} parcelles...")
        
        # Récupérer les géométries par batch
        geometries = []
        total = len(df_parcelles)
        
        for idx, row in tqdm(df_parcelles.iterrows(), total=total, desc="   Géométries"):
            geom = self.get_parcelle_geometry(
                row['code_commune'],
                row['section'],
                row['numero']
            )
            geometries.append(geom)
            
            # Pause toutes les 10 requêtes pour ne pas surcharger l'API
            if (idx + 1) % 10 == 0:
                time.sleep(0.5)
        
        df_parcelles['geometry'] = geometries
        
        # Créer le GeoDataFrame (seulement celles avec géométrie)
        gdf = gpd.GeoDataFrame(
            df_parcelles[df_parcelles['geometry'].notna()],
            geometry='geometry',
            crs="EPSG:4326"
        )
        
        print(f"   ✓ {len(gdf)} parcelles avec géométrie")
        
        return gdf
    
    def convert_all(self, departments=None):
        """
        Convertit tous les fichiers CSV en un seul GeoPackage
        
        Args:
            departments: Liste des départements à traiter (ex: ['06', '13', '83'])
                        Si None, traite tous les fichiers
        """
        
        print("="*80)
        print("🚀 CONVERSION MAJIC CSV → GEOPACKAGE")
        print("="*80)
        
        # Lister tous les fichiers CSV dans TOUS les dossiers
        csv_files = []
        for folder in self.csv_folders:
            if folder.exists():
                files = list(folder.glob("PM_*.txt"))
                csv_files.extend(files)
                print(f"\n📁 Dossier: {folder.name}")
                print(f"   {len(files)} fichiers trouvés")
            else:
                print(f"\n⚠️ Dossier introuvable: {folder}")
        
        if departments:
            # Filtrer par départements
            csv_files = [
                f for f in csv_files 
                if any(f.name.startswith(f"PM_{dept}_") or f"{dept}" in f.stem for dept in departments)
            ]
        
        print(f"\n📋 TOTAL: {len(csv_files)} fichiers à traiter")
        
        if len(csv_files) == 0:
            print("❌ Aucun fichier trouvé !")
            return
        
        # Traiter tous les fichiers
        all_gdfs = []
        
        for csv_file in csv_files:
            gdf = self.process_department(csv_file)
            if gdf is not None and len(gdf) > 0:
                all_gdfs.append(gdf)
        
        if len(all_gdfs) == 0:
            print("\n❌ Aucune donnée géométrique récupérée !")
            return
        
        # Combiner tous les GeoDataFrames
        print(f"\n🔗 Fusion de {len(all_gdfs)} départements...")
        gdf_final = pd.concat(all_gdfs, ignore_index=True)
        
        # Sauvegarder en GeoPackage
        print(f"\n💾 Sauvegarde dans {self.output_gpkg}...")
        gdf_final.to_file(self.output_gpkg, driver="GPKG", layer="proprietaires_parcelles")
        
        print("\n" + "="*80)
        print("✅ CONVERSION TERMINÉE !")
        print("="*80)
        print(f"📦 GeoPackage créé: {self.output_gpkg}")
        print(f"📊 Total parcelles: {len(gdf_final)}")
        print(f"🗂️ Couche: proprietaires_parcelles")
        print("\nProchaine étape: Uploader dans GeoServer")
        print("="*80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Convertir fichiers MAJIC en GeoPackage")
    parser.add_argument(
        "--input-folders",
        nargs="+",
        default=[
            r"C:\Users\Public\Documents\personnes morales\PARCELLES  départements 1 A 61",
            r"C:\Users\Public\Documents\personnes morales\PARCELLES départements 62 A 976"
        ],
        help="Dossiers contenant les fichiers CSV MAJIC (séparés par des espaces)"
    )
    parser.add_argument(
        "--output",
        default="proprietaires_parcelles.gpkg",
        help="Nom du fichier GeoPackage de sortie"
    )
    parser.add_argument(
        "--departments",
        nargs="+",
        help="Liste des départements à traiter (ex: 06 13 83 84). Si omis, traite tous les fichiers"
    )
    
    args = parser.parse_args()
    
    # Créer le convertisseur avec les 2 dossiers
    converter = MajicToGeoPackage(
        csv_folders=args.input_folders,
        output_gpkg=args.output
    )
    
    # Lancer la conversion
    converter.convert_all(departments=args.departments)
