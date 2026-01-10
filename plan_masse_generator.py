"""
Générateur de Plan de Masse Cadastral avec Calpinage PV
Version simplifiée et professionnelle
v2.1 - 2026-01-07: Intégration API Cadastre IGN pour contours parcelles réels
"""

from reportlab.lib.pagesizes import A3, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import io
import requests
from PIL import Image
import json
import base64
import re


class PlanMasseGenerator:
    """Génère un plan de masse cadastral avec implantation PV réelle"""
    
    def __init__(self, prospect_data, calpinage_data=None):
        self.data = prospect_data
        self.calpinage = calpinage_data
        self.width, self.height = A3  # Format A3 pour plus de détails
        
    def generate(self):
        """Génère le plan de masse PDF"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A3)
        
        # En-tête
        self._draw_header(c)
        
        # Zone principale : plan cadastral + calpinage
        self._draw_plan_cadastral(c)
        
        # Légende et informations
        self._draw_legend(c)
        
        # Cartouche technique
        self._draw_cartouche(c)
        
        c.save()
        buffer.seek(0)
        return buffer
    
    def _draw_header(self, c):
        """En-tête du document"""
        y = self.height - 2*cm
        
        # Titre
        c.setFont("Helvetica-Bold", 16)
        c.drawString(3*cm, y, "PLAN DE MASSE - INSTALLATION PHOTOVOLTAÏQUE")
        
        y -= 0.7*cm
        c.setFont("Helvetica", 10)
        commune = self.data.get('commune', '')
        adresse = self.data.get('adresse', '')
        c.drawString(3*cm, y, f"{adresse}, {commune}")
        
        # Échelle réglementaire
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.HexColor('#D32F2F'))
        c.drawRightString(self.width - 3*cm, y, "Échelle 1/500")
        c.setFillColor(colors.black)
        
    def _draw_plan_cadastral(self, c):
        """Dessine le plan cadastral avec parcelles et modules PV"""
        
        # Zone de dessin - Optimisée pour éviter chevauchements avec légende et cartouche
        plan_x = 2*cm
        plan_y = 15*cm  # Plus haut pour laisser place à la légende
        plan_width = self.width - 4*cm
        plan_height = self.height - 18*cm  # Hauteur ajustée
        
        # Cadre
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(plan_x, plan_y, plan_width, plan_height)
        
        # Fond
        c.setFillColor(colors.HexColor('#F5F5F5'))
        c.rect(plan_x, plan_y, plan_width, plan_height, fill=1, stroke=0)
        
        lat = self.data.get('latitude')
        lon = self.data.get('longitude')
        
        # Initialiser screenshot_used
        self.screenshot_used = False
        
        # 🔥 CORRECTION GPS: Utiliser systématiquement les facteurs de conversion précis
        # sauvegardés dans le calpinage (issus de map.distance() de Leaflet)
        gps_conversion = None
        if self.calpinage:
            gps_conversion = self.calpinage.get('gpsConversion')
        
        if gps_conversion and 'metersPerDegreeLat' in gps_conversion and 'metersPerDegreeLng' in gps_conversion:
            # Utiliser les facteurs de conversion PRÉCIS du calpinage
            meters_per_degree_lat = gps_conversion['metersPerDegreeLat']
            meters_per_degree_lng = gps_conversion['metersPerDegreeLng']
            print(f"[PLAN] ✅ Utilisation des facteurs GPS précis: lat={1/meters_per_degree_lat:.9f}°/m, lng={1/meters_per_degree_lng:.9f}°/m")
        else:
            # Fallback: approximation basée sur la latitude (moins précis)
            import math
            lat_rad = lat * math.pi / 180 if lat else 0.785398  # 45° par défaut
            meters_per_degree_lat = 1 / 111320  # Plus précis que 111000
            meters_per_degree_lng = 1 / (111320 * math.cos(lat_rad))
            print(f"[PLAN] ⚠️ Facteurs GPS approximatifs (gpsConversion manquant)")
        
        # 🔥 ÉCHELLE 1/500 OBLIGATOIRE pour plan cadastral
        # 1 cm sur le plan = 500 cm (5 m) dans la réalité
        # Calculer la bbox en mètres selon la taille du cadre PDF
        plan_width_cm = plan_width / cm
        plan_height_cm = plan_height / cm
        
        bbox_width_meters = plan_width_cm * 5  # 1cm = 5m à l'échelle 1/500
        bbox_height_meters = plan_height_cm * 5
        
        # Prendre la plus grande dimension pour créer un bbox carré
        # 🔥 CORRECTION: Ne PAS multiplier par 3.5 pour garder l'échelle exacte 1/500
        bbox_meters = max(bbox_width_meters, bbox_height_meters) / 2  # Rayon = demi-diagonale
        
        print(f"[PLAN] Échelle 1/500: Cadre {plan_width_cm:.1f}x{plan_height_cm:.1f}cm = {bbox_width_meters:.0f}x{bbox_height_meters:.0f}m réels")
        print(f"[PLAN] Bbox satellite: {bbox_meters*2:.0f}m de côté (rayon {bbox_meters:.0f}m) - ÉCHELLE EXACTE 1/500")
        
        # Convertir en degrés avec les BONS facteurs
        meters_to_lat = bbox_meters * meters_per_degree_lat
        meters_to_lon = bbox_meters * meters_per_degree_lng
        
        # Stocker les limites GPS réelles
        self.gps_bounds = {
            'min_lat': lat - meters_to_lat,
            'max_lat': lat + meters_to_lat,
            'min_lon': lon - meters_to_lon,
            'max_lon': lon + meters_to_lon
        }
        
        if lat and lon:
            # 🔥 DÉSACTIVÉ: Ne PAS utiliser le screenshot car coordonnées GPS imprécises
            # On dessine tout manuellement avec les vraies coordonnées GPS
            screenshot_data = None  # Force désactivation du screenshot
            
            if False and screenshot_data:  # Désactivé
                try:
                    # Le screenshot est en base64 data URL: "data:image/png;base64,..."
                    import base64
                    import re
                    
                    # Extraire les données base64
                    base64_match = re.search(r'base64,(.+)', screenshot_data)
                    if base64_match:
                        base64_str = base64_match.group(1)
                        img_data = base64.b64decode(base64_str)
                        img_buffer = io.BytesIO(img_data)
                        
                        print(f"[PLAN] 📸 Utilisation du screenshot de la carte ({len(img_data)} bytes)")
                        
                        # Récupérer les métadonnées de la carte pour calibrer GPS→PDF
                        map_metadata = self.calpinage.get('map_metadata', {})
                        if map_metadata and 'bounds' in map_metadata:
                            bounds = map_metadata['bounds']
                            dimensions = map_metadata.get('dimensions', {})
                            
# 🔥 Comme on dessine avec preserveAspectRatio=False,
                            # l'image remplit TOUT le cadre, donc pas besoin de calculer actual_image_bbox
                            # Les bounds GPS correspondent au cadre PDF complet
                            
                            self.gps_bounds = {
                                'min_lat': bounds['south'],
                                'max_lat': bounds['north'],
                                'min_lon': bounds['west'],
                                'max_lon': bounds['east']
                            }
                            print(f"[PLAN] 🗺️ Bounds GPS screenshot (cadre complet): lat[{bounds['south']:.6f}, {bounds['north']:.6f}] lon[{bounds['west']:.6f}, {bounds['east']:.6f}]")
                        
                        # Dessiner le screenshot - REMPLIR TOUT LE CADRE
                        c.drawImage(ImageReader(img_buffer), 
                                  plan_x, plan_y, 
                                  width=plan_width, height=plan_height,
                                  preserveAspectRatio=False, mask='auto')  # False = remplit tout
                        
                        self.screenshot_used = True
                    else:
                        self.screenshot_used = False
                except Exception as e:
                    print(f"[PLAN] ⚠️ Erreur lecture screenshot: {e}")
                    self.screenshot_used = False
            else:
                self.screenshot_used = False
            
            # 🔥 FALLBACK: Image satellite si pas de screenshot
            if not self.screenshot_used:
                satellite_img = self._fetch_satellite_image_bbox(lat, lon, bbox_meters, width=1600, height=1400)
                if satellite_img:
                    # REMPLIR TOUT LE CADRE (pas de blanc autour)
                    c.drawImage(ImageReader(satellite_img), 
                              plan_x, plan_y, 
                              width=plan_width, height=plan_height,
                              preserveAspectRatio=False, mask='auto')  # False = remplit tout
                    print(f"[PLAN] ✅ Image satellite: {bbox_meters*2:.0f}m de rayon à l'échelle 1/500")
                    
                    # 🔥 IMPORTANT: Définir gps_bounds pour l'image satellite
                    # Calculer les limites GPS du bbox carré centré sur lat/lon
                    import math
                    # Rayon de la Terre en mètres
                    R = 6371000
                    # Conversion mètres → degrés latitude (environ 111km par degré)
                    delta_lat = (bbox_meters / R) * (180 / math.pi)
                    # Conversion mètres → degrés longitude (varie selon latitude)
                    delta_lon = (bbox_meters / (R * math.cos(lat * math.pi / 180))) * (180 / math.pi)
                    
                    self.gps_bounds = {
                        'min_lat': lat - delta_lat,
                        'max_lat': lat + delta_lat,
                        'min_lon': lon - delta_lon,
                        'max_lon': lon + delta_lon
                    }
                    print(f"[PLAN] 🗺️ GPS bounds satellite: lat[{self.gps_bounds['min_lat']:.6f}, {self.gps_bounds['max_lat']:.6f}] lon[{self.gps_bounds['min_lon']:.6f}, {self.gps_bounds['max_lon']:.6f}]")
                    
                self.screenshot_used = False  # Image satellite, pas de screenshot
        
        # Système de coordonnées : conversion GPS → PDF
        # Centre du plan = position GPS du bâtiment
        self.plan_bbox = {
            'x': plan_x,
            'y': plan_y,
            'width': plan_width,
            'height': plan_height,
            'lat_center': lat,
            'lon_center': lon,
            'meters_per_cm': bbox_meters / (plan_width / cm) if plan_width > 0 else 1
        }
        
        # 1. PARCELLES CADASTRALES (avec vraies géométries si disponibles)
        self._draw_parcelles(c, self.plan_bbox['x'] + self.plan_bbox['width']/2, self.plan_bbox['y'] + self.plan_bbox['height']/2, lat, lon)
        
        # 2. BÂTIMENT (à la position GPS) - DÉSACTIVÉ pour plan de masse simple
        # self._draw_batiment(c, self.plan_bbox['x'] + self.plan_bbox['width']/2, self.plan_bbox['y'] + self.plan_bbox['height']/2)
        
        # 3. MODULES PV - TOUJOURS redessiner avec coordonnées GPS précises
        # 🔥 Screenshot désactivé car GPS imprécis → on redessine tout manuellement
        if self.calpinage:
            self._draw_modules_pv_from_gps(c)
            print("[PLAN] ✅ Modules PV dessinés avec coordonnées GPS précises (screenshot désactivé)")
        
        # 4. COTATIONS - Dessiner les cotations sur les zones PV
        if self.calpinage and 'zones' in self.calpinage:
            self._draw_cotations_zones(c)
        
        # 5. ROSE DES VENTS - OBLIGATOIRE pour plan cadastral
        self._draw_compass(c, plan_x, plan_y, plan_width, plan_height)
        
    def _draw_compass(self, c, plan_x, plan_y, plan_width, plan_height):
        """Dessine la rose des vents (Nord/Sud/Est/Ouest) - OBLIGATOIRE"""
        # Position : coin supérieur gauche du plan
        compass_x = plan_x + 1*cm
        compass_y = plan_y + plan_height - 3*cm
        compass_size = 2*cm
        
        # Fond blanc
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.5)
        c.circle(compass_x, compass_y, compass_size/2, fill=1, stroke=1)
        
        # Flèche Nord (rouge)
        c.setFillColor(colors.HexColor('#D32F2F'))
        c.setStrokeColor(colors.HexColor('#D32F2F'))
        c.setLineWidth(2)
        
        # Ligne Nord
        north_y = compass_y + compass_size/2 - 0.2*cm
        c.line(compass_x, compass_y, compass_x, north_y)
        
        # Triangle Nord
        path = c.beginPath()
        path.moveTo(compass_x, north_y)
        path.lineTo(compass_x - 0.25*cm, north_y - 0.4*cm)
        path.lineTo(compass_x + 0.25*cm, north_y - 0.4*cm)
        path.close()
        c.drawPath(path, fill=1, stroke=0)
        
        # Texte Nord
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(compass_x, north_y + 0.15*cm, "N")
        
        # Sud (gris)
        c.setStrokeColor(colors.HexColor('#757575'))
        c.setFillColor(colors.HexColor('#757575'))
        c.setLineWidth(1.5)
        south_y = compass_y - compass_size/2 + 0.2*cm
        c.line(compass_x, compass_y, compass_x, south_y)
        c.setFont("Helvetica", 9)
        c.drawCentredString(compass_x, south_y - 0.35*cm, "S")
        
        # Est
        east_x = compass_x + compass_size/2 - 0.2*cm
        c.line(compass_x, compass_y, east_x, compass_y)
        c.drawCentredString(east_x + 0.3*cm, compass_y - 0.15*cm, "E")
        
        # Ouest
        west_x = compass_x - compass_size/2 + 0.2*cm
        c.line(compass_x, compass_y, west_x, compass_y)
        c.drawCentredString(west_x - 0.3*cm, compass_y - 0.15*cm, "O")
        
    def _calculate_bbox_from_data(self):
        """Calcule la taille de la bbox en mètres basée sur les données"""
        # Estimer depuis les parcelles ou défaut 60m
        parcelles = self._extract_parcelles()
        if parcelles:
            total_surface = sum(float(p.get('surface', 0)) for p in parcelles)
            if total_surface > 0:
                # Approximation: bbox = racine(surface) * 1.5 pour avoir de la marge
                return (total_surface ** 0.5) * 1.5
        
        # Défaut: 60m de rayon (120m de côté)
        return 60
    
    def _lat_lon_to_pdf(self, lat, lon):
        """
        Convertit coordonnées GPS en coordonnées PDF
        Utilise projection Lambert 93 pour éviter les distorsions
        """
        if not hasattr(self, 'gps_bounds'):
            return (0, 0)
        
        # 🔥 Utiliser plan_bbox car l'image remplit TOUT le cadre
        if hasattr(self, 'plan_bbox'):
            bbox = self.plan_bbox
        else:
            return (0, 0)
        
        gps = self.gps_bounds
        
        try:
            # 🔥 CORRECTION: Utiliser projection Lambert 93 pour éviter distorsions
            from pyproj import Transformer
            to_l93 = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
            
            # Convertir les limites GPS en Lambert 93
            min_x_l93, min_y_l93 = to_l93.transform(gps['min_lon'], gps['min_lat'])
            max_x_l93, max_y_l93 = to_l93.transform(gps['max_lon'], gps['max_lat'])
            
            # Convertir le point en Lambert 93
            x_l93, y_l93 = to_l93.transform(lon, lat)
            
            # Normaliser dans l'intervalle [0, 1]
            x_range = max_x_l93 - min_x_l93
            y_range = max_y_l93 - min_y_l93
            
            if x_range == 0 or y_range == 0:
                return (bbox['x'] + bbox['width']/2, bbox['y'] + bbox['height']/2)
            
            x_ratio = (x_l93 - min_x_l93) / x_range
            y_ratio = (y_l93 - min_y_l93) / y_range
            
            # Convertir en coordonnées PDF
            pdf_x = bbox['x'] + x_ratio * bbox['width']
            pdf_y = bbox['y'] + y_ratio * bbox['height']
            
            return (pdf_x, pdf_y)
            
        except Exception as e:
            print(f"[PLAN] ⚠️ Erreur projection Lambert 93: {e}, fallback linéaire")
            # Fallback: conversion linéaire simple
            lat_range = gps['max_lat'] - gps['min_lat']
            lon_range = gps['max_lon'] - gps['min_lon']
            
            if lat_range == 0 or lon_range == 0:
                return (bbox['x'] + bbox['width']/2, bbox['y'] + bbox['height']/2)
            
            lat_ratio = (lat - gps['min_lat']) / lat_range
            lon_ratio = (lon - gps['min_lon']) / lon_range
            
            pdf_x = bbox['x'] + lon_ratio * bbox['width']
            pdf_y = bbox['y'] + lat_ratio * bbox['height']
            
            return (pdf_x, pdf_y)
    
    def _draw_parcelles(self, c, center_x, center_y, lat, lon):
        """Dessine les parcelles avec leurs vraies géométries GeoJSON si disponibles"""
        parcelles = self._extract_parcelles()
        
        if not parcelles:
            print("[PLAN] ⚠️ Aucune parcelle à dessiner")
            return
        
        print(f"[PLAN] 🏘️ Dessin de {len(parcelles)} parcelles...")
        
        # 🔥 SAUVEGARDER l'état du canvas avant le clipping
        c.saveState()
        
        # Ajouter un clipPath pour limiter le dessin au cadre
        if hasattr(self, 'plan_bbox'):
            bbox = self.plan_bbox
            clip_path = c.beginPath()
            clip_path.rect(bbox['x'], bbox['y'], bbox['width'], bbox['height'])
            c.clipPath(clip_path, stroke=0, fill=0)
        
        for i, parcelle in enumerate(parcelles):
            section = parcelle.get('section', '')
            numero = parcelle.get('numero', '')
            surface = parcelle.get('surface', 0)
            geojson = parcelle.get('geojson') or parcelle.get('geometry')
            
            print(f"[PLAN] Parcelle {section}{numero}: geojson={'OUI' if geojson else 'NON'}, surface={surface}")
            
            # Si géométrie GeoJSON disponible, l'utiliser
            if geojson and isinstance(geojson, dict):
                print(f"[PLAN] → Dessin avec GeoJSON")
                self._draw_parcelle_from_geojson(c, geojson, section, numero, surface)
            else:
                # Fallback: rectangle approximatif centré TRÈS VISIBLE
                print(f"[PLAN] → Dessin approximatif (pas de GeoJSON)")
                self._draw_parcelle_approximative(c, section, numero, surface, i, len(parcelles))
        
        # 🔥 RESTAURER l'état du canvas pour ne pas affecter la légende et le cartouche
        c.restoreState()
    
    def _draw_parcelle_from_geojson(self, c, geojson, section, numero, surface):
        """Dessine une parcelle depuis sa géométrie GeoJSON réelle"""
        try:
            geometry = geojson.get('geometry', geojson)
            coords = geometry.get('coordinates', [])
            geom_type = geometry.get('type', '')
            
            print(f"[PLAN] 🎨 Dessin parcelle {section}{numero} avec géométrie {geom_type}")
            
            # Calculer surface depuis géométrie si surface==0
            if not surface or float(surface) == 0:
                try:
                    from shapely.geometry import shape
                    shp = shape(geometry)
                    # Transformer en L93 pour calcul précis de surface
                    from pyproj import Transformer
                    to_l93 = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
                    from shapely.ops import transform as shp_transform
                    shp_l93 = shp_transform(to_l93.transform, shp)
                    surface = int(shp_l93.area)  # m²
                    print(f"[PLAN] 📐 Surface calculée pour {section}{numero}: {surface}m²")
                except Exception as e:
                    print(f"[PLAN] ⚠️ Calcul surface impossible: {e}")
                    surface = 0
            
            # Gestion Polygon et MultiPolygon
            polygons_to_draw = []
            
            if geom_type == 'Polygon' and coords:
                polygons_to_draw.append(coords[0])  # Premier anneau (contour extérieur)
            elif geom_type == 'MultiPolygon' and coords:
                # Dessiner tous les polygones du MultiPolygon
                for polygon in coords:
                    if polygon and len(polygon) > 0:
                        polygons_to_draw.append(polygon[0])
            
            if not polygons_to_draw:
                print(f"[PLAN] ❌ Pas de polygone à dessiner pour {section}{numero}")
                return
            
            print(f"[PLAN] 📍 {len(polygons_to_draw)} polygone(s) à dessiner")
            
            # Dessiner chaque polygone
            label_x, label_y = None, None
            
            for polygon_idx, exterior_ring in enumerate(polygons_to_draw):
                # Convertir chaque point GPS → PDF
                path = c.beginPath()
                first_point = True
                points_converted = 0
                
                for coord in exterior_ring:
                    lon, lat = coord[0], coord[1]
                    pdf_x, pdf_y = self._lat_lon_to_pdf(lat, lon)
                    
                    if first_point:
                        path.moveTo(pdf_x, pdf_y)
                        first_point = False
                        if label_x is None:  # Position étiquette sur le premier polygone
                            label_x, label_y = pdf_x, pdf_y
                        points_converted += 1
                    else:
                        path.lineTo(pdf_x, pdf_y)
                        points_converted += 1
                
                path.close()
                print(f"[PLAN]   Polygone #{polygon_idx+1}: {points_converted} points convertis")
                
                # CONTOUR PARCELLE TRÈS VISIBLE
                # 1. Fond jaune semi-transparent pour voir la parcelle
                c.setFillColorRGB(1, 1, 0, 0.15)  # Jaune transparent 15%
                c.setStrokeColor(colors.HexColor('#FF0000'))  # Rouge vif
                c.setLineWidth(2.5)  # Trait épais
                c.drawPath(path, stroke=1, fill=1)
                
                # 2. Bordure en pointillés noirs pour contraste
                c.setStrokeColor(colors.black)
                c.setLineWidth(1)
                c.setDash(6, 3)
                c.drawPath(path, stroke=1, fill=0)
                c.setDash()  # Réinitialiser
            
            # Étiquette VISIBLE avec fond blanc
            if label_x is not None and label_y is not None:
                # Fond blanc opaque
                c.setFillColor(colors.white)
                c.setStrokeColor(colors.HexColor('#FF0000'))
                c.setLineWidth(1.5)
                
                # Rectangle de fond
                text_w = 2.8*cm
                text_h = 0.8*cm
                c.rect(label_x + 0.1*cm, label_y + 0.1*cm, text_w, text_h, fill=1, stroke=1)
                
                # Texte en gras et visible
                c.setFillColor(colors.HexColor('#FF0000'))
                c.setFont("Helvetica-Bold", 9)
                c.drawString(label_x + 0.2*cm, label_y + 0.5*cm, 
                            f"Parcelle {section} {numero}")
                
                # Surface en dessous
                if surface and float(surface) > 0:
                    c.setFont("Helvetica", 7)
                    c.setFillColor(colors.black)
                    c.drawString(label_x + 0.2*cm, label_y + 0.25*cm, 
                                f"Surface: {int(float(surface))} m²")
            
            print(f"[PLAN] ✅ Parcelle {section}{numero} dessinée avec succès")
            return
            
        except Exception as e:
            print(f"[PLAN] ❌ Erreur dessin parcelle GeoJSON {section}{numero}: {e}")
            import traceback
            traceback.print_exc()
            pass
    
    def _draw_parcelle_approximative(self, c, section, numero, surface, index, total):
        """Dessine une parcelle approximative (rectangle)"""
        if not hasattr(self, 'plan_bbox'):
            return
            
        bbox = self.plan_bbox
        center_x = bbox['x'] + bbox['width'] / 2
        center_y = bbox['y'] + bbox['height'] / 2
        
        # Estimer dimensions
        try:
            surface_m2 = float(surface)
            largeur = (surface_m2 / 1.5) ** 0.5
            longueur = largeur * 1.5
        except:
            largeur = 30
            longueur = 45
        
        # Échelle
        meters_per_cm = bbox['meters_per_cm']
        parc_w = (longueur / meters_per_cm) * cm
        parc_h = (largeur / meters_per_cm) * cm
        
        # Décalage si plusieurs parcelles
        offset_x = (index - total/2) * 5 * cm
        
        parc_x = center_x - parc_w/2 + offset_x
        parc_y = center_y - parc_h/2
        
        # Contour VISIBLE mais pas trop épais
        c.setStrokeColor(colors.HexColor('#FF00FF'))  # Magenta
        c.setLineWidth(3)  # Ligne normale
        c.setDash(10, 5)  # Pointillés
        c.rect(parc_x, parc_y, parc_w, parc_h, fill=0, stroke=1)
        c.setDash()
        
        # Étiquette DISCRÈTE en bas à gauche de la parcelle
        c.setFillColorRGB(1, 1, 1, 0.8)  # Blanc semi-transparent
        c.setStrokeColor(colors.HexColor('#FF00FF'))
        c.setLineWidth(1)
        label_bg_w = 2.5*cm
        label_bg_h = 0.6*cm
        c.rect(parc_x + 0.1*cm, parc_y + 0.1*cm, label_bg_w, label_bg_h, fill=1, stroke=1)
        
        # Étiquette texte compact
        c.setFillColor(colors.HexColor('#FF00FF'))
        c.setFont("Helvetica-Bold", 7)
        c.drawString(parc_x + 0.2*cm, parc_y + 0.35*cm, 
                    f"{section}{numero}")
        if surface and float(surface) > 0:
            c.setFont("Helvetica", 6)
            c.drawString(parc_x + 0.2*cm, parc_y + 0.15*cm, 
                        f"{int(float(surface))}m²")
    
    def _draw_batiment(self, c, center_x, center_y):
        """Dessine le bâtiment"""
        echelle = 0.3  # cm par mètre
        
        # Dimensions avec conversion sécurisée
        try:
            longueur = float(self.data.get('longueur_batiment_m', 15))
            largeur = float(self.data.get('largeur_batiment_m', 10))
        except (ValueError, TypeError):
            longueur = 15
            largeur = 10
        
        bat_w = longueur * echelle * cm
        bat_h = largeur * echelle * cm
        
        bat_x = center_x - bat_w/2
        bat_y = center_y - bat_h/2
        
        # Rectangle bâtiment
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.HexColor('#FFE4B5'))  # Beige
        c.setLineWidth(2)
        c.rect(bat_x, bat_y, bat_w, bat_h, fill=1, stroke=1)
        
        # Étiquette
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(center_x, center_y, "BÂTIMENT")
    
    def _draw_modules_pv_reels(self, c, center_x, center_y, lat, lon):
        """DEPRECATED - Utiliser _draw_modules_pv_from_gps à la place"""
        pass
    
    def _draw_modules_pv_from_gps(self, c):
        """Dessine les modules PV selon leurs VRAIES coordonnées GPS sauvegardées"""
        
        if not self.calpinage or 'zones' not in self.calpinage:
            return
        
        zones = self.calpinage['zones']
        
        for zone in zones:
            # Récupérer les positions GPS de chaque module
            modules_positions = zone.get('modulesPositions', [])
            
            if not modules_positions:
                print(f"[PLAN] ⚠️ Aucune position GPS pour zone {zone.get('numero', '?')}")
                continue
            
            print(f"[PLAN] 📍 Dessin {len(modules_positions)} modules avec coordonnées GPS pour zone {zone.get('numero', '?')}")
            
            # Dessiner chaque module selon ses coordonnées GPS
            c.setStrokeColor(colors.HexColor('#1565C0'))  # Bleu foncé
            c.setFillColor(colors.HexColor('#2196F3'))    # Bleu clair
            c.setLineWidth(0.5)
            
            for module in modules_positions:
                corners = module.get('corners', [])
                
                if len(corners) < 4:
                    continue
                
                # Convertir les 4 coins GPS → coordonnées PDF
                path = c.beginPath()
                first = True
                
                for corner in corners:
                    pdf_x, pdf_y = self._lat_lon_to_pdf(corner['lat'], corner['lng'])
                    
                    if first:
                        path.moveTo(pdf_x, pdf_y)
                        first = False
                    else:
                        path.lineTo(pdf_x, pdf_y)
                
                path.close()
                
                # Dessiner le module
                c.drawPath(path, stroke=1, fill=1)
            
            # Dessiner le contour de la zone (optionnel)
            zone_coords = zone.get('coordinates', [])
            if zone_coords:
                path = c.beginPath()
                first = True
                
                for coord in zone_coords:
                    pdf_x, pdf_y = self._lat_lon_to_pdf(coord['lat'], coord['lng'])
                    
                    if first:
                        path.moveTo(pdf_x, pdf_y)
                        first = False
                    else:
                        path.lineTo(pdf_x, pdf_y)
                
                path.close()
                
                # Contour zone rouge en pointillés
                c.setStrokeColor(colors.HexColor('#D32F2F'))
                c.setLineWidth(2)
                c.setDash(4, 2)
                c.drawPath(path, stroke=1, fill=0)
                c.setDash()
                
                # Étiquette zone
                if zone_coords:
                    label_x, label_y = self._lat_lon_to_pdf(zone_coords[0]['lat'], zone_coords[0]['lng'])
                    c.setFillColor(colors.HexColor('#D32F2F'))
                    c.setFont("Helvetica-Bold", 8)
                    nb_modules = zone.get('nbModules', len(modules_positions))
                    nb_cols = zone.get('nbCols', 0)
                    nb_rows = zone.get('nbRows', 0)
                    c.drawString(label_x + 0.4*cm, label_y + 0.4*cm,
                                f"Zone PV: {nb_modules} modules ({nb_cols}×{nb_rows})")
    
    def _draw_cotations_zones(self, c):
        """Dessine les cotations (largeur et longueur) sur chaque zone PV"""
        if not self.calpinage or 'zones' not in self.calpinage:
            return
        
        zones = self.calpinage['zones']
        
        for zone in zones:
            zone_coords = zone.get('coordinates', [])
            if not zone_coords or len(zone_coords) < 4:
                continue
            
            # Convertir les coordonnées GPS en PDF
            pdf_coords = []
            for coord in zone_coords:
                pdf_x, pdf_y = self._lat_lon_to_pdf(coord['lat'], coord['lng'])
                pdf_coords.append((pdf_x, pdf_y))
            
            if len(pdf_coords) < 4:
                continue
            
            # Calculer les dimensions réelles
            largeur_m = zone.get('largeurMetres', 0)
            longueur_m = zone.get('longueurMetres', 0)
            
            if largeur_m == 0 or longueur_m == 0:
                continue
            
            # Points de la zone (rectangle)
            p1, p2, p3, p4 = pdf_coords[0], pdf_coords[1], pdf_coords[2], pdf_coords[3]
            
            # Style cotations
            c.setStrokeColor(colors.HexColor('#D32F2F'))
            c.setFillColor(colors.HexColor('#D32F2F'))
            c.setFont("Helvetica-Bold", 9)
            c.setLineWidth(1.5)
            
            # Cotation longueur (bas) - entre p1 et p2
            offset_y = -0.8*cm
            mid_x = (p1[0] + p2[0]) / 2
            mid_y = min(p1[1], p2[1]) + offset_y
            
            c.line(p1[0], mid_y, p2[0], mid_y)
            c.line(p1[0], mid_y - 0.15*cm, p1[0], mid_y + 0.15*cm)
            c.line(p2[0], mid_y - 0.15*cm, p2[0], mid_y + 0.15*cm)
            c.drawCentredString(mid_x, mid_y - 0.4*cm, f"{longueur_m:.1f} m")
            
            # Cotation largeur (droite) - entre p2 et p3
            offset_x = 0.8*cm
            mid_x = max(p2[0], p3[0]) + offset_x
            mid_y = (p2[1] + p3[1]) / 2
            
            c.line(mid_x, p2[1], mid_x, p3[1])
            c.line(mid_x - 0.15*cm, p2[1], mid_x + 0.15*cm, p2[1])
            c.line(mid_x - 0.15*cm, p3[1], mid_x + 0.15*cm, p3[1])
            
            c.saveState()
            c.translate(mid_x + 0.4*cm, mid_y)
            c.rotate(90)
            c.drawCentredString(0, 0, f"{largeur_m:.1f} m")
            c.restoreState()

    
    def _draw_cotations(self, c, center_x, center_y):
        """Dessine les cotations"""
        echelle = 0.3
        
        longueur = self.data.get('longueur_batiment_m', 15)
        largeur = self.data.get('largeur_batiment_m', 10)
        
        bat_w = longueur * echelle * cm
        bat_h = largeur * echelle * cm
        
        # Cotation longueur (bas)
        c.setStrokeColor(colors.HexColor('#D32F2F'))
        c.setFillColor(colors.HexColor('#D32F2F'))
        c.setFont("Helvetica-Bold", 9)
        c.setLineWidth(1.5)
        
        cote_y = center_y - bat_h/2 - 1*cm
        c.line(center_x - bat_w/2, cote_y, center_x + bat_w/2, cote_y)
        c.line(center_x - bat_w/2, cote_y - 0.2*cm, center_x - bat_w/2, cote_y + 0.2*cm)
        c.line(center_x + bat_w/2, cote_y - 0.2*cm, center_x + bat_w/2, cote_y + 0.2*cm)
        c.drawCentredString(center_x, cote_y - 0.5*cm, f"{longueur:.1f} m")
        
        # Cotation largeur (droite)
        cote_x = center_x + bat_w/2 + 1*cm
        c.line(cote_x, center_y - bat_h/2, cote_x, center_y + bat_h/2)
        c.line(cote_x - 0.2*cm, center_y - bat_h/2, cote_x + 0.2*cm, center_y - bat_h/2)
        c.line(cote_x - 0.2*cm, center_y + bat_h/2, cote_x + 0.2*cm, center_y + bat_h/2)
        
        c.saveState()
        c.translate(cote_x + 0.5*cm, center_y)
        c.rotate(90)
        c.drawCentredString(0, 0, f"{largeur:.1f} m")
        c.restoreState()
    
    def _draw_legend(self, c):
        """Dessine la légende"""
        x = 2*cm
        y = 12*cm  # Plus haut pour éviter chevauchement
        
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.black)
        c.drawString(x, y, "LÉGENDE :")
        
        y -= 0.6*cm
        c.setFont("Helvetica", 9)
        
        # Parcelle
        c.setStrokeColor(colors.HexColor('#FF00FF'))
        c.setLineWidth(2)
        c.setDash(8, 4)
        c.line(x, y, x + 1.5*cm, y)
        c.setDash()
        c.setFillColor(colors.black)
        c.drawString(x + 2*cm, y - 0.15*cm, "Limites parcellaires cadastrales")
        
        # Bâtiment
        y -= 0.5*cm
        c.setFillColor(colors.HexColor('#FFE4B5'))
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.rect(x, y - 0.25*cm, 1.5*cm, 0.4*cm, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.drawString(x + 2*cm, y - 0.15*cm, "Bâtiment existant")
        
        # Modules PV
        y -= 0.5*cm
        c.setFillColor(colors.HexColor('#2196F3'))
        c.setStrokeColor(colors.HexColor('#1565C0'))
        c.rect(x, y - 0.25*cm, 1.5*cm, 0.4*cm, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.drawString(x + 2*cm, y - 0.15*cm, "Modules photovoltaïques (position réelle)")
        
        # Zone PV
        y -= 0.5*cm
        c.setStrokeColor(colors.HexColor('#D32F2F'))
        c.setLineWidth(2)
        c.setDash(4, 2)
        c.line(x, y, x + 1.5*cm, y)
        c.setDash()
        c.setFillColor(colors.black)
        c.drawString(x + 2*cm, y - 0.15*cm, "Contour zone PV")
        
        # Cotations
        y -= 0.5*cm
        c.setStrokeColor(colors.HexColor('#D32F2F'))
        c.setLineWidth(1.5)
        c.line(x, y, x + 1.5*cm, y)
        c.setFillColor(colors.black)
        c.drawString(x + 2*cm, y - 0.15*cm, "Cotations (en mètres)")
    
    def _draw_cartouche(self, c):
        """Cartouche technique avec informations complètes"""
        x = self.width - 14*cm
        y = 2*cm  # En bas pour éviter chevauchement
        w = 12*cm
        h = 10*cm  # Hauteur augmentée pour toutes les infos
        
        # Cadre
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(x, y, w, h)
        
        # Titre
        c.setFillColor(colors.HexColor('#003366'))
        c.rect(x, y + h - 0.8*cm, w, 0.8*cm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(x + w/2, y + h - 0.55*cm, "CARACTÉRISTIQUES TECHNIQUES")
        
        # Contenu
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        
        info_y = y + h - 1.3*cm
        
        # Informations du projet
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 0.3*cm, info_y, "Projet :")
        info_y -= 0.35*cm
        c.setFont("Helvetica", 8)
        
        commune = self.data.get('commune', 'N/A')
        adresse = self.data.get('adresse', 'N/A')
        c.drawString(x + 0.5*cm, info_y, f"• {adresse}")
        info_y -= 0.3*cm
        c.drawString(x + 0.5*cm, info_y, f"• {commune}")
        info_y -= 0.5*cm
        
        # Parcelles cadastrales
        parcelles = self._extract_parcelles()
        if parcelles:
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x + 0.3*cm, info_y, "Parcelles cadastrales :")
            info_y -= 0.35*cm
            c.setFont("Helvetica", 7.5)
            
            # Afficher TOUTES les parcelles (max 6 pour tenir dans le cadre)
            for p in parcelles[:6]:
                section = p.get('section', '')
                numero = p.get('numero', '')
                surface = p.get('surface', 0)
                # N'afficher la surface que si elle est disponible
                if surface and float(surface) > 0:
                    c.drawString(x + 0.5*cm, info_y, f"• {section}{numero} - {surface} m²")
                else:
                    c.drawString(x + 0.5*cm, info_y, f"• {section}{numero} - Surface N/A")
                info_y -= 0.3*cm
            
            if len(parcelles) > 6:
                c.drawString(x + 0.5*cm, info_y, f"  ... et {len(parcelles) - 6} autre(s)")
                info_y -= 0.3*cm
            
            info_y -= 0.2*cm
        
        # Installation PV
        if self.calpinage and 'zones' in self.calpinage:
            total_modules = sum(z.get('nbModules', 0) for z in self.calpinage['zones'])
            puissance_module = self.calpinage.get('module', {}).get('puissance', 560)
            puissance_totale = total_modules * float(puissance_module) / 1000  # kWc
            
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x + 0.3*cm, info_y, "Installation photovoltaïque :")
            info_y -= 0.35*cm
            c.setFont("Helvetica", 8)
            c.drawString(x + 0.5*cm, info_y, f"• {total_modules} modules de {puissance_module}W")
            info_y -= 0.3*cm
            c.drawString(x + 0.5*cm, info_y, f"• Puissance totale : {puissance_totale:.2f} kWc")
            info_y -= 0.3*cm
            c.drawString(x + 0.5*cm, info_y, f"• {len(self.calpinage['zones'])} zone(s) PV")
        
        # Date et signature
        info_y = y + 0.5*cm
        c.setFont("Helvetica", 8)
        c.drawString(x + 0.3*cm, info_y, "Date : _______________")
        c.drawString(x + w/2 + 0.3*cm, info_y, "Signature :")
    
    def _fetch_satellite_image(self, lat, lon, zoom=19, width=1200, height=1000):
        """Récupère une image satellite via API"""
        try:
            # ArcGIS World Imagery (gratuit, haute résolution)
            url = f"https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
            
            # Calculer bbox autour du point
            # À zoom 19, ~10m de rayon
            delta = 0.0001 * (20 - zoom)  # Approximatif
            bbox = f"{lon - delta},{lat - delta},{lon + delta},{lat + delta}"
            
            params = {
                'bbox': bbox,
                'bboxSR': '4326',
                'size': f'{width},{height}',
                'format': 'png',
                'f': 'image'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return io.BytesIO(response.content)
        except Exception as e:
            print(f"Erreur image satellite: {e}")
        
        return None
    
    def _fetch_satellite_image_bbox(self, lat, lon, bbox_meters, width=1200, height=1000):
        """
        Récupère une image satellite avec une bbox en mètres autour du point central
        
        Args:
            lat, lon: Coordonnées GPS du centre
            bbox_meters: Rayon en mètres pour la bbox
            width, height: Dimensions de l'image en pixels
            
        Returns:
            BytesIO de l'image ou None
        """
        try:
            # Conversion mètres → degrés (approximatif pour France métropolitaine)
            # 1 degré latitude ≈ 111 km
            # 1 degré longitude ≈ 111 km * cos(latitude) ≈ 78 km à 45° de latitude
            meters_to_lat = bbox_meters / 111000
            meters_to_lon = bbox_meters / (111000 * 0.7)  # cos(45°) ≈ 0.7
            
            # Calculer bbox
            min_lon = lon - meters_to_lon
            max_lon = lon + meters_to_lon
            min_lat = lat - meters_to_lat
            max_lat = lat + meters_to_lat
            
            # ArcGIS World Imagery
            url = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
            
            bbox_str = f"{min_lon},{min_lat},{max_lon},{max_lat}"
            
            params = {
                'bbox': bbox_str,
                'bboxSR': '4326',
                'size': f'{width},{height}',
                'format': 'png',
                'f': 'image'
            }
            
            print(f"[PLAN] 🛰️ Téléchargement image satellite: bbox={bbox_meters:.0f}m ({bbox_meters*2:.0f}m côté), size={width}x{height}")
            print(f"[PLAN] 📍 GPS bounds: [{min_lat:.6f}, {max_lat:.6f}] x [{min_lon:.6f}, {max_lon:.6f}]")
            
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                img_size_kb = len(response.content) / 1024
                print(f"[PLAN] ✅ Image satellite téléchargée ({img_size_kb:.1f} KB)")
                return io.BytesIO(response.content)
            else:
                print(f"[PLAN] ❌ Erreur API ArcGIS: HTTP {response.status_code}")
                print(f"[PLAN] 🔗 URL: {response.url}")
        except Exception as e:
            print(f"[PLAN] ❌ Erreur image satellite: {e}")
        
        return None
    
    def _extract_parcelles(self):
        """Extrait les parcelles cadastrales"""
        # Essayer plusieurs champs possibles
        for field in ['parcelles_cadastrales', 'parcelles', 'cadastre', 'data_json']:
            parcelles_data = self.data.get(field)
            
            if parcelles_data:
                # Si c'est un dict avec une clé 'parcelles'
                if isinstance(parcelles_data, dict):
                    if 'parcelles_cadastrales' in parcelles_data:
                        parcelles_data = parcelles_data['parcelles_cadastrales']
                    elif 'parcelles' in parcelles_data:
                        parcelles_data = parcelles_data['parcelles']
                
                # Si c'est déjà une liste
                if isinstance(parcelles_data, list) and len(parcelles_data) > 0:
                    print(f"[PLAN] ✅ Trouvé {len(parcelles_data)} parcelles dans '{field}'")
                    # Enrichir avec géométries depuis API Cadastre si manquantes
                    parcelles_data = self._enrich_parcelles_with_geometry(parcelles_data)
                    # Normaliser les surfaces (essayer plusieurs clés)
                    for p in parcelles_data:
                        surface_val = p.get('surface', 0)
                        if not surface_val or surface_val == 0:
                            # Essayer d'autres clés
                            surface_val = p.get('superficie') or p.get('contenance') or p.get('surface_m2') or 0
                            if isinstance(surface_val, str):
                                try:
                                    surface_val = float(surface_val.replace(' ', '').replace('m²', '').replace(',', '.'))
                                except:
                                    surface_val = 0
                            p['surface'] = surface_val
                        if surface_val > 0:
                            print(f"[PLAN] 📊 Parcelle {p.get('section', '')}{p.get('numero', '')}: surface={surface_val:.0f}m²")
                    return parcelles_data
                
                # Si c'est une chaîne JSON
                if isinstance(parcelles_data, str) and parcelles_data:
                    try:
                        parsed = json.loads(parcelles_data)
                        if isinstance(parsed, list) and len(parsed) > 0:
                            print(f"[PLAN] ✅ Trouvé {len(parsed)} parcelles (JSON) dans '{field}'")
                            # 🔥 ENRICHIR avec l'API Cadastre IGN
                            parsed = self._enrich_parcelles_with_geometry(parsed)
                            return parsed
                        elif isinstance(parsed, dict):
                            for subkey in ['parcelles_cadastrales', 'parcelles']:
                                if subkey in parsed and isinstance(parsed[subkey], list):
                                    print(f"[PLAN] ✅ Trouvé {len(parsed[subkey])} parcelles dans '{field}.{subkey}'")
                                    # 🔥 ENRICHIR avec l'API Cadastre IGN
                                    enriched = self._enrich_parcelles_with_geometry(parsed[subkey])
                                    return enriched
                    except:
                        pass
        
        print(f"[PLAN] ⚠️ Aucune parcelle cadastrale trouvée dans les données prospect")
        print(f"[PLAN] Champs disponibles: {list(self.data.keys())}")
        return []
    
    def _enrich_parcelles_with_geometry(self, parcelles):
        """Enrichit les parcelles avec leurs géométries depuis l'API Cadastre Apicarto"""
        
        print(f"\n[PLAN] 🔍 ENRICHISSEMENT PARCELLES - Début")
        print(f"[PLAN] Nombre de parcelles à enrichir: {len(parcelles)}")
        
        # Afficher les parcelles disponibles
        for p in parcelles:
            print(f"[PLAN]   - Parcelle: section={p.get('section')}, numero={p.get('numero')}, a_geometry={bool(p.get('geojson') or p.get('geometry'))}")
        
        # Calculer la bbox englobante de toutes les zones PV
        if not self.calpinage or 'zones' not in self.calpinage:
            print(f"[PLAN] ⚠️ Aucune zone PV pour calculer la bbox - utilisation des coordonnées du prospect")
            # Fallback: utiliser les coordonnées du prospect avec un buffer de 200m
            lat = self.data.get('latitude')
            lon = self.data.get('longitude')
            if not lat or not lon:
                print(f"[PLAN] ❌ Pas de coordonnées disponibles")
                return parcelles
            
            buffer_deg = 200 / 111000  # 200m en degrés
            min_lat, max_lat = lat - buffer_deg, lat + buffer_deg
            min_lon, max_lon = lon - buffer_deg, lon + buffer_deg
        else:
            zones = self.calpinage['zones']
            if not zones:
                print(f"[PLAN] ⚠️ Liste zones vide")
                return parcelles
            
            # Collecter toutes les coordonnées GPS des zones
            all_lats = []
            all_lons = []
            
            for zone in zones:
                zone_coords = zone.get('coordinates', [])
                for coord in zone_coords:
                    all_lats.append(coord['lat'])
                    all_lons.append(coord['lng'])
            
            if not all_lats or not all_lons:
                print(f"[PLAN] ⚠️ Aucune coordonnée GPS dans les zones")
                return parcelles
            
            # Calculer la bbox avec un petit buffer (10m)
            buffer_deg = 10 / 111000
            min_lat = min(all_lats) - buffer_deg
            max_lat = max(all_lats) + buffer_deg
            min_lon = min(all_lons) - buffer_deg
            max_lon = max(all_lons) + buffer_deg
        
        # Créer un polygon GeoJSON de la bbox pour l'API Cadastre
        bbox_polygon = {
            "type": "Polygon",
            "coordinates": [[
                [min_lon, min_lat],
                [max_lon, min_lat],
                [max_lon, max_lat],
                [min_lon, max_lat],
                [min_lon, min_lat]
            ]]
        }
        
        print(f"[PLAN] 📍 Bbox recherche API: [{min_lat:.6f}, {max_lat:.6f}] x [{min_lon:.6f}, {max_lon:.6f}]")
        
        try:
            # Appel API Cadastre avec bbox des zones PV
            url = "https://apicarto.ign.fr/api/cadastre/parcelle"
            params = {
                "geom": json.dumps(bbox_polygon),
                "_limit": 1000,
                "source_ign": "PCI"
            }
            
            print(f"[PLAN] 🌐 Appel API Cadastre IGN...")
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                api_features = data.get('features', [])
                
                print(f"[PLAN] ✅ API retourne {len(api_features)} parcelles dans la bbox")
                
                # Afficher les premières parcelles de l'API pour debug
                for i, feat in enumerate(api_features[:3]):
                    props = feat.get('properties', {})
                    print(f"[PLAN]   API parcelle #{i+1}: section={props.get('section')}, numero={props.get('numero')}, commune={props.get('commune')}")
                
                # Enrichir chaque parcelle de notre liste avec les données de l'API
                enriched = []
                for p in parcelles:
                    section = str(p.get('section', '')).strip()
                    numero = str(p.get('numero', '')).strip().lstrip('0')  # Supprimer les 0 initiaux
                    
                    print(f"\n[PLAN] 🔎 Recherche parcelle {section}{numero}...")
                    
                    # Si déjà une géométrie, garder telle quelle
                    if p.get('geojson') or p.get('geometry'):
                        enriched.append(p)
                        print(f"[PLAN] ✅ Parcelle {section}{numero} a déjà une géométrie")
                        continue
                    
                    # Chercher la correspondance dans les features de l'API
                    found = False
                    for api_feature in api_features:
                        api_props = api_feature.get('properties', {})
                        api_section = str(api_props.get('section', '')).strip()
                        api_numero = str(api_props.get('numero', '')).strip().lstrip('0')  # Supprimer les 0 initiaux
                        
                        # Matching plus tolérant
                        if api_section == section and api_numero == numero:
                            p['geojson'] = api_feature
                            p['geometry'] = api_feature.get('geometry')
                            
                            # Récupérer la surface si disponible
                            if 'contenance' in api_props and api_props['contenance']:
                                p['surface'] = api_props['contenance']
                            
                            print(f"[PLAN] ✅✅ MATCH TROUVÉ pour {section}{numero} (surface: {p.get('surface', 'N/A')}m²)")
                            found = True
                            break
                    
                    if not found:
                        print(f"[PLAN] ❌ Parcelle {section}{numero} NON TROUVÉE dans l'API")
                    
                    enriched.append(p)
                
                print(f"\n[PLAN] 📊 Résumé enrichissement: {sum(1 for p in enriched if p.get('geojson') or p.get('geometry'))}/{len(enriched)} parcelles ont une géométrie")
                return enriched
            else:
                print(f"[PLAN] ❌ API erreur HTTP {response.status_code}")
                print(f"[PLAN] Réponse: {response.text[:200]}")
                return parcelles
                
        except Exception as e:
            print(f"[PLAN] ❌ Exception API Cadastre: {e}")
            import traceback
            traceback.print_exc()
            return parcelles


def generate_plan_masse(prospect_data, calpinage_data=None):
    """
    Génère un plan de masse cadastral avec calpinage PV
    
    Args:
        prospect_data: dict avec données prospect (parcelles, adresse, lat/lon, dimensions bâtiment)
        calpinage_data: dict optionnel avec zones PV et modules
        
    Returns:
        BytesIO buffer du PDF
    """
    generator = PlanMasseGenerator(prospect_data, calpinage_data)
    return generator.generate()
