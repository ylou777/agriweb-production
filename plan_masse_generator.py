"""
Générateur de Plan de Masse Cadastral avec Calpinage PV
Version simplifiée et professionnelle
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
import math


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
        
        # Échelle
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(self.width - 3*cm, y, "Échelle 1/200")
        
    def _draw_plan_cadastral(self, c):
        """Dessine le plan cadastral avec parcelles et modules PV"""
        
        # Zone de dessin
        plan_x = 3*cm
        plan_y = 8*cm
        plan_width = self.width - 6*cm
        plan_height = self.height - 14*cm
        
        # Cadre
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(plan_x, plan_y, plan_width, plan_height)
        
        # Fond
        c.setFillColor(colors.HexColor('#F5F5F5'))
        c.rect(plan_x, plan_y, plan_width, plan_height, fill=1, stroke=0)
        
        lat = self.data.get('latitude')
        lon = self.data.get('longitude')
        
        # Récupérer les métadonnées de la carte (bounds GPS exacts du screenshot)
        # map_metadata peut être dans prospect_data OU dans calpinage
        map_metadata = self.data.get('map_metadata') or (self.calpinage.get('map_metadata') if self.calpinage else {})
        map_bounds = map_metadata.get('bounds', {}) if map_metadata else {}
        
        print(f"[PLAN] map_metadata trouvé: {'✅' if map_metadata else '❌'}")
        if map_bounds:
            print(f"[PLAN] bounds GPS: N={map_bounds.get('north')}, S={map_bounds.get('south')}, E={map_bounds.get('east')}, W={map_bounds.get('west')}")
        
        # Utiliser les bounds exacts si disponibles, sinon calculer
        if map_bounds:
            # Bounds exacts de la carte Leaflet
            lat_north = map_bounds.get('north', lat)
            lat_south = map_bounds.get('south', lat)
            lon_east = map_bounds.get('east', lon)
            lon_west = map_bounds.get('west', lon)
            
            # Centre des bounds
            lat_center = (lat_north + lat_south) / 2
            lon_center = (lon_east + lon_west) / 2
        else:
            # Fallback: utiliser position du prospect
            lat_center = lat
            lon_center = lon
            # Calculer bbox approximative
            bbox_meters = self._calculate_bbox_from_data()
            delta_lat = (bbox_meters / 2) / 111000
            delta_lon = (bbox_meters / 2) / 78000
            lat_north = lat + delta_lat
            lat_south = lat - delta_lat
            lon_east = lon + delta_lon
            lon_west = lon - delta_lon
        
        if lat and lon:
            # Utiliser le screenshot de la carte si disponible (garantit échelle exacte)
            map_image = self._get_map_screenshot()
            if map_image:
                c.drawImage(ImageReader(map_image), 
                          plan_x, plan_y, 
                          width=plan_width, height=plan_height,
                          preserveAspectRatio=False, mask='auto')  # FALSE pour éviter déformation
            else:
                # Fallback: image satellite avec bbox correcte
                satellite_img = self._fetch_satellite_image_with_bounds(
                    lat_north, lat_south, lon_east, lon_west, width=1200, height=1000
                )
                if satellite_img:
                    c.drawImage(ImageReader(satellite_img), 
                              plan_x, plan_y, 
                              width=plan_width, height=plan_height,
                              preserveAspectRatio=False, mask='auto')
        
        # Système de coordonnées : conversion GPS → PDF
        # Utilise les MÊMES bounds que l'image affichée
        self.plan_bbox = {
            'x': plan_x,
            'y': plan_y,
            'width': plan_width,
            'height': plan_height,
            'lat_north': lat_north,
            'lat_south': lat_south,
            'lon_east': lon_east,
            'lon_west': lon_west,
            'lat_center': lat_center,
            'lon_center': lon_center
        }
        
        # 1. PARCELLES CADASTRALES (avec vraies géométries si disponibles)
        self._draw_parcelles_geojson(c)
        
        # 2. BÂTIMENT (à la position GPS)
        self._draw_batiment_gps(c)
        
        # 3. MODULES PV selon COORDONNÉES GPS DU CALPINAGE
        if self.calpinage:
            self._draw_modules_pv_gps(c)
        
        # 4. COTATIONS
        self._draw_cotations_gps(c)
        
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
        """Convertit coordonnées GPS en coordonnées PDF - MÉTHODE SIMPLE ET PRÉCISE"""
        if not hasattr(self, 'plan_bbox'):
            return (0, 0)
        
        bbox = self.plan_bbox
        
        # Récupérer les bounds GPS de l'image affichée
        lat_north = bbox.get('lat_north')
        lat_south = bbox.get('lat_south')
        lon_east = bbox.get('lon_east')
        lon_west = bbox.get('lon_west')
        
        if not all([lat_north, lat_south, lon_east, lon_west]):
            # Fallback si pas de bounds
            return (bbox['x'] + bbox['width'] / 2, bbox['y'] + bbox['height'] / 2)
        
        # Calculer la position relative dans les bounds (0 à 1)
        # Latitude : Nord = haut (1), Sud = bas (0)
        # Longitude : Ouest = gauche (0), Est = droite (1)
        lat_ratio = (lat - lat_south) / (lat_north - lat_south) if lat_north != lat_south else 0.5
        lon_ratio = (lon - lon_west) / (lon_east - lon_west) if lon_east != lon_west else 0.5
        
        # Convertir en coordonnées PDF
        # ATTENTION: En PDF, Y augmente vers le HAUT (inverse de l'écran)
        pdf_x = bbox['x'] + lon_ratio * bbox['width']
        pdf_y = bbox['y'] + lat_ratio * bbox['height']  # lat_ratio déjà correct (sud=0, nord=1)
        
        return (pdf_x, pdf_y)
    
    def _draw_parcelles(self, c, center_x, center_y, lat, lon):
        """Dessine les parcelles avec leurs vraies géométries GeoJSON si disponibles"""
        parcelles = self._extract_parcelles()
        
        if not parcelles:
            return
        
        for i, parcelle in enumerate(parcelles):
            section = parcelle.get('section', '')
            numero = parcelle.get('numero', '')
            surface = parcelle.get('surface', 0)
            geojson = parcelle.get('geojson')
            
            # Si géométrie GeoJSON disponible, l'utiliser
            if geojson and isinstance(geojson, dict):
                self._draw_parcelle_from_geojson(c, geojson, section, numero, surface)
            else:
                # Fallback: rectangle approximatif centré
                self._draw_parcelle_approximative(c, section, numero, surface, i, len(parcelles))
    
    def _draw_parcelle_from_geojson(self, c, geojson, section, numero, surface):
        """Dessine une parcelle depuis sa géométrie GeoJSON réelle"""
        try:
            geometry = geojson.get('geometry', geojson)
            coords = geometry.get('coordinates', [])
            geom_type = geometry.get('type', '')
            
            if geom_type == 'Polygon' and coords:
                # Prendre le premier ring (exterior)
                exterior_ring = coords[0]
                
                # Convertir chaque point GPS → PDF
                path = c.beginPath()
                first_point = True
                
                for coord in exterior_ring:
                    lon, lat = coord[0], coord[1]
                    pdf_x, pdf_y = self._lat_lon_to_pdf(lat, lon)
                    
                    if first_point:
                        path.moveTo(pdf_x, pdf_y)
                        first_point = False
                        label_x, label_y = pdf_x, pdf_y  # Position étiquette
                    else:
                        path.lineTo(pdf_x, pdf_y)
                
                path.close()
                
                # Dessiner contour parcelle
                c.setStrokeColor(colors.HexColor('#FF00FF'))  # Magenta
                c.setLineWidth(3)
                c.setDash(8, 4)
                c.drawPath(path, stroke=1, fill=0)
                c.setDash()
                
                # Étiquette
                c.setFillColor(colors.HexColor('#FF00FF'))
                c.setFont("Helvetica-Bold", 9)
                c.drawString(label_x + 0.3*cm, label_y + 0.3*cm, 
                            f"Parcelle {section}{numero}")
                c.setFont("Helvetica", 8)
                c.drawString(label_x + 0.3*cm, label_y - 0.2*cm, 
                            f"{surface} m²")
                return
        except Exception as e:
            print(f"[PLAN] Erreur dessin parcelle GeoJSON: {e}")
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
        
        # Contour
        c.setStrokeColor(colors.HexColor('#FF00FF'))
        c.setLineWidth(3)
        c.setDash(8, 4)
        c.rect(parc_x, parc_y, parc_w, parc_h, fill=0, stroke=1)
        c.setDash()
        
        # Étiquette
        c.setFillColor(colors.HexColor('#FF00FF'))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(parc_x + 0.3*cm, parc_y + parc_h + 0.3*cm, 
                    f"Parcelle {section}{numero}")
        c.setFont("Helvetica", 8)
        c.drawString(parc_x + 0.3*cm, parc_y + parc_h - 0.2*cm, 
                    f"{surface} m²")
    
    def _draw_parcelles_geojson(self, c):
        """Dessine les parcelles depuis leurs géométries GeoJSON"""
        parcelles = self._extract_parcelles()
        if not parcelles:
            return
        
        for parcelle in parcelles:
            section = parcelle.get('section', '')
            numero = parcelle.get('numero', '')
            surface = parcelle.get('surface', 0)
            geojson = parcelle.get('geojson')
            
            # Si géométrie GeoJSON disponible, l'utiliser
            if geojson and isinstance(geojson, dict):
                self._draw_parcelle_from_geojson(c, geojson, section, numero, surface)
    
    def _draw_batiment_gps(self, c):
        """Dessine le bâtiment à sa position GPS réelle"""
        lat = self.data.get('latitude')
        lon = self.data.get('longitude')
        
        if not lat or not lon:
            return
        
        # Position GPS du bâtiment convertie en coordonnées PDF
        center_x, center_y = self._lat_lon_to_pdf(lat, lon)
        
        # Dimensions du bâtiment
        try:
            longueur = float(self.data.get('longueur_batiment_m', 15))
            largeur = float(self.data.get('largeur_batiment_m', 10))
        except (ValueError, TypeError):
            longueur = 15
            largeur = 10
        
        # Conversion mètres → PDF (échelle basée sur les bounds GPS réels)
        # Calculer l'échelle en mètres par pixel puis par cm
        lat_range = self.plan_bbox.get('lat_north', lat) - self.plan_bbox.get('lat_south', lat)
        if lat_range > 0:
            meters_per_lat_deg = 111000  # Approximation
            total_height_meters = lat_range * meters_per_lat_deg
            meters_per_cm = total_height_meters / (self.plan_bbox['height'] / cm)
        else:
            meters_per_cm = 1
        
        bat_w = (longueur / meters_per_cm) * cm
        bat_h = (largeur / meters_per_cm) * cm
        
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
    
    def _draw_modules_pv_gps(self, c):
        """Dessine les modules PV selon leurs COORDONNÉES GPS RÉELLES du calpinage"""
        if not self.calpinage or 'zones' not in self.calpinage:
            return
        
        # Dessiner chaque zone avec ses modules
        for zone in self.calpinage['zones']:
            modules_positions = zone.get('modulesPositions', [])
            
            if modules_positions:
                # Utiliser les coordonnées GPS sauvegardées de chaque module
                self._draw_modules_from_positions(c, modules_positions, zone)
            else:
                # Fallback: utiliser l'ancienne méthode (positionnement relatif)
                print(f"[PLAN] Attention: Zone {zone.get('numero', '?')} sans coordonnées GPS des modules")
                lat = self.data.get('latitude')
                lon = self.data.get('longitude')
                if lat and lon:
                    center_x, center_y = self._lat_lon_to_pdf(lat, lon)
                    self._draw_modules_pv_reels(c, center_x, center_y, lat, lon)
                break  # Une seule fois pour toutes les zones sans GPS
    
    def _draw_modules_from_positions(self, c, modules_positions, zone):
        """Dessine chaque module à sa position GPS exacte"""
        if not modules_positions:
            return
        
        # Dimensions module
        try:
            module_longueur_mm = self.calpinage.get('module', {}).get('longueur', 2278)
            module_largeur_mm = self.calpinage.get('module', {}).get('largeur', 1134)
            module_longueur = float(module_longueur_mm) / 1000  # mm → m
            module_largeur = float(module_largeur_mm) / 1000
        except (ValueError, TypeError):
            module_longueur = 2.278
            module_largeur = 1.134
        
        # Calculer l'échelle (même méthode que bâtiment)
        lat_range = self.plan_bbox.get('lat_north', 0) - self.plan_bbox.get('lat_south', 0)
        if lat_range > 0:
            meters_per_lat_deg = 111000
            total_height_meters = lat_range * meters_per_lat_deg
            meters_per_cm = total_height_meters / (self.plan_bbox['height'] / cm)
        else:
            meters_per_cm = 1
        
        orientation = zone.get('moduleOrientation', 'paysage')
        
        c.setStrokeColor(colors.HexColor('#1565C0'))  # Bleu foncé
        c.setFillColor(colors.HexColor('#2196F3'))    # Bleu clair
        c.setLineWidth(0.5)
        
        # Dessiner chaque module
        for module_pos in modules_positions:
            lat = module_pos.get('lat')
            lng = module_pos.get('lng')
            
            if not lat or not lng:
                continue
            
            # Convertir position GPS → PDF
            center_x, center_y = self._lat_lon_to_pdf(lat, lng)
            
            # Dimensions selon orientation
            if orientation == 'paysage':
                mod_h = module_longueur
                mod_v = module_largeur
            else:  # portrait
                mod_h = module_largeur
                mod_v = module_longueur
            
            # Conversion en dimensions PDF
            mod_w = (mod_h / meters_per_cm) * cm
            mod_h_draw = (mod_v / meters_per_cm) * cm
            
            mod_x = center_x - mod_w/2
            mod_y = center_y - mod_h_draw/2
            
            # Dessiner le module
            c.rect(mod_x, mod_y, mod_w, mod_h_draw, fill=1, stroke=1)
        
        # Dessiner le contour de la zone
        self._draw_zone_contour(c, modules_positions, zone)
    
    def _draw_zone_contour(self, c, modules_positions, zone):
        """Dessine le contour d'une zone PV"""
        if not modules_positions:
            return
        
        # Trouver les limites de la zone
        lats = [m['lat'] for m in modules_positions if 'lat' in m]
        lngs = [m['lng'] for m in modules_positions if 'lng' in m]
        
        if not lats or not lngs:
            return
        
        # Convertir les coins en coordonnées PDF
        min_lat, max_lat = min(lats), max(lats)
        min_lng, max_lng = min(lngs), max(lngs)
        
        top_left_x, top_left_y = self._lat_lon_to_pdf(max_lat, min_lng)
        bottom_right_x, bottom_right_y = self._lat_lon_to_pdf(min_lat, max_lng)
        
        # Ajouter une marge
        margin = 0.2 * cm
        
        # Dessiner le contour
        c.setStrokeColor(colors.HexColor('#D32F2F'))  # Rouge
        c.setLineWidth(2)
        c.setDash(4, 2)
        c.rect(top_left_x - margin, bottom_right_y - margin,
              bottom_right_x - top_left_x + 2*margin,
              top_left_y - bottom_right_y + 2*margin,
              fill=0, stroke=1)
        c.setDash()
        
        # Étiquette zone
        nb_modules = zone.get('nbModules', len(modules_positions))
        c.setFillColor(colors.HexColor('#D32F2F'))
        c.setFont("Helvetica-Bold", 8)
        c.drawString(top_left_x, top_left_y + 0.4*cm,
                    f"Zone PV: {nb_modules} modules")
    
    def _draw_cotations_gps(self, c):
        """Dessine les cotations basées sur les dimensions GPS réelles"""
        lat = self.data.get('latitude')
        lon = self.data.get('longitude')
        
        if not lat or not lon:
            return
        
        center_x, center_y = self._lat_lon_to_pdf(lat, lon)
        
        try:
            longueur = float(self.data.get('longueur_batiment_m', 15))
            largeur = float(self.data.get('largeur_batiment_m', 10))
        except (ValueError, TypeError):
            longueur = 15
            largeur = 10
        
        # Calculer l'échelle (même méthode que pour le bâtiment)
        lat_range = self.plan_bbox.get('lat_north', lat) - self.plan_bbox.get('lat_south', lat)
        if lat_range > 0:
            meters_per_lat_deg = 111000
            total_height_meters = lat_range * meters_per_lat_deg
            meters_per_cm = total_height_meters / (self.plan_bbox['height'] / cm)
        else:
            meters_per_cm = 1
        
        bat_w = (longueur / meters_per_cm) * cm
        bat_h = (largeur / meters_per_cm) * cm
        
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
    
    def _draw_parcelles(self, c, center_x, center_y, lat, lon):
        """DEPRECATED - Utiliser _draw_parcelles_geojson"""
        pass
    
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
        """Dessine les modules PV selon le CALPINAGE RÉEL"""
        
        if not self.calpinage or 'zones' not in self.calpinage:
            return
        
        echelle = 0.3  # cm par mètre
        
        # Récupérer dimensions module avec conversion sécurisée
        try:
            module_longueur_mm = self.calpinage.get('module', {}).get('longueur', 2278)
            module_largeur_mm = self.calpinage.get('module', {}).get('largeur', 1134)
            
            # Convertir en float (gère string et int)
            module_longueur = float(module_longueur_mm) / 1000  # mm → m
            module_largeur = float(module_largeur_mm) / 1000    # mm → m
        except (ValueError, TypeError):
            # Valeurs par défaut si conversion échoue
            module_longueur = 2.278  # m
            module_largeur = 1.134   # m
        
        # Pour chaque zone du calpinage
        for zone in self.calpinage['zones']:
            nb_modules = zone.get('nbModules', 0)
            nb_cols = zone.get('nbCols', 0)
            nb_rows = zone.get('nbRows', 0)
            orientation_module = zone.get('moduleOrientation', 'paysage')
            
            # Dimensions selon orientation
            if orientation_module == 'paysage':
                mod_h = module_longueur  # 2.28m horizontal
                mod_v = module_largeur   # 1.13m vertical
            else:  # portrait
                mod_h = module_largeur   # 1.13m horizontal
                mod_v = module_longueur  # 2.28m vertical
            
            # Espacement entre modules
            espacement = 0.02  # 2cm entre modules
            
            # Dimensions totales de la zone
            zone_width = nb_cols * (mod_h + espacement)
            zone_height = nb_rows * (mod_v + espacement)
            
            # Position de départ (centré sur bâtiment)
            start_x = center_x - (zone_width * echelle * cm) / 2
            start_y = center_y - (zone_height * echelle * cm) / 2
            
            # Dessiner chaque module
            c.setStrokeColor(colors.HexColor('#1565C0'))  # Bleu foncé
            c.setFillColor(colors.HexColor('#2196F3'))    # Bleu clair
            c.setLineWidth(0.5)
            
            for row in range(nb_rows):
                for col in range(nb_cols):
                    mod_x = start_x + col * (mod_h + espacement) * echelle * cm
                    mod_y = start_y + row * (mod_v + espacement) * echelle * cm
                    mod_w = mod_h * echelle * cm
                    mod_h_draw = mod_v * echelle * cm
                    
                    # Rectangle module
                    c.rect(mod_x, mod_y, mod_w, mod_h_draw, fill=1, stroke=1)
            
            # Contour zone
            c.setStrokeColor(colors.HexColor('#D32F2F'))  # Rouge
            c.setLineWidth(2)
            c.setDash(4, 2)
            c.rect(start_x - 0.1*cm, start_y - 0.1*cm, 
                  zone_width * echelle * cm + 0.2*cm, 
                  zone_height * echelle * cm + 0.2*cm, 
                  fill=0, stroke=1)
            c.setDash()
            
            # Étiquette zone
            c.setFillColor(colors.HexColor('#D32F2F'))
            c.setFont("Helvetica-Bold", 8)
            c.drawString(start_x, start_y + zone_height * echelle * cm + 0.4*cm,
                        f"Zone PV: {nb_modules} modules ({nb_cols}×{nb_rows})")
    
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
        x = 3*cm
        y = 6*cm
        
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
        """Cartouche technique"""
        x = self.width - 15*cm
        y = 6*cm
        w = 12*cm
        h = 6*cm
        
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
        
        info_y = y + h - 1.5*cm
        
        # Parcelles
        parcelles = self._extract_parcelles()
        if parcelles:
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x + 0.3*cm, info_y, "Parcelles cadastrales :")
            info_y -= 0.4*cm
            c.setFont("Helvetica", 8)
            for p in parcelles[:3]:
                section = p.get('section', '')
                numero = p.get('numero', '')
                surface = p.get('surface', '')
                c.drawString(x + 0.5*cm, info_y, f"• {section}{numero} - {surface} m²")
                info_y -= 0.35*cm
        
        # Installation PV
        info_y -= 0.2*cm
        if self.calpinage and 'zones' in self.calpinage:
            total_modules = sum(z.get('nbModules', 0) for z in self.calpinage['zones'])
            puissance_module = self.calpinage.get('module', {}).get('puissance', 560)
            puissance_totale = total_modules * float(puissance_module) / 1000  # kWc
            
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x + 0.3*cm, info_y, "Installation photovoltaïque :")
            info_y -= 0.4*cm
            c.setFont("Helvetica", 8)
            c.drawString(x + 0.5*cm, info_y, f"• {total_modules} modules")
            info_y -= 0.35*cm
            c.drawString(x + 0.5*cm, info_y, f"• Puissance : {puissance_totale:.2f} kWc")
            info_y -= 0.35*cm
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
    
    def _get_map_screenshot(self):
        """Récupère le screenshot de la carte Leaflet si disponible"""
        # Screenshot peut être dans prospect_data OU dans calpinage
        screenshot_data = self.data.get('map_screenshot') or self.data.get('screenshot_map')
        if not screenshot_data and self.calpinage:
            screenshot_data = self.calpinage.get('screenshot_map')
        
        if not screenshot_data:
            print("[PLAN] Pas de screenshot trouvé")
            return None
        
        print(f"[PLAN] Screenshot trouvé: {len(screenshot_data)} chars")
        
        try:
            # Si c'est une data URL base64
            if isinstance(screenshot_data, str):
                if screenshot_data.startswith('data:image'):
                    # Extraire la partie base64
                    base64_data = screenshot_data.split(',')[1]
                    image_data = base64.b64decode(base64_data)
                    return io.BytesIO(image_data)
                else:
                    # Déjà en base64 pur
                    image_data = base64.b64decode(screenshot_data)
                    return io.BytesIO(image_data)
        except Exception as e:
            print(f"[PLAN] Erreur lecture screenshot: {e}")
        
        return None
    
    def _fetch_satellite_image_with_bounds(self, lat_north, lat_south, lon_east, lon_west, width=1200, height=1000):
        """Récupère une image satellite avec bounds GPS précis (comme Leaflet)"""
        try:
            # ArcGIS World Imagery
            url = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
            
            # Bbox : west, south, east, north
            bbox_str = f"{lon_west},{lat_south},{lon_east},{lat_north}"
            
            params = {
                'bbox': bbox_str,
                'bboxSR': '4326',
                'size': f'{width},{height}',
                'format': 'png',
                'f': 'image'
            }
            
            print(f"[PLAN] Récupération image satellite avec bounds: {bbox_str}")
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return io.BytesIO(response.content)
        except Exception as e:
            print(f"[PLAN] Erreur image satellite: {e}")
        
        return None
    
    def _extract_parcelles(self):
        """Extrait les parcelles cadastrales"""
        parcelles_data = self.data.get('parcelles_cadastrales', [])
        
        if isinstance(parcelles_data, list):
            return parcelles_data
        
        if isinstance(parcelles_data, str) and parcelles_data:
            try:
                return json.loads(parcelles_data)
            except:
                return []
        
        return []


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
