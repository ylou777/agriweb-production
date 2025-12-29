"""
Générateur de Plan de Masse Cadastral avec Calpinage PV - Version 2
Utilise les coordonnées GPS réelles pour un positionnement précis
"""

from reportlab.lib.pagesizes import A3
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import io
import requests
from PIL import Image
import json
import math


class PlanMasseGeneratorV2:
    """Génère un plan de masse cadastral avec positionnement GPS précis"""
    
    def __init__(self, prospect_data, calpinage_data=None):
        self.data = prospect_data
        self.calpinage = calpinage_data
        self.width, self.height = A3
        
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
        
        # Adresse
        y -= 0.6*cm
        c.setFont("Helvetica", 10)
        commune = self.data.get('commune', '')
        adresse = self.data.get('adresse', '')
        c.drawString(3*cm, y, f"{adresse}, {commune}")
        
        # Échelle dynamique
        c.setFont("Helvetica-Bold", 12)
        echelle_txt = self._calculate_scale_text()
        c.drawRightString(self.width - 3*cm, y, echelle_txt)
    
    def _calculate_scale_text(self):
        """Calcule l'échelle du plan"""
        bbox_meters = self._calculate_bbox_from_data()
        # Plan width = 23 cm (environ)
        plan_width_cm = (self.width - 6*cm) / cm
        meters_per_cm = bbox_meters / plan_width_cm
        echelle = int(meters_per_cm * 100)  # Échelle 1/X
        return f"Échelle 1/{echelle}"
    
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
        
        lat = self.data.get('latitude')
        lon = self.data.get('longitude')
        
        if not lat or not lon:
            # Si pas de GPS, afficher message
            c.setFont("Helvetica", 12)
            c.drawCentredString(plan_x + plan_width/2, plan_y + plan_height/2,
                              "Coordonnées GPS manquantes")
            return
        
        # Calculer la bbox en mètres
        bbox_meters = self._calculate_bbox_from_data()
        
        # Initialiser le système de projection
        self.projection = {
            'plan_x': plan_x,
            'plan_y': plan_y,
            'plan_width': plan_width,
            'plan_height': plan_height,
            'lat_center': lat,
            'lon_center': lon,
            'bbox_meters': bbox_meters,
            'meters_per_pixel_x': bbox_meters / plan_width * cm,
            'meters_per_pixel_y': bbox_meters / plan_height * cm
        }
        
        # Image de fond : priorité à l'image du calpinage, sinon image satellite
        calpinage_image = self._get_calpinage_screenshot()
        
        if calpinage_image:
            # Utiliser l'image capturée du calpinage
            c.drawImage(ImageReader(calpinage_image), 
                      plan_x, plan_y, 
                      width=plan_width, height=plan_height,
                      preserveAspectRatio=False, mask='auto')
            print("[PLAN] Image du calpinage utilisée")
        else:
            # Fallback: télécharger image satellite
            satellite_img = self._fetch_satellite_with_bbox(lat, lon, bbox_meters)
            if satellite_img:
                c.drawImage(ImageReader(satellite_img), 
                          plan_x, plan_y, 
                          width=plan_width, height=plan_height,
                          preserveAspectRatio=False, mask='auto')
                print("[PLAN] Image satellite ArcGIS utilisée")
            else:
                # Fond gris si pas d'image
                c.setFillColor(colors.HexColor('#F5F5F5'))
                c.rect(plan_x, plan_y, plan_width, plan_height, fill=1, stroke=0)
                print("[PLAN] Aucune image disponible")
        
        # 1. PARCELLES CADASTRALES
        self._draw_parcelles_with_geojson(c)
        
        # 2. BÂTIMENT
        self._draw_batiment_at_gps(c)
        
        # 3. MODULES PV selon COORDONNÉES GPS
        if self.calpinage:
            self._draw_modules_from_calpinage(c)
        
        # 4. COTATIONS
        self._draw_measurements(c)
    
    def _calculate_bbox_from_data(self):
        """Calcule la taille de la bbox en mètres"""
        # Essayer d'estimer depuis les parcelles
        parcelles = self._extract_parcelles()
        if parcelles:
            total_surface = sum(float(p.get('surface', 0)) for p in parcelles)
            if total_surface > 0:
                # bbox = √surface * 2 pour avoir de la marge
                return max(60, (total_surface ** 0.5) * 2)
        
        # Défaut: 120m (60m de rayon)
        return 120
    
    def _gps_to_pdf(self, lat, lon):
        """Convertit coordonnées GPS en coordonnées PDF"""
        if not hasattr(self, 'projection'):
            return (0, 0)
        
        proj = self.projection
        
        # Conversion GPS → mètres (projection simplifiée)
        # Pour petites distances, approximation linéaire valide
        delta_lat = lat - proj['lat_center']
        delta_lon = lon - proj['lon_center']
        
        # 1 degré latitude ≈ 111 km
        # 1 degré longitude ≈ 111 km * cos(latitude)
        lat_rad = math.radians(proj['lat_center'])
        meters_per_degree_lat = 111000
        meters_per_degree_lon = 111000 * math.cos(lat_rad)
        
        meters_y = delta_lat * meters_per_degree_lat
        meters_x = delta_lon * meters_per_degree_lon
        
        # Conversion mètres → pixels PDF
        pixel_x = meters_x / proj['meters_per_pixel_x']
        pixel_y = meters_y / proj['meters_per_pixel_y']
        
        # Position PDF (centre + offset)
        pdf_x = proj['plan_x'] + proj['plan_width'] / 2 + pixel_x
        pdf_y = proj['plan_y'] + proj['plan_height'] / 2 + pixel_y
        
        return (pdf_x, pdf_y)
    
    def _get_calpinage_screenshot(self):
        """Récupère l'image capturée du calpinage si disponible"""
        if not self.calpinage:
            return None
        
        screenshot_data = self.calpinage.get('screenshot_map')
        
        if not screenshot_data:
            return None
        
        try:
            # Décoder base64 en image
            import base64
            
            # Retirer le préfixe "data:image/png;base64," si présent
            if screenshot_data.startswith('data:image'):
                screenshot_data = screenshot_data.split(',', 1)[1]
            
            # Décoder base64
            image_data = base64.b64decode(screenshot_data)
            return io.BytesIO(image_data)
            
        except Exception as e:
            print(f"[PLAN] Erreur décodage screenshot calpinage: {e}")
            return None
    
    def _fetch_satellite_with_bbox(self, lat, lon, bbox_meters):
        """Récupère image satellite avec bbox précise"""
        try:
            # Calculer bbox en degrés GPS
            # Pour 45° de latitude (France), 1 degré ≈ 111 km
            lat_rad = math.radians(lat)
            meters_per_degree_lat = 111000
            meters_per_degree_lon = 111000 * math.cos(lat_rad)
            
            delta_deg_lat = (bbox_meters / 2) / meters_per_degree_lat
            delta_deg_lon = (bbox_meters / 2) / meters_per_degree_lon
            
            min_lon = lon - delta_deg_lon
            max_lon = lon + delta_deg_lon
            min_lat = lat - delta_deg_lat
            max_lat = lat + delta_deg_lat
            
            # ArcGIS World Imagery
            url = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
            
            bbox = f"{min_lon},{min_lat},{max_lon},{max_lat}"
            
            params = {
                'bbox': bbox,
                'bboxSR': '4326',
                'size': '1200,1000',
                'format': 'png',
                'f': 'image'
            }
            
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                return io.BytesIO(response.content)
        except Exception as e:
            print(f"[PLAN] Erreur image satellite: {e}")
        
        return None
    
    def _draw_parcelles_with_geojson(self, c):
        """Dessine les parcelles avec leurs géométries GeoJSON"""
        parcelles = self._extract_parcelles()
        
        for parcelle in parcelles:
            section = parcelle.get('section', '')
            numero = parcelle.get('numero', '')
            surface = parcelle.get('surface', 0)
            geojson = parcelle.get('geojson')
            
            if geojson and isinstance(geojson, dict):
                self._draw_geojson_polygon(c, geojson, section, numero, surface)
            else:
                # Fallback: rectangle approximatif
                print(f"[PLAN] Pas de GeoJSON pour parcelle {section}{numero}")
    
    def _draw_geojson_polygon(self, c, geojson, section, numero, surface):
        """Dessine un polygone depuis GeoJSON"""
        try:
            geometry = geojson.get('geometry', geojson)
            coords = geometry.get('coordinates', [])
            geom_type = geometry.get('type', '')
            
            if geom_type == 'Polygon' and coords:
                # Premier ring (exterior)
                exterior = coords[0]
                
                path = c.beginPath()
                first = True
                label_x, label_y = 0, 0
                
                for coord in exterior:
                    lon, lat = coord[0], coord[1]
                    pdf_x, pdf_y = self._gps_to_pdf(lat, lon)
                    
                    if first:
                        path.moveTo(pdf_x, pdf_y)
                        label_x, label_y = pdf_x, pdf_y
                        first = False
                    else:
                        path.lineTo(pdf_x, pdf_y)
                
                path.close()
                
                # Contour magenta
                c.setStrokeColor(colors.HexColor('#FF00FF'))
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
        except Exception as e:
            print(f"[PLAN] Erreur dessin GeoJSON: {e}")
    
    def _draw_batiment_at_gps(self, c):
        """Dessine le bâtiment à sa position GPS"""
        lat = self.data.get('latitude')
        lon = self.data.get('longitude')
        
        if not lat or not lon:
            return
        
        # Position centrale
        pdf_x, pdf_y = self._gps_to_pdf(lat, lon)
        
        # Dimensions bâtiment
        try:
            longueur_m = float(self.data.get('longueur_batiment_m', 15))
            largeur_m = float(self.data.get('largeur_batiment_m', 10))
        except:
            longueur_m, largeur_m = 15, 10
        
        # Conversion mètres → PDF
        proj = self.projection
        bat_w = longueur_m / proj['meters_per_pixel_x']
        bat_h = largeur_m / proj['meters_per_pixel_y']
        
        bat_x = pdf_x - bat_w / 2
        bat_y = pdf_y - bat_h / 2
        
        # Rectangle bâtiment
        c.setStrokeColor(colors.HexColor('#FF6B35'))
        c.setFillColor(colors.HexColor('#FFA07A'))
        c.setLineWidth(2.5)
        c.rect(bat_x, bat_y, bat_w, bat_h, fill=1, stroke=1)
        
        # Label
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(pdf_x, pdf_y, "BÂTIMENT")
    
    def _draw_modules_from_calpinage(self, c):
        """Dessine les modules PV depuis les coordonnées GPS du calpinage"""
        if not self.calpinage or 'zones' not in self.calpinage:
            return
        
        # Dimensions module
        try:
            mod_l = float(self.calpinage.get('module', {}).get('longueur', 2278)) / 1000
            mod_w = float(self.calpinage.get('module', {}).get('largeur', 1134)) / 1000
        except:
            mod_l, mod_w = 2.278, 1.134
        
        proj = self.projection
        
        for zone in self.calpinage['zones']:
            coordinates = zone.get('coordinates', [])
            nb_modules = zone.get('nbModules', 0)
            nb_cols = zone.get('nbCols', 1)
            nb_rows = zone.get('nbRows', 1)
            orientation = zone.get('moduleOrientation', 'paysage')
            
            if not coordinates or len(coordinates) < 3:
                continue
            
            # Dessiner contour zone
            path = c.beginPath()
            first = True
            zone_points = []
            
            for coord in coordinates:
                lat, lon = coord.get('lat'), coord.get('lng')
                if lat and lon:
                    pdf_x, pdf_y = self._gps_to_pdf(lat, lon)
                    zone_points.append((pdf_x, pdf_y))
                    
                    if first:
                        path.moveTo(pdf_x, pdf_y)
                        first = False
                    else:
                        path.lineTo(pdf_x, pdf_y)
            
            if zone_points:
                path.close()
                
                # Contour rouge
                c.setStrokeColor(colors.HexColor('#D32F2F'))
                c.setLineWidth(2)
                c.setDash(4, 2)
                c.drawPath(path, stroke=1, fill=0)
                c.setDash()
                
                # Remplir avec modules
                self._fill_zone_with_modules(c, zone_points, nb_cols, nb_rows, 
                                             mod_l, mod_w, orientation)
                
                # Étiquette
                c.setFillColor(colors.HexColor('#D32F2F'))
                c.setFont("Helvetica-Bold", 8)
                c.drawString(zone_points[0][0], zone_points[0][1] + 0.5*cm,
                            f"Zone PV: {nb_modules} modules ({nb_cols}×{nb_rows})")
    
    def _fill_zone_with_modules(self, c, zone_points, nb_cols, nb_rows, 
                                mod_l, mod_w, orientation):
        """Remplit une zone avec les modules"""
        if not zone_points:
            return
        
        # Point de départ (premier coin)
        start_x, start_y = zone_points[0]
        
        # Dimensions module selon orientation
        if orientation == 'paysage':
            mod_w_m, mod_h_m = mod_l, mod_w  # 2.28×1.13
        else:
            mod_w_m, mod_h_m = mod_w, mod_l  # 1.13×2.28
        
        proj = self.projection
        mod_w_pdf = mod_w_m / proj['meters_per_pixel_x']
        mod_h_pdf = mod_h_m / proj['meters_per_pixel_y']
        
        # Dessiner grille de modules (échantillonné pour performance)
        sample = max(1, int(nb_cols * nb_rows / 100))  # Max 100 modules affichés
        
        c.setFillColor(colors.HexColor('#2196F3'))
        c.setStrokeColor(colors.HexColor('#1565C0'))
        c.setLineWidth(0.5)
        
        for row in range(0, nb_rows, sample):
            for col in range(0, nb_cols, sample):
                mod_x = start_x + col * (mod_w_pdf + 0.02/proj['meters_per_pixel_x'])
                mod_y = start_y + row * (mod_h_pdf + 0.02/proj['meters_per_pixel_y'])
                
                c.rect(mod_x, mod_y, mod_w_pdf, mod_h_pdf, fill=1, stroke=1)
    
    def _draw_measurements(self, c):
        """Dessine les cotations du bâtiment"""
        lat = self.data.get('latitude')
        lon = self.data.get('longitude')
        
        if not lat or not lon:
            return
        
        pdf_x, pdf_y = self._gps_to_pdf(lat, lon)
        
        try:
            longueur = float(self.data.get('longueur_batiment_m', 15))
            largeur = float(self.data.get('largeur_batiment_m', 10))
        except:
            longueur, largeur = 15, 10
        
        proj = self.projection
        bat_w = longueur / proj['meters_per_pixel_x']
        bat_h = largeur / proj['meters_per_pixel_y']
        
        c.setStrokeColor(colors.HexColor('#D32F2F'))
        c.setFillColor(colors.HexColor('#D32F2F'))
        c.setFont("Helvetica-Bold", 9)
        c.setLineWidth(1.5)
        
        # Cotation longueur
        cote_y = pdf_y - bat_h/2 - 1*cm
        c.line(pdf_x - bat_w/2, cote_y, pdf_x + bat_w/2, cote_y)
        c.line(pdf_x - bat_w/2, cote_y - 0.2*cm, pdf_x - bat_w/2, cote_y + 0.2*cm)
        c.line(pdf_x + bat_w/2, cote_y - 0.2*cm, pdf_x + bat_w/2, cote_y + 0.2*cm)
        c.drawCentredString(pdf_x, cote_y - 0.6*cm, f"{longueur:.2f} m")
        
        # Cotation largeur
        cote_x = pdf_x + bat_w/2 + 1*cm
        c.line(cote_x, pdf_y - bat_h/2, cote_x, pdf_y + bat_h/2)
        c.line(cote_x - 0.2*cm, pdf_y - bat_h/2, cote_x + 0.2*cm, pdf_y - bat_h/2)
        c.line(cote_x - 0.2*cm, pdf_y + bat_h/2, cote_x + 0.2*cm, pdf_y + bat_h/2)
        
        c.saveState()
        c.translate(cote_x + 0.6*cm, pdf_y)
        c.rotate(90)
        c.drawCentredString(0, 0, f"{largeur:.2f} m")
        c.restoreState()
    
    def _draw_legend(self, c):
        """Dessine la légende"""
        x = 3*cm
        y = 6*cm
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, "LÉGENDE:")
        
        y -= 0.5*cm
        
        # Parcelle
        c.setStrokeColor(colors.HexColor('#FF00FF'))
        c.setLineWidth(3)
        c.setDash(8, 4)
        c.line(x, y, x + 1*cm, y)
        c.setDash()
        c.setFont("Helvetica", 9)
        c.drawString(x + 1.3*cm, y - 0.15*cm, "Limites parcelles cadastrales")
        
        y -= 0.5*cm
        
        # Bâtiment
        c.setFillColor(colors.HexColor('#FFA07A'))
        c.rect(x, y - 0.3*cm, 1*cm, 0.4*cm, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.drawString(x + 1.3*cm, y - 0.15*cm, "Bâtiment existant")
        
        y -= 0.5*cm
        
        # Modules
        c.setFillColor(colors.HexColor('#2196F3'))
        c.rect(x, y - 0.3*cm, 1*cm, 0.4*cm, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.drawString(x + 1.3*cm, y - 0.15*cm, "Modules photovoltaïques")
        
        y -= 0.5*cm
        
        # Zone PV
        c.setStrokeColor(colors.HexColor('#D32F2F'))
        c.setLineWidth(2)
        c.setDash(4, 2)
        c.line(x, y, x + 1*cm, y)
        c.setDash()
        c.setFillColor(colors.black)
        c.drawString(x + 1.3*cm, y - 0.15*cm, "Contour zone PV")
    
    def _draw_cartouche(self, c):
        """Cartouche technique"""
        x = self.width - 10*cm
        y = 4*cm
        w = 8*cm
        h = 3*cm
        
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(x, y, w, h)
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x + 0.3*cm, y + h - 0.6*cm, "CARACTÉRISTIQUES TECHNIQUES")
        
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
    generator = PlanMasseGeneratorV2(prospect_data, calpinage_data)
    return generator.generate()
